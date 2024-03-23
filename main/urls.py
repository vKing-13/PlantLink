from django.urls import path
from . import views
urlpatterns = [
    path('home/', views.home, name='home'),
    path('mychannel/', views.channels, name='channels'),
    path('login/', views.logPlantFeed, name='logPlantFeed'),
    
]