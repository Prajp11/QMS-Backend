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


    filter_backends = [filters.SearchFilter]
    search_fields = ['name']  
    ordering_fields = ['name', 'batch_number', 'expiry_date']  
    ordering = ['name']  

    def create(self, request, *args, **kwargs):
        """
        Handle the creation of a new item with only selected fields (name, batch_number, accepted_or_rejected)
        """
        
        data = {
            'name': request.data.get('name'),
            'batch_number': request.data.get('batch_number'),
            'accepted_or_rejected': request.data.get('accepted_or_rejected'),
        }

        if not all(value is not None for value in data.values()):
            return Response({"error": "All fields (name, batch_number, accepted_or_rejected) are required."}, status=400)

        # Create the item
        item = Item.objects.create(**data)

        serializer = self.get_serializer(item)
        return Response(serializer.data, status=201)