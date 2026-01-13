
#!/usr/bin/env python3
"""
Fixed Proxy Server - Correctly handles POST to /api/generate
"""
import json
import http.server
import socketserver
import urllib.request
import sys

PORT = 3000
OLLAMA_URL = "http://localhost:11434"

class FixedProxyHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.handle_health()
        elif self.path == '/':
            self.handle_root()
        elif self.path == '/api/generate':
            # Return 405 for GET to /api/generate
            self.send_response(405, "Method Not Allowed")
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": True,
                "code": 405,
                "message": "GET method not allowed for /api/generate. Use POST."
            }).encode())
        else:
            self.send_error(404, f"Not found: {self.path}")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/generate':
            self.handle_generate()
        else:
            self.send_error(404, f"Not found: {self.path}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_root(self):
        """Serve root page"""
        html = """
        <html>
        <body>
            <h1>Training Copilot Proxy</h1>
            <p>Server is running!</p>
            <p>Endpoints:</p>
            <ul>
                <li><strong>POST</strong> /api/generate - Generate AI responses</li>
                <li><strong>GET</strong> /health - Check server status</li>
            </ul>
            <p>Remember: /api/generate requires POST method</p>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def handle_health(self):
        """Health check endpoint"""
        try:
            # Check Ollama
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                models_data = json.loads(response.read())
                models = [m.get('name') for m in models_data.get('models', [])]
                
                self.send_json(200, {
                    "status": "healthy",
                    "ollama": "connected",
                    "models": models,
                    "proxy_url": f"http://localhost:{PORT}",
                    "note": "/api/generate requires POST method"
                })
        except Exception as e:
            self.send_json(200, {
                "status": "degraded",
                "ollama": "disconnected",
                "error": str(e),
                "tip": "Run 'ollama serve' in another terminal"
            })
    
    def handle_generate(self):
        """Handle AI generation requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Empty request body")
                return
            
            post_data = self.rfile.read(content_length)
            
            # Forward to Ollama with POST
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/generate",
                data=post_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                ollama_response = response.read()
                
                # Return to client
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(ollama_response)
                
        except urllib.error.HTTPError as e:
            if e.code == 405:
                self.send_error(405, "Ollama: Method Not Allowed - Make sure you're sending POST, not GET")
            else:
                self.send_error(e.code, f"Ollama error: {e.reason}")
        except Exception as e:
            self.send_error(500, f"Proxy error: {str(e)}")
    
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
            "message": message,
            "fix": "Make sure you're using POST method for /api/generate"
        }).encode())
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

def main():
    print(f"""
    🚀 Training Copilot Fixed Proxy
    ================================
    Starting on: http://localhost:{PORT}
    
    Key Fix: /api/generate now properly requires POST method
    
    To test:
    1. Check health: curl http://localhost:{PORT}/health
    2. Test generation: curl -X POST http://localhost:{PORT}/api/generate \\
         -H "Content-Type: application/json" \\
         -d '{{"model":"llama2","prompt":"Hello","stream":false}}'
    
    Common 405 causes:
    - Using GET instead of POST
    - Browser sending preflight OPTIONS incorrectly
    - Bookmarklet using wrong HTTP method
    
    Press Ctrl+C to stop
    """)
    
    try:
        server = socketserver.TCPServer(('', PORT), FixedProxyHandler)
        print(f"✅ Server running at http://localhost:{PORT}")
        print(f"📞 Testing Ollama connection...")
        
        # Test Ollama
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                models = json.loads(response.read()).get('models', [])
                print(f"✅ Ollama connected. Models: {len(models)}")
        except Exception as e:
            print(f"⚠️  Ollama not connected: {e}")
            print(f"   Run 'ollama serve' in another terminal")
        
        print(f"\n🎯 Ready for POST requests to /api/generate")
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
