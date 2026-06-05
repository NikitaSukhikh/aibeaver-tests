#!/usr/bin/env python3
"""Run a fixed-package MCD MCP server over Streamable HTTP.

This server intentionally binds tools to one MCD package path at startup so
remote clients cannot choose arbitrary local files through a `path` argument.
Expose it through a public HTTPS tunnel before using it with OpenAI remote MCP.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import mcd
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcd-path", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--name", default="MultiHiertt MCD Tools")
    parser.add_argument(
        "--allow-remote-hosts",
        action="store_true",
        help="Disable DNS rebinding host/origin checks for use behind an HTTPS tunnel.",
    )
    return parser.parse_args()


def create_server(mcd_path: Path, *, host: str, port: int, name: str, allow_remote_hosts: bool) -> FastMCP:
    package_path = mcd_path.resolve()
    if not package_path.is_file():
        raise FileNotFoundError(package_path)
    doc = mcd.open(package_path)

    security = TransportSecuritySettings(enable_dns_rebinding_protection=not allow_remote_hosts)
    server = FastMCP(
        name,
        host=host,
        port=port,
        streamable_http_path="/mcp",
        transport_security=security,
    )

    def open_doc() -> Any:
        return doc

    def compact_query_result(result: Any) -> dict[str, Any]:
        data = result.as_dict()
        columns = [str(column) for column in data.get("columns", [])]
        rows = data.get("rows", [])
        compact_rows = []
        for row in rows if isinstance(rows, list) else []:
            if isinstance(row, dict):
                compact_rows.append([row.get(column) for column in columns])
            else:
                compact_rows.append(row)
        return {
            "columns": columns,
            "rowCount": data.get("rowCount", len(compact_rows)),
            "rows": compact_rows,
        }

    def format_query_result(result: Any, output: str) -> dict[str, Any] | str:
        if output == "compact":
            return compact_query_result(result)
        if output == "dict":
            return result.as_dict()
        if output == "json":
            return result.to_json()
        if output == "csv":
            return result.to_csv()
        if output == "table":
            return result.to_table()
        raise ValueError("output must be one of: compact, dict, json, csv, table")

    @server.tool(name="mcd_validate")
    def validate_package() -> dict[str, Any]:
        """Validate the fixed MCD package and return diagnostics."""
        return open_doc().validate().as_dict()

    @server.tool(name="mcd_agent_context")
    def agent_context(include_tables: bool = False, include_layout: bool = False) -> dict[str, Any]:
        """Return a compact machine-readable overview of the fixed MCD package."""
        return open_doc().to_agent_context(include_tables=include_tables, include_layout=include_layout)

    @server.tool(name="mcd_markdown")
    def markdown(expand_tables: bool = False) -> str:
        """Read package Markdown, optionally expanding table directives."""
        return open_doc().markdown(expand_tables=expand_tables)

    @server.tool(name="mcd_query")
    def query(sql: str, output: str = "compact") -> dict[str, Any] | str:
        """Run one read-only SQL query against package tables and metadata.

        Use output="compact" to return column names once plus array rows.
        """
        return format_query_result(open_doc().query(sql), output)

    @server.tool(name="mcd_query_batch")
    def query_batch(sql: list[str], output: str = "compact") -> dict[str, Any]:
        """Run multiple read-only SQL queries against the fixed package in one tool call.

        Use output="compact" to reduce repeated column-name payload.
        """
        if not sql:
            raise ValueError("sql must include at least one query")
        if len(sql) > 20:
            raise ValueError("sql may include at most 20 queries")
        return {
            "results": [
                {
                    "index": index,
                    "sql": query_text,
                    "result": format_query_result(open_doc().query(query_text), output),
                }
                for index, query_text in enumerate(sql)
            ],
            "count": len(sql),
        }

    @server.tool(name="mcd_search")
    def search(query: str, limit: int = 10, kind: str | None = None, page: str | None = None) -> dict[str, Any]:
        """Search package content and metadata with BM25."""
        if limit < 0:
            raise ValueError("limit must be non-negative")
        hits = open_doc().search(query, limit=limit, kind=kind, page=page)
        return {"hits": hits, "count": len(hits)}

    @server.tool(name="mcd_table")
    def table(table_id: str, include_rows: bool = True, typed_rows: bool = False, max_rows: int | None = 100) -> dict[str, Any]:
        """Return table schema and optionally rows from the fixed MCD package."""
        item = open_doc().table(table_id)
        data = item.as_dict()
        rows = item.typed_rows() if typed_rows else item.rows()
        data["rowCount"] = len(rows)
        if include_rows:
            if max_rows is not None and max_rows < 0:
                raise ValueError("max_rows must be non-negative or null")
            data["rows"] = rows if max_rows is None else rows[:max_rows]
            data["returnedRowCount"] = len(data["rows"])
        else:
            data.pop("rows", None)
        return data

    @server.tool(name="mcd_relationships")
    def relationships() -> dict[str, Any]:
        """Return table relationship metadata declared by the fixed MCD package."""
        items = open_doc().relationships()
        return {"relationships": items, "count": len(items)}

    @server.tool(name="mcd_annotations")
    def annotations() -> dict[str, Any]:
        """Return annotation metadata from the fixed MCD package."""
        items = [item.as_dict() for item in open_doc().annotations()]
        return {"annotations": items, "count": len(items)}

    @server.tool(name="mcd_provenance")
    def provenance() -> dict[str, Any]:
        """Return package provenance metadata, if present."""
        return {"provenance": open_doc().provenance()}

    return server


def main() -> int:
    args = parse_args()
    server = create_server(
        args.mcd_path,
        host=args.host,
        port=args.port,
        name=args.name,
        allow_remote_hosts=args.allow_remote_hosts,
    )
    server.run(transport="streamable-http")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
