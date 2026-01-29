from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    ItemViewSet, chat_with_ai, UserRegistrationView, UserLoginView,
    UserLogoutView, UserProfileView, ChangePasswordView, TokenRefreshView,
    UsersListView, auth_check, quality_scores, quality_top_performers,
    quality_poor_performers, quality_statistics, quality_by_grade,
    acceptance_stats, alerts_count, alerts_list,
    download_csv_template, bulk_upload_medicines
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
    
    # Quality Score endpoints (MUST be before router.urls)
    path('quality-scores/', quality_scores, name='quality_scores'),
    path('quality-scores/top/', quality_top_performers, name='quality_top_performers'),
    path('quality-scores/poor/', quality_poor_performers, name='quality_poor_performers'),
    path('quality-scores/worst/', quality_poor_performers, name='quality_worst_performers'),  # Alias for poor
    path('quality-scores/statistics/', quality_statistics, name='quality_statistics'),
    path('quality-scores/grade/<str:grade>/', quality_by_grade, name='quality_by_grade'),
    
    # Batch Acceptance Rate Dashboard
    path('acceptance-stats/', acceptance_stats, name='acceptance_stats'),
    
    # Environmental Alert System
    path('alerts/count/', alerts_count, name='alerts_count'),
    path('alerts/list/', alerts_list, name='alerts_list'),
    
    # CSV Template & Bulk Upload
    path('csv-template/', download_csv_template, name='csv_template'),
    path('bulk-upload/', bulk_upload_medicines, name='bulk_upload'),
    
    # AI Chatbot
    path('chat_with_ai/', chat_with_ai, name='chat_with_ai'),
    
    # Medicine/Item management (router must be last)
    path('', include(router.urls)),  # Includes all routes for the ItemViewSet
]
