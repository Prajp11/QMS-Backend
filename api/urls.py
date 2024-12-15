# from django.contrib import admin
# from django.urls import path, include
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('api/', include('api.urls')),  # Include the routes from api/urls.py
    
#     # JWT authentication endpoints
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
# ]


#main urls
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import ItemViewSet

# router = DefaultRouter()
# router.register(r'items', ItemViewSet)

# urlpatterns = [
#     path('', include(router.urls)),  # Correct, no recursion or leading slash
# ]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet

# Create a router and register the ItemViewSet
router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='item')

# Define the app's URL patterns
urlpatterns = [
    path('', include(router.urls)),  # Includes all routes for the ItemViewSet
]


