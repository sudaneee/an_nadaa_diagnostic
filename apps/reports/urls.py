from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('',                                    views.report_list,                name='list'),
    path('create/',                             views.report_create,              name='create'),
    path('<int:pk>/',                           views.report_detail,              name='detail'),
    path('<int:pk>/edit/',                      views.report_edit,                name='edit'),
    path('<int:pk>/print/',                     views.report_print,               name='print'),
    path('api/service-parameters/<int:service_id>/', views.get_service_parameters_api, name='api_parameters'),
    path('api/invoice-info/<int:invoice_id>/',  views.api_invoice_info,           name='api_invoice_info'),
]
