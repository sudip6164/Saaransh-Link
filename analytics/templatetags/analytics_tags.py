from django import template
from django.db.models import Count
from shortener.models import Click
from datetime import timedelta
from django.utils import timezone

register = template.Library()

@register.simple_tag
def get_click_percentage(url, total_clicks):
    """Calculate percentage of clicks for a URL"""
    if total_clicks == 0:
        return 0
    return round((url.click_count / total_clicks) * 100, 1)

@register.simple_tag
def get_growth_rate(current, previous):
    """Calculate growth rate between two values"""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)

@register.simple_tag
def get_recent_clicks(url, days=7):
    """Get recent clicks for a URL"""
    start_date = timezone.now() - timedelta(days=days)
    return Click.objects.filter(
        url=url,
        clicked_at__gte=start_date
    ).count()

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    if total == 0:
        return 0
    return round((value / total) * 100, 1)

@register.inclusion_tag('analytics/widgets/chart_widget.html')
def render_chart(chart_type, data, title="Chart"):
    """Render a chart widget"""
    return {
        'chart_type': chart_type,
        'data': data,
        'title': title
    }

@register.inclusion_tag('analytics/widgets/stat_card.html')
def stat_card(title, value, subtitle="", icon="", color="blue"):
    """Render a statistics card"""
    return {
        'title': title,
        'value': value,
        'subtitle': subtitle,
        'icon': icon,
        'color': color
    }
