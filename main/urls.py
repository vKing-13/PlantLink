from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),

    path('login/', views.logPlantFeed, name='logPlantFeed'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
]