import http.server
import socketserver
import os
from datetime import datetime

PORT = 8080
UPLOAD_DIR = "uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

class BLEUploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No data received")
            return

        post_data = self.rfile.read(content_length)

        # Generate filename based on timestamp
        filename = datetime.now().strftime("upload_%Y%m%d_%H%M%S.csv")
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(post_data)

        print(f"[+] Received {len(post_data)} bytes, saved to {filepath}")
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data received and saved.")

if __name__ == "__main__":
    handler = BLEUploadHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"[*] BLE Upload Server started on port {PORT}")
        print(f"[*] Waiting for POSTs on port {PORT}/")
        httpd.serve_forever()
