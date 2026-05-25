from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator

from apps.services.models import Service, ServiceCategory
from .models import Invoice, InvoiceItem, Payment, Referral
from .forms import InvoiceCreateForm
from .filters import InvoiceFilter
from .utils import generate_invoice_qr


# ── Permission helpers ─────────────────────────────────────────────────────────

def is_cashier_or_admin(user):
    return user.is_authenticated and user.role in ('ADMIN', 'CASHIER')


# ── Invoice list ───────────────────────────────────────────────────────────────

@login_required
def invoice_list(request):
    """
    Admin: all invoices + comprehensive filter panel.
    Cashier: only their own invoices + simpler filters.
    """
    if request.user.is_admin:
        base_qs = Invoice.objects.select_related(
            'created_by', 'referral'
        ).prefetch_related('items__service', 'payments')
    else:
        # Cashier sees only their own invoices
        base_qs = Invoice.objects.filter(
            created_by=request.user
        ).select_related('created_by', 'referral').prefetch_related('items__service', 'payments')

    f = InvoiceFilter(request.GET, queryset=base_qs)
    filtered_qs = f.qs

    # Aggregate totals across the filtered set (before pagination)
    totals = filtered_qs.aggregate(
        grand_total=Sum('total_amount'),
        cash_total=Sum('amount_paid', filter=Q(payment_method='CASH')),
        transfer_total=Sum('amount_paid', filter=Q(payment_method='TRANSFER')),
        card_total=Sum('amount_paid', filter=Q(payment_method='CARD')),
        count=Count('id'),
    )

    paginator = Paginator(filtered_qs, 25)
    page = request.GET.get('page')
    invoices = paginator.get_page(page)

    return render(request, 'invoices/list.html', {
        'invoices': invoices,
        'filter': f,
        'totals': totals,
        'is_admin': request.user.is_admin,
    })


# ── Invoice create ─────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_cashier_or_admin)
def invoice_create(request):
    """
    Single-step invoice creation:
    1. Patient info entered inline
    2. Examinations selected
    3. Payment processed immediately
    All created atomically — no separate payment step.
    """
    # Build grouped service list for the template
    categories = (
        ServiceCategory.objects
        .prefetch_related('services')
        .filter(services__is_active=True)
        .distinct()
        .order_by('name')
    )
    referrals = Referral.objects.filter(is_active=True).order_by('category', 'name')

    if request.method == 'POST':
        form = InvoiceCreateForm(request.POST)

        service_ids = request.POST.getlist('service[]')
        quantities = request.POST.getlist('quantity[]')

        # Pre-validate: at least one examination must be selected
        valid_items = [(sid, qty) for sid, qty in zip(service_ids, quantities)
                       if sid.strip() and qty.strip()]
        if not valid_items:
            messages.error(request, 'Please add at least one examination.')
            return render(request, 'invoices/create.html', {
                'form': form,
                'categories': categories,
                'referrals': referrals,
            })

        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    # 1. Create the invoice shell (generates invoice_number)
                    invoice = Invoice(
                        surname=cd['surname'],
                        first_name=cd['first_name'],
                        other_names=cd.get('other_names', ''),
                        age=cd['age'],
                        sex=cd['sex'],
                        phone_number=cd['phone_number'],
                        referral=cd.get('referral'),
                        discount=cd.get('discount') or 0,
                        payment_method=cd['payment_method'],
                        reference_number=cd.get('reference_number', '') or '',
                        notes=cd.get('notes', '') or '',
                        status='PAID',
                        created_by=request.user,
                    )
                    invoice.save()

                    # 2. Create invoice items
                    for service_id, qty in valid_items:
                        try:
                            service = Service.objects.get(id=int(service_id))
                            InvoiceItem.objects.create(
                                invoice=invoice,
                                service=service,
                                quantity=max(int(qty), 1),
                                unit_price=service.price,
                            )
                        except (Service.DoesNotExist, ValueError):
                            continue

                    # 3. Compute and persist total
                    subtotal = sum(i.total_price for i in invoice.items.all())
                    total = max(subtotal - invoice.discount, 0)
                    Invoice.objects.filter(pk=invoice.pk).update(
                        total_amount=total,
                        amount_paid=total,
                    )
                    invoice.refresh_from_db()

                    # 4. Record payment
                    Payment.objects.create(
                        invoice=invoice,
                        amount=invoice.total_amount,
                        payment_method=cd['payment_method'],
                        reference_number=cd.get('reference_number', '') or '',
                        received_by=request.user,
                    )

                    # 5. Generate QR code (non-blocking)
                    try:
                        qr_path = generate_invoice_qr(invoice)
                        Invoice.objects.filter(pk=invoice.pk).update(qr_code=qr_path)
                        invoice.refresh_from_db()
                    except Exception:
                        pass

            except Exception as exc:
                messages.error(request, f'Error creating invoice: {exc}')
                return render(request, 'invoices/create.html', {
                    'form': form,
                    'categories': categories,
                    'referrals': referrals,
                })

            messages.success(
                request,
                f'Invoice {invoice.invoice_number} created. '
                f'₦{invoice.total_amount:,.2f} received via '
                f'{invoice.get_payment_method_display()}.'
            )
            return redirect('invoices:receipt', pk=invoice.pk)

        # Form invalid — re-render with errors
        return render(request, 'invoices/create.html', {
            'form': form,
            'categories': categories,
            'referrals': referrals,
        })

    # GET
    form = InvoiceCreateForm()
    return render(request, 'invoices/create.html', {
        'form': form,
        'categories': categories,
        'referrals': referrals,
    })


# ── Invoice detail ─────────────────────────────────────────────────────────────

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('created_by', 'referral')
                       .prefetch_related('items__service', 'payments__received_by'),
        pk=pk
    )

    # Cashiers can only view their own invoices
    if request.user.is_cashier and invoice.created_by != request.user:
        messages.error(request, 'You can only view your own invoices.')
        return redirect('invoices:list')

    return render(request, 'invoices/detail.html', {'invoice': invoice})


# ── Receipt (printable) ────────────────────────────────────────────────────────

@login_required
def invoice_receipt(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('created_by', 'referral')
                       .prefetch_related('items__service', 'payments__received_by'),
        pk=pk
    )

    # Cashiers can only print their own invoices
    if request.user.is_cashier and invoice.created_by != request.user:
        messages.error(request, 'You can only print your own receipts.')
        return redirect('invoices:list')

    payment = invoice.payments.first()

    return render(request, 'invoices/receipt.html', {
        'invoice': invoice,
        'payment': payment,
        'centre_name': 'An-Nadaa Diagnostic Centre',
        'centre_address': '123 Medical Road, Abuja',
        'centre_phone': '+234 800 123 4567',
    })


# ── AJAX: service details ──────────────────────────────────────────────────────

@login_required
def api_service_details(request):
    """Return price and meta for a single service (used by JS when adding rows)."""
    service_id = request.GET.get('service_id')
    try:
        service = Service.objects.get(id=service_id, is_active=True)
        return JsonResponse({
            'id': service.id,
            'name': service.name,
            'price': str(service.price),
            'requires_report': service.requires_report,
        })
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)


# ── AJAX: referral search ──────────────────────────────────────────────────────

@login_required
def api_referral_search(request):
    """Search referrals for Select2 AJAX (returns JSON list)."""
    q = request.GET.get('q', '').strip()
    referrals = Referral.objects.filter(is_active=True)
    if q:
        referrals = referrals.filter(name__icontains=q)
    data = [
        {'id': r.id, 'text': str(r)}
        for r in referrals.order_by('category', 'name')[:50]
    ]
    return JsonResponse({'results': data})
