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
from django.http import JsonResponse, HttpResponse
import json
import csv
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


# ============================================
# QUALITY SCORE VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def quality_scores(request):
    """
    Get all medicines with quality scores
    Returns sorted list with quality metrics
    """
    try:
        medicines = Item.objects.all()
        
        # Calculate quality scores for all medicines
        medicine_scores = []
        for medicine in medicines:
            medicine_scores.append({
                'id': medicine.id,
                'name': medicine.name,
                'batch_number': medicine.batch_number,
                'manufacturer': medicine.manufacturer,
                'category': medicine.category,
                'supplier': medicine.supplier,
                'temperature': medicine.temperature,
                'humidity': medicine.humidity,
                'ph_level': medicine.ph_level,
                'contaminant_level': medicine.contaminant_level,
                'active_ingredient_purity': medicine.active_ingredient_purity,
                'quality_score': medicine.quality_score,
                'quality_grade': medicine.quality_grade,
                'quality_status': medicine.quality_status,
                'expiry_date': medicine.expiry_date,
                'days_until_expiry': medicine.days_until_expiry,
                'expiry_status': medicine.expiry_status
            })
        
        # Sort by quality score (descending - highest first)
        medicine_scores.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return Response({
            'total': len(medicine_scores),
            'medicines': medicine_scores
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to calculate quality scores',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def quality_top_performers(request):
    """
    Get top 5 best quality medicines
    """
    try:
        medicines = Item.objects.all()
        
        # Calculate quality scores
        medicine_scores = []
        for medicine in medicines:
            medicine_scores.append({
                'id': medicine.id,
                'name': medicine.name,
                'batch_number': medicine.batch_number,
                'manufacturer': medicine.manufacturer,
                'supplier': medicine.supplier,
                'quality_score': medicine.quality_score,
                'quality_grade': medicine.quality_grade,
                'quality_status': medicine.quality_status,
                'temperature': medicine.temperature,
                'humidity': medicine.humidity,
                'ph_level': medicine.ph_level,
                'contaminant_level': medicine.contaminant_level,
                'active_ingredient_purity': medicine.active_ingredient_purity
            })
        
        # Sort by quality score (descending) and get top 5
        medicine_scores.sort(key=lambda x: x['quality_score'], reverse=True)
        top_5 = medicine_scores[:5]
        
        return Response({
            'count': len(top_5),
            'top_performers': top_5
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch top performers',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def quality_poor_performers(request):
    """
    Get top 5 worst quality medicines (need attention)
    """
    try:
        medicines = Item.objects.all()
        
        # Calculate quality scores
        medicine_scores = []
        for medicine in medicines:
            medicine_scores.append({
                'id': medicine.id,
                'name': medicine.name,
                'batch_number': medicine.batch_number,
                'manufacturer': medicine.manufacturer,
                'supplier': medicine.supplier,
                'quality_score': medicine.quality_score,
                'quality_grade': medicine.quality_grade,
                'quality_status': medicine.quality_status,
                'temperature': medicine.temperature,
                'humidity': medicine.humidity,
                'ph_level': medicine.ph_level,
                'contaminant_level': medicine.contaminant_level,
                'active_ingredient_purity': medicine.active_ingredient_purity
            })
        
        # Sort by quality score (ascending) and get bottom 5
        medicine_scores.sort(key=lambda x: x['quality_score'])
        bottom_5 = medicine_scores[:5]
        
        return Response({
            'count': len(bottom_5),
            'poor_performers': bottom_5
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch poor performers',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def quality_statistics(request):
    """
    Get overall quality statistics
    """
    try:
        medicines = Item.objects.all()
        total = medicines.count()
        
        if total == 0:
            return Response({
                'total_medicines': 0,
                'average_score': 0,
                'grade_distribution': {},
                'status_distribution': {}
            })
        
        # Calculate scores for all medicines
        scores = []
        grade_count = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        status_count = {'Excellent': 0, 'Good': 0, 'Fair': 0, 'Poor': 0, 'Failed': 0}
        
        for medicine in medicines:
            score = medicine.quality_score
            scores.append(score)
            grade_count[medicine.quality_grade] += 1
            status_count[medicine.quality_status] += 1
        
        average_score = sum(scores) / len(scores)
        
        return Response({
            'total_medicines': total,
            'average_score': round(average_score, 2),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'grade_distribution': grade_count,
            'status_distribution': status_count,
            'excellent_count': status_count['Excellent'],
            'good_count': status_count['Good'],
            'fair_count': status_count['Fair'],
            'poor_count': status_count['Poor'],
            'failed_count': status_count['Failed']
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to calculate quality statistics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def quality_by_grade(request, grade):
    """
    Get medicines filtered by quality grade (A, B, C, D, F)
    """
    try:
        if grade not in ['A', 'B', 'C', 'D', 'F']:
            return Response({
                'error': 'Invalid grade. Use A, B, C, D, or F'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        medicines = Item.objects.all()
        
        filtered_medicines = []
        for medicine in medicines:
            if medicine.quality_grade == grade:
                serializer = ItemSerializer(medicine)
                filtered_medicines.append(serializer.data)
        
        return Response({
            'grade': grade,
            'count': len(filtered_medicines),
            'medicines': filtered_medicines
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to filter by grade',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# BATCH ACCEPTANCE RATE DASHBOARD
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def acceptance_stats(request):
    """
    Batch Acceptance Rate Dashboard
    Returns acceptance/rejection statistics with supplier breakdown
    
    Query Parameters:
    - date_from: Start date (YYYY-MM-DD) - optional
    - date_to: End date (YYYY-MM-DD) - optional
    
    Response:
    - total_batches: Total number of batches
    - accepted_batches: Number of accepted batches
    - rejected_batches: Number of rejected batches
    - acceptance_rate: Percentage of accepted batches
    - rejection_reasons: Top rejection reasons with counts
    - supplier_stats: Per-supplier acceptance/rejection breakdown
    """
    try:
        # Get date range filters from query parameters
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Start with all items
        queryset = Item.objects.all()
        
        # Apply date filters if provided
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__gte=date_from_obj)
            except ValueError:
                return Response({
                    'error': 'Invalid date_from format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                # Add one day to include the end date
                date_to_obj = date_to_obj + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=date_to_obj)
            except ValueError:
                return Response({
                    'error': 'Invalid date_to format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate overall statistics
        total_batches = queryset.count()
        accepted_batches = queryset.filter(accepted_or_rejected__iexact='accepted').count()
        rejected_batches = queryset.filter(accepted_or_rejected__iexact='rejected').count()
        
        # Calculate acceptance rate
        acceptance_rate = round((accepted_batches / total_batches * 100), 2) if total_batches > 0 else 0.0
        rejection_rate = round((rejected_batches / total_batches * 100), 2) if total_batches > 0 else 0.0
        
        # Get rejection reasons - calculate quality status in Python (it's a @property, not a DB field)
        rejection_reasons = []
        rejected_items = queryset.filter(accepted_or_rejected__iexact='rejected')
        
        # Group rejected items by quality status (calculated in Python)
        reason_map = {}
        for item in rejected_items:
            status = item.quality_status  # This is a @property, calculated on-the-fly
            if status in reason_map:
                reason_map[status] += 1
            else:
                reason_map[status] = 1
        
        # Convert to list and sort by count
        for reason, count in sorted(reason_map.items(), key=lambda x: x[1], reverse=True)[:5]:
            rejection_reasons.append({
                'reason': reason or 'Unknown',
                'count': count,
                'percentage': round((count / rejected_batches * 100), 2) if rejected_batches > 0 else 0.0
            })
        
        # Get supplier-wise breakdown
        from django.db.models import Q
        suppliers = queryset.values('supplier').distinct()
        supplier_stats = []
        
        for supplier_obj in suppliers:
            supplier_name = supplier_obj['supplier']
            supplier_items = queryset.filter(supplier=supplier_name)
            
            supplier_total = supplier_items.count()
            supplier_accepted = supplier_items.filter(accepted_or_rejected__iexact='accepted').count()
            supplier_rejected = supplier_items.filter(accepted_or_rejected__iexact='rejected').count()
            supplier_acceptance_rate = round((supplier_accepted / supplier_total * 100), 2) if supplier_total > 0 else 0.0
            
            supplier_stats.append({
                'supplier': supplier_name,
                'total_batches': supplier_total,
                'accepted': supplier_accepted,
                'rejected': supplier_rejected,
                'acceptance_rate': supplier_acceptance_rate,
                'rejection_rate': round(100 - supplier_acceptance_rate, 2)
            })
        
        # Sort by acceptance rate (best suppliers first)
        supplier_stats.sort(key=lambda x: x['acceptance_rate'], reverse=True)
        
        # Response data
        response_data = {
            'overview': {
                'total_batches': total_batches,
                'accepted_batches': accepted_batches,
                'rejected_batches': rejected_batches,
                'acceptance_rate': acceptance_rate,
                'rejection_rate': rejection_rate
            },
            'rejection_reasons': rejection_reasons,
            'supplier_stats': supplier_stats,
            'date_range': {
                'from': date_from or 'All time',
                'to': date_to or 'Present'
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to generate acceptance statistics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# ENVIRONMENTAL ALERT SYSTEM
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def alerts_count(request):
    """
    Get count of environmental alerts
    Returns total alerts, critical alerts, and breakdown by type
    """
    try:
        items = Item.objects.all()
        
        total_alerts = 0
        critical_alerts = 0
        warning_alerts = 0
        alert_types = {
            'temperature': 0,
            'humidity': 0,
            'contamination': 0,
            'purity': 0,
            'ph_level': 0
        }
        items_with_alerts = 0
        
        for item in items:
            if item.alerts and len(item.alerts) > 0:
                items_with_alerts += 1
                for alert in item.alerts:
                    total_alerts += 1
                    
                    # Count by severity
                    if alert.get('severity') == 'critical':
                        critical_alerts += 1
                    else:
                        warning_alerts += 1
                    
                    # Count by type
                    alert_type = alert.get('type')
                    if alert_type in alert_types:
                        alert_types[alert_type] += 1
        
        return Response({
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'items_with_alerts': items_with_alerts,
            'total_items': items.count(),
            'alert_types': alert_types
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to count alerts',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def alerts_list(request):
    """
    Get list of all items with environmental alerts
    Query Parameters:
    - severity: Filter by severity (critical, warning)
    - type: Filter by alert type (temperature, humidity, contamination, purity, ph_level)
    - limit: Limit number of results (default: all)
    """
    try:
        severity_filter = request.GET.get('severity')  # 'critical' or 'warning'
        type_filter = request.GET.get('type')  # alert type
        limit = request.GET.get('limit')  # number of items to return
        
        items = Item.objects.all()
        items_with_alerts = []
        
        for item in items:
            if item.alerts and len(item.alerts) > 0:
                # Apply filters
                filtered_alerts = item.alerts
                
                if severity_filter:
                    filtered_alerts = [a for a in filtered_alerts if a.get('severity') == severity_filter]
                
                if type_filter:
                    filtered_alerts = [a for a in filtered_alerts if a.get('type') == type_filter]
                
                # Only include if alerts remain after filtering
                if filtered_alerts:
                    items_with_alerts.append({
                        'id': item.id,
                        'name': item.name,
                        'batch_number': item.batch_number,
                        'manufacturer': item.manufacturer,
                        'supplier': item.supplier,
                        'category': item.category,
                        'alerts': filtered_alerts,
                        'alert_count': len(filtered_alerts),
                        'critical_count': sum(1 for a in filtered_alerts if a.get('severity') == 'critical'),
                        'warning_count': sum(1 for a in filtered_alerts if a.get('severity') == 'warning'),
                        'quality_score': item.quality_score,
                        'quality_grade': item.quality_grade,
                        'temperature': item.temperature,
                        'humidity': item.humidity,
                        'contaminant_level': item.contaminant_level,
                        'active_ingredient_purity': item.active_ingredient_purity,
                        'ph_level': item.ph_level
                    })
        
        # Sort by alert count (most alerts first)
        items_with_alerts.sort(key=lambda x: (x['critical_count'], x['alert_count']), reverse=True)
        
        # Apply limit if specified
        if limit:
            try:
                limit = int(limit)
                items_with_alerts = items_with_alerts[:limit]
            except ValueError:
                pass
        
        return Response({
            'count': len(items_with_alerts),
            'items': items_with_alerts
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to list alerts',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# CSV TEMPLATE DOWNLOAD
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])  # Can be accessed without authentication
def download_csv_template(request):
    """
    Generate and download CSV template for bulk medicine upload
    Includes all required columns with 1 sample data row
    """
    # Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="medicine_import_template.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row (exact column names matching your model)
    headers = [
        'Medicine Name',
        'Batch Number',
        'Manufacture Date',
        'Expiry Date',
        'Quantity',
        'Manufacturer',
        'Category',
        'Price',
        'Supplier',
        'Temperature (°C)',
        'Humidity (%)',
        'pH Level',
        'Contaminant Level (ppm)',
        'Active Ingredient Purity (%)',
        'Inspected By',
        'Status (Accepted/Rejected)'
    ]
    writer.writerow(headers)
    
    # Write sample data row
    sample_row = [
        'Aspirin',                    # Medicine Name
        'ASP-2024-001',              # Batch Number
        '2024-01-15',                # Manufacture Date (YYYY-MM-DD)
        '2026-01-15',                # Expiry Date (YYYY-MM-DD)
        '1000',                      # Quantity
        'PharmaCorp Ltd',            # Manufacturer
        'Pain Relief',               # Category
        '25.99',                     # Price
        'MedSupply Inc',             # Supplier
        '22.5',                      # Temperature (°C)
        '50.0',                      # Humidity (%)
        '7.0',                       # pH Level
        '0.001',                     # Contaminant Level (ppm)
        '99.5',                      # Active Ingredient Purity (%)
        'Dr. John Smith',            # Inspected By
        'Accepted'                   # Status
    ]
    writer.writerow(sample_row)
    
    # Write additional example rows for better understanding
    writer.writerow([
        'Paracetamol',
        'PAR-2024-002',
        '2024-02-10',
        '2026-02-10',
        '2000',
        'HealthCare Pharma',
        'Fever & Pain',
        '15.50',
        'Global Meds',
        '23.0',
        '45.0',
        '6.8',
        '0.002',
        '98.5',
        'Dr. Sarah Johnson',
        'Accepted'
    ])
    
    writer.writerow([
        'Ibuprofen',
        'IBU-2024-003',
        '2024-03-05',
        '2026-03-05',
        '1500',
        'MediCare Industries',
        'Anti-Inflammatory',
        '30.00',
        'Prime Distributors',
        '21.5',
        '55.0',
        '7.2',
        '0.0005',
        '99.8',
        'Dr. Michael Brown',
        'Accepted'
    ])
    
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_upload_medicines(request):
    """
    Bulk upload medicines from CSV file
    Expects CSV file with same format as template
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file uploaded',
                'message': 'Please upload a CSV file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = request.FILES['file']
        
        # Validate file type
        if not csv_file.name.endswith('.csv'):
            return Response({
                'error': 'Invalid file type',
                'message': 'Please upload a CSV file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Read and decode CSV file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        
        created_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            try:
                # Create medicine from CSV row
                medicine = Item.objects.create(
                    name=row.get('Medicine Name', '').strip(),
                    batch_number=row.get('Batch Number', '').strip(),
                    manufacture_date=row.get('Manufacture Date', '2000-01-01'),
                    expiry_date=row.get('Expiry Date', '2100-01-01'),
                    quantity=int(row.get('Quantity', 0)),
                    manufacturer=row.get('Manufacturer', 'Unknown').strip(),
                    category=row.get('Category', 'General').strip(),
                    price=float(row.get('Price', 0.0)),
                    supplier=row.get('Supplier', 'Unknown').strip(),
                    temperature=float(row.get('Temperature (°C)', 0.0)),
                    humidity=float(row.get('Humidity (%)', 0.0)),
                    ph_level=float(row.get('pH Level', 0.0)),
                    contaminant_level=float(row.get('Contaminant Level (ppm)', 0.0)),
                    active_ingredient_purity=float(row.get('Active Ingredient Purity (%)', 0.0)),
                    inspected_by=row.get('Inspected By', 'Unknown').strip(),
                    accepted_or_rejected=row.get('Status (Accepted/Rejected)', 'Unknown').strip()
                )
                created_count += 1
                
            except Exception as e:
                errors.append({
                    'row': row_num,
                    'data': dict(row),
                    'error': str(e)
                })
        
        response_data = {
            'message': 'Bulk upload completed',
            'created': created_count,
            'total_rows': created_count + len(errors),
            'errors_count': len(errors)
        }
        
        if errors:
            response_data['errors'] = errors[:10]  # Return first 10 errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'Bulk upload failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)