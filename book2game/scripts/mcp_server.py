# -*- coding: utf-8 -*-
"""
mcp_server.py — Optional Model Context Protocol (MCP) server wrapper for book2game.
Provides JSON-RPC over stdio interface for tools like search_rag and parse_book
without adding any mandatory dependencies to the core package.
"""

import sys
import json
from pathlib import Path

# Ensure scripts/ or repo root is in sys.path
this_dir = Path(__file__).resolve().parent
if str(this_dir) not in sys.path:
    sys.path.insert(0, str(this_dir))

try:
    from query_rag import search_rag
    from parse_book import parse_book_pipeline
except ImportError:
    try:
        from scripts.query_rag import search_rag
        from scripts.parse_book import parse_book_pipeline
    except ImportError:
        search_rag = None
        parse_book_pipeline = None

def handle_tools_list() -> dict:
    return {
        "tools": [
            {
                "name": "query_rag",
                "description": "Lexical relevance search (BM25) across book chapters and full text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "game_dir": {"type": "string", "description": "Path to game project output directory."},
                        "query": {"type": "string", "description": "Search query terms."}
                    },
                    "required": ["game_dir", "query"]
                }
            },
            {
                "name": "book2game_search",
                "description": "Alias for query_rag: BM25 lexical relevance search.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "game_dir": {"type": "string", "description": "Path to game project output directory."},
                        "query": {"type": "string", "description": "Search query terms."}
                    },
                    "required": ["game_dir", "query"]
                }
            },
            {
                "name": "parse_book",
                "description": "Parse a book file (PDF, EPUB, DOCX, TXT) into Game Studio structured assets.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "book_path": {"type": "string", "description": "Path to input book file."},
                        "out_dir": {"type": "string", "description": "Output directory for generated assets."}
                    },
                    "required": ["book_path", "out_dir"]
                }
            }
        ]
    }

def handle_call_tool(params: dict) -> dict:
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name in ["query_rag", "book2game_search"]:
        game_dir = Path(arguments.get("game_dir", "."))
        query = arguments.get("query", "")
        if not search_rag:
            return {"content": [{"type": "text", "text": "Error: search_rag not available."}], "isError": True}
        results = search_rag(game_dir, query)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(results, ensure_ascii=False, indent=2)
                }
            ]
        }
    else:
        return {
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
            "isError": True
        }

def handle_request(req: dict) -> dict:
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "book2game-mcp", "version": "1.0.0"}
        }
    elif method == "tools/list":
        result = handle_tools_list()
    elif method == "tools/call":
        result = handle_call_tool(req.get("params", {}))
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result
    }

def run_stdio_server():
    """Runs the MCP server over standard input/output streams using JSON-RPC."""
    sys.stderr.write("[mcp_server] Starting book2game MCP stdio server...\n")
    sys.stderr.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_request(req)
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    run_stdio_server()
