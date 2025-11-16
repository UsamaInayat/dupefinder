"""List all routes in the FastAPI app"""
from app.main import app

print("\n" + "=" * 60)
print("Registered Routes in FastAPI App")
print("=" * 60 + "\n")

for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(sorted(route.methods))
        print(f"{methods:20} {route.path}")
    elif hasattr(route, 'path'):
        print(f"{'STATIC/MOUNT':20} {route.path}")

print("\n" + "=" * 60)






