from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .models import ShortenedURL
import re

class URLShortenForm(forms.ModelForm):
    original_url = forms.URLField(
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'placeholder': 'Enter your long URL here...'
        }),
        help_text='Enter a valid URL starting with http:// or https://'
    )
    
    custom_alias = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'placeholder': 'Custom alias (optional)'
        }),
        help_text='Optional: Choose your own short code (letters, numbers, hyphens only)'
    )
    
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'type': 'datetime-local'
        }),
        help_text='Optional: Set an expiry date for this link'
    )
    
    is_public = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 accent-teal-600 focus:ring-teal-500 border-gray-300 rounded'
        }),
        help_text='Make this link publicly visible in your profile'
    )

    class Meta:
        model = ShortenedURL
        fields = ['original_url', 'custom_alias', 'expires_at', 'is_public']

    def clean_original_url(self):
        url = self.cleaned_data.get('original_url')
        
        # Basic URL validation
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            raise ValidationError("Please enter a valid URL.")
        
        # Check for malicious patterns
        malicious_patterns = [
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'file:',
            r'ftp:',
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, url.lower()):
                raise ValidationError("This URL type is not allowed for security reasons.")
        
        # Check for localhost/internal IPs (basic check)
        if any(x in url.lower() for x in ['localhost', '127.0.0.1', '0.0.0.0', '192.168.', '10.', '172.']):
            raise ValidationError("Internal/localhost URLs are not allowed.")
        
        return url

    def clean_custom_alias(self):
        alias = self.cleaned_data.get('custom_alias')
        if alias:
            # Check format (alphanumeric and hyphens only)
            if not re.match(r'^[a-zA-Z0-9-]+$', alias):
                raise ValidationError("Custom alias can only contain letters, numbers, and hyphens.")
            
            # Check if already exists
            if ShortenedURL.objects.filter(short_code=alias).exists():
                raise ValidationError("This custom alias is already taken.")
            
            # Check reserved words
            reserved_words = ['admin', 'api', 'www', 'dashboard', 'accounts', 'static', 'media']
            if alias.lower() in reserved_words:
                raise ValidationError("This alias is reserved and cannot be used.")
        
        return alias

class URLEditForm(forms.ModelForm):
    original_url = forms.URLField(
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent'
        })
    )
    
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent',
            'type': 'datetime-local'
        })
    )
    
    is_public = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 accent-teal-600 focus:ring-teal-500 border-gray-300 rounded'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 accent-teal-600 focus:ring-teal-500 border-gray-300 rounded'
        })
    )

    class Meta:
        model = ShortenedURL
        fields = ['original_url', 'expires_at', 'is_public', 'is_active']
