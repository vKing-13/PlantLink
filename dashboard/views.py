from django.shortcuts import render, redirect
from bson import ObjectId
from django.http import HttpResponse, JsonResponse
from dashboard.forms import ChannelForm
from main.mongo_setup import connect_to_mongodb
from datetime import datetime
import pytz
# Create your views here.

def channels(request):
    db,collection=connect_to_mongodb('Channel','dashboard')
    user_id="12345"
    if db is not None and collection is not None:
        channels=collection.find({"user_id":user_id})
        if channels:
            channel_list=[]
            public_channel=0
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
                channel_status=channel.get('privacy',' ')
                if(channel_status=="public"):
                    public_channel+=1
                channel_list.append(channel_data)
            #pass the channels match with user_id and pass as context
            channel_count = len(channel_list)
            context = {
                'channels': channel_list,
                'channel_count':channel_count,
                "public_channel":public_channel
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
                return redirect('view_channel', channel_id=channel_id)
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
                    'user_id':"12345",
                    "date_created":current_date,
                    "date_modified":current_date,
                }
                # Insert the new channel data into MongoDB
                result = collection.insert_one(new_channel)
                
                if result.inserted_id:
                    # Redirect to the channels page or any other URL upon successful insertion
                    return redirect('view_channel', channel_id=result.inserted_id)
                else:
                    # Handle if insertion failed
                    return JsonResponse({"success": False, "error": "Failed to insert channel data"})
            else:
                # Handle MongoDB connection error
                return JsonResponse({"success": False, "error": "Error connecting to MongoDB"})
    else:
        form = ChannelForm()

    context = {'form': form}
    return render(request, 'create_channel.html', context)

def add_sensor(request, channel_id):
    if request.method == 'POST':
        # Form 1: Generate API Key
        if 'generate_api_key' in request.POST:
            # Logic to generate API key (random string or algorithm)
            # For demonstration purposes, I'll use a simple random string
            api_key = generate_api_key()

            # Pass the generated API key back to the template via JSON response
            return JsonResponse({'api_key': api_key})

        # Form 2: Sensor Details
        elif 'sensor_details' in request.POST:
            form = ChannelForm(request.POST)
            if form.is_valid():
                # Connect to MongoDB
                db, collection = connect_to_mongodb('Sensor', 'sensor_data')
                if db is not None and collection is not None:
                    # Create a new sensor data dictionary
                    current_date = datetime.now().strftime('%d/%m/%Y')
                    new_sensor = {
                        'channel_id': channel_id,
                        'sensor_name': form.cleaned_data['sensor_name'],
                        'sensor_type': form.cleaned_data['sensor_type'],
                        'api_key': request.POST.get('api_key'),  # Get API Key from Form 1
                        'date_created': current_date,
                        'date_modified': current_date,
                    }
                    # Insert the new sensor data into MongoDB
                    # result = collection.insert_one(new_sensor)
                    
                    # if result.inserted_id:
                        # Redirect to the view_channel page upon successful insertion
                        # return redirect('view_channel', channel_id=channel_id)
                    print(new_sensor)
                    # else:
                        # Handle if insertion failed
                        # return JsonResponse({"success": False, "error": "Failed to insert sensor data"})
                else:
                    # Handle MongoDB connection error
                    return JsonResponse({"success": False, "error": "Error connecting to MongoDB"})

    # GET request or invalid POST data, render the template with ChannelForm
    form = ChannelForm()
    context = {'form': form}
    return render(request, 'add_sensor.html', context)

def generate_api_key():
    # Logic to generate API key (random string or algorithm)
    # For demonstration purposes, I'll use a simple random string
    import random
    import string
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))