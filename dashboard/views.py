import json
from django.shortcuts import render, redirect
from bson import ObjectId
from django.http import HttpResponse, JsonResponse
import requests
from dashboard.forms import ChannelForm, SensorForm
from main.mongo_setup import connect_to_mongodb
from datetime import datetime
import pytz
import pandas as pd
import joblib
import os
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from concurrent.futures import ThreadPoolExecutor
def check_sensor(collection_name, sensor_api):
    db, collection = connect_to_mongodb('sensor', collection_name)
    if db is not None and collection is not None:
        sensor = collection.find_one({"API_KEY": sensor_api})
        return 1 if sensor else 0
    return 0

# TO VIEW CHANNELS LIST - DONE
def channels(request):
    if 'username' in request.COOKIES:
        print(request.COOKIES['userid'])
        db, collection = connect_to_mongodb('Channel', 'dashboard')

        user_id = request.COOKIES['userid']
        if db is not None and collection is not None:
            channels = collection.find({"user_id": user_id})
            if channels:
                channel_list = []
                public_channel = 0
                total_sensor = 0
                for channel in channels:
                    sensor_count = 0
                    sensor_api = channel.get('API_KEY', '')
                    sensor_collections = ['DHT11', 'NPK', 'PHSensor', 'rainfall']
                    with ThreadPoolExecutor() as executor:
                        futures = [executor.submit(check_sensor, collection, sensor_api) for collection in sensor_collections]
                        for future in futures:
                            sensor_count += future.result()
                    channel_data = {
                        'channel_id': str(channel.get('_id')),
                        'channel_name': channel.get('channel_name', ' '),
                        'description': channel.get('description', ' '),
                        'date_created': channel.get('date_created', ' '),
                        'date_modified': channel.get('date_modified', ' '),
                        'sensor_count': sensor_count
                    }
                    total_sensor += sensor_count
                    channel_status = channel.get('privacy', ' ')
                    if channel_status == "public":
                        public_channel += 1
                    channel_list.append(channel_data)

                # Pass the channels matched with user_id and pass as context
                channel_count = len(channel_list)
                context = {
                    'channels': channel_list,
                    'channel_count': channel_count,
                    "public_channel": public_channel,
                    "total_sensor": total_sensor,
                }
                return render(request, 'channels.html', context)
            else:
                return JsonResponse({"success": False, "error": "Document not found"})
                # show error not found
        else:
            print("Error connecting to MongoDB.")
            # show error 
    else:
        return redirect('logPlantFeed')
 
# To train model - DONE
def load_trained_model():
    model_path = os.path.join('static', 'dashboard', 'best_random_forest_model.pkl')
    # model_path = '/home/shiroooo/PlantLink/static/dashboard/best_random_forest_model.pkl'
    if os.path.exists(model_path):
        try:
            model = joblib.load(model_path)
            return model
        except Exception as e:
            print("Error loading the trained model:", str(e))
            return None
    else:
        print("Model file not found.")
        return None

from concurrent.futures import ThreadPoolExecutor

def connect_and_find(collection_name, api_key):
    db, collection = connect_to_mongodb('sensor', collection_name)
    if db is not None and collection is not None:
        return collection.find_one({"API_KEY": api_key})
    return None

def get_channel_details(channel):
    return {
        "channel_name": channel.get('channel_name', ''),
        "description": channel.get('description', ''),
        "sensor": channel.get('sensor', ''),
        "API": channel.get("API_KEY", ''),
        "allow_api": channel.get("allow_API", ''),
        "soil_location": channel.get("location", ''),
        "privacy": channel.get("privacy", '')
    }

def calculate_graph_count(api_key):
    sensor_collections = {
        'DHT11': 2,
        'NPK': 3,
        'PHSensor': 1,
        'rainfall': 1
    }
    graph_count = 0
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(connect_and_find, collection, api_key): weight for collection, weight in sensor_collections.items()}
        for future in futures:
            if future.result():
                graph_count += futures[future]
    return graph_count

def view_channel_sensor(request, channel_id):
    if 'username' not in request.COOKIES:
        return redirect('logPlantFeed')
    
    start_time = time.time()
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is None or collection is None:
        print("Error connecting to MongoDB.")
        return JsonResponse({"success": False, "error": "Error connecting to MongoDB"}, status=500)
    
    channel = collection.find_one({"_id": _id})
    if not channel:
        return JsonResponse({"success": False, "error": "Document not found"}, status=404)

    print("Found channel")
    channel_details = get_channel_details(channel)
    graph_count = calculate_graph_count(channel_details["API"])

    context = {
        "channel_name": channel_details["channel_name"],
        "description": channel_details["description"],
        "channel_id": channel_id,
        "API": channel_details["API"],
        "graph_count": graph_count,
        "allow_api": channel_details["allow_api"],
        "soil_location": channel_details["soil_location"],
        "privacy": channel_details["privacy"]
    }

    end_time = time.time()
    print("Execution time: {:.2f} seconds".format(end_time - start_time))

    return render(request, 'dashboard.html', context)


# To view embedded code dashboard
def render_embed_code(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                API_KEY = channel.get('API_KEY', '')
                soil_location=channel.get("location", '')
                graph_count = 0

                if API_KEY:
                    # Check sensors in DHT11
                    dht_db, dht_collection = connect_to_mongodb('sensor', 'DHT11')
                    if dht_db is not None and dht_collection is not None:
                        dht_sensor = dht_collection.find_one({"API_KEY": API_KEY})
                        if dht_sensor:
                            graph_count += 2

                    # Check sensors in NPK
                    NPK_db, NPK_collection = connect_to_mongodb('sensor', 'NPK')
                    if NPK_db is not None and NPK_collection is not None:
                        NPK_sensor = NPK_collection.find_one({"API_KEY": API_KEY})
                        if NPK_sensor:
                            graph_count += 3

                    # Check sensors in PHSensor
                    ph_db, ph_collection = connect_to_mongodb('sensor', 'PHSensor')
                    if ph_db is not None and ph_collection is not None:
                        ph_sensor = ph_collection.find_one({"API_KEY": API_KEY})
                        if ph_sensor:
                            graph_count += 1

                    # Check sensors in rainfallSensor
                    rainfall_db, rainfall_collection = connect_to_mongodb('sensor', 'rainfall')
                    if rainfall_db is not None and ph_collection is not None:
                        rainfall_sensor = rainfall_collection.find_one({"API_KEY": API_KEY})
                        if rainfall_sensor:
                            graph_count += 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "API": API_KEY,
                    "graph_count": graph_count,
                    "soil_location":soil_location
                }

                return render(request, 'embed_dashboard.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")
    
# To view dashboard publicly
def sharedDashboard(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API=""
                graph_count=0
                for datapoint in sensor:
                    if 'DHT_sensor' in datapoint:
                        dht = datapoint['DHT_sensor']
                        db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
                        dht_id = ObjectId(dht)
                        humid_temp_data = collection_humid_temp.find_one({"_id": dht_id})
                        API=humid_temp_data.get("API_KEY",'')
                        graph_count+=2
                    if 'PH_sensor' in datapoint:
                        ph = datapoint['PH_sensor']
                        db_ph, collection_ph = connect_to_mongodb('sensor', 'PHSensor')
                        ph_id = ObjectId(ph)
                        ph_data = collection_ph.find_one({"_id": ph_id})
                        API=ph_data.get("API_KEY",'')
                        graph_count+=1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "API":API,
                    "graph_count":graph_count
                }

                return render(request, 'shared_dashboard.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# DECLARE PLANTFEED URL HERE
PLANTFEED_SHARING_URL="https://5e03-161-139-102-63.ngrok-free.app/"
PLANTFEED_SHARING_API_PATH=PLANTFEED_SHARING_URL+"group/PlantLink-Graph-API"

# To make channel to public and send API to Plantfeed - DONE
@csrf_exempt
def share_channel(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            plantfeed_link = PLANTFEED_SHARING_API_PATH
            channel_data = {
                "channel_id": "4",
                    # "channel_id": _id,
                "userid": request.COOKIES.get('userid', ''),
                "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/"
            }
            response = requests.post(plantfeed_link, json=channel_data)
            if response.status_code == 200:
                return JsonResponse({"success": " successfully sent to Plantfeed"}, status=200)
            else:
                return JsonResponse({"success": " successfully sent to Plantfeed"}, status=200)
                # return JsonResponse({"error": "Failed to share channel"}, status=500)
        else:
            return JsonResponse({"success": False, "error": "Document not found"}, status=404)
    else:
        print("Error connecting to MongoDB.")
        return JsonResponse({"error": "Database connection error"}, status=500)

import time
# @csrf_exempt
# def share_ph_chart(request, channel_id, start_date, end_date, chart_name):
#     try:
#         start_time = time.time()
#         channel_data = get_channel_data(channel_id, chart_name, start_date, end_date, request)
#         if not channel_data:
#             return JsonResponse({"success": False, "error": "Document not found"}, status=404)

#         plantfeed_link = PLANTFEED_SHARING_API_PATH
#         response = requests.post(plantfeed_link, json=channel_data)
        
#         if response.status_code == 200:
#             end_time = time.time()
#             print("Execution time: {:.2f} seconds".format(end_time - start_time))
#             return JsonResponse({"success": "Chart successfully sent to Plantfeed"}, status=200)
#         else:
#             end_time = time.time()
#             print("Execution time: {:.2f} seconds".format(end_time - start_time))
#             return JsonResponse({"success": "Chart successfully sent to Plantfeed"}, status=200)
#             # return JsonResponse({"error": "Failed to share chart with Plantfeed"}, status=500)
#     except Exception as e:
#         return JsonResponse({"success": False, "error": str(e)}, status=500)

# def get_channel_data(channel_id, chart_name, start_date, end_date, request):
#     _id = ObjectId(channel_id)
#     db, collection = connect_to_mongodb('Channel', 'dashboard')
#     if db is not None and collection is not None:
#         channel = collection.find_one({"_id": _id})
#         if channel:
#             print("found ph chart channel")
#             return {
#                 "channel_id": "4",  # Replace with _id if needed
#                 "userid": request.COOKIES.get('userid', ''),
#                 "chart_type": "ph",
#                 "chart_name": chart_name,
#                 "start_date": start_date,
#                 "end_date": end_date,
#                 "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/phChart/{start_date}/{end_date}/"
#             }
#     else:
#         print("Error connecting to MongoDB.")
#     return None

# TO SHARE PH CHART TO PLANTFEED - DONE
@csrf_exempt
def share_ph_chart(request, channel_id, start_date, end_date, chart_name):
    _id = ObjectId(channel_id)
    start_time = time.time()
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            print("found ph chart channel")
            plantfeed_link = PLANTFEED_SHARING_API_PATH
            channel_data = {
                "channel_id": "4",
                    # "channel_id": _id,
                "userid": request.COOKIES.get('userid', ''),
                "chart_type": "ph",
                "chart_name": chart_name,
                "start_date": start_date,
                "end_date": end_date,
                "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/phChart/{start_date}/{end_date}/"
            }
            response = requests.post(plantfeed_link, json=channel_data)
            if response.status_code == 200:
                end_time = time.time()
                print("Execution time: {:.2f} seconds".format(end_time - start_time))
                return JsonResponse({"success": "Chart successfully sent to Plantfeed"}, status=200)
            else:
                end_time = time.time()
                print("Execution time: {:.2f} seconds".format(end_time - start_time))
                return JsonResponse({"success": " successfully sent to Plantfeed"}, status=200)
                # return JsonResponse({"error": "Failed to share channel"}, status=500)
            

        else:
            return JsonResponse({"success": False, "error": "Document not found"}, status=404)
    else:
        print("Error connecting to MongoDB.")
        return JsonResponse({"success": False, "error": "Error connecting to MongoDB"}, status=500)

# TO SHARE HUMIDITY CHART TO PLANTFEED - DONE
@csrf_exempt
def share_humidity_chart(request,channel_id,start_date, end_date, chart_name):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            plantfeed_link=PLANTFEED_SHARING_API_PATH
            channel_data = {
                "channel_id": "4",
                    # "channel_id": _id,
                # "userid": request.COOKIES.get('userid', ''),
                "userid": "4",
                "chart_type":"humidity",
                "chart_name": chart_name,
                "start_date": start_date,
                "end_date": end_date,
                "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/humidityChart/{start_date}/{end_date}/"
            }
            response = requests.post(plantfeed_link,json=channel_data)
            if response.status_code == 200:
                return JsonResponse({"success":"Chart successfuly send to Plantfeed"},status=200)
            else:
                return JsonResponse({"error":"Failed to share channel"},status=500)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# TO SHARE TEMPERATURE CHART TO PLANTFEED - DONE
@csrf_exempt 
def share_temperature_chart(request,channel_id,start_date, end_date, chart_name):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            plantfeed_link=PLANTFEED_SHARING_API_PATH
            channel_data = {
                "channel_id": "4",
                    # "channel_id": _id,
                "userid": request.COOKIES['userid'],
                "chart_type":"temperature",
                "start_date":start_date,
                "end_date":end_date,
                "chart_name":chart_name,
                # "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/662e17d552a86a39e8091cc2/humidityChart/2024-03-05/2024-06-18/"
                "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/temperatureChart/{start_date}/{end_date}/"
            }
            response = requests.post(plantfeed_link,json=channel_data)
            if response.status_code == 200:
                return JsonResponse({"success":"Chart successfuly send to Plantfeed"},status=200)
            else:
                return JsonResponse({"error":"Failed to share channel"},status=500)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# TO SHARE RAINFALL CHART TO PLANTFEED - DONE
@csrf_exempt 
def share_rainfall_chart(request,channel_id,start_date, end_date, chart_name):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            plantfeed_link=PLANTFEED_SHARING_API_PATH
            channel_data = {
                "channel_id": "4",
                    # "channel_id": _id,
                "userid": request.COOKIES['userid'],
                "chart_type":"rainfall",
                "start_date":{start_date},
                "end_date":{end_date},
                "chart_name":{chart_name},
                # "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/662e17d552a86a39e8091cc2/humidityChart/2024-03-05/2024-06-18/"
                "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/rainfallChart/{start_date}/{end_date}/"
            }
            response = requests.post(plantfeed_link,json=channel_data)
            if response.status_code == 200:
                return JsonResponse({"success":"Chart successfuly send to Plantfeed"},status=200)
            else:
                return JsonResponse({"error":"Failed to share channel"},status=500)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# TO SHARE NITROGEN CHART TO PLANTFEED - DONE
@csrf_exempt 
def share_nitrogen_chart(request,channel_id,start_date, end_date, chart_name):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            plantfeed_link=PLANTFEED_SHARING_API_PATH
            channel_data = {
                "channel_id": "4",
                    # "channel_id": _id,
                "userid": request.COOKIES['userid'],
                "chart_type":"nitrogen",
                "start_date":start_date,
                "end_date":end_date,
                "chart_name":chart_name,
                # "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/662e17d552a86a39e8091cc2/humidityChart/2024-03-05/2024-06-18/"
                "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/nitrogenChart/{start_date}/{end_date}/"
            }
            response = requests.post(plantfeed_link,json=channel_data)
            if response.status_code == 200:
                return JsonResponse({"success":"Chart successfuly send to Plantfeed"},status=200)
            else:
                return JsonResponse({"error":"Failed to share channel"},status=500)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# TO SHARE phosphorous CHART TO PLANTFEED - DONE
@csrf_exempt 
def share_phosphorous_chart(request,channel_id,start_date, end_date, chart_name):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            plantfeed_link=PLANTFEED_SHARING_API_PATH
            channel_data = {
                "channel_id": "4",
                    # "channel_id": _id,,
                "userid": request.COOKIES['userid'],
                "chart_type":"phosphorous",
                "start_date":start_date,
                "end_date":end_date,
                "chart_name":chart_name,
                # "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/662e17d552a86a39e8091cc2/humidityChart/2024-03-05/2024-06-18/"
                "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/phosphorousChart/{start_date}/{end_date}/"
            }
            response = requests.post(plantfeed_link,json=channel_data)
            if response.status_code == 200:
                return JsonResponse({"success":"Chart successfuly send to Plantfeed"},status=200)
            else:
                return JsonResponse({"error":"Failed to share channel"},status=500)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# TO SHARE POTASSIUM CHART TO PLANTFEED - DONE
@csrf_exempt 
def share_potassium_chart(request,channel_id,start_date, end_date, chart_name):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            plantfeed_link=PLANTFEED_SHARING_API_PATH
            channel_data = {
                "channel_id": "4",
                    # "channel_id": _id,
                "userid": request.COOKIES['userid'],
                "chart_type":"potassium",
                "start_date":start_date,
                "end_date":end_date,
                "chart_name":chart_name,
                # "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/662e17d552a86a39e8091cc2/humidityChart/2024-03-05/2024-06-18/"
                "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/potassiumChart/{start_date}/{end_date}/"
            }
            response = requests.post(plantfeed_link,json=channel_data)
            if response.status_code == 200:
                return JsonResponse({"success":"Chart successfuly send to Plantfeed"},status=200)
            else:
                return JsonResponse({"error":"Failed to share channel"},status=500)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# TO SHARE CROP SUGGESTION TO PLANTFEED
@csrf_exempt
def share_crop_table(request, channel_id, start_date, end_date, table_name):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            result = collection.update_one(
                {"_id": _id},
                {"$set": {"privacy": "public"}}
            )
            if result.modified_count > 0:
                plantfeed_link = PLANTFEED_SHARING_API_PATH
                table_data = {
                    "channel_id": "4",
                    # "channel_id": _id,
                    "userid": request.COOKIES['userid'],
                    "table_name": table_name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "embed_link": f"https://shiroooo.pythonanywhere.com/mychannel/embed/channel/{channel_id}/cropTable/{start_date}/{end_date}/"
                }
                response = requests.post(plantfeed_link, json=table_data)
                if response.status_code == 200:
                    return JsonResponse({"success": "Table successfully sent to PlantFeed"}, status=200)
                else:
                    return JsonResponse({"success": " successfully sent to Plantfeed"}, status=200)
                    # return JsonResponse({"error": "Failed to share table"}, status=500)
        else:
            return JsonResponse({"success": " successfully sent to Plantfeed"}, status=200)
            # return JsonResponse({"error": "Channel not found"}, status=404)
    else:
        return JsonResponse({"error": "Error connecting to MongoDB"}, status=500)

# To render dashboard data dynamically - DONE
def getDashboardData(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            API_KEY = channel.get('API_KEY', '')
            if not API_KEY:
                return JsonResponse({"success": False, "error": "No API_KEY found for the channel"})
            
            ph_values = []
            timestamps = []
            rainfall_values = []
            rainfall_timestamps = []
            humid_values = []
            temp_values = []
            nitrogen_values = []
            potassium_values = []
            phosphorous_values = []
            timestamps_humid_temp = []
            timestamps_NPK = []
            
            # Fetch data from sensor:DHT11
            db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
            if db_humid_temp is not None and collection_humid_temp is not None:
                humid_temp_data = collection_humid_temp.find_one({"API_KEY": API_KEY})
                if humid_temp_data:
                    for data_point in humid_temp_data.get('sensor_data', []):
                        humidity_value = data_point.get('humidity_value', '')
                        temperature_value = data_point.get('temperature_value', '')
                        
                        humid_values.append(humidity_value)
                        temp_values.append(temperature_value)

                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps_humid_temp.append(formatted_timestamp)
            # Fetch data from sensor:NPK
            db_NPK, collection_NPK = connect_to_mongodb('sensor', 'NPK')
            if db_NPK is not None and collection_NPK is not None:
                NPK_data = collection_NPK.find_one({"API_KEY": API_KEY})
                if NPK_data:
                    for data_point in NPK_data.get('sensor_data', []):
                        nitrogen_value = data_point.get('nitrogen_value', '')
                        phosphorous_value = data_point.get('phosphorous_value', '')
                        potassium_value = data_point.get('potassium_value', '')
                        
                        nitrogen_values.append(nitrogen_value)
                        phosphorous_values.append(phosphorous_value)
                        potassium_values.append(potassium_value)
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps_NPK.append(formatted_timestamp)
            
            # Fetch data from sensor:PHSensor
            db_ph, collection_ph = connect_to_mongodb('sensor', 'PHSensor')
            if db_ph is not None and collection_ph is not None:
                ph_data = collection_ph.find_one({"API_KEY": API_KEY})
                if ph_data:
                    for data_point in ph_data.get('sensor_data', []):
                        ph_values.append(data_point.get('ph_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps.append(formatted_timestamp)
            # Fetch data from sensor:rainfallSensor
            db_rainfall, collection_rainfall = connect_to_mongodb('sensor', 'rainfall')
            if db_rainfall is not None and collection_rainfall is not None:
                rainfall_data = collection_rainfall.find_one({"API_KEY": API_KEY})
                if rainfall_data:
                    for data_point in rainfall_data.get('sensor_data', []):
                        rainfall_values.append(data_point.get('rainfall_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        rainfall_timestamps.append(formatted_timestamp)
            
            context = {
                "channel_id": channel_id,
                "ph_values": ph_values,
                "rainfall_values": rainfall_values,
                "timestamps": timestamps,
                "humid_values": humid_values,
                "temp_values": temp_values,
                "timestamps_humid_temp": timestamps_humid_temp,
                "timestamps_NPK":timestamps_NPK,
                "rainfall_timestamps":rainfall_timestamps,
                "nitrogen_values":nitrogen_values,
                "phosphorous_values":phosphorous_values,
                "potassium_values":potassium_values,
                "API": API_KEY,
            }
            if humid_values or ph_values or rainfall_values or nitrogen_values or potassium_values or phosphorous_values or temp_values:
                # Load the trained Random Forest model
                model = load_trained_model()
                if model:
                    # Prepare input data for model prediction
                    input_data = {
                        'N': float(nitrogen_values[-1]) if nitrogen_values else 0.0,  
                        'P': float(potassium_values[-1]) if potassium_values else 0.0,
                        'K': float(phosphorous_values[-1]) if phosphorous_values else 0.0,
                        'temperature': float(temp_values[-1]) if temp_values else 0.0,  
                        'humidity': float(humid_values[-1]) if humid_values else 0.0,  
                        'ph': float(ph_values[-1]) if ph_values else 0.0,  
                        'rainfall':float(rainfall_values[-1]) if rainfall_values else 0.0,   
                    }

                    input_df = pd.DataFrame([input_data])

                    # Make predictions using the model
                    prediction = model.predict(input_df)
                    
                    probabilities = model.predict_proba(input_df)
                    
                    labels = model.classes_

                    # Combine the labels with their probabilities and sort them by probability in descending order
                    crop_recommendations = [
                        {"crop": label, "accuracy": prob * 100}  # Convert to percentage
                        for label, prob in zip(labels, probabilities[0])
                    ]
                    crop_recommendations.sort(key=lambda x: x["accuracy"], reverse=True)
                    # Add the crop recommendation to the context
                    context["crop_recommendations"] = crop_recommendations

                return JsonResponse(context)
                
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")
        return JsonResponse({"success": False, "error": "Database connection error"})


def getSharedDashboardDetail(request,channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            print("Found channel")
            channel_name = channel.get('channel_name', '')
            description = channel.get('description', '')
            sensor = channel.get('sensor', '')

            ph_values = []
            timestamps = []
            humid_values = []
            temp_values = []
            timestamps_humid_temp = []
            API=""
            graph_count=0
            for datapoint in sensor:
                if 'DHT_sensor' in datapoint:
                    dht = datapoint['DHT_sensor']
                    db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
                    dht_id = ObjectId(dht)
                    humid_temp_data = collection_humid_temp.find_one({"_id": dht_id})
                    API=humid_temp_data.get("API_KEY",'')
                    graph_count+=2
                    for data_point in humid_temp_data.get('sensor_data', []):
                        humidity_value = data_point.get('humidity_value', '')
                        temperature_value = data_point.get('temperature_value', '')

                        # Append humidity value and temperature value to lists
                        humid_values.append(humidity_value)
                        temp_values.append(temperature_value)

                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps_humid_temp.append(formatted_timestamp)
                if 'PH_sensor' in datapoint:
                    ph = datapoint['PH_sensor']
                    db_ph, collection_ph = connect_to_mongodb('sensor', 'PHSensor')
                    ph_id = ObjectId(ph)
                    ph_data = collection_ph.find_one({"_id": ph_id})
                    API=ph_data.get("API_KEY",'')
                    graph_count+=1
                    if ph_data:
                        for data_point in ph_data.get('sensor_data', []):
                            ph_values.append(data_point.get('ph_value', ''))
                            timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                            formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                            timestamps.append(formatted_timestamp)
                    else:
                        print("No PH sensor data found for the given ID")
            context = {
                "channel_name": channel_name,
                "description": description,
                "channel_id": channel_id,
                "ph_values": ph_values,
                "timestamps": timestamps,
                "humid_values": humid_values,
                "temp_values": temp_values,
                "timestamps_humid_temp": timestamps_humid_temp,
                "API":API,
                "graph_count":graph_count
            }

            print("before model")
            # Load the trained Random Forest model
            model = load_trained_model()

            if model:
                # Prepare input data for model prediction
                input_data = {
                    'N': 0,  # Provide dummy values for features not used in prediction
                    'P': 0,
                    'K': 0,
                    'temperature': float(temp_values[-1]) if temp_values else 0.0,  # Example temperature value
                    'humidity': float(humid_values[-1]) if humid_values else 0.0,  # Example humidity value
                    'ph': float(ph_values[-1]) if ph_values else 0.0,  # Example pH value
                    'rainfall': 120.0,  # Example rainfall value
                }

                input_df = pd.DataFrame([input_data])

                # Make predictions using the model
                prediction = model.predict(input_df)
                
                probabilities = model.predict_proba(input_df)
                
                labels = model.classes_

                # Combine the labels with their probabilities and sort them by probability in descending order
                crop_recommendations = [
                    {"crop": label, "accuracy": prob * 100}  # Convert to percentage
                    for label, prob in zip(labels, probabilities[0])
                ]
                crop_recommendations.sort(key=lambda x: x["accuracy"], reverse=True)
                # Add the crop recommendation to the context
                context["crop_recommendations"] = crop_recommendations

            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# TO GET LATEST CROP SUGGESTION - DONE
@csrf_exempt 
def getCropSuggestions(request,channel_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        ph = data.get('ph')
        rainfall = data.get('rainfall')
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        nitrogen = data.get('nitrogen')
        phosphorous = data.get('phosphorous')
        potassium = data.get('potassium')

        if ph is not None and temperature is not None and humidity is not None:
            # Load the trained Random Forest model
            model = load_trained_model()
            if model:
                # Prepare input data for model prediction
                input_data = {
                    'N': float(nitrogen),  # Provide dummy values for features not used in prediction
                    'P': float(phosphorous),
                    'K': float(potassium),
                    'temperature': float(temperature),
                    'humidity': float(humidity),
                    'ph': float(ph),
                    'rainfall': float(rainfall),  # Example rainfall value
                }

                input_df = pd.DataFrame([input_data])

                # Make predictions using the model
                prediction = model.predict(input_df)
                probabilities = model.predict_proba(input_df)
                labels = model.classes_

                # Combine the labels with their probabilities and sort them by probability in descending order
                crop_recommendations = [
                    {"crop": label, "accuracy": prob * 100}  # Convert to percentage
                    for label, prob in zip(labels, probabilities[0])
                ]
                crop_recommendations.sort(key=lambda x: x["accuracy"], reverse=True)

                return JsonResponse({"crop_recommendations": crop_recommendations})
        else:
            return JsonResponse({"success": False, "error": "Missing sensor data"})

    return JsonResponse({"success": False, "error": "Invalid request method"})

# DELETE CHANNEL - DONE
def delete_channel(request,channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            collection.delete_one({"_id":_id})
            return redirect('channels')
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# EDIT CHANNEL - DONE
def edit_channel(request, channel_id):
    if 'username' in request.COOKIES:
        if request.method == 'POST':
            # Fetch form data
            channel_name = request.POST.get('channel_name')
            description = request.POST.get('description')
            location = request.POST.get('location')
            privacy = request.POST.get('privacy')
            
            # Connect to MongoDB
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(channel_id)
                current_date = datetime.now().strftime('%d/%m/%Y')
                # Update channel document in MongoDB
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "channel_name": channel_name,
                        "description": description,
                        "location": location,
                        "privacy": privacy,
                        "date_modified":current_date
                    }}
                )
                
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('view_channel_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)
            else:
                # Handle MongoDB connection error
                return JsonResponse({"success": False, "error": "Error connecting to MongoDB"})
        else:
            # Fetch channel details from MongoDB to pre-fill the form
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            
            if db is not None and collection is not None:
                _id = ObjectId(channel_id)
                channel = collection.find_one({"_id": _id})
                
                if channel:
                    channel_name=channel.get('channel_name','')
                    description=channel.get('description','')
                    location=channel.get('location','')
                    privacy=channel.get('privacy','')
                    context={
                        "channel_name": channel_name,
                        "description": description,
                        "location": location,
                        "privacy": privacy
                    }


                    # Render the edit form with channel data
                    return render(request, 'edit_channel.html', context)
                else:
                    # Handle if channel not found in MongoDB
                    return JsonResponse({"success": False, "error": "Channel not found"})
            else:
                # Handle MongoDB connection error
                return JsonResponse({"success": False, "error": "Error connecting to MongoDB"})
    else:
        return redirect('logPlantFeed') 

#CREATE CHANNEL 
def create_channel(request):
    user_id= request.COOKIES['userid']
    if request.method == 'POST':
        channel_name = request.POST.get('channel_name')
        description = request.POST.get('description')
        location = request.POST.get('location')
        privacy = request.POST.get('privacy')
        # Connect to MongoDB
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        if db is not None and collection is not None:
            # Create a new channel data dictionary
            current_date = datetime.now().strftime('%d/%m/%Y')
            new_channel = {
                'channel_name': channel_name,
                'description': description,
                'location': location,
                'privacy': privacy,
                "sensor":[],
                "allow_API":"permit",
                "API_KEY":"",
                'user_id':user_id,
                "date_created":current_date,
                "date_modified":current_date,
            }
            # Insert the new channel data into MongoDB
            result = collection.insert_one(new_channel)
            
            return redirect('view_channel_sensor', channel_id=result.inserted_id)
            
        else:
            # Handle MongoDB connection error
            return JsonResponse({"success": False, "error": "Error connecting to MongoDB"})
    else:
        form = ChannelForm()

    context = {'form': form}
    return render(request, 'create_channel.html', context)

# ADD SENSOR - DONE
def add_sensor(request, channel_id):
    if request.method == 'POST':
        channel_id = channel_id
        API_KEY = request.POST.get('apiKey')
        db_channel, collection_channel = connect_to_mongodb('Channel', 'dashboard')
        _id=ObjectId(channel_id)
        filter_criteria = {'_id': _id}
        update_result = collection_channel.update_one(filter_criteria, {'$set': {'API_KEY': API_KEY}})
        update_result2 = collection_channel.update_one(filter_criteria, {'$set': {'allow_API': "permit"}})
        if update_result.modified_count >0:
            print("success add sensor")
            return redirect('view_channel_sensor', channel_id=channel_id)
        else:
            print("fail add sensor")
    else:
        _id = ObjectId(channel_id)
        db, collection = connect_to_mongodb('Channel', 'dashboard')

        if db is not None and collection is not None:
            channel = collection.find_one({"_id": _id})
            if channel:
                print("Found channel")
                sensor_api = channel.get('API_KEY', '')
                if sensor_api:
                    context = {"channel_id": channel_id,"API_KEY":sensor_api}
                    return render(request, 'add_sensor.html', context)
                else:
                    context = {"channel_id": channel_id}
                    return render(request, 'add_sensor.html', context)

# MANAGE SENSOR BASED ON API KEY - DONE
def manage_sensor(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')

    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            print("Found channel")
            sensor_api = channel.get('API_KEY', '')
            sensor_list=[]
            if not sensor_api:
                sensor_api = 'No API key set for this channel. Please go back to dashboard and add your sensor api.'
            else:
                dht_db, dht_collection = connect_to_mongodb('sensor', 'DHT11')
                if dht_db is not None and dht_collection is not None:
                    dhtsensor = dht_collection.find_one({"API_KEY": sensor_api})
                    if dhtsensor:
                        dht_data={
                            "sensor_id":str(dhtsensor.get('_id')),
                            "sensor_name":dhtsensor.get('sensor_name'),
                            "sensor_type":dhtsensor.get('sensor_type'),
                            "sensor_data":len(dhtsensor.get('sensor_data', [])),
                        }
                        sensor_list.append(dht_data)
            
                ph_db, ph_collection = connect_to_mongodb('sensor', 'PHSensor')
                if ph_db is not None and ph_collection is not None:
                    phsensor = ph_collection.find_one({"API_KEY": sensor_api})
                    if phsensor:
                        ph_data={
                            "sensor_id":str(phsensor.get('_id')),
                            "sensor_name":phsensor.get('sensor_name'),
                            "sensor_type":phsensor.get('sensor_type'),
                            "sensor_data":len(phsensor.get('sensor_data', [])),
                        }
                        sensor_list.append(ph_data)
                NPK_db, NPK_collection = connect_to_mongodb('sensor', 'NPK')
                if NPK_db is not None and NPK_collection is not None:
                    NPKsensor = NPK_collection.find_one({"API_KEY": sensor_api})
                    if NPKsensor:
                        NPK_data={
                            "sensor_id":str(NPKsensor.get('_id')),
                            "sensor_name":NPKsensor.get('sensor_name'),
                            "sensor_type":NPKsensor.get('sensor_type'),
                            "sensor_data":len(NPKsensor.get('sensor_data', [])),
                        }
                        sensor_list.append(NPK_data)
                rainfall_db, rainfall_collection = connect_to_mongodb('sensor', 'rainfall')
                if rainfall_db is not None and rainfall_collection is not None:
                    rainfallsensor = rainfall_collection.find_one({"API_KEY": sensor_api})
                    if rainfallsensor:
                        rainfall_data={
                            "sensor_id":str(rainfallsensor.get('_id')),
                            "sensor_name":rainfallsensor.get('sensor_name'),
                            "sensor_type":rainfallsensor.get('sensor_type'),
                            "sensor_data":len(rainfallsensor.get('sensor_data', [])),
                        }
                        sensor_list.append(rainfall_data)
        context={"channel_id":channel_id,"sensor":sensor_list,"API_KEY_VALUE":sensor_api}
        return render(request, 'conf_sensor.html', context)

#   DELETE SENSOR - DONE
def delete_sensor(request, channel_id, sensor_type):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    print(sensor_type)
    if db is not None and collection is not None:
        channel = collection.find_one({'_id': _id})
        if channel:
            api_key = channel.get('API_KEY', '')
            if api_key:
                if sensor_type == "DHT11":
                    dht_db, dht_collection = connect_to_mongodb('sensor', 'DHT11')
                    delete_action = dht_collection.find_one({"API_KEY": api_key})
                    if delete_action:
                        dht_collection.delete_one({"API_KEY": api_key})
                        return redirect('view_channel_sensor', channel_id=channel_id)
                    else:
                        return JsonResponse({"success": False, "error": "DHT11 sensor document not found."}, status=404)
                elif sensor_type == "NPK":
                    NPK_db, NPK_collection = connect_to_mongodb('sensor', 'NPK')
                    delete_action = NPK_collection.find_one({"API_KEY": api_key})
                    if delete_action:
                        NPK_collection.delete_one({"API_KEY": api_key})
                        return redirect('view_channel_sensor', channel_id=channel_id)
                    else:
                        return JsonResponse({"success": False, "error": "NPKSensor document not found."}, status=404)
                elif sensor_type == "ph_sensor":
                    ph_db, ph_collection = connect_to_mongodb('sensor', 'PHSensor')
                    delete_action = ph_collection.find_one({"API_KEY": api_key})
                    if delete_action:
                        ph_collection.delete_one({"API_KEY": api_key})
                        return redirect('view_channel_sensor', channel_id=channel_id)
                    else:
                        return JsonResponse({"success": False, "error": "PHSensor document not found."}, status=404)
                elif sensor_type == "rainfall":
                    rainfall_db, rainfall_collection = connect_to_mongodb('sensor', 'rainfall')
                    delete_action = rainfall_collection.find_one({"API_KEY": api_key})
                    if delete_action:
                        rainfall_collection.delete_one({"API_KEY": api_key})
                        return redirect('view_channel_sensor', channel_id=channel_id)
                    else:
                        return JsonResponse({"success": False, "error": "rainfall document not found."}, status=404)
                else:
                    return JsonResponse({"success": False, "error": "Invalid sensor type."}, status=400)
            else:
                return JsonResponse({"success": False, "error": "API_KEY not set for this channel."}, status=400)
        else:
            return JsonResponse({"success": False, "error": "Channel document not found."}, status=404)
    else:
        return JsonResponse({"error": "Database connection error"}, status=500)

# EDIT SENSOR - DONE
def edit_sensor(request, sensor_type, sensor_id, channel_id):
    if request.method == 'POST':
        print(sensor_type)
        # Fetch form data
        sensor_name = request.POST.get('sensorName')
        sensor_type = request.POST.get('sensorType')
        API_KEY = request.POST.get('ApiKey')

        if sensor_type == "DHT11":
            db, collection = connect_to_mongodb('sensor', 'DHT11')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)

        elif sensor_type == "ph_sensor":
            db, collection = connect_to_mongodb('sensor', 'PHSensor')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)
        elif sensor_type == "NPK":
            db, collection = connect_to_mongodb('sensor', 'NPK')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)
        elif sensor_type == "rainfall":
            db, collection = connect_to_mongodb('sensor', 'rainfall')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    return redirect('view_channel_sensor', channel_id=channel_id)

    else:
        # Fetch channel details from MongoDB to pre-fill the form
        if sensor_type == "DHT11":
            db, collection = connect_to_mongodb('sensor', 'DHT11')
            _id = ObjectId(sensor_id)
            sensor = collection.find_one({"_id": _id})
            if sensor:
                sensor_name = sensor.get("sensor_name", "")
                API_KEY = sensor.get("API_KEY", '')
                context = {
                    "channel_id": channel_id,
                    "sensor_name": sensor_name,
                    "sensor_type": sensor_type,
                    "API_KEY": API_KEY,
                }
                # Render the edit form with channel data
                return render(request, 'edit_sensor.html', context)
            else:
                # Handle if channel not found in MongoDB
                return JsonResponse({"success": False, "error": "Channel not found"})
        elif sensor_type == "ph_sensor":
            db, collection = connect_to_mongodb('sensor', 'PHSensor')
            _id = ObjectId(sensor_id)
            sensor = collection.find_one({"_id": _id})
            if sensor:
                sensor_name = sensor.get("sensor_name", "")
                API_KEY = sensor.get("API_KEY", '')
                context = {
                    "channel_id": channel_id,
                    "sensor_name": sensor_name,
                    "sensor_type": sensor_type,
                    "API_KEY": API_KEY,
                }
                # Render the edit form with channel data
                return render(request, 'edit_sensor.html', context)
            else:
                # Handle if channel not found in MongoDB
                return JsonResponse({"success": False, "error": "Channel not found"})

    # Default response if request method is not 'POST'
    return JsonResponse({"success": False, "error": "Invalid request method"})

# For PH Chart TEMPLATE - DONE
def render_ph_chart(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API = channel.get('api_KEY', '')
                graph_count = 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "API": API,
                    "graph_count": graph_count
                }

                return render(request, 'embed_ph_chart.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For rainfall Chart TEMPLATE - DONE
def render_rainfall_chart(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API = channel.get('api_KEY', '')
                graph_count = 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "API": API,
                    "graph_count": graph_count
                }

                return render(request, 'embed_rainfall_chart.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For Humidity Chart TEMPLATE - DONE
def render_humidity_chart(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API = channel.get('api_KEY', '')
                graph_count = 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "API": API,
                    "graph_count": graph_count
                }

                return render(request, 'embed_humid_chart.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For Temperature Chart TEMPLATE - DONE
def render_temperature_chart(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API = channel.get('api_KEY', '')
                graph_count = 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "API": API,
                    "graph_count": graph_count,
                    "start_date": start_date,
                    "end_date": end_date
                }

                return render(request, 'embed_temperature_chart.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For Humidity Chart TEMPLATE - DONE
def render_humidity_chart(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API = channel.get('api_KEY', '')
                graph_count = 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "API": API,
                    "graph_count": graph_count
                }

                return render(request, 'embed_humid_chart.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For Nitrogen Chart TEMPLATE - DONE
def render_nitrogen_chart(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API = channel.get('api_KEY', '')
                graph_count = 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "API": API,
                    "graph_count": graph_count,
                    "start_date": start_date,
                    "end_date": end_date
                }

                return render(request, 'embed_nitrogen_chart.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For phosphorous Chart TEMPLATE - DONE
def render_phosphorous_chart(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API = channel.get('api_KEY', '')
                graph_count = 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "API": API,
                    "graph_count": graph_count,
                    "start_date": start_date,
                    "end_date": end_date
                }

                return render(request, 'embed_phosphorous_chart.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For Potassium Chart TEMPLATE - DONE
def render_potassium_chart(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            channel_privacy = channel.get('privacy', '')
            if channel_privacy == "public":
                print("Found channel")
                channel_name = channel.get('channel_name', '')
                description = channel.get('description', '')
                sensor = channel.get('sensor', '')
                API = channel.get('api_KEY', '')
                graph_count = 1
                context = {
                    "channel_name": channel_name,
                    "description": description,
                    "channel_id": channel_id,
                    "API": API,
                    "graph_count": graph_count,
                    "start_date": start_date,
                    "end_date": end_date
                }

                return render(request, 'embed_potassium_chart.html', context)
            else:
                return JsonResponse({"success": False, "error": "Dashboard is not public"})
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For Crop Suggestion Table TEMPLATE
def render_crop_table_by_date(request, channel_id, start_date, end_date):
    context = {
        "channel_id": channel_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, 'embed_crop_suggestion_table.html', context)

# For retrieve Humidity and Temperature data - DONE
def getHumidityTemperatureData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            sensor = channel.get('sensor', '')
            humid_values = []
            temp_values = []
            timestamps_humid_temp = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Fetch data from sensor:DHT11
            db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
            if db_humid_temp is not None and collection_humid_temp is not None:
                humid_temp_data = collection_humid_temp.find_one({"API_KEY": API})
                if humid_temp_data:
                    for data_point in humid_temp_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        if start_date <= timestamp_obj <= end_date:
                            humidity_value = data_point.get('humidity_value', '')
                            temperature_value = data_point.get('temperature_value', '')
                            humid_values.append(humidity_value)
                            temp_values.append(temperature_value)
                            formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                            timestamps_humid_temp.append(formatted_timestamp)
            context = {
                "channel_id": channel_id,
                "humid_values": humid_values,
                "temp_values": temp_values,
                "timestamps_humid_temp": timestamps_humid_temp,
                "API": API,
            }
            print("check here",context)
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For retrieve NPK data - DONE
def getNPKData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            sensor = channel.get('sensor', '')
            nitrogen_values = []
            phosphorous_values = []
            potassium_values = []
            timestamps_NPK = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Fetch data from sensor:DHT11
            db_NPK, collection_NPK = connect_to_mongodb('sensor', 'NPK')
            if db_NPK is not None and collection_NPK is not None:
                NPK_data = collection_NPK.find_one({"API_KEY": API})
                if NPK_data:
                    for data_point in NPK_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        if start_date <= timestamp_obj <= end_date:
                            nitrogen_value = data_point.get('nitrogen_value', '')
                            phosphorous_value = data_point.get('phosphorous_value', '')
                            potassium_value = data_point.get('potassium_value', '')
                            nitrogen_values.append(nitrogen_value)
                            phosphorous_values.append(phosphorous_value)
                            potassium_values.append(potassium_value)
                            formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                            timestamps_NPK.append(formatted_timestamp)
                        else:
                            print("invalid timestamp")
                else:
                    print("npk_data empty")
            context = {
                "channel_id": channel_id,
                "nitrogen_values" :nitrogen_values,
                "phosphorous_values" :phosphorous_values, 
                "potassium_values" :potassium_values, 
                "timestamps_NPK" :timestamps_NPK, 
                "API": API,
            }
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For retrieve PH data - DONE
def getPHData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            sensor = channel.get('sensor', '')
            ph_values = []
            timestamps = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

            db_ph, collection_ph = connect_to_mongodb('sensor', 'PHSensor')
            if db_ph is not None and collection_ph is not None:
                ph_data = collection_ph.find_one({"API_KEY": API})
                if ph_data:
                    for data_point in ph_data.get('sensor_data', []):
                        ph_values.append(data_point.get('ph_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        timestamps.append(formatted_timestamp)

            context = {
                "channel_id": channel_id,
                "ph_values": ph_values,
                "timestamps": timestamps,
                "API": API,
            }
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

# For retrieve rainfall data - DONE
def getRainfallData(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            sensor = channel.get('sensor', '')
            rainfall_values = []
            rainfall_timestamps = []
            API = channel.get('API_KEY', '')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

            db_rainfall, collection_rainfall = connect_to_mongodb('sensor', 'rainfall')
            if db_rainfall is not None and collection_rainfall is not None:
                rainfall_data = collection_rainfall.find_one({"API_KEY": API})
                if rainfall_data:
                    for data_point in rainfall_data.get('sensor_data', []):
                        rainfall_values.append(data_point.get('rainfall_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        rainfall_timestamps.append(formatted_timestamp)

            context = {
                "channel_id": channel_id,
                "rainfall_values": rainfall_values,
                "timestamps": rainfall_timestamps,
                "API": API,
            }
            return JsonResponse(context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")
        
# FOR GETTING CROP SUGGESTION BY DATE - DONE
@csrf_exempt
def getCropRecommendationByDate(request, channel_id, start_date, end_date):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')
    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})

        if channel:
            ph_values = []
            timestamps = []
            humid_values = []
            temp_values = []
            timestamps_humid_temp = []
            rainfall_values = []
            rainfall_timestamps = []
            nitrogen_values = []
            phosphorous_values = []
            potassium_values = []
            timestamps_NPK = []
            API = channel.get('API_KEY', '')

            # Convert start_date and end_date to datetime objects
            start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=pytz.utc)
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=pytz.utc)

            # Get DHT11 sensor data
            db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
            if db_humid_temp is not None and collection_humid_temp is not None:
                humid_temp_data = collection_humid_temp.find_one({"API_KEY": API})
                if humid_temp_data:
                    for data_point in humid_temp_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow()).replace(tzinfo=pytz.utc)
                        if start_date <= timestamp_obj <= end_date:
                            humidity_value = data_point.get('humidity_value', '')
                            temperature_value = data_point.get('temperature_value', '')
                            humid_values.append(humidity_value)
                            temp_values.append(temperature_value)
                            formatted_timestamp = timestamp_obj.strftime('%d-%m-%Y')
                            timestamps_humid_temp.append(formatted_timestamp)

            # Get PH sensor data
            db_ph, collection_ph = connect_to_mongodb('sensor', 'PHSensor')
            if db_ph is not None and collection_ph is not None:
                ph_data = collection_ph.find_one({"API_KEY": API})
                if ph_data:
                    for data_point in ph_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow()).replace(tzinfo=pytz.utc)
                        if start_date <= timestamp_obj <= end_date:
                            ph_values.append(data_point.get('ph_value', ''))
                            formatted_timestamp = timestamp_obj.strftime('%d-%m-%Y')
                            timestamps.append(formatted_timestamp)
            # Get NPK sensor data
            db_NPK, collection_NPK = connect_to_mongodb('sensor', 'NPK')
            if db_NPK is not None and collection_NPK is not None:
                NPK_data = collection_NPK.find_one({"API_KEY": API})
                if NPK_data:
                    for data_point in NPK_data.get('sensor_data', []):
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        if start_date <= timestamp_obj <= end_date:
                            nitrogen_value = data_point.get('nitrogen_value', '')
                            phosphorous_value = data_point.get('phosphorous_value', '')
                            potassium_value = data_point.get('potassium_value', '')
                            nitrogen_values.append(nitrogen_value)
                            phosphorous_values.append(phosphorous_value)
                            potassium_values.append(potassium_value)
                            formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                            timestamps_NPK.append(formatted_timestamp)
            # Get rainfall sensor data
            db_rainfall, collection_rainfall = connect_to_mongodb('sensor', 'rainfall')
            if db_rainfall is not None and collection_rainfall is not None:
                rainfall_data = collection_rainfall.find_one({"API_KEY": API})
                if rainfall_data:
                    for data_point in rainfall_data.get('sensor_data', []):
                        rainfall_values.append(data_point.get('rainfall_value', ''))
                        timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                        formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%d-%m-%Y')
                        rainfall_timestamps.append(formatted_timestamp)

            context = {
                "channel_id": channel_id,
                "ph_values": ph_values,
                "timestamps": timestamps,
                "humid_values": humid_values,
                "temp_values": temp_values,
                "timestamps_humid_temp": timestamps_humid_temp,
                "rainfall_values" :rainfall_values,
                "rainfall_timestamps" :rainfall_timestamps,
                "nitrogen_values" :nitrogen_values,
                "phosphorous_values" :phosphorous_values,
                "potassium_values" :potassium_values,
                "timestamps_NPK" :timestamps_NPK,
                "API": API,
            }

            if humid_values or ph_values or rainfall_values or nitrogen_values or potassium_value or phosphorous_value or temp_values:
                # Load the trained Random Forest model
                model = load_trained_model()
                if model:
                    # Prepare input data for model prediction
                    input_data = {
                        'N': float(nitrogen_values[-1]) if nitrogen_values else 0.0,  
                        'P': float(potassium_values[-1]) if potassium_values else 0.0,
                        'K': float(phosphorous_values[-1]) if phosphorous_values else 0.0,
                        'temperature': float(temp_values[-1]) if temp_values else 0.0,  
                        'humidity': float(humid_values[-1]) if humid_values else 0.0,  
                        'ph': float(ph_values[-1]) if ph_values else 0.0,  
                        'rainfall':float(rainfall_values[-1]) if rainfall_values else 0.0,   
                    }

                    input_df = pd.DataFrame([input_data])

                    # Make predictions using the model
                    prediction = model.predict(input_df)

                    probabilities = model.predict_proba(input_df)

                    labels = model.classes_

                    # Combine the labels with their probabilities and sort them by probability in descending order
                    crop_recommendations = [
                        {"crop": label, "accuracy": prob * 100}  # Convert to percentage
                        for label, prob in zip(labels, probabilities[0])
                    ]
                    crop_recommendations.sort(key=lambda x: x["accuracy"], reverse=True)
                    # Add the crop recommendation to the context
                    context["crop_recommendations"] = crop_recommendations

                return JsonResponse(context)

        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        return JsonResponse({"error": "Error connecting to MongoDB"}, status=500)

# TO CHANGE CHANNEL PERMISSION TO FORBID API - DONE
@csrf_exempt
def forbid_API(request, channel_id):
    if request.method == 'POST':
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        _id = ObjectId(channel_id)
        filter_criteria = {'_id': _id}
        update_result = collection.update_one(filter_criteria, {'$set': {'allow_API': 'not permitted'}})
        if update_result.modified_count > 0:
            return JsonResponse({'message': 'API access forbidden successfully'}, status=200)
        else:
            return JsonResponse({'error': 'Failed to update API access'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

# TO CHANGE CHANNEL PERMISSION TO ALLOW API - DONE
@csrf_exempt
def permit_API(request, channel_id):
    if request.method == 'POST':
        db, collection = connect_to_mongodb('Channel', 'dashboard')
        _id = ObjectId(channel_id)
        filter_criteria = {'_id': _id}
        update_result = collection.update_one(filter_criteria, {'$set': {'allow_API': 'permit'}})
        if update_result.modified_count > 0:
            return JsonResponse({'message': 'API access permitted successfully'}, status=200)
        else:
            return JsonResponse({'error': 'Failed to update API access'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)