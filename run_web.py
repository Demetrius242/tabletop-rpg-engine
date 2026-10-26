from __future__ import annotations

import argparse
import pathlib
import sys
import threading
import webbrowser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from web.server import serve


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Start the RPG web interface.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--server", default=None,
                    help="llama-server completion URL; if given, the real model is used")
    ap.add_argument("--fake", action="store_true", help="force the canned (no-model) backend")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)

    use_fake = args.fake or not args.server
    try:
        httpd = serve(args.host, args.port, fake=use_fake, server_url=args.server)
    except OSError as exc:
        print(f"[web] Could not start on {args.host}:{args.port} -- {exc}", file=sys.stderr)
        return 1

    url = f"http://{args.host}:{args.port}/"
    backend = "canned (no model)" if use_fake else f"llama-server @ {args.server}"
    print(f"[web] Serving the RPG interface at {url}")
    print(f"[web] Backend: {backend}")
    print("[web] Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[web] Shutting down.")
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
