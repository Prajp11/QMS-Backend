# Create your views here.
# from rest_framework import viewsets
# from .models import Item
# from .serializers import ItemSerializer

# class ItemViewSet(viewsets.ModelViewSet):
#     queryset = Item.objects.all()
#     serializer_class = ItemSerializer



#Main Views
# from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated  # Import IsAuthenticated permission class
# from .models import Item
# from .serializers import ItemSerializer

# class ItemViewSet(viewsets.ModelViewSet):
#     queryset = Item.objects.all()
#     serializer_class = ItemSerializer
#     permission_classes = [IsAuthenticated]  # Protect the API with authentication


from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated  # Import IsAuthenticated permission class
from .models import Item
from .serializers import ItemSerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]  # Protect the API with authentication

    # Add search functionality
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'supplier', 'batch_number']  # Fields that can be searched