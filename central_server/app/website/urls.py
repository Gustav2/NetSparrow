from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('myblacklist/', views.myblacklist_view, name='myblacklist'),
    path('central_blacklist/', views.central_blacklist_view, name='central_blacklist'),
    path('mysettings/', views.mysettings, name='mysettings'),
    path('update_settings/', views.update_settings, name='update_settings'),
    path('api/settings/update/', views.settings_update, name='settings_update'),
    path('api/settings/get/', views.settings_get, name='settings_get'),
    path('api/settings/pi/get', views.settings_pi, name='settings_pi'),
    path('add_to_my_blacklist/<int:blacklist_id>/', views.add_to_my_blacklist, name='add_to_my_blacklist'),
    path('remove_from_my_blacklist/<int:blacklist_id>/', views.remove_from_my_blacklist, name='remove_from_my_blacklist'),
    path('add_all_to_my_blacklist/', views.add_all_to_my_blacklist, name='add_all_to_my_blacklist'),
    path('remove_all_from_my_blacklist/', views.remove_all_from_my_blacklist, name='remove_all_from_my_blacklist'),
    path('packet_capture/', views.packet_capture, name='packet_capture'),
    path('settings/myblacklist/', views.settings_myblacklist, name='settings_myblacklist'),
    path('settings/centralblacklist/', views.settings_centralblacklist, name='settings_centralblacklist'),
    path('settings/add_to_myblacklist/', views.settings_add_to_myblacklist, name='settings_add_to_myblacklist'),
    path('settings/remove_from_myblacklist/', views.settings_remove_from_myblacklist, name='settings_remove_from_myblacklist'),
]
