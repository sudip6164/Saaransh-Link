from rest_framework import serializers
from shortener.models import ShortenedURL, Click, QRCode
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_premium', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class ShortenedURLSerializer(serializers.ModelSerializer):
    short_url = serializers.ReadOnlyField()
    click_count = serializers.ReadOnlyField()
    unique_clicks = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ShortenedURL
        fields = [
            'id', 'original_url', 'short_code', 'custom_alias', 'short_url',
            'is_active', 'is_public', 'expires_at', 'click_count', 'unique_clicks',
            'is_expired', 'created_at', 'updated_at', 'user'
        ]
        read_only_fields = ['id', 'short_code', 'short_url', 'click_count', 'unique_clicks', 'created_at', 'updated_at', 'user']

    def validate_original_url(self, value):
        """Validate the original URL"""
        validator = URLValidator()
        try:
            validator(value)
        except ValidationError:
            raise serializers.ValidationError("Please enter a valid URL.")
        
        # Check for malicious patterns
        malicious_patterns = [
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'file:',
            r'ftp:',
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, value.lower()):
                raise serializers.ValidationError("This URL type is not allowed for security reasons.")
        
        return value

    def validate_custom_alias(self, value):
        """Validate custom alias"""
        if value:
            # Check format
            if not re.match(r'^[a-zA-Z0-9-]+$', value):
                raise serializers.ValidationError("Custom alias can only contain letters, numbers, and hyphens.")
            
            # Check if already exists
            if ShortenedURL.objects.filter(short_code=value).exists():
                raise serializers.ValidationError("This custom alias is already taken.")
            
            # Check reserved words
            reserved_words = ['admin', 'api', 'www', 'dashboard', 'accounts', 'static', 'media']
            if value.lower() in reserved_words:
                raise serializers.ValidationError("This alias is reserved and cannot be used.")
        
        return value

class ShortenedURLCreateSerializer(ShortenedURLSerializer):
    """Serializer for creating URLs with custom alias handling"""
    
    def create(self, validated_data):
        # Handle custom alias
        custom_alias = validated_data.pop('custom_alias', None)
        url = ShortenedURL.objects.create(**validated_data)
        
        if custom_alias:
            url.short_code = custom_alias
            url.save()
        
        return url

class ClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = Click
        fields = [
            'id', 'ip_address', 'user_agent', 'referrer', 'browser',
            'device', 'os', 'country', 'city', 'clicked_at'
        ]
        read_only_fields = ['id', 'clicked_at']

class URLAnalyticsSerializer(serializers.Serializer):
    """Serializer for URL analytics data"""
    total_clicks = serializers.IntegerField()
    unique_clicks = serializers.IntegerField()
    clicks_today = serializers.IntegerField()
    clicks_this_week = serializers.IntegerField()
    clicks_this_month = serializers.IntegerField()
    top_countries = serializers.ListField()
    top_browsers = serializers.ListField()
    top_devices = serializers.ListField()
    daily_clicks = serializers.ListField()

class QRCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRCode
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['id', 'created_at']

class BulkURLCreateSerializer(serializers.Serializer):
    """Serializer for bulk URL creation"""
    urls = serializers.ListField(
        child=serializers.URLField(),
        min_length=1,
        max_length=50
    )
    is_public = serializers.BooleanField(default=True)
    expires_at = serializers.DateTimeField(required=False)

class URLStatsSerializer(serializers.Serializer):
    """Serializer for user URL statistics"""
    total_urls = serializers.IntegerField()
    active_urls = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    avg_clicks_per_url = serializers.FloatField()
    top_performing_url = ShortenedURLSerializer()
