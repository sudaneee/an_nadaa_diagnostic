from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Client
from .forms import ClientForm

@login_required
def client_list(request):
    query = request.GET.get('q', '')
    clients = Client.objects.all()
    
    if query:
        clients = clients.filter(
            Q(full_name__icontains=query) | 
            Q(phone_number__icontains=query)
        )
    
    paginator = Paginator(clients, 20)
    page = request.GET.get('page')
    clients = paginator.get_page(page)
    
    return render(request, 'clients/list.html', {
        'clients': clients,
        'query': query
    })

@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()
            messages.success(request, f'Client {client.full_name} created successfully!')
            return redirect('clients:list')
    else:
        form = ClientForm()
    
    return render(request, 'clients/form.html', {
        'form': form,
        'title': 'Add New Client'
    })

@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client {client.full_name} updated successfully!')
            return redirect('clients:list')
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'clients/form.html', {
        'form': form,
        'title': 'Edit Client',
        'client': client
    })

@login_required
def client_history(request, pk):
    client = get_object_or_404(Client, pk=pk)
    from apps.invoices.models import Invoice
    invoices = Invoice.objects.filter(client=client).order_by('-created_at')
    
    return render(request, 'clients/history.html', {
        'client': client,
        'invoices': invoices
    })

@login_required
def client_search_api(request):
    """API endpoint for searching clients (for AJAX)"""
    from django.http import JsonResponse
    query = request.GET.get('q', '')
    clients = Client.objects.filter(
        Q(full_name__icontains=query) | 
        Q(phone_number__icontains=query)
    )[:10]
    
    data = [{
        'id': c.id,
        'full_name': c.full_name,
        'phone_number': c.phone_number
    } for c in clients]
    
    return JsonResponse(data, safe=False)