#!/usr/bin/env python3
"""
Training Copilot ALL-IN-ONE Server
Combines proxy server, Ollama check, and monitoring
"""
import json
import http.server
import socketserver
import urllib.request
from datetime import datetime
import threading
import time
import webbrowser
import os

PORT = 3000
OLLAMA_URL = "http://localhost:11434"
BOOKMARKLET_CODE = """
javascript:(function(){
  // Ultra-simple bookmarklet for testing
  const div = document.createElement('div');
  div.innerHTML = `
    <div style="position:fixed;top:20px;right:20px;background:white;padding:20px;border:2px solid #007bff;border-radius:10px;z-index:9999;width:300px;">
      <h3 style="margin:0 0 10px 0;">🤖 Training Copilot</h3>
      <p>✅ Server is running!</p>
      <p>📚 Pages recorded: 0</p>
      <button onclick="alert('Test successful!')" style="padding:10px;background:#007bff;color:white;border:none;border-radius:5px;cursor:pointer;width:100%;">
        Test AI Connection
      </button>
    </div>
  `;
  document.body.appendChild(div);
})();
"""

class TrainingCopilotHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_CORS_headers()
    
    def do_GET(self):
        if self.path == '/':
            self.serve_homepage()
        elif self.path == '/health':
            self.serve_health_check()
        elif self.path == '/bookmarklet':
            self.serve_bookmarklet()
        elif self.path == '/api/models':
            self.get_ollama_models()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/generate':
            self.forward_to_ollama()
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_CORS_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def serve_homepage(self):
        """Serve a simple HTML dashboard"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Training Copilot Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .card {{ background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .warning {{ color: orange; }}
                button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
                code {{ background: #eee; padding: 2px 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>🤖 Training Copilot</h1>
            
            <div class="card">
                <h2>Status</h2>
                <p>Server: <span class="success">✅ Running</span> on http://localhost:{PORT}</p>
                <p>Ollama: {self.check_ollama_status()}</p>
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="card">
                <h2>Quick Start</h2>
                <ol>
                    <li>Create a bookmark in your browser</li>
                    <li>Name it: <code>Training Copilot</code></li>
                    <li>Paste this code as URL:</li>
                </ol>
                <textarea id="bookmarkletCode" rows="4" style="width: 100%; font-family: monospace; padding: 10px;">{BOOKMARKLET_CODE}</textarea>
                <button onclick="copyBookmarklet()">📋 Copy Bookmarklet Code</button>
            </div>
            
            <div class="card">
                <h2>Testing</h2>
                <button onclick="testOllama()">Test Ollama Connection</button>
                <button onclick="testBookmarklet()">Test Bookmarklet</button>
                <div id="testResult" style="margin-top: 10px;"></div>
            </div>
            
            <script>
                function copyBookmarklet() {{
                    const textarea = document.getElementById('bookmarkletCode');
                    textarea.select();
                    document.execCommand('copy');
                    alert('Copied! Create a bookmark with this code.');
                }}
                
                async function testOllama() {{
                    const resultDiv = document.getElementById('testResult');
                    resultDiv.innerHTML = 'Testing...';
                    
                    try {{
                        const response = await fetch('/health');
                        const data = await response.json();
                        if (data.ollama === 'connected') {{
                            resultDiv.innerHTML = '<span class="success">✅ Ollama is connected!</span>';
                        }} else {{
                            resultDiv.innerHTML = '<span class="warning">⚠️ Ollama not detected. Run: ollama serve</span>';
                        }}
                    }} catch (error) {{
                        resultDiv.innerHTML = '<span class="error">❌ Connection failed</span>';
                    }}
                }}
                
                function testBookmarklet() {{
                    // Create a test bookmarklet
                    const testCode = `javascript:(function(){{alert('Training Copilot Test!\\\\nIf you see this, bookmarklets work.');}})();`;
                    const link = document.createElement('a');
                    link.href = testCode;
                    link.textContent = 'Test Bookmarklet';
                    link.style.display = 'block';
                    link.style.margin = '10px 0';
                    link.style.padding = '10px';
                    link.style.background = '#28a745';
                    link.style.color = 'white';
                    link.style.textDecoration = 'none';
                    document.body.appendChild(link);
                }}
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_health_check(self):
        """Health check endpoint"""
        ollama_status = self.check_ollama_status()
        
        health_data = {
            "status": "running",
            "server": "training-copilot",
            "ollama": "connected" if "✅" in ollama_status else "disconnected",
            "timestamp": datetime.now().isoformat(),
            "port": PORT
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_CORS_headers()
        self.end_headers()
        self.wfile.write(json.dumps(health_data).encode('utf-8'))
    
    def serve_bookmarklet(self):
        """Return the bookmarklet code"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript')
        self.send_CORS_headers()
        self.end_headers()
        self.wfile.write(BOOKMARKLET_CODE.encode('utf-8'))
    
    def get_ollama_models(self):
        """Get available models from Ollama"""
        try:
            with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2) as response:
                ollama_data = json.loads(response.read())
                models = [m.get("name", "") for m in ollama_data.get("models", [])]
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_CORS_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"models": models}).encode('utf-8'))
        except:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_CORS_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"models": [], "error": "Ollama not available"}).encode('utf-8'))
    
    def forward_to_ollama(self):
        """Forward request to Ollama"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/generate",
                data=post_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                ollama_response = json.loads(response.read())
                
                # Format response for our bookmarklet
                result = {
                    "success": True,
                    "response": ollama_response.get("response", ""),
                    "model": json.loads(post_data).get("model", "unknown")
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_CORS_headers()
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
        except urllib.error.URLError as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_CORS_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": f"Cannot connect to Ollama: {e.reason}"
            }).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_CORS_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": f"Internal error: {str(e)}"
            }).encode('utf-8'))
    
    def check_ollama_status(self):
        """Check if Ollama is running"""
        try:
            with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2) as response:
                data = json.loads(response.read())
                model_count = len(data.get("models", []))
                return f"✅ Connected ({model_count} models)"
        except:
            return "❌ Not connected - Run 'ollama serve'"
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def open_browser():
    """Open browser to dashboard after a short delay"""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    print(f"""
    🚀 TRAINING COPILOT - ALL IN ONE
    =================================
    Starting server on: http://localhost:{PORT}
    
    This server provides:
    ✅ CORS proxy for Ollama
    ✅ Dashboard for monitoring
    ✅ Bookmarklet generator
    ✅ Health checks
    
    NO external Python packages needed!
    
    Requirements:
    1. Python 3.6+ (already installed)
    2. Ollama (optional, for AI features)
       - Install from: https://ollama.com
       - Run: ollama pull llama2
       - Run: ollama serve (in another terminal)
    
    Press Ctrl+C to stop
    """)
    
    # Open browser automatically
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        with socketserver.TCPServer(("", PORT), TrainingCopilotHandler) as httpd:
            print(f"✅ Server started successfully!")
            print(f"🌐 Dashboard: http://localhost:{PORT}")
            print(f"🤖 AI Endpoint: http://localhost:{PORT}/api/generate")
            print(f"\n📖 Open your browser to the dashboard for instructions.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   Try using a different port or check permissions")

if __name__ == "__main__":
    main()
