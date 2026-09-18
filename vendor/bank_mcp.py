#!/usr/bin/env python3
"""MCP server exposing the bank's operations as structured tools.

This is the agent's only interface to the bank. It advertises the 14-tool core
toolkit with each tool's real JSON schema, plus three tools that reach the 44
specialised operations:

    bank_search              find an operation by describing what you want
    bank_describe_operation  read its signature: arguments, types, defaults
    bank_call_operation      run it, passing arguments as an object

It replaced a shell CLI that made the agent compose JSON inside shell quoting.
No deployed agent works that way — it calls a tool against a schema.

bank_cli.py is still imported here for the dispatcher, session state, autounlock
and toolset filtering, but it is no longer an interface and is not on PATH.

Speaks MCP over stdio using JSON-RPC 2.0 — stdlib only, no SDK.
"""

from __future__ import annotations

import inspect
import json
import math
import os
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

VENDOR = Path(__file__).resolve().parent
sys.path.insert(0, str(VENDOR))

import bank_cli  # noqa: E402  (reuse the dispatcher, session and toolset logic)

PROTOCOL_VERSION = "2024-11-05"
KB_DEFAULT_LIMIT = 8
KB_MAX_LIMIT = 10
KB_SNIPPET_CHARS = 260
KB_MAX_DOCUMENT_BYTES = 8192
KB_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "customer",
    "for", "from", "how", "i", "in", "is", "it", "of", "on", "or",
    "the", "their", "this", "to", "user", "want", "wants", "with",
}


def _core_tools() -> list[dict]:
    """The always-available toolkit, as MCP tool definitions."""
    tk = bank_cli._toolkit(bank_cli._load(), "assistant")
    out = []
    for name, tool in sorted(tk.get_tools().items()):
        fn = (getattr(tool, "openai_schema", None) or {}).get("function", {})
        out.append(
            {
                "name": name,
                "description": (getattr(tool, "short_desc", "") or "").strip(),
                "inputSchema": fn.get("parameters")
                or {"type": "object", "properties": {}},
            }
        )
    return out


def _search_tool() -> dict:
    return {
        "name": "bank_search",
        "description": (
            "Find a bank operation by what it does. The bank runs many more "
            "operations than are listed here; search returns matching names and "
            "descriptions. Finding an operation does not tell you how to use it "
            "correctly — use kb_search and kb_get for eligibility rules, fees "
            "and policy."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What you need to do"}
            },
            "required": ["query"],
        },
    }


def _kb_search_tool() -> dict:
    return {
        "name": "kb_search",
        "description": (
            "Search Rho-Bank's internal policy and procedure knowledge base. "
            "Returns a bounded ranked list of document IDs, titles and short "
            "snippets; it never returns full documents. Use kb_get on only "
            "the relevant result."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific policy, procedure, product or reason code to find",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results, from 1 to 10 (default 8)",
                    "default": KB_DEFAULT_LIMIT,
                    "minimum": 1,
                    "maximum": KB_MAX_LIMIT,
                },
            },
            "required": ["query"],
        },
    }


def _kb_get_tool() -> dict:
    return {
        "name": "kb_get",
        "description": (
            "Read one internal policy document selected from kb_search. "
            "Takes an exact document ID and returns only that document."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "Exact document ID returned by kb_search",
                }
            },
            "required": ["document_id"],
        },
    }


def _call_discovered_tool() -> dict:
    return {
        "name": "bank_call_operation",
        "description": (
            "Run one of the specialised operations found with bank_search. "
            "Check bank_describe_operation first for its arguments. "
            "Arguments are passed as a plain object, not a string."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "description": "Operation name"},
                "arguments": {
                    "type": "object",
                    "description": "Arguments for the operation",
                },
            },
            "required": ["operation"],
        },
    }


def _describe_tool() -> dict:
    return {
        "name": "bank_describe_operation",
        "description": (
            "Show the full signature of an operation found with bank_search: "
            "its documentation, every argument with its type, which arguments "
            "are required, and any defaults. Call this before "
            "bank_call_operation — search returns names, not signatures."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "description": "Operation name"}
            },
            "required": ["operation"],
        },
    }


def _type_name(ann) -> str:
    """Readable name for a signature annotation."""
    return getattr(ann, "__name__", None) or str(ann).replace("typing.", "")


def _run_describe(operation: str) -> str:
    """Mirror `bank <operation> --help` over MCP.

    The 14 core tools ship an ``openai_schema``, so their MCP ``inputSchema``
    already carries descriptions, enums and defaults. The 44 discoverable
    operations do not: their shape lives in the Python signature, which
    ``bank_search`` reduced to a list of argument names. The CLI exposed the
    rest through ``--help``; without an equivalent here the MCP agent was
    working blind on exactly the operations the benchmark is about.
    """
    tk = bank_cli._toolkit(bank_cli._load(), "assistant")
    spec = bank_cli._spec_for(tk, operation)
    if spec is None:
        return (f"No operation named {operation!r}. "
                "Use bank_search to find one.")
    kind, params, required, doc = spec
    lines = [f"{operation}", ""]
    if doc:
        lines += [doc.strip(), ""]
    if not params:
        lines.append("Takes no arguments.")
        return "\n".join(lines)

    lines.append("Arguments:")
    if kind == "core":
        # params is a JSON-schema properties block.
        for name, pschema in params.items():
            bits = [pschema.get("type", "string")]
            if name in required:
                bits.append("required")
            if pschema.get("default") is not None:
                bits.append(f"default: {pschema['default']}")
            if pschema.get("enum"):
                bits.append("one of: " + ", ".join(map(str, pschema["enum"])))
            lines.append(f"  {name} ({'; '.join(bits)})")
            if pschema.get("description"):
                lines.append(f"      {pschema['description']}")
    else:
        # params maps argument name -> signature annotation.
        import inspect
        sig = inspect.signature(
            getattr(tk, "_tk", tk).get_discoverable_tools()[operation])
        for name, ann in params.items():
            bits = [_type_name(ann)]
            if name in required:
                bits.append("required")
            else:
                dflt = sig.parameters[name].default
                if dflt is not inspect._empty:
                    bits.append(f"default: {dflt!r}")
            lines.append(f"  {name} ({'; '.join(bits)})")
    return "\n".join(lines)


def list_tools() -> list[dict]:
    return _core_tools() + [
        _kb_search_tool(),
        _kb_get_tool(),
        _search_tool(),
        _describe_tool(),
        _call_discovered_tool(),
    ]


def _kb_root() -> Path:
    configured = os.environ.get("BANK_KB_DIR")
    if configured:
        return Path(configured)
    container_path = Path("/opt/bank/knowledge")
    if container_path.is_dir():
        return container_path
    return VENDOR.parent / "data" / "banking_knowledge" / "documents"


def _tokens(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in KB_STOPWORDS
    ]


@lru_cache(maxsize=1)
def _kb_index() -> tuple[list[dict], dict[str, float], float]:
    root = _kb_root()
    documents = []
    document_frequency: Counter[str] = Counter()
    for path in sorted(root.glob("*.json")):
        try:
            raw = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        document_id = str(raw.get("id") or path.stem)
        title = str(raw.get("title") or document_id)
        content = str(raw.get("content") or "")
        title_tokens = _tokens(title)
        content_tokens = _tokens(content)
        searchable = title_tokens * 4 + content_tokens
        term_frequency = Counter(searchable)
        document_frequency.update(term_frequency.keys())
        documents.append({
            "id": document_id,
            "title": title,
            "content": content,
            "title_lower": title.lower(),
            "content_lower": content.lower(),
            "title_terms": set(title_tokens),
            "terms": term_frequency,
            "length": len(searchable),
        })
    count = max(len(documents), 1)
    inverse_document_frequency = {
        term: math.log(1 + (count - freq + 0.5) / (freq + 0.5))
        for term, freq in document_frequency.items()
    }
    average_length = (
        sum(document["length"] for document in documents) / count
    ) or 1.0
    return documents, inverse_document_frequency, average_length


def _snippet(content: str, query_terms: list[str]) -> str:
    collapsed = re.sub(r"\s+", " ", content).strip()
    lowered = collapsed.lower()
    positions = [lowered.find(term) for term in query_terms]
    center = next((position for position in positions if position >= 0), 0)
    start = max(0, center - KB_SNIPPET_CHARS // 3)
    end = min(len(collapsed), start + KB_SNIPPET_CHARS)
    prefix = "…" if start else ""
    suffix = "…" if end < len(collapsed) else ""
    return prefix + collapsed[start:end].strip() + suffix


def _run_kb_search(query: str, limit: int = KB_DEFAULT_LIMIT) -> str:
    query = (query or "").strip()
    query_terms = list(dict.fromkeys(_tokens(query)))
    if not query_terms:
        return "No searchable terms were provided. Use a specific policy or procedure."
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = KB_DEFAULT_LIMIT
    limit = max(1, min(limit, KB_MAX_LIMIT))

    documents, idf, average_length = _kb_index()
    phrase = re.sub(r"\s+", " ", query.lower()).strip()
    scored = []
    for document in documents:
        score = 0.0
        matched = 0
        title_matches = 0
        for term in query_terms:
            frequency = document["terms"].get(term, 0)
            if not frequency:
                continue
            matched += 1
            if term in document["title_terms"]:
                title_matches += 1
            denominator = frequency + 1.2 * (
                0.25 + 0.75 * document["length"] / average_length
            )
            score += idf.get(term, 0.0) * frequency * 2.2 / denominator
        if not matched:
            continue
        if phrase and phrase in document["title_lower"]:
            score += 8.0
        elif phrase and phrase in document["content_lower"]:
            score += 3.0
        score += 2.0 * matched / len(query_terms)
        scored.append((score, matched, title_matches, document))

    hits = sorted(
        scored,
        key=lambda item: (-item[1], -item[2], -item[0], item[3]["id"]),
    )[:limit]
    if not hits:
        return f"No knowledge-base documents match {query!r}."

    lines = [f"{len(hits)} document(s) matching {query!r}:"]
    for _, _, _, document in hits:
        lines.append(
            f"\n[{document['id']}] {document['title']}\n"
            f"  {_snippet(document['content'], query_terms)}"
        )
    lines.append("\nUse kb_get with one exact document ID to read it.")
    return "\n".join(lines)


def _run_kb_get(document_id: str) -> str:
    document_id = (document_id or "").strip()
    documents, _, _ = _kb_index()
    match = next((doc for doc in documents if doc["id"] == document_id), None)
    if match is None:
        return f"No knowledge-base document has ID {document_id!r}. Use kb_search first."
    header = f"# {match['title']}\n\nDocument ID: {match['id']}\n\n"
    content = match["content"]
    marker = "\n\n[Document truncated to the 8 KiB response limit.]"
    available = KB_MAX_DOCUMENT_BYTES - len(header.encode())
    encoded = content.encode()
    if len(encoded) > available:
        available -= len(marker.encode())
        content = encoded[:available].decode(errors="ignore") + marker
    return header + content


def _run_search(query: str) -> str:
    tk = bank_cli._toolkit(bank_cli._load(), "assistant")
    inner = getattr(tk, "_tk", tk)
    terms = [t for t in query.lower().split() if t]
    catalogue = {
        n: (getattr(t, "short_desc", "") or "").strip()
        for n, t in tk.get_tools().items()
    }
    for n, f in inner.get_discoverable_tools().items():
        catalogue[n] = (f.__doc__ or "").strip().split("\n")[0]

    scored = []
    for name, desc in catalogue.items():
        hay = f"{name} {desc}".lower().replace("_", " ")
        s = sum(1 for t in terms if t in hay)
        if s:
            scored.append((s, name, desc))
    full = [h for h in scored if h[0] == len(terms)]
    hits = sorted(full or scored, key=lambda h: (-h[0], h[1]))[:15]
    if not hits:
        return f"No operations match {query!r}."
    lines = [f"{len(hits)} operation(s) matching {query!r}:"]
    for _, name, desc in hits:
        params = ""
        disc = inner.get_discoverable_tools()
        if name in disc:
            keys = [p for p in inspect.signature(disc[name]).parameters if p != "self"]
            params = f"  (arguments: {', '.join(keys)})"
        lines.append(f"  {name}{params}\n      {desc[:140]}")
    lines.append("\nUse kb_search and kb_get for the procedure before acting.")
    return "\n".join(lines)


def call_tool(name: str, arguments: dict) -> str:
    db = bank_cli._load()
    tk = bank_cli._toolkit(db, "assistant")

    if name == "bank_search":
        return _run_search(arguments.get("query", ""))

    if name == "kb_search":
        return _run_kb_search(
            arguments.get("query", ""),
            arguments.get("limit", KB_DEFAULT_LIMIT),
        )

    if name == "kb_get":
        return _run_kb_get(arguments.get("document_id", ""))

    if name == "bank_describe_operation":
        return _run_describe(arguments.get("operation", ""))

    if name == "bank_call_operation":
        # The whole point of the MCP surface: take arguments as an object and do
        # the JSON-string packing the underlying tool expects ourselves.
        op = arguments.get("operation", "")
        inner_args = arguments.get("arguments") or {}
        payload = {
            "agent_tool_name": op,
            "arguments": json.dumps(inner_args),
        }
        bank_cli._autounlock(tk, "call_discoverable_agent_tool", payload)
        result = tk.use_tool("call_discoverable_agent_tool", **payload)
        bank_cli._save(db)
        bank_cli._save_session(tk)
        # Log in tau2's vocabulary, not MCP's: the action verifier matches the
        # gold action name, which is always call_discoverable_agent_tool with a
        # JSON-string `arguments`. Logging "bank_call_operation" here would make
        # every ACTION-scored task unpassable.
        bank_cli._log_call("assistant", "call_discoverable_agent_tool", payload)
        return result

    if not tk.has_tool(name):
        return f"Error: no such tool {name!r}."
    result = tk.use_tool(name, **arguments)
    bank_cli._save(db)
    bank_cli._save_session(tk)
    bank_cli._log_call("assistant", name, arguments)
    return result


def respond(rid, result=None, error=None) -> None:
    msg = {"jsonrpc": "2.0", "id": rid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method")
        rid = req.get("id")

        if method == "initialize":
            respond(rid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "bank", "version": "1.0"},
            })
        elif method == "notifications/initialized":
            continue  # notification: no response
        elif method == "tools/list":
            respond(rid, {"tools": list_tools()})
        elif method == "tools/call":
            params = req.get("params") or {}
            try:
                text = call_tool(params.get("name", ""), params.get("arguments") or {})
                respond(rid, {"content": [{"type": "text", "text": str(text)}]})
            except Exception as exc:
                # Surface domain errors as tool results, not protocol errors, so
                # the agent can read and recover from them.
                respond(rid, {
                    "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                    "isError": True,
                })
        elif rid is not None:
            respond(rid, error={"code": -32601, "message": f"unknown method {method}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
