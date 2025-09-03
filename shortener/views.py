from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from .models import ShortenedURL, Click, QRCode
from .forms import URLShortenForm, URLEditForm
from .utils import generate_qr_code, get_client_info, get_location_info
import json

@login_required
@ratelimit(key='user', rate='20/d', method='POST')
def dashboard_view(request):
    # Check rate limit for free users
    if not request.user.is_premium and getattr(request, 'limited', False):
        messages.error(request, f'You have reached your daily limit of {request.user.daily_url_limit} URLs. Upgrade to premium for unlimited access.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = URLShortenForm(request.POST)
        if form.is_valid():
            url = form.save(commit=False)
            url.user = request.user
            
            # Use custom alias if provided
            if form.cleaned_data.get('custom_alias'):
                url.short_code = form.cleaned_data['custom_alias']
            
            url.save()
            
            # Generate QR code
            generate_qr_code(url)
            
            messages.success(request, f'URL shortened successfully! Your short URL: {url.short_url}')
            return redirect('dashboard')
    else:
        form = URLShortenForm()
    
    # Get user's URLs with pagination
    urls = ShortenedURL.objects.filter(user=request.user).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        urls = urls.filter(
            Q(original_url__icontains=search_query) |
            Q(short_code__icontains=search_query)
        )
    
    # Filter functionality
    filter_type = request.GET.get('filter')
    if filter_type == 'active':
        urls = urls.filter(is_active=True)
    elif filter_type == 'inactive':
        urls = urls.filter(is_active=False)
    elif filter_type == 'expired':
        urls = urls.filter(expires_at__lt=timezone.now())
    
    paginator = Paginator(urls, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_urls = ShortenedURL.objects.filter(user=request.user).count()
    total_clicks = Click.objects.filter(url__user=request.user).count()
    active_urls = ShortenedURL.objects.filter(user=request.user, is_active=True).count()
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_type': filter_type,
        'total_urls': total_urls,
        'total_clicks': total_clicks,
        'active_urls': active_urls,
    }
    
    return render(request, 'shortener/dashboard.html', context)

@login_required
def url_detail_view(request, pk):
    url = get_object_or_404(ShortenedURL, pk=pk, user=request.user)
    
    # Get recent clicks
    recent_clicks = Click.objects.filter(url=url).order_by('-clicked_at')[:10]
    
    # Get click statistics
    click_stats = {
        'total_clicks': url.click_count,
        'unique_clicks': url.unique_clicks,
        'today_clicks': Click.objects.filter(
            url=url,
            clicked_at__date=timezone.now().date()
        ).count(),
        'this_week_clicks': Click.objects.filter(
            url=url,
            clicked_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
    }
    
    # Browser statistics
    browser_stats = Click.objects.filter(url=url).values('browser').annotate(
        count=Count('browser')
    ).order_by('-count')[:5]
    
    # Country statistics
    country_stats = Click.objects.filter(url=url).values('country').annotate(
        count=Count('country')
    ).order_by('-count')[:5]
    
    context = {
        'url': url,
        'recent_clicks': recent_clicks,
        'click_stats': click_stats,
        'browser_stats': browser_stats,
        'country_stats': country_stats,
    }
    
    return render(request, 'shortener/url_detail.html', context)

@login_required
def url_edit_view(request, pk):
    url = get_object_or_404(ShortenedURL, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = URLEditForm(request.POST, instance=url)
        if form.is_valid():
            form.save()
            messages.success(request, 'URL updated successfully!')
            return redirect('url_detail', pk=url.pk)
    else:
        form = URLEditForm(instance=url)
    
    return render(request, 'shortener/url_edit.html', {'form': form, 'url': url})

@login_required
def url_delete_view(request, pk):
    url = get_object_or_404(ShortenedURL, pk=pk, user=request.user)
    
    if request.method == 'POST':
        url.delete()
        messages.success(request, 'URL deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'shortener/url_delete.html', {'url': url})

def redirect_view(request, short_code):
    try:
        url = ShortenedURL.objects.get(short_code=short_code)
    except ShortenedURL.DoesNotExist:
        return render(request, 'errors/404.html', {'message': 'Short URL not found'}, status=404)
    
    # Check if URL is active
    if not url.is_active:
        return render(request, 'errors/410.html', {'message': 'This link has been disabled'}, status=410)
    
    # Check if URL is expired
    if url.is_expired:
        return render(request, 'errors/410.html', {'message': 'This link has expired'}, status=410)
    
    # Track the click
    client_info = get_client_info(request)
    location_info = get_location_info(client_info['ip_address'])
    
    # Check if this is a unique click (same IP within 24 hours)
    is_unique = not Click.objects.filter(
        url=url,
        ip_address=client_info['ip_address'],
        clicked_at__gte=timezone.now() - timezone.timedelta(hours=24)
    ).exists()
    
    # Create click record
    Click.objects.create(
        url=url,
        ip_address=client_info['ip_address'],
        user_agent=client_info['user_agent'],
        referrer=client_info['referrer'],
        browser=client_info['browser'],
        device=client_info['device'],
        os=client_info['os'],
        country=location_info.get('country', ''),
        city=location_info.get('city', ''),
    )
    
    # Update click counts
    url.click_count += 1
    if is_unique:
        url.unique_clicks += 1
    url.save()
    
    return redirect(url.original_url)

@login_required
def qr_code_view(request, pk):
    url = get_object_or_404(ShortenedURL, pk=pk, user=request.user)
    
    try:
        qr_code = url.qr_code
    except QRCode.DoesNotExist:
        # Generate QR code if it doesn't exist
        qr_code = generate_qr_code(url)
    
    with open(qr_code.image.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="{url.short_code}_qr.png"'
        return response

@login_required
def export_analytics_view(request, pk):
    url = get_object_or_404(ShortenedURL, pk=pk, user=request.user)
    
    # Get all clicks for this URL
    clicks = Click.objects.filter(url=url).order_by('-clicked_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{url.short_code}_analytics.csv"'
    
    import csv
    writer = csv.writer(response)
    writer.writerow(['Date', 'IP Address', 'Browser', 'Device', 'OS', 'Country', 'City', 'Referrer'])
    
    for click in clicks:
        writer.writerow([
            click.clicked_at.strftime('%Y-%m-%d %H:%M:%S'),
            click.ip_address,
            click.browser,
            click.device,
            click.os,
            click.country,
            click.city,
            click.referrer or 'Direct'
        ])
    
    return response

@require_http_methods(["GET"])
def url_preview_view(request, short_code):
    """Preview page showing URL info before redirect"""
    try:
        url = ShortenedURL.objects.get(short_code=short_code)
    except ShortenedURL.DoesNotExist:
        raise Http404("Short URL not found")
    
    if not url.is_active or url.is_expired:
        raise Http404("Short URL not available")
    
    context = {
        'url': url,
        'short_url': request.build_absolute_uri(f'/{short_code}/'),
    }
    
    return render(request, 'shortener/url_preview.html', context)
