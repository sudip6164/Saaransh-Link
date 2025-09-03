from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import string
import random

User = get_user_model()

class ShortenedURL(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='urls')
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=20, unique=True, db_index=True)
    custom_alias = models.CharField(max_length=50, blank=True, null=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Tracking
    click_count = models.PositiveIntegerField(default=0)
    unique_clicks = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def short_url(self):
        from django.conf import settings
        return f"{settings.BASE_URL}/{self.short_code}"
    
    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)
    
    def generate_short_code(self):
        from django.conf import settings
        length = getattr(settings, 'SHORT_URL_LENGTH', 6)
        characters = string.ascii_letters + string.digits
        
        while True:
            code = ''.join(random.choice(characters) for _ in range(length))
            if not ShortenedURL.objects.filter(short_code=code).exists():
                return code

class Click(models.Model):
    url = models.ForeignKey(ShortenedURL, on_delete=models.CASCADE, related_name='clicks')
    
    # Visitor info
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(blank=True, null=True)
    
    # Parsed info
    browser = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Location (if available)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Timestamp
    clicked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-clicked_at']
    
    def __str__(self):
        return f"Click on {self.url.short_code} at {self.clicked_at}"

class QRCode(models.Model):
    url = models.OneToOneField(ShortenedURL, on_delete=models.CASCADE, related_name='qr_code')
    image = models.ImageField(upload_to='qr_codes/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"QR Code for {self.url.short_code}"
