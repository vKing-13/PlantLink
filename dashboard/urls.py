from django.urls import path
from . import views
urlpatterns = [
    path('', views.channels, name='channels'),
    # path('', views.dashboard, name='dashboard'),
    path('create_channel/', views.create_channel, name='create_channel'),
    path('<str:channel_id>/', views.view_channel, name="view_channel"),
    path('<str:channel_id>/edit', views.edit_channel, name="edit_channel"),
    path('<str:channel_id>/delete', views.delete_channel, name="delete_channel"),
]