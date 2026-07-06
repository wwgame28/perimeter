#!/usr/bin/env python3
"""Amvera/local entrypoint for the Perimeter Telegram bot."""
import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _health_port() -> int:
    for key in ("PORT", "AMVERA_PORT", "CONTAINER_PORT", "HEALTH_PORT"):
        value = os.getenv(key)
        if value and value.isdigit():
            return int(value)
    return 8080


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = b"Perimeter Telegram bot is running\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def start_health_server() -> None:
    try:
        port = _health_port()
        server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
        print(f"Health server started on 0.0.0.0:{port}", flush=True)
        server.serve_forever()
    except OSError as exc:
        print(f"Health server was not started: {exc}", flush=True)


def main() -> None:
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    threading.Thread(target=start_health_server, daemon=True).start()
    from telegram_bot.bot import main as bot_main
    asyncio.run(bot_main())


if __name__ == "__main__":
    main()
