from __future__ import annotations

import argparse

import uvicorn

from .app_factory import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="O6 DEV HTTP transport adapter (DEV only).")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()

    app = create_app()
    import sys
    print("SERVER sys.executable =", sys.executable)
    print("SERVER sys.prefix     =", sys.prefix)
    print("SERVER base_prefix    =", sys.base_prefix)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()