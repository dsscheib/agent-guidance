"""Minimal server-rendered web app."""
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGES = {"/": ("Home", "<p>Welcome to the team portal.</p>")}
NAV = [("/", "Home")]


def render(title, body):
    links = "".join(f'<li><a href="{escape(href)}">{escape(label)}</a></li>' for href, label in NAV)
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{escape(title)} – Team portal</title></head>"
        f'<body><header><nav aria-label="Main"><ul>{links}</ul></nav></header>'
        f"<main><h1>{escape(title)}</h1>{body}</main></body></html>"
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        page = PAGES.get(self.path)
        if page is None:
            self.send_error(404)
            return
        data = render(*page).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
