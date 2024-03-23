
#include <ESP8266WiFi.h>
#include <ArduinoJson.h> // For handling JSON data

const char* ssid = "M403163@Rate One";
const char* password = "wifipw_M403163";
const char* mongodbServer = "175.143.29.95";
const int mongodbPort = 27017; // Default MongoDB port
const char* mongodbDatabase = "sensor";
const char* mongodbCollection = "data";

#define SensorPin A0                  // pH meter Analog output connected to Arduino's Analog A0 pin
unsigned long int avgValue;           // Store the average value of the sensor feedback
int buf[10], temp;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(115200);
  delay(1000);
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // Get pH sensor readings
    for (int i = 0; i < 10; i++) {    // Get 10 sample values from the sensor for smoothing
      buf[i] = analogRead(SensorPin);
      delay(10);
    }
    for (int i = 0; i < 9; i++) {      // Sort the analog values from small to large
      for (int j = i + 1; j < 10; j++) {
        if (buf[i] > buf[j]) {
          temp = buf[i];
          buf[i] = buf[j];
          buf[j] = temp;
        }
      }
    }
    avgValue = 0;
    for (int i = 2; i < 8; i++) {                    // Take the average value of 6 center samples
      avgValue += buf[i];
    }
    float phValue = (float)avgValue * 5.0 / 1024 / 6; // Convert the analog into millivolt
    phValue = 3.5 * phValue;                          // Convert the millivolt into pH value
    
    // Print pH value to serial monitor
    Serial.print("pH:");
    Serial.println(phValue, 2);
    
    // Send pH value to MongoDB
    sendToMongoDB(phValue);
    
    delay(5000); // Adjust delay as needed
  }else {
    Serial.println("WiFi not connected. Reconnecting...");
    // Reconnect to WiFi network
    WiFi.begin(ssid, password);
  }
}

void sendToMongoDB(float value) {
  WiFiClient client;
  IPAddress server(103, 144, 185, 242);
  if (client.connect(server, mongodbPort)) {
    Serial.println("Connected to MongoDB server.");
    
    // Create JSON object for pH value
    StaticJsonDocument<200> doc;
    doc["pH"] = value;
    
    // Convert JSON object to string
    String jsonString;
    serializeJson(doc, jsonString);
    
    // Construct HTTP POST request to insert data into MongoDB
    String request = "POST /" + String(mongodbDatabase) + "/" + String(mongodbCollection) + " HTTP/1.1\r\n";
    request += "Host: " + String(mongodbServer) + "\r\n";
    request += "Content-Type: application/json\r\n";
    request += "Content-Length: " + String(jsonString.length()) + "\r\n\r\n";
    request += jsonString;
    
    client.print(request);
    delay(10);
    Serial.println("Data sent to MongoDB.");
  } else {
    Serial.println("Connection to MongoDB server failed.");
  }
}

