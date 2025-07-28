#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "SPIFFS.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h> // Add this include

// Final Project

// WiFi credentials
const char* ssid = "LAPTOP-9EBF657I 3346";
const char* password = "1/bB6076";

// Server endpoint
const char* serverURL = "http://192.168.137.1:8080";

// Generated UUIDs for the service and characteristics
#define SERVICE_UUID "8bc7b016-7196-4f95-a33c-cc541b4509a9"


BLEScan* pBLEScan;
BLEAdvertisementData adData;
BLEAdvertising* pAdvertising;

// Duration of the scan in seconds
unsigned long myTime;
unsigned long currentTime;
const unsigned long interval = 10000;
uint8_t manufacturerData[2];
int scanTime = 20; 
int rssiThreshold = -70;
String mfgData = ""; 


// Logging variables
int logCount = 0;
const int maxLogs = 5;
const char* csvFilePath = "/data.csv";

// Add NTP server info
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 0; // Set your timezone offset in seconds
const int   daylightOffset_sec = 0; // Set daylight offset if needed


void logDeviceToCSV(BLEAdvertisedDevice device) {
  File file = SPIFFS.open(csvFilePath, FILE_APPEND);
  if (!file) {
    Serial.println("Failed to open file for writing");
    return;
  }

  // Get current Unix epoch timestamp
  time_t timestamp = time(nullptr);
  
  // Get service UUIDs if available
  String serviceUUIDs = "None";
  if (device.haveServiceUUID()) {
    serviceUUIDs = device.getServiceUUID().toString().c_str();
  }
  
  // Get manufacturer data if available
  String manufacturerDataStr = "None";
  if (device.haveManufacturerData()) {
    String mfgData = device.getManufacturerData();
    manufacturerDataStr = "";
    for (int i = 0; i < mfgData.length(); i++) {
      if (i > 0) manufacturerDataStr += ":";
      if ((uint8_t)mfgData[i] < 16) manufacturerDataStr += "0"; // Add leading zero for single hex digits
      manufacturerDataStr += String((uint8_t)mfgData[i], HEX);
    }
    manufacturerDataStr.toUpperCase(); // Convert to uppercase for consistency
  }
  
  // Create CSV row: timestamp, device_address, rssi, name, service_uuid, manufacturer_data
  String csvRow = String(timestamp) + "," + 
                  String(device.getAddress().toString().c_str()) + "," +
                  String(device.getRSSI()) + "," +
                  (device.haveName() ? device.getName().c_str() : "Unknown") + "," +
                  manufacturerDataStr + "\n";
  
  file.print(csvRow);
  file.close();
  
  logCount++;
  Serial.println("Device logged to CSV. Count: " + String(logCount));
  Serial.println("Service UUID: " + serviceUUIDs);
  Serial.println("Manufacturer Data: " + manufacturerDataStr);
  
}



void clearCSVFile() {
  if (SPIFFS.remove(csvFilePath)) {
    Serial.println("CSV file cleared successfully");
    
    // Re-create file with headers
    File file = SPIFFS.open(csvFilePath, FILE_WRITE);
    if (file) {
      file.println("timestamp,device_address,rssi,device_name,manufacturer_data");
      file.close();
      Serial.println("CSV file recreated with headers");
    } else {
      Serial.println("Failed to recreate CSV file with headers");
    }
  } else {
    Serial.println("Failed to clear CSV file");
  }
}

void printCSVContents() {
  Serial.println("\n--- Current CSV File Contents ---");
  
  File file = SPIFFS.open(csvFilePath, FILE_READ);
  if (!file) {
    Serial.println("Failed to open CSV file for reading");
    return;
  }
  
  if (file.size() == 0) {
    Serial.println("CSV file is empty");
    file.close();
    return;
  }
  
  // Print file contents line by line
  while (file.available()) {
    String line = file.readStringUntil('\n');
    Serial.println(line);
  }
  
  file.close();
  Serial.println("--- End of CSV Contents ---\n");
}

bool connectToWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  Serial.println(WiFi.status());
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected!");
    Serial.println("IP address: " + WiFi.localIP().toString());
    return true;
  } else {
    Serial.println("");
    Serial.println("WiFi connection failed!");
    return false;
  }
}

void uploadDataToServer() {
  // Connect to WiFi
  if (!connectToWiFi()) {
    Serial.println("Failed to connect to WiFi. Upload cancelled.");
    return;
  }

  // Sync time again if needed
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  time_t now = time(nullptr);

  // Read CSV file
  File file = SPIFFS.open(csvFilePath, FILE_READ);
  if (!file) {
    Serial.println("Failed to open CSV file for reading");
    return;
  }
  
  String csvData = file.readString();
  file.close();
  
  if (csvData.length() == 0) {
    Serial.println("No data to upload");
    return;
  }
  
  Serial.println("Uploading CSV data to server...");
  
  // Send data to server
  HTTPClient http;
  http.begin(serverURL);
  
  // Add HTTP headers
  http.addHeader("Content-Type", "text/csv");
  http.addHeader("Content-Length", String(csvData.length()));
  http.addHeader("User-Agent", "ESP32-BLE-ContactTracer/1.0");
  http.addHeader("X-Device-ID", String(ESP.getEfuseMac(), HEX));
  http.addHeader("X-Data-Type", "contact-trace");
  http.addHeader("X-Timestamp", String(now)); // Use Unix epoch time here
  
  Serial.println("Sending " + String(csvData.length()) + " bytes of CSV data...");
  
  int httpResponseCode = http.POST(csvData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Upload successful! Response code: " + String(httpResponseCode));
    Serial.println("Server response: " + response);
    // Clear data 
    clearCSVFile();
  } else {
    Serial.println("Upload failed. Response code: " + String(httpResponseCode));
  }
  
  http.end();
  
  // Disconnect WiFi to save power
  WiFi.disconnect();
  Serial.println("WiFi disconnected");
}

void initializeCSVFile() {
  // Check if file exists, if not create with header
  if (!SPIFFS.exists(csvFilePath)) {
    File file = SPIFFS.open(csvFilePath, FILE_WRITE);
    if (file) {
      file.println("timestamp,device_address,rssi,device_name,manufacturer_data");
      file.close();
      Serial.println("CSV file created with header");
    } else {
      Serial.println("Failed to create CSV file");
    }
  }
}

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    int rssi = advertisedDevice.getRSSI();
    BLEUUID found_service_UUID = advertisedDevice.getServiceUUID();
    if (rssi > rssiThreshold and found_service_UUID.toString() == SERVICE_UUID) {
      Serial.print("Device found: ");
      Serial.println(advertisedDevice.toString().c_str());
      
      // Log to CSV file
      logDeviceToCSV(advertisedDevice);
    }
  }
};

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.println("Starting BLE Contact Tracer...");

  // Initialize SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("An error occurred while mounting SPIFFS");
    return;
  }
  Serial.println("SPIFFS mounted successfully");
  
  // Initialize CSV file
  initializeCSVFile();

  // Connect to WiFi temporarily to get time
  if (connectToWiFi()) {
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    Serial.println("Waiting for NTP time sync...");
    time_t now = time(nullptr);
    int retry = 0;
    while (now < 1000000000 && retry < 30) { // Wait for valid epoch time
      delay(500);
      now = time(nullptr);
      retry++;
    }
    if (now < 1000000000) {
      Serial.println("Failed to get NTP time.");
    } else {
      Serial.print("Current epoch time: ");
      Serial.println(now);
    }
    WiFi.disconnect();
  } else {
    Serial.println("Could not connect to WiFi for NTP sync.");
  }

  // Generate device name
  String deviceName = "BLE Contact Tracer";

  // Initialize BLE
  BLEDevice::init(deviceName.c_str());

  // Create BLE Server
  BLEServer* pServer = BLEDevice::createServer();

  // Create the service
  BLEService* pService = pServer->createService(SERVICE_UUID);
  
  // Start the service
  pService->start();

  // Start advertising
  pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);

  String random_mfg = randomize_manufacturer_data();
  // Set manufacturer data (0x4C00 is Apple's company ID - use for testing)
  adData = BLEAdvertisementData();
  adData.setManufacturerData(random_mfg);
  pAdvertising->setAdvertisementData(adData);

  pAdvertising->start();
  Serial.println("BLE Advertisement started!");

  pBLEScan = BLEDevice::getScan(); // Create BLE scan object
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true); // Active scan retrieves more data, but uses more power
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);  // Window <= Interval

  currentTime = millis();
}

String randomize_manufacturer_data(){
    //get random data
    manufacturerData[0] = random(0, 256);
    manufacturerData[1] = random(0, 256);

    //clear mfgData
    mfgData = "";
    mfgData += (char)manufacturerData[0];
    mfgData += (char)manufacturerData[1];

    return mfgData;
}

void loop() {
  myTime = millis();
  if(myTime - currentTime >= interval){
    pAdvertising->stop();
    String random_mfg = randomize_manufacturer_data();
    adData.setManufacturerData(random_mfg);
    pAdvertising->setAdvertisementData(adData);
    pAdvertising->start();

    Serial.println("Scanning...");
    BLEScanResults* foundDevices = pBLEScan->start(scanTime, false);
    Serial.print("Devices found: ");
    Serial.println(foundDevices->getCount());
    Serial.println("Scan done!");
      // Print current CSV file contents
    printCSVContents();
    
    // Upload to Server 
    uploadDataToServer();

    pBLEScan->clearResults(); // Delete results to free memory
    currentTime = myTime;
  }

}
