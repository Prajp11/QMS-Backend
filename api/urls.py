from django.urls import path, include  # Import path and include
from rest_framework.routers import DefaultRouter
from api.views import ItemViewSet  # Import ItemViewSet from views

# Create a router and register the ItemViewSet
router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='item')

# Define the app's URL patterns
urlpatterns = [
    path('', include(router.urls)),  # Includes all routes for the ItemViewSet
]
