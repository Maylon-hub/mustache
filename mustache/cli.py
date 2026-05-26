import sys
import argparse
from mustache import create_app

def main():
    parser = argparse.ArgumentParser(description="MustaCHE Explorer CLI")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the UI on (default: 5000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    app = create_app()
    
    print(f"Starting MustaCHE on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
