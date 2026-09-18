import unittest
import sys
from pathlib import Path

# Ensure scripts/ in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import mcp_server

class TestMCPServer(unittest.TestCase):
    def test_mcp_server_module_exists(self):
        self.assertTrue(hasattr(mcp_server, "handle_request"), "mcp_server must have handle_request function")
        
    def test_mcp_list_tools(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        resp = mcp_server.handle_request(req)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertIn("result", resp)
        self.assertIn("tools", resp["result"])
        tool_names = [t["name"] for t in resp["result"]["tools"]]
        self.assertIn("parse_book", tool_names)
        self.assertIn("book2game_search", tool_names)

    def test_mcp_call_tool(self):
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "query_rag",
                "arguments": {"game_dir": "nonexistent", "query": "test"}
            }
        }
        resp = mcp_server.handle_request(req)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertIn("result", resp)

if __name__ == "__main__":
    unittest.main()
