from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
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

    # Enable filtering and search functionality
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']  # Searchable fields
    ordering_fields = ['name', 'batch_number', 'expiry_date']  # Fields that can be ordered
    ordering = ['name']  # Default ordering
