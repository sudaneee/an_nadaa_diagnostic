from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='list'),
    path('create/', views.client_create, name='create'),
    path('<int:pk>/edit/', views.client_edit, name='edit'),
    path('<int:pk>/history/', views.client_history, name='history'),
    path('api/search/', views.client_search_api, name='api_search'),
]