from django.shortcuts import render, redirect
from bson import ObjectId
from django.http import HttpResponse, JsonResponse
from main.mongo_setup import connect_to_mongodb
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
            context={
                "channel_name":channel_name,
                "description":description,
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
            
            # Update channel document in MongoDB
            result = collection.update_one(
                {"_id": _id},
                {"$set": {
                    "channel_name": channel_name,
                    "description": description,
                    "location": location,
                    "privacy": privacy
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