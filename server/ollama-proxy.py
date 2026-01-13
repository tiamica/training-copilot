#!/usr/bin/env python3
"""
Ollama Proxy Server
Solves CORS issues for bookmarklet
"""
import asyncio
import json
import logging
from aiohttp import web, ClientSession
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_HOST = "http://localhost:11434"
ALLOWED_ORIGINS = ["*"]  # In production, specify your domains
PORT = 3000

async def handle_options(request):
    """Handle CORS preflight requests"""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }
    return web.Response(status=200, headers=headers)

async def generate_completion(request):
    """Proxy requests to Ollama"""
    try:
        # Get request data
        data = await request.json()
        model = data.get("model", "llama2")
        prompt = data.get("prompt", "")
        max_tokens = data.get("max_tokens", 500)
        
        logger.info(f"Generating completion with model: {model}")
        
        # Call Ollama
        async with ClientSession() as session:
            ollama_url = f"{OLLAMA_HOST}/api/generate"
            
            ollama_payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.3,
                    "top_p": 0.9,
                }
            }
            
            async with session.post(ollama_url, json=ollama_payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama error: {error_text}")
                    return web.json_response(
                        {"error": f"Ollama returned {response.status}"},
                        status=500
                    )
                
                result = await response.json()
                
                # Log the request for analysis
                await log_interaction({
                    "timestamp": datetime.now().isoformat(),
                    "model": model,
                    "prompt_length": len(prompt),
                    "response_length": len(result.get("response", "")),
                    "prompt_preview": prompt[:100]
                })
                
                return web.json_response({
                    "success": True,
                    "response": result.get("response", ""),
                    "model": model,
                    "tokens": result.get("eval_count", 0)
                })
                
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return web.json_response(
            {"error": "Invalid JSON", "details": str(e)},
            status=400
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return web.json_response(
            {"error": "Internal server error", "details": str(e)},
            status=500
        )

async def list_models(request):
    """List available Ollama models"""
    try:
        async with ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags") as response:
                if response.status != 200:
                    return web.json_response(
                        {"error": "Cannot connect to Ollama"},
                        status=503
                    )
                models = await response.json()
                
                return web.json_response({
                    "success": True,
                    "models": [m["name"] for m in models.get("models", [])]
                })
    except Exception as e:
        return web.json_response(
            {"error": str(e)},
            status=500
        )

async def health_check(request):
    """Health check endpoint"""
    try:
        async with ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags", timeout=2) as response:
                ollama_ok = response.status == 200
                
                return web.json_response({
                    "status": "healthy" if ollama_ok else "degraded",
                    "ollama": "connected" if ollama_ok else "disconnected",
                    "timestamp": datetime.now().isoformat(),
                    "server": "training-copilot-proxy"
                })
    except:
        return web.json_response({
            "status": "unhealthy",
            "ollama": "disconnected",
            "timestamp": datetime.now().isoformat()
        }, status=503)

async def log_interaction(data):
    """Log interactions to file"""
    try:
        with open("data/llm_interactions.log", "a") as f:
            f.write(json.dumps(data) + "\n")
    except:
        pass  # Don't fail if logging fails

def setup_cors(app):
    """Setup CORS middleware"""
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "OPTIONS":
                return await handle_options(request)
            
            response = await handler(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response
        return middleware_handler
    
    app.middlewares.append(cors_middleware)

async def init_app():
    """Initialize the application"""
    app = web.Application()
    
    # Setup CORS
    setup_cors(app)
    
    # Routes
    app.router.add_post("/api/generate", generate_completion)
    app.router.add_get("/api/models", list_models)
    app.router.add_get("/health", health_check)
    app.router.add_options("/{tail:.*}", handle_options)
    
    # Static files for UI
    app.router.add_static("/ui", "ui/")
    
    return app

if __name__ == "__main__":
    print(f"""
    🚀 Training Copilot Proxy Server
    =================================
    Starting server on: http://localhost:{PORT}
    
    Endpoints:
      POST /api/generate  - Generate completions
      GET  /api/models    - List available models
      GET  /health        - Health check
      
    Requirements:
      1. Ollama must be running at http://localhost:11434
      2. A model must be downloaded (e.g., 'ollama pull llama2')
      
    Press Ctrl+C to stop the server.
    """)
    
    web.run_app(init_app(), port=PORT, access_log=None)
