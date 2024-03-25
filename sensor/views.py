from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from datetime import datetime


from .mongo_setup import connect_to_mongodb
# Create your views here.
@csrf_exempt
def arduino_data(request):
    if request.method == 'POST' and settings.RECEIVE_DATA_ENABLED:
        # Process incoming data
        # For example:
        # arduino_data = request.POST.get('data')
        # SensorData.objects.create(**arduino_data)
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'data reception disabled'})

def toggle_data_reception(request):
    if request.method == 'POST':
        settings.RECEIVE_DATA_ENABLED = not settings.RECEIVE_DATA_ENABLED
        return JsonResponse({'status': 'success', 'receive_data_enabled': settings.RECEIVE_DATA_ENABLED})
    else:
        return JsonResponse({'status': 'invalid request method'})

import socket

def get_ip_address(request):
    ip_address = socket.gethostbyname(socket.gethostname())
    return HttpResponse(f"Server IP Address: {ip_address}")



@csrf_exempt
def post_ph_sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ph_value = data.get('pH')
            ip_address = data.get('IP')
            print(f"Received pH value: {ph_value}")
            print(f"Received IP address: {ip_address}")
            
            # to  check the ip is whitelisted
            is_permitted=check_ip(ip_address)
            if is_permitted:
                ph_value_formatted = f'{ph_value:.4f}'
                timestamp = datetime.now()
                doc = {
                        'ph_value': ph_value,
                        'timestamp': ph_value_formatted
                    }
            
                
                db, collection = connect_to_mongodb('sensor','PH_data')
                if db is not None and collection is not None:
                    print("Connected to MongoDB successfully.")
                    # Use db and collection objects for further operations
                    # For example, insert data into collection
                    insertion_result = collection.insert_one(doc)
                    print(f"Inserted document ID: {insertion_result.inserted_id}")
                else:
                    print("Error connecting to MongoDB.")
            return JsonResponse({'message': 'pH data received successfully'}, status=200)
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def post_humid_temp_sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            humidity_value = data.get('humidity')
            temperature_value = data.get('temperature')
            ip_address = data.get('IP')
            print(f"Received pH value: {humidity_value}")
            print(f"Received pH value: {temperature_value}")
            print(f"Received IP address: {ip_address}")

            # to  check the ip is whitelisted
            is_permitted=check_ip(ip_address)
            if is_permitted:
                humidity_value_formatted = f'{humidity_value:.2f}'
                temperature_value_formatted = f'{temperature_value:.2f}'
                timestamp = datetime.now()
                doc = {
                        'humidity_value': humidity_value_formatted,
                        'temperature_value': temperature_value_formatted,
                        'timestamp': timestamp
                    }


                db, collection = connect_to_mongodb('sensor','humid_temperature_data')
                if db is not None and collection is not None:
                    print("Connected to MongoDB successfully.")
                    # Use db and collection objects for further operations
                    # For example, insert data into collection
                    insertion_result = collection.insert_one(doc)
                    print(f"Inserted document ID: {insertion_result.inserted_id}")
                else:
                    print("Error connecting to MongoDB.")
            return JsonResponse({'message': 'humidity and temperature data received successfully'}, status=200)
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

from pymongo import MongoClient
def check_ip(ip_address):
    mongo_uri = 'mongodb+srv://vicolee1363:KHw5zZkg8JirjK0E@cluster0.c0yyh6f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

    try:
        # Create a new client and connect to the server
        client = MongoClient(mongo_uri)
        db = client.sensor
        collection = db['permitted_ips']
        result = collection.find_one({'ip': ip_address})

        client.close()

        # Debug print to check if data is retrieved
        return result
    except Exception as e:
        # If an error occurs during MongoDB connection or data retrieval
        print(f"Error: {str(e)}")
        return False
    

def another_view(request):
    ip_to_check = '192.168.100.49'  # Example IP address to check

    # Call the is_ip_permitted function to check if the IP is permitted
    is_permitted = check_ip(ip_to_check)

    if is_permitted:
        return HttpResponse("IP is permitted.")
    else:
        return HttpResponse("IP is not permitted.")