#!/usr/bin/env python3
"""
TTA Knowledge MCP Server

Exposes tools to search the TTA.dev documentation.
"""

import os
import sys
import json
import glob
import subprocess

# Basic MCP Protocol Implementation (stdio)

def list_tools():
    return {
        "tools": [
            {
                "name": "search_docs",
                "description": "Search the TTA.dev documentation for a query string.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query."
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    }

def search_docs(query):
    # Simple grep search
    docs_dir = "docs"
    try:
        cmd = ["grep", "-r", "-i", query, docs_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        if len(output) > 2000:
            output = output[:2000] + "\n... (truncated)"
        return output if output else "No results found."
    except Exception as e:
        return f"Error searching docs: {e}"

def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    id = request.get("id")

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": id, "result": list_tools()}
    
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        
        if name == "search_docs":
            result = search_docs(args.get("query"))
            return {
                "jsonrpc": "2.0", 
                "id": id, 
                "result": {
                    "content": [{"type": "text", "text": result}]
                }
            }
            
    return {"jsonrpc": "2.0", "id": id, "error": {"code": -32601, "message": "Method not found"}}

def main():
    # Read from stdin, write to stdout
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            # Log error to stderr
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
