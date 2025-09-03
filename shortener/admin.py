from django.contrib import admin
from .models import ShortenedURL, Click, QRCode

@admin.register(ShortenedURL)
class ShortenedURLAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'original_url', 'user', 'click_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_public', 'created_at')
    search_fields = ('short_code', 'original_url', 'user__email')
    readonly_fields = ('short_code', 'click_count', 'unique_clicks', 'created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ('url', 'ip_address', 'browser', 'country', 'clicked_at')
    list_filter = ('browser', 'device', 'country', 'clicked_at')
    search_fields = ('url__short_code', 'ip_address', 'country')
    readonly_fields = ('clicked_at',)
    ordering = ('-clicked_at',)

@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('url', 'created_at')
    readonly_fields = ('created_at',)
