from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('', views.invoice_list, name='list'),
    path('create/', views.invoice_create, name='create'),
    path('<int:pk>/', views.invoice_detail, name='detail'),
    path('<int:pk>/receipt/', views.invoice_receipt, name='receipt'),

    # AJAX endpoints
    path('api/service-details/', views.api_service_details, name='api_service_details'),
    path('api/referral-search/', views.api_referral_search, name='api_referral_search'),
]
