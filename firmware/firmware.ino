#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "BLE2902.h"  
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// Final Project

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


class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    int rssi = advertisedDevice.getRSSI();
    BLEUUID found_service_UUID = advertisedDevice.getServiceUUID();
      if (rssi > rssiThreshold and found_service_UUID.toString() == SERVICE_UUID) {
        Serial.print("Device found: ");
        Serial.println(advertisedDevice.toString().c_str());
      }
  }
};

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.println("Starting BLE Broadcaster...");

  // Generate device name
  String deviceName = "BLE Contact Tracer";

  // Initialize BLE
  BLEDevice::init(deviceName.c_str());

  // Create BLE Server
  BLEServer* pServer = BLEDevice::createServer();


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
    pBLEScan->clearResults(); // Delete results to free memory
    currentTime = myTime;
  }
}
