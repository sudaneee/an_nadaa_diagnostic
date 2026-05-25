from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
import json
from .models import Service, ServiceCategory
from .forms import ServiceForm, ServiceCategoryForm

def is_admin_or_manager(user):
    return user.is_authenticated and (user.role == 'ADMIN' or user.role == 'DOCTOR')

@login_required
def service_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    services = Service.objects.all()
    
    if query:
        services = services.filter(
            Q(name__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    if category:
        services = services.filter(category__id=category)
    
    categories = ServiceCategory.objects.all()
    paginator = Paginator(services, 20)
    page = request.GET.get('page')
    services = paginator.get_page(page)
    
    return render(request, 'services/list.html', {
        'services': services,
        'categories': categories,
        'query': query,
        'selected_category': category
    })

@login_required
@user_passes_test(is_admin_or_manager)
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'Service {service.name} created successfully!')
            return redirect('services:list')
    else:
        form = ServiceForm()
    
    return render(request, 'services/form.html', {
        'form': form,
        'title': 'Add New Service'
    })

@login_required
@user_passes_test(is_admin_or_manager)
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f'Service {service.name} updated successfully!')
            return redirect('services:list')
    else:
        # Format JSON for display
        initial_data = {
            'report_template': json.dumps(service.report_template, indent=2) if service.report_template else ''
        }
        form = ServiceForm(instance=service, initial=initial_data)
    
    return render(request, 'services/form.html', {
        'form': form,
        'title': 'Edit Service',
        'service': service
    })

@login_required
@user_passes_test(is_admin_or_manager)
def service_toggle(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.is_active = not service.is_active
    service.save()
    status = 'activated' if service.is_active else 'deactivated'
    messages.success(request, f'Service {service.name} has been {status}.')
    return redirect('services:list')

@login_required
def category_list(request):
    categories = ServiceCategory.objects.all()
    return render(request, 'services/categories.html', {'categories': categories})

@login_required
@user_passes_test(is_admin_or_manager)
def category_create(request):
    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('services:categories')
    else:
        form = ServiceCategoryForm()
    
    return render(request, 'services/category_form.html', {
        'form': form,
        'title': 'Add Category'
    })