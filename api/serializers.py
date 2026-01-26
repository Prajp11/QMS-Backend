from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Item, UserProfile
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


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'department', 'employee_id', 'role', 'avatar']
        

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with profile information"""
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile']
        read_only_fields = ['date_joined']
    
    def get_profile(self, obj):
        """Get profile data, create if not exists"""
        try:
            if hasattr(obj, 'profile'):
                return UserProfileSerializer(obj.profile).data
            else:
                # Create profile if it doesn't exist
                profile = UserProfile.objects.create(user=obj)
                return UserProfileSerializer(profile).data
        except Exception as e:
            print(f"Error getting profile for user {obj.username}: {e}")
            # Return default profile data
            return {
                'phone_number': '',
                'department': '',
                'employee_id': '',
                'role': 'inspector',
                'avatar': None
            }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters long"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirm your password"
    )
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    
    # Profile fields
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    employee_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=[
            ('inspector', 'Quality Inspector'),
            ('supervisor', 'Supervisor'),
            ('admin', 'Administrator'),
            ('analyst', 'Quality Analyst')
        ],
        default='inspector'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'phone_number', 'department', 'employee_id', 'role'
        ]
        
    def validate_username(self, value):
        """Validate username is unique"""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value.lower()
    
    def validate_email(self, value):
        """Validate email is unique"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value.lower()
    
    def validate_employee_id(self, value):
        """Validate employee ID is unique if provided"""
        if value and UserProfile.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("A user with this employee ID already exists.")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation and strength"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        # Use Django's built-in password validation
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        return attrs
    
    def create(self, validated_data):
        """Create user and profile"""
        # Remove profile fields and password_confirm
        profile_data = {
            'phone_number': validated_data.pop('phone_number', ''),
            'department': validated_data.pop('department', ''),
            'employee_id': validated_data.pop('employee_id', ''),
            'role': validated_data.pop('role', 'inspector'),
        }
        validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Update profile (created by signal)
        profile = user.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    
    def validate(self, attrs):
        """Validate user credentials"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Try to authenticate with username or email
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            # If username auth fails, try with email
            if not user:
                try:
                    user_obj = User.objects.get(email__iexact=username)
                    user = authenticate(
                        request=self.context.get('request'),
                        username=user_obj.username,
                        password=password
                    )
                except User.DoesNotExist:
                    pass
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "username" and "password".',
                code='authorization'
            )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        """Validate new password confirmation"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match."})
        
        # Use Django's built-in password validation
        try:
            validate_password(new_password, self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return attrs


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile']
    
    def validate_email(self, value):
        """Validate email is unique (excluding current user)"""
        if User.objects.filter(email__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value.lower()
    
    def update(self, instance, validated_data):
        """Update user and profile"""
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile fields
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance