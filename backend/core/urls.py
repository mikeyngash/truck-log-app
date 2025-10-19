from django.urls import path
from . import views

urlpatterns = [
    path('trip/', views.TripView.as_view(), name='trip'),
    path('locations/search/', views.location_search, name='location_search'),
]
