from django.urls import path
from . import views
urlpatterns = [
    path('ph_sensor/', views.post_ph_sensor_data, name='post_ph_sensor_data'),
    path('ph_sensor_data/', views.post_ph_data, name='post_ph_data'),

    path('new_data/', views.combined_post, name='combined_post'),

    path('dht_sensor/', views.post_dht_sensor_data, name='post_dht_sensor_data'),
    path('humid_temp_sensor/', views.post_humid_temp_sensor_data, name='post_humid_temp_sensor_data'),

]