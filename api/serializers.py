from rest_framework import serializers
from .models import Item
from django.utils import timezone

class ItemSerializer(serializers.ModelSerializer):
    days_until_expiry = serializers.SerializerMethodField()
    expiry_status = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    days_since_manufacture = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'batch_number', 'manufacture_date', 'expiry_date', 
            'quantity', 'manufacturer', 'category', 'price',
            'supplier', 'temperature', 'humidity', 'ph_level', 
            'contaminant_level', 'active_ingredient_purity', 
            'inspected_by', 'accepted_or_rejected',
            'days_until_expiry', 'expiry_status', 'is_expired', 'days_since_manufacture',
            'created_at', 'updated_at'
        ]

    def get_days_until_expiry(self, obj):
        """Get days until expiry"""
        return obj.days_until_expiry

    def get_expiry_status(self, obj):
        """Get expiry status (expired, urgent, warning, safe)"""
        return obj.expiry_status

    def get_is_expired(self, obj):
        """Check if item is expired"""
        return obj.is_expired

    def get_days_since_manufacture(self, obj):
        """Calculate days since manufacture"""
        today = timezone.now().date()
        return (today - obj.manufacture_date).days

class ItemSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    days_until_expiry = serializers.SerializerMethodField()
    expiry_status = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'batch_number', 'expiry_date', 'quantity',
            'manufacturer', 'category', 'days_until_expiry', 'expiry_status'
        ]

    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry

    def get_expiry_status(self, obj):
        return obj.expiry_status