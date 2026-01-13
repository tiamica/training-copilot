#!/usr/bin/env python3
"""
Training Copilot Proxy Server
Simplified and debugged version
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
from urllib.error import URLError
import sys

PORT = 3000
OLLAMA_URL = "http://localhost:11434"

class ProxyHandler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        print(f"GET request to: {self.path}")
        
        if self.path == '/health':
            self.handle_health()
        elif self.path == '/':
            self.handle_root()
        elif self.path == '/api/generate':
            self.send_error(405, "Method Not Allowed - Use POST")
        else:
            self.send_error(404, f"Not Found: {self.path}")
    
    def do_POST(self):
        """Handle POST requests"""
        print(f"POST request to: {self.path}")
        
        if self.path == '/api/generate':
            self.handle_generate()
        else:
            self.send_error(404, f"Not Found: {self.path}")
    
    def handle_root(self):
        """Handle root path"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        html = """
        <html>
        <body>
            <h1>Training Copilot Proxy</h1>
            <p>Server is running!</p>
            <p>Endpoints:</p>
            <ul>
                <li>POST /api/generate - Send prompts to Ollama</li>
                <li>GET /health - Check server status</li>
            </ul>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def handle_health(self):
        """Health check endpoint"""
        try:
            # Try to connect to Ollama
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", 
                                        headers={'User-Agent': 'Training-Copilot'})
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read())
                models = [m.get("name") for m in data.get("models", [])]
                
                response_data = {
                    "status": "healthy",
                    "proxy": f"http://localhost:{PORT}",
                    "ollama": "connected",
                    "models": models,
                    "ollama_url": OLLAMA_URL
                }
                
                self.send_json(200, response_data)
                
        except Exception as e:
            response_data = {
                "status": "degraded",
                "proxy": f"http://localhost:{PORT}",
                "ollama": "disconnected",
                "error": str(e),
                "tip": "Run 'ollama serve' in another terminal"
            }
            self.send_json(200, response_data)
    
    def handle_generate(self):
        """Handle AI generation requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Empty request body")
                return
                
            post_data = self.rfile.read(content_length)
            print(f"Received {len(post_data)} bytes")
            
            # Parse JSON
            try:
                request_json = json.loads(post_data)
                print(f"Model: {request_json.get('model')}")
                print(f"Prompt preview: {request_json.get('prompt', '')[:100]}...")
            except json.JSONDecodeError as e:
                self.send_error(400, f"Invalid JSON: {e}")
                return
            
            # Forward to Ollama
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/generate",
                data=post_data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Training-Copilot-Proxy'
                },
                method='POST'
            )
            
            print(f"Forwarding to {OLLAMA_URL}/api/generate...")
            
            with urllib.request.urlopen(req) as response:
                ollama_response = response.read()
                response_json = json.loads(ollama_response)
                
                print(f"Ollama response: {len(ollama_response)} bytes")
                
                # Return response to client
                self.send_json(200, {
                    "success": True,
                    "response": response_json.get("response", ""),
                    "model": request_json.get("model", "unknown"),
                    "done": response_json.get("done", True)
                })
                
        except URLError as e:
            print(f"Network error: {e}")
            self.send_error(502, f"Cannot connect to Ollama: {e.reason}")
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def send_json(self, code, data):
        """Send JSON response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_error(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": True,
            "code": code,
            "message": message
        }).encode())
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[Proxy] {format % args}")

def main():
    print(f"""
    🚀 Training Copilot Proxy Server
    =================================
    Starting server on: http://localhost:{PORT}
    
    Endpoints:
      POST /api/generate  -> Forward to Ollama
      GET  /health        -> Health check
    
    Testing Ollama connection...
    """)
    
    # Test Ollama connection
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            models = data.get("models", [])
            if models:
                print(f"✅ Ollama is running at {OLLAMA_URL}")
                for model in models:
                    print(f"   Model available: {model.get('name')}")
            else:
                print(f"⚠️  Ollama running but no models found")
                print(f"   Run: ollama pull llama2")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
        print(f"   Error: {e}")
        print(f"   Make sure Ollama is running: 'ollama serve'")
        print(f"   The proxy will start, but AI features won't work.")
    
    print(f"\n🎯 Starting proxy server...")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        server = HTTPServer(('localhost', PORT), ProxyHandler)
        print(f"✅ Proxy running at http://localhost:{PORT}")
        print(f"✅ Health check: http://localhost:{PORT}/health")
        print(f"\n📋 Waiting for requests...")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        if "Address already in use" in str(e):
            print(f"   Port {PORT} is already in use.")
            print(f"   Kill the process or use a different port.")
        sys.exit(1)

if __name__ == "__main__":
    main()
