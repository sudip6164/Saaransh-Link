from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('url/<int:pk>/', views.url_analytics_detail, name='url_analytics_detail'),
    path('api/', views.analytics_api, name='analytics_api'),
    path('admin/', views.admin_analytics, name='admin_analytics'),
    path('export/', views.export_user_analytics, name='export_user_analytics'),
    path('export/system/', views.export_system_analytics, name='export_system_analytics'),
]
