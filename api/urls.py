from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('auth/token/', views.CustomAuthToken.as_view(), name='api_token_auth'),
    
    # URL management
    path('urls/', views.ShortenedURLListCreateView.as_view(), name='api_url_list_create'),
    path('urls/<int:pk>/', views.ShortenedURLDetailView.as_view(), name='api_url_detail'),
    path('urls/<int:pk>/analytics/', views.url_analytics_view, name='api_url_analytics'),
    path('urls/<int:pk>/clicks/', views.url_clicks_view, name='api_url_clicks'),
    path('urls/<int:pk>/qr/', views.url_qr_code_view, name='api_url_qr'),
    path('urls/<int:pk>/toggle/', views.toggle_url_status_view, name='api_url_toggle'),
    
    # Bulk operations
    path('urls/bulk-create/', views.bulk_create_urls_view, name='api_bulk_create_urls'),
    path('urls/bulk-delete/', views.bulk_delete_urls_view, name='api_bulk_delete_urls'),
    
    # User data
    path('user/stats/', views.user_stats_view, name='api_user_stats'),
    path('user/profile/', views.user_profile_view, name='api_user_profile'),
    
    # Public endpoints
    path('public/<str:short_code>/', views.public_url_info_view, name='api_public_url_info'),
]
