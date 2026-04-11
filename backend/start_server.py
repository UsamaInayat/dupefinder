"""
Start DupeFinder Backend Server
Run this from the backend directory: python start_server.py

Hot reload is off by default on Windows: multiple uvicorn --reload processes on the
same port can leave stale workers and break MongoDB (e.g. admin login 500). Enable
with: set DUPEFINDER_RELOAD=1 && python start_server.py
Listen address: set DUPEFINDER_HOST=0.0.0.0 to accept LAN; default is 127.0.0.1.
"""

import os
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("DupeFinder API Server")
    print("=" * 60)
    print("\nStarting server...")
    print("Docs: http://localhost:8000/api/docs")
    print("API:  http://localhost:8000/api")
    print("\nPress CTRL+C to stop")
    print("=" * 60)
    
    _reload = os.environ.get("DUPEFINDER_RELOAD", "").strip() in ("1", "true", "yes")
    # Default 127.0.0.1: on some Windows setups0.0.0.0:8000 stays "busy" (ghost/zombie
    # listeners) while 127.0.0.1 is free; localhost in the browser still works.
    _host = os.environ.get("DUPEFINDER_HOST", "127.0.0.1").strip() or "127.0.0.1"
    uvicorn.run(
        "app.main:app",
        host=_host,
        port=8000,
        reload=_reload,
        log_level="info"
    )






