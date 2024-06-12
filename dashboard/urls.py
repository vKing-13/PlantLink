from django.urls import path
from . import views
urlpatterns = [
    path('', views.channels, name='channels'),
    # path('', views.dashboard, name='dashboard'),
    path('create_channel/', views.create_channel, name='create_channel'),
    # path('<str:channel_id>/', views.view_channel, name="view_channel"),
    path('<str:channel_id>/', views.view_channel_sensor, name="view_channel_sensor"),
    path('<str:channel_id>/edit', views.edit_channel, name="edit_channel"),
    path('<str:channel_id>/delete', views.delete_channel, name="delete_channel"),
    path('<str:channel_id>/share', views.share_channel, name="share_channel"),
    path('<str:channel_id>/get_dashboard_data/', views.getDashboardData, name="getDashboardData"),
    path('<str:channel_id>/get_shared_dashboard', views.getSharedDashboardDetail, name="getSharedDashboardDetail"),
    path('<str:channel_id>/shared_dashboard/', views.sharedDashboard, name="sharedDashboard"),
    path('embed/channel/<str:channel_id>/', views.sharedDashboard, name='sharedDashboard'),

    path('<str:channel_id>/manage_sensor', views.manage_sensor, name="manage_sensor"),

    path('<str:channel_id>/edit_sensor/<str:sensor_type>/<str:sensor_id>/', views.edit_sensor, name="edit_sensor"),
    path('<str:channel_id>/add_sensor', views.add_sensor, name="add_sensor"),
    path('<str:channel_id>/delete_sensor/<str:sensor_type>/<str:sensor_id>/', views.delete_sensor, name="delete_sensor"),
]