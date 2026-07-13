"""
web_main.py — Web server entry point for AIRefiner.

Usage:
    python web_main.py             # runs on http://localhost:5000
    python web_main.py --port 8080 # custom port

CLI mode is unchanged:
    python main.py
"""

import argparse
import os
import sys

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web.app import create_app


def parse_args():
    parser = argparse.ArgumentParser(description='AIRefiner Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable Flask debug mode')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    app = create_app()
    print(f"\n🌐 AIRefiner Web UI starting at http://localhost:{args.port}")
    print("   CLI mode still works: python main.py\n")
    app.run(host=args.host, port=args.port, debug=args.debug)
