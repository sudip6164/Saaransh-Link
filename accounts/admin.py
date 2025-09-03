from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, EmailVerification

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_email_verified', 'is_premium', 'created_at')
    list_filter = ('is_email_verified', 'is_premium', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('is_email_verified', 'is_premium', 'daily_url_limit')
        }),
    )

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')
