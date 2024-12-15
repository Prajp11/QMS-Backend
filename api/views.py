# from rest_framework import viewsets, filters
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from .models import Item
# from .serializers import ItemSerializer

# class ItemViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint for viewing, adding, updating, or deleting items.
#     Includes search, filtering, and ordering.
#     """
#     queryset = Item.objects.all()
#     serializer_class = ItemSerializer
#     permission_classes = [IsAuthenticated]  # Authentication required

#     # Add filtering and search functionality
#     filter_backends = [filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ['name', 'supplier', 'batch_number']
#     ordering_fields = ['name', 'batch_number', 'manufacture_date', 'expiry_date']
#     ordering = ['name']

#     @action(detail=False, methods=['get'], url_path='batch/(?P<batch_number>[^/.]+)')
#     def get_by_batch(self, request, batch_number=None):
#         """
#         Custom action to fetch items by batch number.
#         Example: /api/items/batch/<batch_number>/
#         """
#         items = self.queryset.filter(batch_number=batch_number)
#         serializer = self.get_serializer(items, many=True)
#         return Response(serializer.data)

#     @action(detail=False, methods=['get'], url_path='expired')
#     def expired_items(self, request):
#         """
#         Custom action to fetch expired items.
#         Example: /api/items/expired/
#         """
#         expired_items = self.queryset.filter(expiry_date__lt=datetime.date.today())
#         serializer = self.get_serializer(expired_items, many=True)
#         return Response(serializer.data)


from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated  # Import IsAuthenticated permission class
from .models import Item
from .serializers import ItemSerializer

class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows items to be viewed, added, updated, or deleted.
    Includes search functionality for querying items by specific fields.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]  # Protect the API with authentication

    # Add filtering and search functionality
    filter_backends = [filters.SearchFilter]  # Enable filtering 
    search_fields = ['name']  
    ordering_fields = ['name', 'batch_number', 'expiry_date']  # Fields that can be ordered
    ordering = ['name']  # Default ordering