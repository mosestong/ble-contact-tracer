Final Project - P1: BLE Contact Tracer with Exposure Logic and Energy Budget
Group XX: 09
Track: Undergraduate

Team Members:
- Branden McInnis (ID: B00895969) - Undergraduate
- Tyler Herritt (ID: B00889461) - Undergraduate
- Tobi Onibudo (ID: B00888581) - Undergraduate
- Moses Tong (ID: B00898277) - Undergraduate

Project choice (P1):
- We chose project P1 because the Contact Tracer application seemed more generally applicable than the Peer-Messaging LoRaWAN service. Since our group members were more interested in this project, we felt it would be easier to work on together.

Work Distribution:
  -

File Structure:
- README.txt: This file. Used to give general information about the project, and steps to use or deploy the project.
- requirements.txt: Python dependencies for data analysis and visualization
- data/
  - detected_contacts.csv: Processed contact data with exposure tracking
- firmware/
  - firmware.ino: Main ESP32-C6 firmware for BLE contact tracing
  - bulk_upload_server.py: Python HTTP server to receive and process BLE data
  - packet_analysis.py: Additional packet analysis utilities
- plots/
  - advertising_interval_vs_battery_life.png: Battery life analysis plot
  - messages_per_minute_per_sender.png: Message frequency analysis
  - plots.py: Python script for generating analysis plots
  - radio_tx_power_vs_battery_life.png: Power consumption analysis
  - rssi_vs_distance.csv: RSSI vs distance data
  - rssi_vs_distance.png: RSSI vs distance visualization
  - statistics.ipynb: Jupyter notebook for statistical analysis
  - total_average_current_vs_battery_life.png: Current consumption analysis
- uploads/
  - upload_YYYYMMDD_HHMMSS.csv: Raw BLE data uploads from ESP32 devices

Hardware Setup:
- Parts:
  - 2x ESP32-C6 DevKit C-1
- Pin Connections:
  - No additional pin connections required (uses built-in BLE and WiFi)
- Assembly Instructions:
  - Simply connect ESP32-C6 devices to USB for power and programming

Software dependencies:
- Arduino IDE: 2.3.6
- ESP32 by Espressif Systems (library)
- Python 3.7+ for server and analysis
- Required Python packages (see requirements.txt):
  - pandas
  - matplotlib
  - numpy
  - jupyter
  - ipykernel

Execution Instructions:

1. Setting up the ESP32-C6 Firmware:
   - Open Arduino IDE 2.3.6
   - Install ESP32 board support package (Tools > Board > Boards Manager > search "ESP32")
   - Select "ESP32C6 Dev Module" as the board
   - Configure board settings:
     - Partition Scheme: 8M with spiffs (3MB APP/ 1.5MB spiffs)
     - Flash size: 8Mb
   - Open firmware/firmware.ino
   - Update WiFi credentials in the firmware:
     - Change ssid and password variables to match your network
     - Update serverURL to point to your computer's IP address
   - Upload the firmware to both ESP32-C6 devices
   - Monitor serial output at 115200 baud to verify operation

2. Running the Data Collection Server:
   - Open terminal/command prompt
   - Navigate to the project directory
   - Install Python dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Start the server:
     ```bash
     cd firmware
     python bulk_upload_server.py
     ```
   - The server will start on port 8081 and wait for ESP32 uploads
   - Raw data will be saved to uploads/ directory
   - Processed contact data will be saved to data/detected_contacts.csv

3. Data Analysis and Visualization:
   - For statistical analysis, open plots/statistics.ipynb in Jupyter:
     ```bash
     jupyter notebook plots/statistics.ipynb
     ```
   - For generating plots, run:
     ```bash
     cd plots
     python plots.py
     ```

System Operation:
- ESP32 devices continuously scan for BLE advertisements every 10 seconds
- When devices with matching service UUID are found, contact data is logged
- Data is uploaded to the server every 10 seconds when WiFi is available
- The server tracks cumulative contact time and triggers exposure alerts at 5+ minutes
- All data is timestamped and stored for analysis

requirements:
pip install ipykernel for running jupyter notebook with virtualenv

Reproduction guide:
- Testing Environment:
  - Location: Indoor environment with WiFi coverage
  - Phone/Device models: Any BLE-capable device can be used for testing
  - Network: Local WiFi network for data uploads

Troubleshooting:
- Known limitations or issues:
  - ESP32 devices must be within WiFi range for data uploads
  - BLE scanning may miss devices if they're not advertising
  - Server must be running before ESP32 devices attempt uploads
- Common setup issues:
  - WiFi connection failures: Check credentials and network availability (Ensure wifi hotspot is running)
  - Upload failures: Verify server is running and IP address is correct
  - Serial monitor not showing output: Check baud rate (115200)
- Workarounds:
  - If WiFi is unavailable, data is stored locally on ESP32 until connection is restored
  - Multiple ESP32 devices can upload to the same server simultaneously
  - Server automatically handles multiple upload files and processes them sequentially