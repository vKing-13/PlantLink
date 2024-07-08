#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char *ssid = "shirooo";
const char *password = "qwer1234";
const char *base_rest_url = "http://192.168.1.236:8000/";
const char *API_KEY = "fyppresent78";

WiFiClient client;
HTTPClient http;

#define DHTPIN D4    // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11 // DHT sensor type (DHT11, DHT21, DHT22)

#define SensorPin A0  // pH meter Analog output connected to Arduino's Analog A0 pin

DHT dht(DHTPIN, DHTTYPE);
unsigned long int avgHumidity;
unsigned long int avgTemperature;
unsigned long int avgPhValue;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);
  delay(1000);  // Give some time to open the serial monitor
  Serial.println("Connecting to WiFi...");

  // Connect to WiFi network
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  dht.begin();  // Initialize DHT sensor
}

#define MAX_RETRIES 3

bool sendHttpPost(String url, String jsonData) {
  for (int i = 0; i < MAX_RETRIES; i++) {
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(10000);  // Set timeout to 10 seconds
    int httpResponseCode = http.POST(jsonData);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println(response);
      http.end();
      return true;
    } else {
      Serial.print("Error in HTTP POST: ");
      Serial.println(httpResponseCode);
    }
    http.end();
    delay(1000);  // Wait 1 second before retrying
  }
  return false;
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // WiFi is connected, proceed with sensor reading and data sending

    // Check if DHT11 sensor is connected
    float humidityValue = 0;
    float temperatureValue = 0;
    int validDHTReadings = 0;
    for (int i = 0; i < 3; i++) {
      delay(1000);  // Delay 1 second between readings
      float humidity = dht.readHumidity();
      float temperature = dht.readTemperature();
      if (!isnan(humidity) && !isnan(temperature)) {
        humidityValue += humidity;
        temperatureValue += temperature;
        validDHTReadings++;
      }
    }

    if (validDHTReadings > 0) {
      avgHumidity = humidityValue / validDHTReadings;
      avgTemperature = temperatureValue / validDHTReadings;

      Serial.print("Average Humidity: ");
      Serial.println(avgHumidity);
      Serial.print("Average Temperature: ");
      Serial.println(avgTemperature);

      // Construct JSON data for DHT sensor
      StaticJsonDocument<200> jsonDHT;
      jsonDHT["sensor_type"] = "DHT11";
      jsonDHT["humidity"] = avgHumidity;
      jsonDHT["temperature"] = avgTemperature;
      jsonDHT["API_KEY"] = API_KEY;
      String jsonDataDHT;
      serializeJson(jsonDHT, jsonDataDHT);

      // Send DHT data to Django server via HTTP POST
      String urlDHT = String(base_rest_url) + "sensor/new_data/";
      if (!sendHttpPost(urlDHT, jsonDataDHT)) {
        Serial.println("Failed to send DHT data after multiple attempts.");
      }
    } else {
      Serial.println("Invalid DHT readings (NaN). Skipping DHT data transmission.");
    }

    // Add a delay to ensure no back-to-back requests
    delay(7000);  // Adjust this delay as needed

    // Check if pH sensor is connected
    int buf[3]; // Array to store pH sensor readings
    int temp; // Temporary variable for sorting
    int avgValue = 0; // Average value of pH sensor readings
    int validPhReadings = 0;
    for (int i = 0; i < 3; i++) {
      buf[i] = analogRead(SensorPin);
      delay(10);
    }
    for (int i = 0; i < 2; i++) {
      for (int j = i + 1; j < 3; j++) {
        if (buf[i] > buf[j]) {
          temp = buf[i];
          buf[i] = buf[j];
          buf[j] = temp;
        }
      }
    }
    avgValue = 0;
    for (int i = 1; i < 2; i++) { // use middle value for better averaging
      avgValue += buf[i];
    }
    float phValue = (float)avgValue * 5.0 / 1024;
    phValue = 3.5 * phValue;

    // Print pH value to serial monitor
    Serial.print("pH:");
    Serial.println(phValue, 2);
    if (phValue > 1) {
      StaticJsonDocument<200> jsonPH;
      jsonPH["sensor_type"] = "ph_sensor";
      jsonPH["phValue"] = phValue;
      jsonPH["API_KEY"] = API_KEY;
      String jsonDataPH;
      serializeJson(jsonPH, jsonDataPH);

      // Send pH data to Django server via HTTP POST
      String urlPH = String(base_rest_url) + "sensor/new_data/";
      if (!sendHttpPost(urlPH, jsonDataPH)) {
        Serial.println("Failed to send pH data after multiple attempts.");
      }
    } else {
      Serial.println("Invalid pH readings (NaN). Skipping pH data transmission.");
    }

    // Add a delay before the next iteration to prevent rapid consecutive requests
    delay(10000);  // Adjust this delay as needed
  } else {
    Serial.println("WiFi not connected. Reconnecting...");
    // Reconnect to WiFi network
    WiFi.begin(ssid, password);
  }
}
