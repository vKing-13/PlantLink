from django.urls import path
from . import views
urlpatterns = [
    path('ph_sensor/', views.post_ph_sensor_data, name='post_ph_sensor_data'),
    path('humid_temp_sensor/', views.post_humid_temp_sensor_data, name='post_humid_temp_sensor_data'),

]