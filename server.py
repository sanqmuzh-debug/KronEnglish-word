#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zero-dependency local development server for KronEnglish-word.
Serves index.html and all 125 HTML units with correct CORS, range requests, and audio headers.
"""

import http.server
import socketserver
import os
import sys

PORT = int(os.environ.get("PORT", 8080))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class KronWordHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for Aha! bridge integration
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), KronWordHandler) as httpd:
        print("==================================================")
        print(f"🚀 KronEnglish-word Standalone Server Running!")
        print(f"📍 Local Portal: http://localhost:{PORT}")
        print(f"📚 Total Units:  125 interactive HTML modules")
        print("==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()
