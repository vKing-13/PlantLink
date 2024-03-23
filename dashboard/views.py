from django.shortcuts import render

# Create your views here.
def dashboard(request): 
    name="Soil 001"
    description="First soil research"
    return render(request, 'dashboard.html',{'name':name,'description':description})