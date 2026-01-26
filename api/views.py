from rest_framework import viewsets, filters, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from django.db import connection
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import datetime, timedelta
from .models import Item
from .serializers import ItemSerializer, ItemSummarySerializer

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