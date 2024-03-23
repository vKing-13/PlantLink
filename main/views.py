from django.shortcuts import render

# Create your views here.
  
def home(request): 
    return render(request, 'home.html')

def channels(request):
    return render(request, 'channels.html')

def logPlantFeed(request):
    return render(request, 'logPlantFeed.html')