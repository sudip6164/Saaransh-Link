from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from shortener.models import Click, ShortenedURL

class AnalyticsProcessor:
    """Utility class for processing analytics data"""
    
    @staticmethod
    def get_click_trends(user=None, url=None, days=30):
        """Get click trends over time"""
        clicks = Click.objects.all()
        
        if user:
            clicks = clicks.filter(url__user=user)
        if url:
            clicks = clicks.filter(url=url)
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        return clicks.filter(
            clicked_at__date__gte=start_date
        ).extra(
            select={'day': 'date(clicked_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
    
    @staticmethod
    def get_geographic_distribution(user=None, url=None):
        """Get geographic distribution of clicks"""
        clicks = Click.objects.all()
        
        if user:
            clicks = clicks.filter(url__user=user)
        if url:
            clicks = clicks.filter(url=url)
        
        return clicks.exclude(
            country__in=['', 'Unknown']
        ).values('country').annotate(
            count=Count('country')
        ).order_by('-count')
    
    @staticmethod
    def get_technology_stats(user=None, url=None):
        """Get browser, device, and OS statistics"""
        clicks = Click.objects.all()
        
        if user:
            clicks = clicks.filter(url__user=user)
        if url:
            clicks = clicks.filter(url=url)
        
        browsers = clicks.exclude(
            browser__in=['', 'Unknown']
        ).values('browser').annotate(
            count=Count('browser')
        ).order_by('-count')[:10]
        
        devices = clicks.exclude(
            device__in=['', 'Unknown']
        ).values('device').annotate(
            count=Count('device')
        ).order_by('-count')[:10]
        
        operating_systems = clicks.exclude(
            os__in=['', 'Unknown']
        ).values('os').annotate(
            count=Count('os')
        ).order_by('-count')[:10]
        
        return {
            'browsers': browsers,
            'devices': devices,
            'operating_systems': operating_systems
        }
    
    @staticmethod
    def get_referrer_stats(user=None, url=None):
        """Get referrer statistics"""
        clicks = Click.objects.all()
        
        if user:
            clicks = clicks.filter(url__user=user)
        if url:
            clicks = clicks.filter(url=url)
        
        # Group similar referrers
        referrers = clicks.exclude(
            Q(referrer__isnull=True) | Q(referrer__exact='')
        ).values('referrer').annotate(
            count=Count('referrer')
        ).order_by('-count')[:20]
        
        # Process referrers to extract domains
        processed_referrers = {}
        for ref in referrers:
            try:
                from urllib.parse import urlparse
                domain = urlparse(ref['referrer']).netloc
                if domain:
                    if domain in processed_referrers:
                        processed_referrers[domain] += ref['count']
                    else:
                        processed_referrers[domain] = ref['count']
            except:
                continue
        
        return sorted(
            [{'domain': k, 'count': v} for k, v in processed_referrers.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
    
    @staticmethod
    def get_performance_metrics(user=None):
        """Get performance metrics for URLs"""
        urls = ShortenedURL.objects.all()
        
        if user:
            urls = urls.filter(user=user)
        
        # Calculate metrics
        total_urls = urls.count()
        active_urls = urls.filter(is_active=True).count()
        total_clicks = sum(url.click_count for url in urls)
        
        if total_urls > 0:
            avg_clicks_per_url = total_clicks / total_urls
            click_through_rate = (urls.filter(click_count__gt=0).count() / total_urls) * 100
        else:
            avg_clicks_per_url = 0
            click_through_rate = 0
        
        return {
            'total_urls': total_urls,
            'active_urls': active_urls,
            'total_clicks': total_clicks,
            'avg_clicks_per_url': round(avg_clicks_per_url, 2),
            'click_through_rate': round(click_through_rate, 2)
        }

def generate_analytics_report(user, start_date=None, end_date=None):
    """Generate comprehensive analytics report for a user"""
    if not start_date:
        start_date = timezone.now().date() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now().date()
    
    processor = AnalyticsProcessor()
    
    # Get basic metrics
    performance = processor.get_performance_metrics(user=user)
    
    # Get trends
    trends = processor.get_click_trends(user=user, days=30)
    
    # Get geographic data
    geographic = processor.get_geographic_distribution(user=user)
    
    # Get technology stats
    technology = processor.get_technology_stats(user=user)
    
    # Get referrer stats
    referrers = processor.get_referrer_stats(user=user)
    
    return {
        'performance': performance,
        'trends': list(trends),
        'geographic': list(geographic),
        'technology': technology,
        'referrers': referrers,
        'generated_at': timezone.now(),
        'period': {
            'start': start_date,
            'end': end_date
        }
    }
