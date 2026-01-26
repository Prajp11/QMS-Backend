from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver

class Item(models.Model):
    # Basic Medicine Information (existing fields from migration 0002)
    name = models.CharField(max_length=100)  # Keep original max_length from migration
    batch_number = models.CharField(max_length=100, default='Unknown')
    manufacture_date = models.DateField(default='2000-01-01')
    expiry_date = models.DateField(default='2100-01-01')
    
    # New fields we need to add
    quantity = models.IntegerField(default=0)
    manufacturer = models.CharField(max_length=200, default='Unknown')
    category = models.CharField(max_length=100, default='General')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Quality Control Information (existing fields from migration 0002)
    supplier = models.CharField(max_length=255, default='Unknown')
    temperature = models.FloatField(default=0.0)
    humidity = models.FloatField(default=0.0)
    ph_level = models.FloatField(default=0.0)
    contaminant_level = models.FloatField(default=0.0)
    active_ingredient_purity = models.FloatField(default=0.0)
    inspected_by = models.CharField(max_length=255, default='Unknown')
    accepted_or_rejected = models.CharField(max_length=50, default='Unknown')
    
    # Timestamps - new fields
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['expiry_date']

    def __str__(self):
        return f"{self.name} - {self.batch_number}"

    @property
    def days_until_expiry(self):
        """Calculate days until expiry"""
        today = timezone.now().date()
        return (self.expiry_date - today).days

    @property
    def expiry_status(self):
        """Return expiry status based on days left"""
        days_left = self.days_until_expiry
        if days_left < 0:
            return 'expired'
        elif days_left <= 7:
            return 'urgent'
        elif days_left <= 30:
            return 'warning'
        else:
            return 'safe'
    
    @property
    def is_expired(self):
        """Check if medicine is expired"""
        return self.days_until_expiry < 0

class UserProfile(models.Model):
    """Extended user profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=50, default='inspector')
    avatar = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        ordering = ['-created_at']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)

    @property
    def is_expired(self):
        """Check if medicine is expired"""
        return self.days_until_expiry < 0