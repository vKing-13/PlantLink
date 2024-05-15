import json
from django.shortcuts import render, redirect
from bson import ObjectId
from django.http import HttpResponse, JsonResponse
from dashboard.forms import ChannelForm, SensorForm
from main.mongo_setup import connect_to_mongodb
from datetime import datetime
import pytz
import pandas as pd
import joblib
import os
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
# Create your views here.

def channels(request):
    db,collection=connect_to_mongodb('Channel','dashboard')

    user_id = request.COOKIES['userid']
    if db is not None and collection is not None:
        channels=collection.find({"user_id":user_id})
        if channels:
            channel_list=[]
            public_channel=0
            total_sensor=0
            for channel in channels:
                sensor_count = len(channel.get('sensor', []))
                channel_data={
                    'channel_id': str(channel.get('_id')),
                    'channel_name':channel.get('channel_name',' '),
                    'description':channel.get('description',' '),
                    'date_created':channel.get('date_created',' '),
                    'date_modified':channel.get('date_modified',' '),
                    'sensor_count':sensor_count
                }
                total_sensor+=sensor_count
                channel_status=channel.get('privacy',' ')
                if(channel_status=="public"):
                    public_channel+=1
                channel_list.append(channel_data)
            #pass the channels match with user_id and pass as context
            channel_count = len(channel_list)
            context = {
                'channels': channel_list,
                'channel_count':channel_count,
                "public_channel":public_channel,
                "total_sensor":total_sensor,
            }
            return render(request, 'channels.html', context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
            # show error not found
    else:
        print("Error connecting to MongoDB.")
        # show error 

def dashboard(request): 
    name="Soil 001"
    description="First soil research"
    return render(request, 'dashboard.html',{'name':name,'description':description})

def view_channel(request,channel_id):
    _id=ObjectId(channel_id)
    db,collection=connect_to_mongodb('Channel','dashboard')
    if db is not None and collection is not None:
        channel=collection.find_one({"_id":_id})

        if channel:
            print("found channel")
            channel_name=channel.get('channel_name','')
            description=channel.get('description','')

            db_ph,collection_ph=connect_to_mongodb('sensor','PH_data')
            if db_ph is not None and collection_ph is not None:
                ph_data = collection_ph.find({})
                
                ph_values=[]
                timestamps=[]
                
                for data_point in ph_data:
                    ph_values.append(data_point.get('ph_value',''))

                    timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                    formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%H:%M:%S')
                    timestamps.append(formatted_timestamp)
            db_humid_temp,collection_humid_temp=connect_to_mongodb('sensor','humid_temperature_data')
            if db_humid_temp is not None and collection_humid_temp is not None:
                humid_temp_data = collection_humid_temp.find({})
                
                humid_values=[]
                temp_values=[]
                timestamps_humid_temp=[]
                
                for data_point in humid_temp_data:
                    humid_values.append(data_point.get('humidity_value',''))
                    temp_values.append(data_point.get('temperature_value',''))

                    timestamp_obj = data_point.get('timestamp', datetime.utcnow())
                    formatted_timestamp = timestamp_obj.astimezone(pytz.utc).strftime('%H:%M:%S')
                    timestamps_humid_temp.append(formatted_timestamp)
            context={
                "channel_name":channel_name,
                "description":description,
                "ph_values": ph_values,
                "timestamps": timestamps,
                "humid_values": humid_values,
                "temp_values":temp_values,
                "timestamps_humid_temp":timestamps_humid_temp,
                "channel_id":channel_id,
            }
            # Render a template or return JSON response with the document data
            return render(request, 'dashboard.html',context)

        else:
            return JsonResponse({"success": False, "error": "Document not found"})
            # show error not found
    else:
        print("Error connecting to MongoDB.")
        # show error 

def load_trained_model():
    model_path = os.path.join('static', 'dashboard', 'best_random_forest_model.pkl')
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

def view_channel_sensor(request, channel_id):
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
            for datapoint in sensor:
                if 'DHT_sensor' in datapoint:
                    dht = datapoint['DHT_sensor']
                    db_humid_temp, collection_humid_temp = connect_to_mongodb('sensor', 'DHT11')
                    dht_id = ObjectId(dht)
                    humid_temp_data = collection_humid_temp.find_one({"_id": dht_id})
                    
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
                "timestamps_humid_temp": timestamps_humid_temp
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
                    'temperature': float(temp_values[-1]),  # Example temperature value
                    'humidity': float(humid_values[-1]),  # Example humidity value
                    'ph': float(ph_values[-1]),  # Example pH value
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

                # Send the updated context data to WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'sensor_data',
                    {
                        'type': 'sensor_data_message',
                        'data': context  # You can customize the data you send
                    }
                )
            return render(request, 'dashboard.html', context)
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

def delete_channel(request,channel_id):
    _id=ObjectId(channel_id)
    db, collection = connect_to_mongodb("channel","dashboard")
    if db is not None and collection is not None:
        channel=collection.find_one({"_id":_id})
        if channel:
            collection.delete_one({"_id":_id})
            return redirect('channels')
        else:
            return JsonResponse({"success": False, "error": "Document not found"})
    else:
        print("Error connecting to MongoDB.")

def edit_channel(request, channel_id):
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
                # Handle if update operation failed
                return JsonResponse({"success": False, "error": "Failed to update channel"})
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
        
def create_channel(request):
    user_id= request.COOKIES['userid']
    if request.method == 'POST':
        form = ChannelForm(request.POST)
        if form.is_valid():
            # Connect to MongoDB
            db, collection = connect_to_mongodb('Channel', 'dashboard')
            if db is not None and collection is not None:
                # Create a new channel data dictionary
                current_date = datetime.now().strftime('%d/%m/%Y')
                new_channel = {
                    'channel_name': form.cleaned_data['channel_name'],
                    'description': form.cleaned_data['description'],
                    'location': form.cleaned_data['location'],
                    'privacy': form.cleaned_data['privacy'],
                    "sensor":[],
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

def add_sensor(request, channel_id):
    if request.method == 'POST':
        channel_id = channel_id
        API_KEY = request.POST.get('generatedApiKey')
        sensor_name = request.POST.get('sensorNameConfirmation')
        sensor_type = request.POST.get('sensorTypeConfirmation')
        
        if sensor_type == "DHT11":
            db_dht, collection_dht = connect_to_mongodb('sensor', 'DHT11')
            if db_dht is not None and collection_dht is not None:
                # Add a new sensor data dictionary
                new_sensor = {
                    'channel_id': channel_id,
                    'API_KEY': API_KEY,
                    'sensor_name': sensor_name,
                    'sensor_type': sensor_type,
                    "sensor_data":[],
                }
                # Insert the new sensor data into MongoDB
                result = collection_dht.insert_one(new_sensor)
                
                if result.inserted_id:
                    # Redirect to the channels page or any other URL upon successful insertion
                    db_channel, collection_channel = connect_to_mongodb('Channel', 'dashboard')
                    _id=ObjectId(channel_id)
                    filter_criteria = {'_id': _id}
                    doc = {
                        'DHT_sensor': result.inserted_id,
                    }
                    print(doc)
                    update_result = collection_channel.update_one(filter_criteria, {'$push': {'sensor': doc}})
                    return redirect('view_channel_sensor', channel_id=channel_id)
                    
                else:
                    # Handle if insertion failed
                    return JsonResponse({"success": False, "error": "Failed to insert channel data"})
            else:
                # Handle MongoDB connection error
                return JsonResponse({"success": False, "error": "Error connecting to MongoDB"})
        
        elif sensor_type == "PHSensor":
            db_ph, collection_ph = connect_to_mongodb('sensor', 'PHSensor')
            if db_ph is not None and collection_ph is not None:
                # Add a new sensor data dictionary
                new_sensor = {
                    'channel_id': channel_id,
                    'API_KEY': API_KEY,
                    'sensor_name': sensor_name,
                    'sensor_type': sensor_type,
                    "sensor_data":[],
                }
                # Insert the new sensor data into MongoDB
                result = collection_ph.insert_one(new_sensor)
                
                if result.inserted_id:
                    # Redirect to the channels page or any other URL upon successful insertion
                    db_channel, collection_channel = connect_to_mongodb('Channel', 'dashboard')
                    _id=ObjectId(channel_id)
                    filter_criteria = {'_id': _id}
                    doc = {
                        'PH_sensor': result.inserted_id,
                    }
                    update_result = collection_channel.update_one(filter_criteria, {'$push': {'sensor': doc}})
                    return redirect('view_channel_sensor', channel_id=channel_id)
                else:
                    # Handle if insertion failed
                    return JsonResponse({"success": False, "error": "Failed to insert channel data"})
            else:
                # Handle MongoDB connection error
                return JsonResponse({"success": False, "error": "Error connecting to MongoDB"})
    else:
        form = SensorForm()

    context = {'form': form, "channel_id": channel_id}
    return render(request, 'add_sensor.html', context)

def manage_sensor(request, channel_id):
    _id = ObjectId(channel_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')

    if db is not None and collection is not None:
        channel = collection.find_one({"_id": _id})
        if channel:
            print("Found channel")
            sensor = channel.get('sensor', '')
            for datapoint in sensor:
                if 'DHT_sensor' in datapoint:
                    dht = datapoint['DHT_sensor']
                    dht_id=ObjectId(dht)
                if 'PH_sensor' in datapoint:
                    ph = datapoint['PH_sensor']
                    ph_id=ObjectId(ph)
        sensor_list=[]
        if dht_id:
            dht_db, dht_collection = connect_to_mongodb('sensor', 'DHT11')
            if dht_db is not None and dht_collection is not None:
                dhtsensor = dht_collection.find_one({"_id": dht_id})
                dht_data={
                    "sensor_id":dht,
                    "sensor_name":dhtsensor.get('sensor_name'),
                    "sensor_type":dhtsensor.get('sensor_type'),
                    "sensor_data":len(dhtsensor.get('sensor_data', [])),
                }
                sensor_list.append(dht_data)
        if ph_id:
            ph_db, ph_collection = connect_to_mongodb('sensor', 'PHSensor')
            if ph_db is not None and ph_collection is not None:
                phsensor = ph_collection.find_one({"_id": ph_id})
                ph_data={
                    "sensor_id":ph,
                    "sensor_name":phsensor.get('sensor_name'),
                    "sensor_type":phsensor.get('sensor_type'),
                    "sensor_data":len(phsensor.get('sensor_data', [])),
                }
                sensor_list.append(ph_data)
        context={"channel_id":channel_id,"sensor":sensor_list}
        return render(request, 'conf_sensor.html', context)
    
def delete_sensor(request, channel_id,sensor_id,sensor_type):
    _id = ObjectId(channel_id)
    sensor_id_to_delete = ObjectId(sensor_id)
    db, collection = connect_to_mongodb('Channel', 'dashboard')

    if db is not None and collection is not None:
        filter_criteria = {'_id': _id}
        if sensor_type == "DHT11":
            # Use the $pull operator to remove the specified sensor from the array
            update_result = collection.update_one(filter_criteria, {'$pull': {'sensor': {'DHT_sensor': sensor_id_to_delete}}})

            if update_result.modified_count > 0:
                print("Sensor removed successfully.")
            else:
                print("No matching sensor found to remove.")

            dht_db, dht_collection = connect_to_mongodb('sensor', 'DHT11')
            delete_action=dht_collection.find_one({"_id":sensor_id_to_delete})
            if delete_action:
                collection.delete_one({"_id":sensor_id_to_delete})
                return redirect('view_channel_sensor', channel_id=channel_id)
            else:
                return JsonResponse({"success": False, "error": "Document not found"})
        elif sensor_type == "PHSensor":
            # Use the $pull operator to remove the specified sensor from the array
            update_result = collection.update_one(filter_criteria, {'$pull': {'sensor': {'PH_sensor': sensor_id_to_delete}}})

            if update_result.modified_count > 0:
                print("Sensor removed successfully.")
            else:
                print("No matching sensor found to remove.")

            ph_db, ph_collection = connect_to_mongodb('sensor', 'PHSensor')
            delete_action=ph_collection.find_one({"_id":sensor_id_to_delete})
            if delete_action:
                collection.delete_one({"_id":sensor_id_to_delete})
                return redirect('view_channel_sensor', channel_id=channel_id)
            else:
                return JsonResponse({"success": False, "error": "Document not found"})

def edit_sensor(request, sensor_type, sensor_id, channel_id):
    if request.method == 'POST':
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
                        "sensor_type": sensor_type,
                        "API_KEY": API_KEY,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    # Handle if update operation failed
                    return JsonResponse({"success": False, "error": "Failed to update channel"})

        elif sensor_type == "PHSensor":
            db, collection = connect_to_mongodb('sensor', 'PHSensor')
            if db is not None and collection is not None:
                # Convert channel_id to ObjectId
                _id = ObjectId(sensor_id)
                result = collection.update_one(
                    {"_id": _id},
                    {"$set": {
                        "sensor_name": sensor_name,
                        "sensor_type": sensor_type,
                        "API_KEY": API_KEY,
                    }}
                )
                if result.modified_count > 0:
                    # Channel updated successfully
                    return redirect('manage_sensor', channel_id=channel_id)
                else:
                    # Handle if update operation failed
                    return JsonResponse({"success": False, "error": "Failed to update channel"})

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
        elif sensor_type == "PHSensor":
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