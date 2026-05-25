from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_list, name='list'),
    path('create/', views.service_create, name='create'),
    path('<int:pk>/edit/', views.service_edit, name='edit'),
    path('<int:pk>/toggle/', views.service_toggle, name='toggle'),
    path('categories/', views.category_list, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
]