from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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

    def create(self, request, *args, **kwargs):
        """
        Handle the creation of a new item with only selected fields (name, batch_number, accepted_or_rejected)
        """
        # Only allow name, batch_number, and accepted_or_rejected fields to be used for creating an item
        data = {
            'name': request.data.get('name'),
            'batch_number': request.data.get('batch_number'),
            'accepted_or_rejected': request.data.get('accepted_or_rejected'),
        }

        # Ensure all required fields are present
        if not all(value is not None for value in data.values()):
            return Response({"error": "All fields (name, batch_number, accepted_or_rejected) are required."}, status=400)

        # Create the item
        item = Item.objects.create(**data)

        # Serialize and return the new item
        serializer = self.get_serializer(item)
        return Response(serializer.data, status=201)