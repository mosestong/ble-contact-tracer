import http.server
import socketserver
import os
from io import BytesIO
from datetime import datetime
import pandas as pd
import time

PORT = 8080
UPLOAD_DIR = "uploads"
exposure_df = pd.DataFrame(columns=["peer_id", "start", "last_rec", "duration"])
exposure_df.set_index('peer_id', inplace=True)

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

class BLEUploadHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler to process POST requests for file uploads.
    """
    def do_POST(self):
        sent_time = int(self.headers.get("X-Timestamp"))
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No data received")
            return
        
        # Assumes unix epoch time in seconds
        if not sent_time is None:
            print("Air time:", time.time() - sent_time)

        # Read the POST data from the request
        post_data = self.rfile.read(content_length)
        data_log = pd.read_csv(BytesIO(post_data))
        track_contacts(data_log, exposure_df)

        # Generate filename based on timestamp
        filename = datetime.now().strftime("upload_%Y%m%d_%H%M%S.csv")
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(post_data)

        print(f"[+] Received {len(post_data)} bytes, saved to {filepath}")
        
        # Respond to client with success
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data received and saved.")

        print(exposure_df)

def track_contacts(contact_df: pd.DataFrame, exposure_df: pd.DataFrame):
    for (index, timestamp, device_address, rssi, device_name, service_uuid) in contact_df.itertuples():
        print(index, timestamp, device_address, rssi, device_name, service_uuid)

        if not device_address in exposure_df.index:
            exposure_df.loc[device_address, "start"] = timestamp
            exposure_df.loc[device_address, "last_rec"] = timestamp
            exposure_df.loc[device_address, "duration"] = 0.0
        else:
            exposure_df.loc[device_address, "duration"] += (timestamp - exposure_df.loc[device_address, "last_rec"]) / 1000
            exposure_df.loc[device_address, "last_rec"] = timestamp

if __name__ == "__main__":
    # Setup and start HTTP server
    handler = BLEUploadHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"[*] BLE Upload Server started on port {PORT}")
        print(f"[*] Waiting for POSTs on port {PORT}/")
        httpd.serve_forever()
