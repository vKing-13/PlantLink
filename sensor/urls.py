from django.urls import path
from . import views
urlpatterns = [
    path('ph_sensor/', views.post_ph_sensor_data, name='post_ph_sensor_data'),
    path('arduino/hihi', views.another_view, name='another_view'),
]