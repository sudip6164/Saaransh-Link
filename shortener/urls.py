from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('url/<int:pk>/', views.url_detail_view, name='url_detail'),
    path('url/<int:pk>/edit/', views.url_edit_view, name='url_edit'),
    path('url/<int:pk>/delete/', views.url_delete_view, name='url_delete'),
    path('url/<int:pk>/qr/', views.qr_code_view, name='url_qr'),
    path('url/<int:pk>/export/', views.export_analytics_view, name='export_analytics'),
]
