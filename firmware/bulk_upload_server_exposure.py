import http.server
import socketserver
import os
import csv
from datetime import datetime

PORT = 8081
UPLOAD_DIR = "uploads"
PROCESSED_DATA_FILE = "detected_contacts.csv"
# Generate filename based on timestamp
filename = datetime.now().strftime("upload_%Y%m%d_%H%M%S.csv")

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize processed data file with headers if it doesn't exist
if not os.path.exists(PROCESSED_DATA_FILE):
    with open(PROCESSED_DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['server_timestamp','device_timestamp', 'delay', 'sender_id', 'rssi', 'manufacturer_data', 'device_name', 'total_contact_minutes', 'status', 'alert_triggered'])

# Initialize processed data file with headers if it doesn't exist
UPLOAD_FILE = UPLOAD_DIR+"/"+filename
if not os.path.exists(UPLOAD_FILE):
    with open(UPLOAD_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp','device_address','rssi','device_name','manufacturer_data','sender_id'])

# Simple in-memory contact tracking
contact_tracker = {}  # manufacturer_data -> {'first_seen': datetime, 'total_minutes': float}
EXPOSURE_THRESHOLD_MINUTES = 5

def track_contacts(csv_data):
    """
    Simple contact tracking function - tracks cumulative contact time,
    logs when devices reach 5+ minutes of exposure, and saves processed data
    """
    print(f"[+] track_contacts started")
    try:
        current_time = datetime.now()
    
        # Handle CSV data without headers by adding them
        expected_headers = ['timestamp', 'device_address', 'rssi', 'device_name', 'manufacturer_data', 'sender_id']
        
        # Add headers if they don't exist
        lines = csv_data.splitlines()
        if lines and not any(line.startswith('timestamp') for line in lines):
            # No headers found, add them
            csv_data_with_headers = ','.join(expected_headers) + '\n' + csv_data
            print(f"[DEBUG] Added headers to CSV data")
        else:
            csv_data_with_headers = csv_data
            
        csv_reader = csv.DictReader(csv_data_with_headers.splitlines())
        
        for row in csv_reader:
            manufacturer_data = row.get('manufacturer_data', '').strip()
            device_name = row.get('device_name', 'Unknown').strip()
            sender_id = row.get('sender_id', 'Unknown').strip()
            rssi = row.get('rssi', 'Unknown').strip()
            
            device_epoch_time = row.get('timestamp', 'Unknown').strip()
            try:
                device_timestamp = datetime.fromtimestamp(int(device_epoch_time))
                delay = (current_time - device_timestamp).total_seconds()
            except (ValueError, TypeError) as e:
                print(f"[!] Error parsing timestamp '{device_epoch_time}': {e}")
                # Use current time as fallback
                device_timestamp = current_time
                delay = 0
            
            if not manufacturer_data or manufacturer_data == 'None':
                continue
                
            # Track this contact
            if manufacturer_data not in contact_tracker:
                # New contact
                contact_tracker[manufacturer_data] = {
                    'first_seen': current_time,
                    'last_seen': current_time,
                    'total_minutes': 0,
                    'device_name': device_name,
                    'sender_id': sender_id,
                    'rssi': rssi,
                    'alerted': False
                }
                print(f"[+] New contact: {manufacturer_data} ({device_name})")
                
                # Save new contact to processed data file
                save_contact_data(current_time, device_timestamp, delay, sender_id, rssi, manufacturer_data, device_name, 0, 'new_contact', False)
                
            else:
                # Update existing contact
                contact = contact_tracker[manufacturer_data]
                time_since_last = (current_time - contact['last_seen']).total_seconds() / 60
                
                # If less than 2 minutes since last contact, add to total time
                if time_since_last <= 2:
                    contact['total_minutes'] += time_since_last
                
                contact['last_seen'] = current_time
                contact['device_name'] = device_name
                contact['sender_id'] = sender_id
                contact['rssi'] = rssi
                
                # Check for exposure alert
                if contact['total_minutes'] >= EXPOSURE_THRESHOLD_MINUTES and not contact['alerted']:
                    print(f"EXPOSURE ALERT: {manufacturer_data} ({device_name}) - {contact['total_minutes']:.2f} minutes of contact!")
                    contact['alerted'] = True
                    
                    # Save exposure alert to processed data file
                    save_contact_data(current_time, device_timestamp, delay, contact['sender_id'], contact['rssi'], manufacturer_data, device_name, contact['total_minutes'], 'exposure_detected', True)
                else:
                    # Save regular contact update
                    save_contact_data(current_time, device_timestamp, delay, contact['sender_id'], contact['rssi'], manufacturer_data, device_name, contact['total_minutes'], 'contact_update', contact['alerted'])
        
        # Clean up old contacts (remove if not seen for 10 minutes)
        to_remove = []
        for mfg_data, contact in contact_tracker.items():
            minutes_since_last = (current_time - contact['last_seen']).total_seconds() / 60
            if minutes_since_last > 10:
                to_remove.append(mfg_data)
        
        for mfg_data in to_remove:
            contact = contact_tracker[mfg_data]
            print(f"[+] Removing old contact: {mfg_data}")
            
            # Save contact removal to processed data file
            save_contact_data(current_time, device_timestamp, delay, contact['sender_id'], contact['rssi'], mfg_data, contact['device_name'], contact['total_minutes'], 'contact_ended', contact['alerted'])
            
            del contact_tracker[mfg_data]
            
    except Exception as e:
        print(f"[!] Error tracking contacts: {e}")

def save_contact_data(current_time, device_timestamp, delay, sender_id,rssi, manufacturer_data, device_name, total_minutes, status, alert_triggered):
    """Save processed contact data to separate CSV file"""
    try:
        with open(PROCESSED_DATA_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                current_time.strftime('%Y-%m-%d %H:%M:%S'),
                device_timestamp,
                delay,
                sender_id,
                rssi,
                manufacturer_data,
                device_name,
                round(total_minutes, 2),
                status,
                alert_triggered,
            ])
    except Exception as e:
        print(f"[!] Error saving processed data: {e}")

class BLEUploadHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler to process POST requests for file uploads.
    """
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        print(f"[+] Received {content_length} bytes")
        if content_length == 0:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No data received")
            return

        # Read the POST data from the request
        post_data = self.rfile.read(content_length)
        csv_data = post_data.decode('utf-8')
        # Generate filename based on timestamp
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Save raw upload
        with open(filepath, "ab") as f:
            f.write(post_data)

        print(f"[+] Received {len(post_data)} bytes, saved to {filepath}")
        
        # Process contacts for tracking and save processed data separately
        track_contacts(csv_data)
        
        print(f"[+] track contacts done")
        print(f"[+] Processed data saved to {PROCESSED_DATA_FILE}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Data received and saved.")

if __name__ == "__main__":
    # Setup and start HTTP server
    handler = BLEUploadHandler
    # Start the server
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"[*] BLE Contact Tracker started on port {PORT}")
        print(f"[*] Exposure threshold: {EXPOSURE_THRESHOLD_MINUTES} minutes")
        print(f"[*] Raw uploads saved to: {UPLOAD_DIR}/")
        print(f"[*] Processed data saved to: {PROCESSED_DATA_FILE}")
        print(f"[*] Waiting for uploads...")
        httpd.serve_forever()
