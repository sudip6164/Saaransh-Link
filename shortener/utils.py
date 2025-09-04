import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings
from .models import QRCode
import user_agents
import socket

def generate_qr_code(url_obj):
    """Generate QR code for a shortened URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_obj.short_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Create or update QR code record
    qr_code, created = QRCode.objects.get_or_create(url=url_obj)
    qr_code.image.save(
        f'{url_obj.short_code}_qr.png',
        File(buffer),
        save=True
    )
    
    return qr_code

def get_client_info(request):
    """Extract client information from request"""
    # Get IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    # Get user agent
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = user_agents.parse(user_agent_string)
    
    # Get referrer
    referrer = request.META.get('HTTP_REFERER')
    
    return {
        'ip_address': ip_address,
        'user_agent': user_agent_string,
        'referrer': referrer,
        'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
        'device': user_agent.device.family,
        'os': f"{user_agent.os.family} {user_agent.os.version_string}",
    }

def get_location_info(ip_address):
    """Get location information from IP address using free ip-api.com service"""
    import requests
    try:
        url = f'http://ip-api.com/json/{ip_address}?fields=status,country,city'
        response = requests.get(url, timeout=2)
        data = response.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country', 'Unknown'),
                'city': data.get('city', 'Unknown')
            }
        else:
            return {'country': 'Unknown', 'city': 'Unknown'}
    except Exception:
        return {'country': 'Unknown', 'city': 'Unknown'}

def validate_url_safety(url):
    """Additional URL safety validation"""
    import re
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'bit\.ly',
        r'tinyurl\.com',
        r'short\.link',
        # Add more URL shortener domains to prevent chaining
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, url.lower()):
            return False, "URL shortener chaining is not allowed"
    
    return True, "URL is safe"
