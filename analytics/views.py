from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from shortener.models import ShortenedURL, Click
from django.contrib.auth import get_user_model
import json
from collections import defaultdict

User = get_user_model()

@login_required
def analytics_dashboard(request):
    """Main analytics dashboard for users"""
    user_urls = ShortenedURL.objects.filter(user=request.user)
    
    # Overall statistics
    total_urls = user_urls.count()
    total_clicks = Click.objects.filter(url__user=request.user).count()
    active_urls = user_urls.filter(is_active=True).count()
    
    # Time-based statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    clicks_today = Click.objects.filter(
        url__user=request.user,
        clicked_at__date=today
    ).count()
    
    clicks_this_week = Click.objects.filter(
        url__user=request.user,
        clicked_at__date__gte=week_ago
    ).count()
    
    clicks_this_month = Click.objects.filter(
        url__user=request.user,
        clicked_at__date__gte=month_ago
    ).count()
    
    # Top performing URLs
    top_urls = user_urls.order_by('-click_count')[:5]
    
    # Recent activity
    recent_clicks = Click.objects.filter(
        url__user=request.user
    ).order_by('-clicked_at')[:10]
    
    context = {
        'total_urls': total_urls,
        'total_clicks': total_clicks,
        'active_urls': active_urls,
        'clicks_today': clicks_today,
        'clicks_this_week': clicks_this_week,
        'clicks_this_month': clicks_this_month,
        'top_urls': top_urls,
        'recent_clicks': recent_clicks,
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
def url_analytics_detail(request, pk):
    """Detailed analytics for a specific URL"""
    url = get_object_or_404(ShortenedURL, pk=pk, user=request.user)
    
    # Time range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    clicks = Click.objects.filter(url=url, clicked_at__gte=start_date)
    
    # Basic statistics
    total_clicks = clicks.count()
    unique_visitors = clicks.values('ip_address').distinct().count()
    
    # Time-based analysis
    daily_clicks = get_daily_clicks(clicks, days)
    hourly_distribution = get_hourly_distribution(clicks)
    
    # Geographic analysis
    country_stats = clicks.values('country').annotate(
        count=Count('country')
    ).order_by('-count')[:10]
    
    # Technology analysis
    browser_stats = clicks.values('browser').annotate(
        count=Count('browser')
    ).order_by('-count')[:10]
    
    device_stats = clicks.values('device').annotate(
        count=Count('device')
    ).order_by('-count')[:10]
    
    os_stats = clicks.values('os').annotate(
        count=Count('os')
    ).order_by('-count')[:10]
    
    # Referrer analysis
    referrer_stats = clicks.exclude(referrer__isnull=True).exclude(
        referrer__exact=''
    ).values('referrer').annotate(
        count=Count('referrer')
    ).order_by('-count')[:10]
    
    context = {
        'url': url,
        'total_clicks': total_clicks,
        'unique_visitors': unique_visitors,
        'daily_clicks': json.dumps(daily_clicks),
        'hourly_distribution': json.dumps(hourly_distribution),
        'country_stats': country_stats,
        'browser_stats': browser_stats,
        'device_stats': device_stats,
        'os_stats': os_stats,
        'referrer_stats': referrer_stats,
        'days': days,
    }
    
    return render(request, 'analytics/url_detail.html', context)

@login_required
def analytics_api(request):
    """API endpoint for real-time analytics data"""
    if request.method == 'GET':
        action = request.GET.get('action')
        
        if action == 'daily_clicks':
            days = int(request.GET.get('days', 7))
            url_id = request.GET.get('url_id')
            
            if url_id:
                url = get_object_or_404(ShortenedURL, pk=url_id, user=request.user)
                clicks = Click.objects.filter(url=url)
            else:
                clicks = Click.objects.filter(url__user=request.user)
            
            data = get_daily_clicks(clicks, days)
            return JsonResponse({'data': data})
        
        elif action == 'top_countries':
            url_id = request.GET.get('url_id')
            
            if url_id:
                url = get_object_or_404(ShortenedURL, pk=url_id, user=request.user)
                clicks = Click.objects.filter(url=url)
            else:
                clicks = Click.objects.filter(url__user=request.user)
            
            countries = clicks.values('country').annotate(
                count=Count('country')
            ).order_by('-count')[:10]
            
            return JsonResponse({'data': list(countries)})
        
        elif action == 'browser_stats':
            url_id = request.GET.get('url_id')
            
            if url_id:
                url = get_object_or_404(ShortenedURL, pk=url_id, user=request.user)
                clicks = Click.objects.filter(url=url)
            else:
                clicks = Click.objects.filter(url__user=request.user)
            
            browsers = clicks.values('browser').annotate(
                count=Count('browser')
            ).order_by('-count')[:10]
            
            return JsonResponse({'data': list(browsers)})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin)
def admin_analytics(request):
    """Admin analytics dashboard"""
    # Overall system statistics
    total_users = User.objects.count()
    total_urls = ShortenedURL.objects.count()
    total_clicks = Click.objects.count()
    active_urls = ShortenedURL.objects.filter(is_active=True).count()
    
    # Time-based statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
    new_users_month = User.objects.filter(date_joined__date__gte=month_ago).count()
    
    new_urls_today = ShortenedURL.objects.filter(created_at__date=today).count()
    new_urls_week = ShortenedURL.objects.filter(created_at__date__gte=week_ago).count()
    new_urls_month = ShortenedURL.objects.filter(created_at__date__gte=month_ago).count()
    
    clicks_today = Click.objects.filter(clicked_at__date=today).count()
    clicks_week = Click.objects.filter(clicked_at__date__gte=week_ago).count()
    clicks_month = Click.objects.filter(clicked_at__date__gte=month_ago).count()
    
    # Top users by URL count
    top_users = User.objects.annotate(
        url_count=Count('urls')
    ).order_by('-url_count')[:10]
    
    # Top URLs by clicks
    top_urls = ShortenedURL.objects.order_by('-click_count')[:10]
    
    # Geographic distribution
    top_countries = Click.objects.values('country').annotate(
        count=Count('country')
    ).order_by('-count')[:10]
    
    context = {
        'total_users': total_users,
        'total_urls': total_urls,
        'total_clicks': total_clicks,
        'active_urls': active_urls,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        'new_urls_today': new_urls_today,
        'new_urls_week': new_urls_week,
        'new_urls_month': new_urls_month,
        'clicks_today': clicks_today,
        'clicks_week': clicks_week,
        'clicks_month': clicks_month,
        'top_users': top_users,
        'top_urls': top_urls,
        'top_countries': top_countries,
    }
    
    return render(request, 'analytics/admin_dashboard.html', context)

@login_required
def export_user_analytics(request):
    """Export all user analytics to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="my_analytics.csv"'
    
    import csv
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'URL', 'Short Code', 'Total Clicks', 'Unique Clicks', 
        'Created Date', 'Is Active', 'Expires At'
    ])
    
    # Write data
    urls = ShortenedURL.objects.filter(user=request.user).order_by('-created_at')
    for url in urls:
        writer.writerow([
            url.original_url,
            url.short_code,
            url.click_count,
            url.unique_clicks,
            url.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Yes' if url.is_active else 'No',
            url.expires_at.strftime('%Y-%m-%d %H:%M:%S') if url.expires_at else 'Never'
        ])
    
    return response

@user_passes_test(is_admin)
def export_system_analytics(request):
    """Export system-wide analytics to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="system_analytics.csv"'
    
    import csv
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'User Email', 'URL Count', 'Total Clicks', 'Join Date', 
        'Is Premium', 'Email Verified'
    ])
    
    # Write data
    users = User.objects.annotate(
        url_count=Count('urls'),
        total_clicks=Count('urls__clicks')
    ).order_by('-total_clicks')
    
    for user in users:
        writer.writerow([
            user.email,
            user.url_count,
            user.total_clicks,
            user.date_joined.strftime('%Y-%m-%d'),
            'Yes' if user.is_premium else 'No',
            'Yes' if user.is_email_verified else 'No'
        ])
    
    return response

# Utility functions
def get_daily_clicks(clicks_queryset, days):
    """Get daily click counts for the last N days"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Initialize data structure
    daily_data = {}
    current_date = start_date
    while current_date <= end_date:
        daily_data[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    # Get actual click counts
    daily_clicks = clicks_queryset.filter(
        clicked_at__date__gte=start_date
    ).extra(
        select={'day': 'date(clicked_at)'}
    ).values('day').annotate(
        count=Count('id')
    )
    
    # Update data structure with actual counts
    for item in daily_clicks:
        day_str = item['day'].strftime('%Y-%m-%d')
        if day_str in daily_data:
            daily_data[day_str] = item['count']
    
    # Convert to list format for charts
    return [{'date': date, 'clicks': count} for date, count in daily_data.items()]

def get_hourly_distribution(clicks_queryset):
    """Get hourly distribution of clicks"""
    hourly_data = {str(i): 0 for i in range(24)}
    
    hourly_clicks = clicks_queryset.extra(
        select={'hour': 'extract(hour from clicked_at)'}
    ).values('hour').annotate(
        count=Count('id')
    )
    
    for item in hourly_clicks:
        hour = str(int(item['hour']))
        hourly_data[hour] = item['count']
    
    return [{'hour': hour, 'clicks': count} for hour, count in hourly_data.items()]
