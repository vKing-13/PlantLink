from django.urls import path
from . import views
urlpatterns = [
    path('', views.channels, name='channels'),
    path('create_channel/', views.create_channel, name='create_channel'),
    path('<str:channel_id>/', views.view_channel_sensor, name="view_channel_sensor"),
    path('<str:channel_id>/edit', views.edit_channel, name="edit_channel"),
    path('<str:channel_id>/delete', views.delete_channel, name="delete_channel"),
    path('<str:channel_id>/share', views.share_channel, name="share_channel"),
    # RETRIEVE DASHBOARD DATA
    path('<str:channel_id>/get_dashboard_data/', views.getDashboardData, name="getDashboardData"),
    # VIEW PUBLIC DASHBOARD OR EMBED
    path('<str:channel_id>/get_shared_dashboard', views.getSharedDashboardDetail, name="getSharedDashboardDetail"),
    path('<str:channel_id>/shared_dashboard/', views.sharedDashboard, name="sharedDashboard"),
    path('embed/channel/<str:channel_id>/', views.render_embed_code, name='render_embed_code'),

    # RENDER CHART TEMPLATE
    path('embed/channel/<str:channel_id>/phChart/<str:start_date>/<str:end_date>/', views.render_ph_chart, name='render_ph_chart'),
    path('embed/channel/<str:channel_id>/humidityChart/<str:start_date>/<str:end_date>/', views.render_humidity_chart, name='render_humidity_chart'),
    path('embed/channel/<str:channel_id>/temperatureChart/<str:start_date>/<str:end_date>/', views.render_temperature_chart, name='render_temperature_chart'),

    # RENDER CHART BASED ON TIMEFRAME
    path('ph_data/<str:channel_id>/<str:start_date>/<str:end_date>/', views.getPHData, name='get_ph_data'),
    path('humidity_temperature/<str:channel_id>/<str:start_date>/<str:end_date>/', views.getHumidityTemperatureData, name='getHumidityTemperatureData'),

    path('<str:channel_id>/manage_sensor', views.manage_sensor, name="manage_sensor"),

    path('<str:channel_id>/edit_sensor/<str:sensor_type>/<str:sensor_id>/', views.edit_sensor, name="edit_sensor"),
    path('<str:channel_id>/add_sensor', views.add_sensor, name="add_sensor"),
    path('<str:channel_id>/delete_sensor/<str:sensor_type>/<str:sensor_id>/', views.delete_sensor, name="delete_sensor"),
]