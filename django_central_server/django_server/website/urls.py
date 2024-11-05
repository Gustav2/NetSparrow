from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('myblacklist/', views.myblacklist_view, name='myblacklist'),
    path('central_blacklist/', views.central_blacklist_view, name='central_blacklist'),
    path('add_to_my_blacklist/<int:blacklist_id>/', views.add_to_my_blacklist, name='add_to_my_blacklist'),
    path('remove_from_my_blacklist/<int:blacklist_id>/', views.remove_from_my_blacklist, name='remove_from_my_blacklist'),
    path('add_all_to_my_blacklist/', views.add_all_to_my_blacklist, name='add_all_to_my_blacklist'),
    path('remove_all_from_my_blacklist/', views.remove_all_from_my_blacklist, name='remove_all_from_my_blacklist'),
    path('packet_capture/', views.packet_capture, name='packet_capture'),
]