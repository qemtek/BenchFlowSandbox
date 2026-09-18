#!/usr/bin/env python3
"""Capture the provider side of a rollout while running on a Claude subscription.

BenchFlow writes `trajectory/llm_trajectory.jsonl` — the request and response of
every model call — by routing agents through its LiteLLM proxy. That proxy
authenticates upstream with an API key, so BenchFlow skips it for subscription
auth ("native-subscription auth (no API key to proxy)"), and the file is never
written. What is lost with it: the exact context window per turn, per-call token
usage, provider failures, and the dated snapshot that actually answered.

This is the missing proxy for that case. It speaks Anthropic's wire protocol,
forwards verbatim to api.anthropic.com, and writes the same record BenchFlow
would have. Claude Code honours ANTHROPIC_BASE_URL with subscription auth, which
is the fact the whole thing rests on.

It also closes an exposure that predates it. Today the subscription token is
injected into the sandbox so the agent can authenticate; an agent with
`network_mode: public` could carry it out. Run this with `--inject`, and the
token stays on the host: the sandbox gets a per-run secret, the proxy checks it,
strips it, and attaches the real credential on the way upstream — the same
property BenchFlow's own proxy has, where "the raw provider key never reaches
the agent".

    python tools/capture_proxy.py --out jobs/<run>/capture.jsonl \\
        --secret "$RUN_SECRET" --inject

Deliberate limits, because this listens on a port a sandbox can reach:

  * upstream is hardcoded — a client cannot redirect it, so the sandbox cannot
    use this as a pivot to anywhere else
  * only POST to /v1/messages* is proxied; everything else is refused
  * with --secret, a request that does not present it is refused before any
    upstream call, so the port is useless to anything without the run secret
  * credentials are never written to the capture, and never logged
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import pathlib
import sys
import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM_HOST = "api.anthropic.com"
ALLOWED_PREFIX = "/v1/messages"
# Headers describing this hop rather than the request itself.
HOP_HEADERS = {"host", "content-length", "accept-encoding", "connection"}
AUTH_HEADERS = {"authorization", "x-api-key"}

_write_lock = threading.Lock()


def _iso(when: datetime) -> str:
    return when.astimezone(UTC).isoformat()


def assemble_sse(raw: bytes) -> dict:
    """Rebuild the final Anthropic message from a streamed response.

    Claude Code always streams, so the wire carries deltas rather than a
    message. BenchFlow's consumers expect a whole response body, so the stream
    is folded back into one: text blocks concatenated, tool_use arguments
    reassembled from their partial JSON, usage merged from the start and end
    events.
    """
    message: dict = {}
    blocks: list[dict] = []
    partial: dict[int, list[str]] = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        if not line.startswith("data:"):
            continue
        try:
            event = json.loads(line[5:].strip())
        except ValueError:
            continue
        kind = event.get("type")
        if kind == "message_start":
            message = dict(event.get("message") or {})
            blocks = list(message.get("content") or [])
        elif kind == "content_block_start":
            idx = event.get("index", len(blocks))
            block = dict(event.get("content_block") or {})
            while len(blocks) <= idx:
                blocks.append({})
            blocks[idx] = block
            partial[idx] = []
        elif kind == "content_block_delta":
            idx = event.get("index", 0)
            delta = event.get("delta") or {}
            if idx >= len(blocks):
                continue
            if delta.get("type") == "text_delta":
                blocks[idx]["text"] = (blocks[idx].get("text") or "") + delta.get("text", "")
            elif delta.get("type") == "thinking_delta":
                blocks[idx]["thinking"] = (
                    blocks[idx].get("thinking") or "") + delta.get("thinking", "")
            elif delta.get("type") == "input_json_delta":
                partial.setdefault(idx, []).append(delta.get("partial_json", ""))
        elif kind == "content_block_stop":
            idx = event.get("index", 0)
            chunks = partial.pop(idx, None)
            if chunks and idx < len(blocks):
                try:
                    blocks[idx]["input"] = json.loads("".join(chunks) or "{}")
                except ValueError:
                    # Keep the raw text rather than dropping the call: a
                    # truncated stream is evidence too.
                    blocks[idx]["input_raw"] = "".join(chunks)
        elif kind == "message_delta":
            message.update(
                {k: v for k, v in (event.get("delta") or {}).items() if v is not None})
            usage = event.get("usage")
            if isinstance(usage, dict):
                message["usage"] = {**(message.get("usage") or {}), **usage}
    if message:
        message["content"] = blocks
    return message


def openai_shaped_request(body: dict) -> dict:
    """Anthropic request body, adjusted so BenchFlow's readers understand it.

    Two differences matter downstream. Anthropic carries the system prompt
    beside the messages rather than as one, and describes a tool with
    `input_schema` where the trainer-export path reads `parameters`. Everything
    else is passed through untouched, and the unmodified body is kept alongside
    in the raw sidecar.
    """
    out = dict(body)
    messages = list(out.get("messages") or [])
    system = out.get("system")
    if system:
        text = system if isinstance(system, str) else "\n".join(
            part.get("text", "") for part in system if isinstance(part, dict))
        messages = [{"role": "system", "content": text}, *messages]
    out["messages"] = messages
    tools = out.get("tools")
    if isinstance(tools, list):
        out["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema")
                    or tool.get("parameters")
                    or {"type": "object", "properties": {}},
                },
            }
            if isinstance(tool, dict) and "function" not in tool else tool
            for tool in tools
        ]
    return out


class CaptureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    # Set by main().
    out_path: pathlib.Path
    raw_path: pathlib.Path
    secret: str | None
    upstream_token: str | None

    def _refuse(self, code: int, reason: str) -> None:
        payload = json.dumps({"error": {"type": "proxy_refused", "message": reason}})
        body = payload.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler's spelling
        if not self.path.startswith(ALLOWED_PREFIX):
            self._refuse(404, f"only {ALLOWED_PREFIX} is proxied")
            return
        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length)
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in HOP_HEADERS}

        if self.secret:
            presented = (self.headers.get("authorization") or "").removeprefix("Bearer ")
            if presented.strip() != self.secret:
                self._refuse(403, "missing or wrong run secret")
                return
        if self.upstream_token:
            # The sandbox never held the real credential; attach it here.
            for key in list(headers):
                if key.lower() in AUTH_HEADERS:
                    headers.pop(key)
            headers["Authorization"] = f"Bearer {self.upstream_token}"

        started = datetime.now(UTC)
        try:
            conn = http.client.HTTPSConnection(UPSTREAM_HOST, timeout=900)
            conn.request("POST", self.path, body=body,
                         headers={**headers, "Host": UPSTREAM_HOST})
            upstream = conn.getresponse()
        except OSError as exc:
            self._refuse(502, f"upstream unreachable: {exc}")
            return

        self.send_response(upstream.status)
        for key, value in upstream.getheaders():
            if key.lower() not in ("transfer-encoding", "connection", "content-length"):
                self.send_header(key, value)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        # Relay unbuffered: the agent is streaming, and holding chunks back
        # would change its behaviour as well as its timing.
        collected: list[bytes] = []
        while True:
            chunk = upstream.read(8192)
            if not chunk:
                break
            collected.append(chunk)
            self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
            self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()
        conn.close()
        ended = datetime.now(UTC)
        self._record(body, b"".join(collected), upstream.status, started, ended)

    def _record(self, request_bytes: bytes, response_bytes: bytes, status: int,
                started: datetime, ended: datetime) -> None:
        try:
            request_body = json.loads(request_bytes or b"{}")
        except ValueError:
            request_body = {"unparsed": request_bytes[:2000].decode("utf-8", "replace")}
        text = response_bytes.decode("utf-8", "replace")
        if text.lstrip().startswith("{"):
            try:
                response_body = json.loads(text)
            except ValueError:
                response_body = {"raw": text[:4000]}
        else:
            response_body = assemble_sse(response_bytes)

        usage = response_body.get("usage") if isinstance(response_body, dict) else None
        record = {
            "event": "success" if 200 <= status < 300 else "failure",
            "status_code": status,
            "request_model": request_body.get("model"),
            "provider_model": (response_body or {}).get("model"),
            "call_type": "anthropic_messages",
            "input_shape": {
                "has_messages": bool(request_body.get("messages")),
                "has_input": False,
                "n_messages": len(request_body.get("messages") or []),
            },
            "request": {
                "method": "POST",
                "path": self.path,
                "body": openai_shaped_request(request_body),
            },
            # status_code belongs inside `response`, matching BenchFlow's
            # LLMResponse shape: the trainer export treats an exchange as
            # successful only when `response.status_code` is 200, and reads the
            # assistant turn out of `response.body`.
            "response": {"status_code": status, "body": response_body},
            "usage": usage,
            # Left null deliberately: no price source is attached to a
            # subscription call, and a fabricated 0.0 reads as "free".
            "response_cost": None,
            "start_time": _iso(started),
            "end_time": _iso(ended),
            "duration_ms": (ended - started).total_seconds() * 1000,
            "capture": {"source": "tools/capture_proxy.py"},
        }
        raw = {
            "start_time": _iso(started),
            "path": self.path,
            "request_body": request_body,
            "response_text": text,
        }
        with _write_lock:
            with self.out_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            with self.raw_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(raw) + "\n")

    def log_message(self, *args) -> None:  # noqa: D102 — silence per-request noise
        pass


def _prompt_key(rollout_dir: pathlib.Path) -> str | None:
    """A string from this rollout's prompt that no other task's prompt contains.

    Every task shares the same briefing preamble, so the opening lines identify
    nothing. The case notes do: they name a customer and a situation drawn from
    one tau2 case. That text is echoed verbatim in the request body of every
    call the agent makes about that task, which makes it the attribution key.
    """
    prompts_file = rollout_dir / "prompts.json"
    if not prompts_file.is_file():
        return None
    try:
        prompts = json.loads(prompts_file.read_text())
    except ValueError:
        return None
    text = prompts if isinstance(prompts, str) else " ".join(
        p for p in prompts if isinstance(p, str))
    start = text.find("<case_notes>")
    if start < 0:
        return None
    start += len("<case_notes>")
    end = text.find("</case_notes>", start)
    # The whole block, not a prefix of it. task-045 and task-046 share their
    # opening verbatim and diverge partway through one utterance, so any fixed
    # prefix maps both onto the same key while the full block separates them.
    key = " ".join(text[start:end if end > 0 else len(text)].split())
    return key or None


def _request_text(row: dict) -> str:
    """Every piece of message text in one captured request, whitespace-normalised."""
    body = ((row.get("request") or {}).get("body")) or {}
    parts: list[str] = []
    for message in body.get("messages") or []:
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    parts.append(str(block.get("text") or ""))
    return " ".join(" ".join(parts).split())


def _as_aware(value: object) -> datetime:
    """Parse a timestamp, reading a naive one as the host's local time."""
    parsed = datetime.fromisoformat(str(value))
    return parsed.astimezone() if parsed.tzinfo is None else parsed


def _within_window(row: dict, rollout_dir: pathlib.Path) -> bool:
    """Fallback attribution: did this call happen during that rollout?"""
    result_file = rollout_dir / "result.json"
    if not result_file.is_file():
        return False
    try:
        result = json.loads(result_file.read_text())
        # BenchFlow writes these naive, in the host's local time, while the
        # proxy stamps each call in UTC. Reading the naive values as UTC put
        # every window an hour out under BST and silently produced no match at
        # all. `astimezone()` on a naive datetime reads it as local, which is
        # what it is.
        started = _as_aware(result["started_at"])
        finished = _as_aware(result["finished_at"])
        when = datetime.fromisoformat(row["start_time"])
    except (ValueError, KeyError, TypeError):
        return False
    return started <= when <= finished


def attribute(capture_path: pathlib.Path, job_dir: pathlib.Path) -> int:
    """Split one run's capture into each rollout's `trajectory/llm_trajectory.jsonl`.

    The proxy sees one stream of calls for the whole run and no rollout ids —
    Claude Code has no reason to send one. Calls are matched to rollouts by the
    case notes echoed in the request, which works at any concurrency; the time
    window is only a fallback, and only when exactly one rollout was running.
    """
    rows = [json.loads(line) for line in
            capture_path.read_text().splitlines() if line.strip()]
    raw_path = capture_path.with_name(capture_path.stem + "-raw" + capture_path.suffix)
    raw_rows = ([json.loads(line) for line in
                 raw_path.read_text().splitlines() if line.strip()]
                if raw_path.is_file() else [])

    rollouts = sorted({p.parent for p in job_dir.rglob("result.json")})
    keys = {r: _prompt_key(r) for r in rollouts}
    assigned: dict[pathlib.Path, list[int]] = {r: [] for r in rollouts}
    unmatched = 0

    for index, row in enumerate(rows):
        text = _request_text(row)
        hits = [r for r in rollouts if keys[r] and keys[r] in text]
        if len(hits) > 1:
            # A repeated arm (`--trials N`) runs every task N times, so the
            # case notes no longer identify one rollout: the same block is
            # echoed by each repeat. Content narrows the call to one task and
            # the clock picks the repeat, which is sound because BenchFlow runs
            # trials in sequence — their windows do not overlap.
            hits = [r for r in hits if _within_window(row, r)]
        if len(hits) != 1:
            windowed = [r for r in rollouts if _within_window(row, r)]
            hits = windowed if len(windowed) == 1 else []
        if len(hits) == 1:
            assigned[hits[0]].append(index)
        else:
            unmatched += 1

    for rollout_dir, indices in assigned.items():
        if not indices:
            continue
        target = rollout_dir / "trajectory"
        target.mkdir(parents=True, exist_ok=True)
        (target / "llm_trajectory.jsonl").write_text(
            "".join(json.dumps(rows[i]) + "\n" for i in indices))
        if raw_rows:
            (target / "anthropic_raw.jsonl").write_text(
                "".join(json.dumps(raw_rows[i]) + "\n"
                        for i in indices if i < len(raw_rows)))

    placed = sum(len(v) for v in assigned.values())
    covered = sum(1 for v in assigned.values() if v)
    print(f"capture: {placed}/{len(rows)} calls attributed across "
          f"{covered}/{len(rollouts)} rollouts"
          + (f"; {unmatched} unattributed" if unmatched else ""))
    return 0


def read_credential(name: str) -> str | None:
    """The subscription token, from the environment or the repo's `.env`.

    Read here rather than passed in, so the credential never travels through a
    shell command or an argument list. BenchFlow loads `.env` the same way.
    """
    value = os.environ.get(name)
    if value:
        return value.strip()
    env_file = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not env_file.is_file():
        return None
    for line in env_file.read_text().splitlines():
        key, _, raw = line.partition("=")
        if key.strip() == name:
            return raw.strip().strip("'\"") or None
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="capture JSONL path")
    ap.add_argument("--bind", default="0.0.0.0",
                    help="interface to listen on; the sandbox reaches the host "
                         "via host.docker.internal, which loopback cannot serve")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--secret", default="",
                    help="reject requests not presenting this bearer token")
    ap.add_argument("--inject", action="store_true",
                    help="attach the host's subscription token upstream, so the "
                         "sandbox never holds it")
    ap.add_argument("--token-env", default="CLAUDE_CODE_OAUTH_TOKEN")
    ap.add_argument("--attribute", metavar="JOB_DIR",
                    help="do not serve: split an existing capture into each "
                         "rollout's trajectory/llm_trajectory.jsonl")
    args = ap.parse_args()

    if args.attribute:
        return attribute(pathlib.Path(args.out), pathlib.Path(args.attribute))

    token = None
    if args.inject:
        token = read_credential(args.token_env)
        if not token:
            print(f"--inject needs {args.token_env} in the environment or .env",
                  file=sys.stderr)
            return 1

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    CaptureHandler.out_path = out_path
    CaptureHandler.raw_path = out_path.with_name(
        out_path.stem + "-raw" + out_path.suffix)
    CaptureHandler.secret = args.secret or None
    CaptureHandler.upstream_token = token

    server = ThreadingHTTPServer((args.bind, args.port), CaptureHandler)
    print(f"capture proxy on {args.bind}:{args.port} → {UPSTREAM_HOST}"
          f"{' (injecting host credential)' if token else ''}"
          f"{' (run secret required)' if args.secret else ''}", file=sys.stderr,
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
