# decorators.py
from functools import wraps
from django.http import JsonResponse
from pymongo import MongoClient

def allow_ip_address():
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Connect to MongoDB
            client = MongoClient('mongodb://localhost:27017/')
            db = client['your_database_name']
            collection = db['permitted_ips']  # Collection storing permitted IPs

            # Get permitted IPs from MongoDB
            permitted_ips = [ip['ip_address'] for ip in collection.find()]

            # Check if the request's IP is in the permitted list
            remote_ip = request.META.get('REMOTE_ADDR')
            if remote_ip not in permitted_ips:
                return JsonResponse({'error': 'Unauthorized IP'}, status=401)

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator