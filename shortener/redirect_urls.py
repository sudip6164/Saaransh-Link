from django.urls import path
from . import views

urlpatterns = [
    path('', views.redirect_view, name='redirect'),
    path('preview/', views.url_preview_view, name='url_preview'),
]
