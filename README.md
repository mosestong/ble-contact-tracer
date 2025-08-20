# BLE Contact Tracer with Exposure Logic and Energy Budget

## Description

A **decentralized Bluetooth Low Energy (BLE) contact tracing system** built with ESP32-C6 devices for proximity-based exposure detection and tracking. This project explores privacy preserving digital contact tracing solutions inspired by COVID-19 outbreak response technologies, focusing on decentralized architecture and energy-efficient IoT deployment.

### Key Features

- **Decentralized Architecture**: No central server required. Devices operate independently using peer-to-peer communication
- **Privacy-First Design**: Uses randomized identifiers to protect user anonymity while enabling contact tracing
- **Dual Functionality**: Each device simultaneously advertises its presence and scans for nearby devices
- **Proximity Detection**: Logs contact encounters with timestamps and RSSI values for distance estimation
- **Configurable Exposure Rules**: Implements customizable risk assessment (e.g., cumulative exposure of 5+ minutes within ~2 meters, based on empirical RSSI thresholds)
- **Robust Performance**: Effectively identifies contacts in noisy environments and tracks contact duration for accurate exposure monitoring

### Technical Implementation

- **Hardware**: ESP32-C6 microcontrollers with built-in BLE capabilities
- **RSSI Calibration**: Experimental distance-to-signal strength mapping, determining an RSSI threshold of -70 dBm for approximately 2 meters in typical indoor public conditions 
- **Data Logging**: Local storage of encounter data with timestamp correlation
- **Performance Metrics**: Evaluation of detection accuracy and power consumption

### Experimental Results

This project includes empirical analysis to validate system performance, such as:
- RSSI-distance relationships for proximity estimation
- Battery life and energy consumption metrics under varying conditions
- Additional statistics on message rates and contact tracking 

## Contributors

- **Branden McInnis**: Report, debugging, C++ testing, peer ID system, energy profiling, distance/RSSI data collection.
- **Tyler Herritt**: Report, debugging, HTTP server, Python plots, distance/RSSI data, statistics aggregation.
- **Tobi Onibudo**: Report, debugging, contact tracer data structure, HTTP server, architecture.
- **Moses Tong**: Report, debugging, statistics code, energy profiling, data collection, architecture.

---

## File Structure

```
.
├── README.md                       # Project overview and usage
├── requirements.txt                # Python dependencies
├── data/
│   └── detected_contacts.csv       # Processed contact data
├── firmware/
│   ├── firmware.ino
│   ├── bulk_upload_server.py       # Server for processing BLE data
│   └── packet_analysis.py          # Additional packet analysis utilities
├── plots/
│   ├── advertising_interval_vs_battery_life.png  # Battery Life Analysis Plot
│   ├── messages_per_minute_per_sender.png
│   ├── plots.py
│   ├── radio_tx_power_vs_battery_life.png
│   ├── rssi_vs_distance.csv
│   ├── rssi_vs_distance.png
│   ├── statistics.ipynb
│   └── total_average_current_vs_battery_life.png
├── uploads/
│   └── upload_YYYYMMDD_HHMMSS.csv  # Raw BLE data uploads from ESP32
```

---

## Hardware Setup

- **Parts:**  
  - 2× ESP32-C6 DevKit C-1

- **Pin Connections:**  
  - None required (uses built-in BLE and WiFi)

- **Assembly:**  
  - Connect ESP32-C6 devices to USB for power and programming

---

## Software Dependencies

- **Arduino IDE:** 2.3.6
- **ESP32 by Espressif Systems** (Arduino library)
- **Python:** 3.7+
- **Python Packages:**  
  - `pandas`
  - `matplotlib`
  - `numpy`
  - `jupyter`
  - `ipykernel`

---

## Execution Instructions

### 1. ESP32-C6 Firmware Setup

1. Open **Arduino IDE 2.3.6**
2. Install ESP32 board support package  
   *(Tools → Board → Boards Manager → search "ESP32")*
3. Select **ESP32C6 Dev Module** as the board
4. Configure board settings:
   - Partition Scheme: `8M with spiffs (3MB APP/ 1.5MB spiffs)`
   - Flash size: `8Mb`
5. Open `firmware/firmware.ino`
6. Update WiFi credentials:
   - Change `ssid` and `password` variables
   - Update `serverURL` to your computer's IP
7. Upload firmware to both ESP32-C6 devices
8. Monitor serial output at **115200 baud** to verify operation

---

### 2. Running the Data Collection Server

```bash
# In terminal/command prompt:
pip install -r requirements.txt

cd firmware
python bulk_upload_server.py
```

- Server starts on **port 8081** and waits for ESP32 uploads
- Raw data saved to `uploads/`
- Processed contacts saved to `data/detected_contacts.csv`

---

### 3. Data Analysis & Visualization

- **Statistical analysis:**  
  ```bash
  jupyter notebook plots/statistics.ipynb
  ```
- **Generate plots:**  
  ```bash
  cd plots
  python plots.py
  ```

---

## System Operation

- ESP32 devices scan for BLE advertisements every **10 seconds**
- Devices with matching service UUID are logged as contacts
- Data uploaded to server every **10 seconds** (when WiFi available)
- Server tracks cumulative contact time, triggers exposure alerts at **5+ minutes**
- All data timestamped and stored for analysis

---

## Reproduction Guide

- **Testing Environment:**  
  - Indoor, with WiFi coverage
  - Any BLE-capable device for testing
  - Local WiFi network for uploads

---

## Troubleshooting

- **Known Issues:**
  - ESP32 must be within WiFi range for uploads
  - BLE scanning may miss non-advertising devices
  - Server must be running before ESP32 uploads

- **Common Setup Issues:**
  - **WiFi failures:** Check credentials/network (ensure hotspot is running)
  - **Upload failures:** Verify server is running and IP is correct
  - **No serial output:** Check baud rate (115200)

- **Workarounds:**
  - If WiFi unavailable, data stored locally on ESP32 until reconnected
  - Multiple ESP32 devices can upload to the same server
  - Server handles multiple upload files