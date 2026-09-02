#!/usr/bin/env python3
"""로컬 미리보기용 정적 서버.  실행: python serve.py  ->  http://localhost:4599"""
import http.server, os, socketserver
os.chdir(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("PORT", "4599"))
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"Serving tech_blog_ai_clip at http://localhost:{PORT}")
    httpd.serve_forever()
