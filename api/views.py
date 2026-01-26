from rest_framework import viewsets, filters, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import connection
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import datetime, timedelta
from .models import Item, UserProfile
from .serializers import (
    ItemSerializer, ItemSummarySerializer, UserSerializer, UserProfileSerializer,
    UserRegistrationSerializer, UserLoginSerializer, ChangePasswordSerializer,
    UserUpdateSerializer
)

# Import chatbot with error handling
import traceback
try:
    from .ml_models.Medicines_Chatbot import chatbot_response
    CHATBOT_AVAILABLE = True
    print("✅ Chatbot imported successfully!")
except Exception as e:
    print(f"❌ Chatbot import failed: {e}")
    traceback.print_exc()
    CHATBOT_AVAILABLE = False
    def chatbot_response(message):
        return "Sorry, the chatbot service is temporarily unavailable."
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def chat_with_ai(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"error": "Message is required"}, status=400)

        if not CHATBOT_AVAILABLE:
            print("❌ CHATBOT_AVAILABLE is False")
            return JsonResponse({"response": "Sorry, the chatbot service is temporarily unavailable."}, status=200)

        print(f"🤖 Processing message: '{user_message}'")
        ai_response = chatbot_response(user_message)
        print(f"✅ Bot response: '{ai_response}'")
        return JsonResponse({"response": ai_response}, status=200)

    except Exception as e:
        print(f"❌ Chatbot Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"response": "I'm having trouble processing your request right now. Please try again later."}, status=200)


# ============================================
# AUTHENTICATION VIEWS
# ============================================

class UserRegistrationView(APIView):
    """API endpoint for user registration/signup"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Register a new user"""
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                # Get user data with profile
                user_serializer = UserSerializer(user)
                
                return Response({
                    'message': 'User registered successfully',
                    'user': user_serializer.data,
                    'tokens': {
                        'access': access_token,
                        'refresh': refresh_token
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'error': 'Registration failed',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': 'Invalid data provided',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """API endpoint for user login"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Authenticate user and return JWT tokens"""
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Get user data with profile
            user_serializer = UserSerializer(user)
            
            return Response({
                'message': 'Login successful',
                'user': user_serializer.data,
                'tokens': {
                    'access': access_token,
                    'refresh': refresh_token
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Invalid credentials',
            'details': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)


class UserLogoutView(APIView):
    """API endpoint for user logout"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Logout user by blacklisting refresh token"""
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Logout failed',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """API endpoint for user profile management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile"""
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            })
        
        return Response({
            'error': 'Invalid data provided',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """API endpoint for changing user password"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            })
        
        return Response({
            'error': 'Invalid data provided',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(APIView):
    """Custom token refresh view with error handling"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Refresh JWT access token"""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
            
            return Response({
                'access': access_token
            })
            
        except TokenError:
            return Response({
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'error': 'Token refresh failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UsersListView(generics.ListAPIView):
    """API endpoint to list all users (admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter users based on permissions"""
        user = self.request.user
        if user.is_staff or (hasattr(user, 'profile') and user.profile.role in ['admin', 'supervisor']):
            return User.objects.all().order_by('-date_joined')
        return User.objects.filter(id=user.id)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_check(request):
    """Check if user is authenticated and return user info"""
    serializer = UserSerializer(request.user)
    return Response({
        'authenticated': True,
        'user': serializer.data
    })


# ============================================
# MEDICINE/ITEM MANAGEMENT VIEWS
# ============================================

class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows items to be viewed, added, updated, or deleted.
    Includes search functionality for querying items by specific fields.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'batch_number', 'manufacturer', 'category']
    ordering_fields = ['name', 'batch_number', 'expiry_date', 'manufacture_date', 'quantity']
    ordering = ['expiry_date']  # Order by expiry date by default
    
    def list(self, request, *args, **kwargs):
        """Override list to add error handling"""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            print(f"❌ Error fetching medicines: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': 'Failed to fetch medicines',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def expiry_report(self, request):
        """Get medicines with expiry calculations using raw SQL for better performance"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, name, batch_number, expiry_date, quantity,
                    manufacturer, category, price, manufacture_date,
                    DATEDIFF(expiry_date, CURDATE()) AS days_left,
                    CASE 
                        WHEN DATEDIFF(expiry_date, CURDATE()) < 0 THEN 'expired'
                        WHEN DATEDIFF(expiry_date, CURDATE()) <= 7 THEN 'urgent'
                        WHEN DATEDIFF(expiry_date, CURDATE()) <= 30 THEN 'warning'
                        ELSE 'safe'
                    END AS status,
                    CASE 
                        WHEN DATEDIFF(expiry_date, CURDATE()) < 0 THEN 1
                        ELSE 0
                    END AS is_expired
                FROM api_item 
                ORDER BY days_left ASC
            """)
            
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return Response(results)

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get medicines filtered by expiry status"""
        status_filter = request.GET.get('status', None)
        
        queryset = Item.objects.all()
        
        if status_filter == 'expired':
            queryset = queryset.filter(expiry_date__lt=timezone.now().date())
        elif status_filter == 'urgent':
            queryset = queryset.filter(
                expiry_date__gte=timezone.now().date(),
                expiry_date__lte=timezone.now().date() + timedelta(days=7)
            )
        elif status_filter == 'warning':
            queryset = queryset.filter(
                expiry_date__gt=timezone.now().date() + timedelta(days=7),
                expiry_date__lte=timezone.now().date() + timedelta(days=30)
            )
        elif status_filter == 'safe':
            queryset = queryset.filter(
                expiry_date__gt=timezone.now().date() + timedelta(days=30)
            )
        
        serializer = ItemSummarySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiry_stats(self, request):
        """Get expiry statistics for dashboard"""
        today = timezone.now().date()
        
        stats = {
            'total_medicines': Item.objects.count(),
            'expired': Item.objects.filter(expiry_date__lt=today).count(),
            'urgent': Item.objects.filter(
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=7)
            ).count(),
            'warning': Item.objects.filter(
                expiry_date__gt=today + timedelta(days=7),
                expiry_date__lte=today + timedelta(days=30)
            ).count(),
            'safe': Item.objects.filter(
                expiry_date__gt=today + timedelta(days=30)
            ).count()
        }
        
        return Response(stats)