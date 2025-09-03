from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from shortener.models import ShortenedURL, Click, QRCode
from shortener.utils import generate_qr_code, get_client_info, get_location_info
from .serializers import (
    ShortenedURLSerializer, ShortenedURLCreateSerializer, ClickSerializer,
    URLAnalyticsSerializer, QRCodeSerializer, BulkURLCreateSerializer,
    URLStatsSerializer, UserSerializer
)
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthToken(ObtainAuthToken):
    """Custom authentication token view"""
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'is_premium': user.is_premium
        })

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

@method_decorator(ratelimit(key='user', rate='100/h', method='POST'), name='post')
class ShortenedURLListCreateView(generics.ListCreateAPIView):
    """List and create shortened URLs"""
    serializer_class = ShortenedURLSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = ShortenedURL.objects.filter(user=self.request.user)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by public status
        is_public = self.request.query_params.get('is_public')
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(original_url__icontains=search) |
                Q(short_code__icontains=search)
            )
        
        # Order by creation date (newest first)
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ShortenedURLCreateSerializer
        return ShortenedURLSerializer
    
    def perform_create(self, serializer):
        # Check rate limit for free users
        if not self.request.user.is_premium:
            today = timezone.now().date()
            today_count = ShortenedURL.objects.filter(
                user=self.request.user,
                created_at__date=today
            ).count()
            
            if today_count >= self.request.user.daily_url_limit:
                return Response(
                    {'error': f'Daily limit of {self.request.user.daily_url_limit} URLs reached'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
        
        url = serializer.save(user=self.request.user)
        
        # Generate QR code
        generate_qr_code(url)

class ShortenedURLDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a shortened URL"""
    serializer_class = ShortenedURLSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ShortenedURL.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def url_analytics_view(request, pk):
    """Get analytics for a specific URL"""
    try:
        url = ShortenedURL.objects.get(pk=pk, user=request.user)
    except ShortenedURL.DoesNotExist:
        return Response({'error': 'URL not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Time range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    clicks = Click.objects.filter(url=url, clicked_at__gte=start_date)
    
    # Basic statistics
    total_clicks = clicks.count()
    unique_visitors = clicks.values('ip_address').distinct().count()
    
    # Time-based statistics
    today = timezone.now().date()
    clicks_today = clicks.filter(clicked_at__date=today).count()
    clicks_this_week = clicks.filter(clicked_at__gte=today - timedelta(days=7)).count()
    clicks_this_month = clicks.filter(clicked_at__gte=today - timedelta(days=30)).count()
    
    # Geographic statistics
    top_countries = list(clicks.exclude(
        country__in=['', 'Unknown']
    ).values('country').annotate(
        count=Count('country')
    ).order_by('-count')[:10])
    
    # Technology statistics
    top_browsers = list(clicks.exclude(
        browser__in=['', 'Unknown']
    ).values('browser').annotate(
        count=Count('browser')
    ).order_by('-count')[:10])
    
    top_devices = list(clicks.exclude(
        device__in=['', 'Unknown']
    ).values('device').annotate(
        count=Count('device')
    ).order_by('-count')[:10])
    
    # Daily clicks for the period
    daily_clicks = []
    for i in range(days):
        date = (timezone.now() - timedelta(days=i)).date()
        count = clicks.filter(clicked_at__date=date).count()
        daily_clicks.append({
            'date': date.strftime('%Y-%m-%d'),
            'clicks': count
        })
    
    analytics_data = {
        'total_clicks': total_clicks,
        'unique_clicks': url.unique_clicks,
        'clicks_today': clicks_today,
        'clicks_this_week': clicks_this_week,
        'clicks_this_month': clicks_this_month,
        'top_countries': top_countries,
        'top_browsers': top_browsers,
        'top_devices': top_devices,
        'daily_clicks': daily_clicks[::-1]  # Reverse to show oldest first
    }
    
    serializer = URLAnalyticsSerializer(analytics_data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def url_clicks_view(request, pk):
    """Get click details for a specific URL"""
    try:
        url = ShortenedURL.objects.get(pk=pk, user=request.user)
    except ShortenedURL.DoesNotExist:
        return Response({'error': 'URL not found'}, status=status.HTTP_404_NOT_FOUND)
    
    clicks = Click.objects.filter(url=url).order_by('-clicked_at')
    
    # Pagination
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(clicks, request)
    
    if page is not None:
        serializer = ClickSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = ClickSerializer(clicks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def url_qr_code_view(request, pk):
    """Get QR code for a specific URL"""
    try:
        url = ShortenedURL.objects.get(pk=pk, user=request.user)
    except ShortenedURL.DoesNotExist:
        return Response({'error': 'URL not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        qr_code = url.qr_code
    except QRCode.DoesNotExist:
        # Generate QR code if it doesn't exist
        qr_code = generate_qr_code(url)
    
    serializer = QRCodeSerializer(qr_code)
    return Response(serializer.data)

@method_decorator(ratelimit(key='user', rate='10/h', method='POST'), name='post')
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_create_urls_view(request):
    """Create multiple URLs at once"""
    serializer = BulkURLCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    urls_data = serializer.validated_data['urls']
    is_public = serializer.validated_data.get('is_public', True)
    expires_at = serializer.validated_data.get('expires_at')
    
    # Check rate limit for free users
    if not request.user.is_premium:
        today = timezone.now().date()
        today_count = ShortenedURL.objects.filter(
            user=request.user,
            created_at__date=today
        ).count()
        
        if today_count + len(urls_data) > request.user.daily_url_limit:
            return Response(
                {'error': f'This would exceed your daily limit of {request.user.daily_url_limit} URLs'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
    
    created_urls = []
    for original_url in urls_data:
        url = ShortenedURL.objects.create(
            user=request.user,
            original_url=original_url,
            is_public=is_public,
            expires_at=expires_at
        )
        generate_qr_code(url)
        created_urls.append(url)
    
    serializer = ShortenedURLSerializer(created_urls, many=True)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats_view(request):
    """Get user statistics"""
    user = request.user
    
    # Basic counts
    total_urls = ShortenedURL.objects.filter(user=user).count()
    active_urls = ShortenedURL.objects.filter(user=user, is_active=True).count()
    total_clicks = Click.objects.filter(url__user=user).count()
    unique_visitors = Click.objects.filter(url__user=user).values('ip_address').distinct().count()
    
    # Calculate average clicks per URL
    avg_clicks_per_url = total_clicks / total_urls if total_urls > 0 else 0
    
    # Get top performing URL
    top_url = ShortenedURL.objects.filter(user=user).order_by('-click_count').first()
    
    stats_data = {
        'total_urls': total_urls,
        'active_urls': active_urls,
        'total_clicks': total_clicks,
        'unique_visitors': unique_visitors,
        'avg_clicks_per_url': round(avg_clicks_per_url, 2),
        'top_performing_url': top_url
    }
    
    serializer = URLStatsSerializer(stats_data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_view(request):
    """Get user profile information"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def bulk_delete_urls_view(request):
    """Delete multiple URLs at once"""
    url_ids = request.data.get('url_ids', [])
    
    if not url_ids:
        return Response({'error': 'No URL IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count = ShortenedURL.objects.filter(
        id__in=url_ids,
        user=request.user
    ).delete()[0]
    
    return Response({
        'message': f'Successfully deleted {deleted_count} URLs',
        'deleted_count': deleted_count
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_url_status_view(request, pk):
    """Toggle URL active status"""
    try:
        url = ShortenedURL.objects.get(pk=pk, user=request.user)
    except ShortenedURL.DoesNotExist:
        return Response({'error': 'URL not found'}, status=status.HTTP_404_NOT_FOUND)
    
    url.is_active = not url.is_active
    url.save()
    
    serializer = ShortenedURLSerializer(url)
    return Response(serializer.data)

# Public API endpoints (no authentication required)
@api_view(['GET'])
def public_url_info_view(request, short_code):
    """Get public information about a short URL"""
    try:
        url = ShortenedURL.objects.get(short_code=short_code, is_public=True, is_active=True)
    except ShortenedURL.DoesNotExist:
        return Response({'error': 'URL not found or not public'}, status=status.HTTP_404_NOT_FOUND)
    
    if url.is_expired:
        return Response({'error': 'URL has expired'}, status=status.HTTP_410_GONE)
    
    data = {
        'short_code': url.short_code,
        'original_url': url.original_url,
        'created_at': url.created_at,
        'click_count': url.click_count,
        'is_active': url.is_active
    }
    
    return Response(data)
