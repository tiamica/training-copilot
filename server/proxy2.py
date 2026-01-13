#!/usr/bin/env python3
"""
Simple HTTP server that serves files AND acts as Ollama proxy
NO CORS issues - everything runs on same origin!
"""
import json
import http.server
import socketserver
import urllib.request
from urllib.parse import urlparse
import os

PORT = 8000
OLLAMA_URL = "http://localhost:11434"

class TrainingCopilotHandler(http.server.SimpleHTTPRequestHandler):
    """Handler that serves static files AND proxies Ollama requests"""
    
    def do_GET(self):
        """Serve files for GET requests"""
        # Serve static files normally
        super().do_GET()
    
    def do_POST(self):
        """Handle POST requests to /api/generate"""
        if self.path == '/api/generate':
            self.handle_ollama_request()
        else:
            self.send_error(404, f"Not found: {self.path}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_ollama_request(self):
        """Forward request to Ollama"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            print(f"[Ollama Proxy] Forwarding request: {len(post_data)} bytes")
            
            # Forward to Ollama
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/generate",
                data=post_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                ollama_response = response.read()
                
                # Send response back
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(ollama_response)
                
                print(f"[Ollama Proxy] Response: {len(ollama_response)} bytes")
                
        except Exception as e:
            print(f"[Ollama Proxy] Error: {e}")
            self.send_error(500, f"Ollama proxy error: {str(e)}")

def main():
    print(f"""
    🌐 TRAINING COPILOT - ALL IN ONE SERVER
    ========================================
    Serving files AND Ollama proxy on: http://localhost:{PORT}
    
    Features:
    ✅ Serves HTML/JS/CSS files
    ✅ Proxies Ollama requests (no CORS issues!)
    ✅ Single server for everything
    
    Usage:
    1. Open http://localhost:{PORT}/test.html in browser
    2. Everything will work (no CORS errors!)
    
    Requirements:
    - Ollama must be running: ollama serve
    - Model downloaded: ollama pull llama2
    
    Press Ctrl+C to stop
    """)
    
    # Change to current directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        with socketserver.TCPServer(("", PORT), TrainingCopilotHandler) as httpd:
            print(f"✅ Server started at http://localhost:{PORT}")
            print(f"📁 Serving files from: {os.getcwd()}")
            print(f"🤖 Ollama proxy: http://localhost:{PORT}/api/generate")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
