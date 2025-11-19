"""
Start DupeFinder Backend Server
Run this from the backend directory: python start_server.py
"""

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
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )






