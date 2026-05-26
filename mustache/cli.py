import sys
import time
import argparse

def print_progress(step_name, percentage, start_time=None):
    width = 30
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    
    elapsed_str = ""
    if start_time is not None:
        elapsed = time.time() - start_time
        elapsed_str = f" [{elapsed:.2f}s]"
        
    # Using \r to overwrite the line and keeping it clean
    sys.stdout.write(f"\r\033[K\033[32mMustaCHE\033[0m :: [{bar}] {percentage}%{elapsed_str} | {step_name}")
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="MustaCHE Explorer CLI")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the UI on (default: 5000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    print("\n\033[32m")
    print("                            ████          ████")
    print("                        ████████████  ████████████")
    print("                      ██████████████████████████████")
    print("              ██    ██████████████████████████████████    ██")
    print("              ██████████████████████  ██████████████████████")
    print("                ██████████████████      ██████████████████")
    print("                    ██████████              ██████████\033[0m")
    print("                     MustaCHE Explorer v2.0")
    print("                     ======================\n")

    start_time = time.time()

    print_progress("Initializing system modules...", 10, start_time)
    time.sleep(0.1)

    print_progress("Loading Flask framework...", 25, start_time)
    from flask import Flask
    time.sleep(0.1)

    print_progress("Loading Data Science stack (numpy, pandas)...", 50, start_time)
    import numpy as np
    import pandas as pd
    time.sleep(0.15)

    print_progress("Loading Scientific algorithms (scipy, sklearn)...", 75, start_time)
    import scipy
    import sklearn
    time.sleep(0.15)

    print_progress("Loading Clustering Engine (core-sg)...", 90, start_time)
    try:
        import core_sg
    except ImportError:
        pass
    time.sleep(0.1)

    print_progress("Initializing application routes...", 98, start_time)
    from mustache import create_app
    app = create_app()
    time.sleep(0.1)

    print_progress("Server ready!", 100, start_time)
    print("\n\nStarting MustaCHE on http://{}:{}".format(args.host, args.port))
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()

