from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
import requests

def home(request): 
    return render(request, 'home.html')

def logPlantFeed(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)

        api_data = {
            'email': email,
            'password': password
        }

        try:
            response = requests.post('https://a76b-2a09-bac5-4cee-232-00-38-7f.ngrok-free.app/plantlink/Login/', json=api_data)
            response_data = response.json()
        
            user_details = response_data.get('user', {})
            username = user_details.get('username', '')
            email = user_details.get('email', '')
            userLevel = user_details.get('userlevel', '')
            userid = user_details.get('userid', '')
            name = user_details.get('name', '')

            # Set cookies with user details
            response = HttpResponseRedirect('/mychannel/')  # Redirect to 'channels' URL after successful login
            response.set_cookie('username', username)
            response.set_cookie('email', email)
            response.set_cookie('userlevel', userLevel)
            response.set_cookie('userid', userid)
            response.set_cookie('name', name)
            return response
            

        except requests.exceptions.RequestException as e:
            warning_message = True
            return render(request, 'logPlantFeed.html', {'warning_message': warning_message})

    else:
        return render(request, 'logPlantFeed.html')

def logout(request):
    # Create a response to redirect to the login page
    response = redirect('logPlantFeed')  # Replace 'login' with the appropriate URL name for your login page

    # Delete all cookies related to user authentication
    response.delete_cookie('username')
    response.delete_cookie('email')
    response.delete_cookie('userlevel')
    response.delete_cookie('userid')
    response.delete_cookie('name')

    return response

def profile(request):
    if 'username' in request.COOKIES:
        return render(request, 'profile.html')
    else:
        return redirect('logPlantFeed')    