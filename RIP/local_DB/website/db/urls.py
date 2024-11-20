from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('db', views.db, name='db'),
    path("testplate", views.testplate, name="testplate")
]
