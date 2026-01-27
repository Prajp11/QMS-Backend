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
    
    def calculate_quality_score(self):
        """
        Calculate overall quality score based on multiple parameters
        Score range: 0-100
        Higher score = Better quality
        
        Formula breakdown:
        - Temperature: Ideal range 20-25°C (20% weight)
        - Humidity: Ideal range 40-60% (20% weight)
        - pH Level: Ideal range 6.5-7.5 (15% weight)
        - Contaminant Level: Lower is better, <0.01 ppm (25% weight)
        - Active Ingredient Purity: Higher is better, >95% (20% weight)
        """
        score = 0.0
        
        # Temperature Score (20 points max)
        # Ideal: 20-25°C, acceptable: 15-30°C
        temp = self.temperature
        if 20 <= temp <= 25:
            temp_score = 20
        elif 15 <= temp <= 30:
            # Linear decay outside ideal range
            deviation = min(abs(temp - 20), abs(temp - 25))
            temp_score = max(0, 20 - (deviation * 2))
        else:
            temp_score = 0
        score += temp_score
        
        # Humidity Score (20 points max)
        # Ideal: 40-60%, acceptable: 30-70%
        humidity = self.humidity
        if 40 <= humidity <= 60:
            humidity_score = 20
        elif 30 <= humidity <= 70:
            deviation = min(abs(humidity - 40), abs(humidity - 60))
            humidity_score = max(0, 20 - (deviation * 1.5))
        else:
            humidity_score = 0
        score += humidity_score
        
        # pH Level Score (15 points max)
        # Ideal: 6.5-7.5, acceptable: 6.0-8.0
        ph = self.ph_level
        if 6.5 <= ph <= 7.5:
            ph_score = 15
        elif 6.0 <= ph <= 8.0:
            deviation = min(abs(ph - 6.5), abs(ph - 7.5))
            ph_score = max(0, 15 - (deviation * 10))
        else:
            ph_score = 0
        score += ph_score
        
        # Contaminant Level Score (25 points max)
        # Ideal: <0.001 ppm, acceptable: <0.01 ppm
        contaminant = self.contaminant_level
        if contaminant <= 0.001:
            contaminant_score = 25
        elif contaminant <= 0.01:
            # Linear scoring between 0.001 and 0.01
            contaminant_score = 25 - ((contaminant - 0.001) / 0.009 * 15)
        elif contaminant <= 0.1:
            contaminant_score = max(0, 10 - (contaminant * 50))
        else:
            contaminant_score = 0
        score += contaminant_score
        
        # Active Ingredient Purity Score (20 points max)
        # Ideal: >99%, acceptable: >90%
        purity = self.active_ingredient_purity
        if purity >= 99:
            purity_score = 20
        elif purity >= 95:
            purity_score = 15 + ((purity - 95) / 4 * 5)
        elif purity >= 90:
            purity_score = 10 + ((purity - 90) / 5 * 5)
        else:
            purity_score = max(0, purity / 90 * 10)
        score += purity_score
        
        # Round to 2 decimal places
        return round(score, 2)
    
    @property
    def quality_score(self):
        """Get the calculated quality score"""
        return self.calculate_quality_score()
    
    @property
    def quality_grade(self):
        """
        Get quality grade based on score
        A: 90-100 (Excellent)
        B: 80-89 (Good)
        C: 70-79 (Fair)
        D: 60-69 (Poor)
        F: <60 (Failed)
        """
        score = self.quality_score
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    @property
    def quality_status(self):
        """Get quality status description"""
        score = self.quality_score
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 70:
            return 'Fair'
        elif score >= 60:
            return 'Poor'
        else:
            return 'Failed'

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