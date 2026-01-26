from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    ItemViewSet, chat_with_ai, UserRegistrationView, UserLoginView,
    UserLogoutView, UserProfileView, ChangePasswordView, TokenRefreshView,
    UsersListView, auth_check
)

# Create a router and register the ItemViewSet
router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='item')

# Define the app's URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/signup/', UserRegistrationView.as_view(), name='user_signup'),
    path('auth/login/', UserLoginView.as_view(), name='user_login'),
    path('auth/logout/', UserLogoutView.as_view(), name='user_logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/check/', auth_check, name='auth_check'),
    path('users/', UsersListView.as_view(), name='users_list'),
    
    # Medicine/Item management
    path('', include(router.urls)),  # Includes all routes for the ItemViewSet
    
    # AI Chatbot
    path('chat_with_ai/', chat_with_ai, name='chat_with_ai'),
]
