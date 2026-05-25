from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse

from apps.accounts.models import CentreProfile
from apps.invoices.models import Invoice, InvoiceItem
from apps.services.models import Service
from .models import Report, ReportParameter
from .forms import ReportForm


# ── Permission helpers ─────────────────────────────────────────────────────────

def is_lab_tech(user):
    return user.is_authenticated and user.role in ('LAB_TECH', 'ADMIN')


# ── Report list ────────────────────────────────────────────────────────────────

@login_required
def report_list(request):
    query      = request.GET.get('q', '')
    service_id = request.GET.get('service', '')

    if request.user.is_lab_tech:
        reports = Report.objects.filter(created_by=request.user)
    else:
        # Admin, Doctor, Cashier all see everything
        reports = Report.objects.all()

    if query:
        reports = reports.filter(
            Q(report_number__icontains=query)
            | Q(invoice__surname__icontains=query)
            | Q(invoice__first_name__icontains=query)
            | Q(invoice__phone_number__icontains=query)
            | Q(service__name__icontains=query)
            | Q(signatory__icontains=query)
        )

    if service_id:
        reports = reports.filter(service__id=service_id)

    reports = reports.select_related('invoice', 'service', 'created_by')

    paginator = Paginator(reports, 25)
    reports   = paginator.get_page(request.GET.get('page'))

    services = Service.objects.filter(requires_report=True)

    return render(request, 'reports/list.html', {
        'reports':          reports,
        'services':         services,
        'query':            query,
        'selected_service': service_id,
    })


# ── Report create ──────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_lab_tech)
def report_create(request):
    if request.method == 'POST':
        service_id      = request.POST.get('service')
        invoice_id      = request.POST.get('invoice')
        invoice_item_id = request.POST.get('invoice_item')

        if not service_id or not invoice_id:
            messages.error(request, 'Please select both an invoice and a service.')
            return redirect('reports:create')

        service = get_object_or_404(Service, id=service_id)
        invoice = get_object_or_404(Invoice, id=invoice_id)

        # Build report
        report = Report(
            invoice    = invoice,
            service    = service,
            created_by = request.user,
            signatory  = request.POST.get('signatory', '').strip(),
            clinical_notes = request.POST.get('clinical_notes', '').strip(),
            lab_notes      = request.POST.get('lab_notes', '').strip(),
        )
        report.save()

        # Link invoice item if provided
        if invoice_item_id:
            try:
                item = InvoiceItem.objects.get(id=invoice_item_id, invoice=invoice)
                report.invoice_item = item
                report.save(update_fields=['invoice_item'])
            except InvoiceItem.DoesNotExist:
                pass

        # Save parameter values
        params = {
            key.replace('param_', ''): value
            for key, value in request.POST.items()
            if key.startswith('param_')
        }
        if params:
            report.parameters = params
            report.save(update_fields=['parameters'])

        messages.success(request, f'Report {report.report_number} created successfully.')
        return redirect('reports:detail', pk=report.pk)

    # GET — build context
    # Invoice items that need reports (not yet reported)
    pending_items = (
        InvoiceItem.objects
        .filter(service__requires_report=True, invoice__status='PAID')
        .exclude(reports__isnull=False)
        .select_related('invoice', 'service')
        .order_by('-invoice__created_at')
    )

    # All paid invoices for manual lookup
    invoices = Invoice.objects.filter(status='PAID').order_by('-created_at')[:300]

    return render(request, 'reports/create.html', {
        'pending_items': pending_items,
        'invoices':      invoices,
    })


# ── Report detail ──────────────────────────────────────────────────────────────

@login_required
def report_detail(request, pk):
    report = get_object_or_404(
        Report.objects.select_related('invoice', 'service', 'created_by'),
        pk=pk,
    )

    # Lab techs can only view their own reports
    if request.user.is_lab_tech and report.created_by != request.user:
        messages.error(request, 'You can only view your own reports.')
        return redirect('reports:list')

    parameters = ReportParameter.objects.filter(service=report.service)
    param_list = [
        {
            'name':         p.name,
            'value':        report.parameters.get(str(p.id), ''),
            'unit':         p.unit,
            'normal_range': p.normal_range,
            'type':         p.parameter_type,
        }
        for p in parameters
    ]

    can_edit = request.user.is_lab_tech and report.created_by == request.user

    return render(request, 'reports/detail.html', {
        'report':    report,
        'parameters': param_list,
        'can_edit':  can_edit,
    })


# ── Report edit ────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_lab_tech)
def report_edit(request, pk):
    report = get_object_or_404(Report, pk=pk)

    if report.created_by != request.user:
        messages.error(request, 'You can only edit your own reports.')
        return redirect('reports:list')

    parameters = ReportParameter.objects.filter(service=report.service)

    # Build param_list for template rendering (avoids dict subscript in template)
    param_list = [
        {
            'id':           p.id,
            'name':         p.name,
            'type':         p.parameter_type,
            'unit':         p.unit,
            'normal_range': p.normal_range,
            'options':      p.options,
            'required':     p.required,
            'value':        report.parameters.get(str(p.id), ''),
        }
        for p in parameters
    ]

    if request.method == 'POST':
        # Extract parameter values
        new_params = {}
        for p in parameters:
            key = f'param_{p.id}'
            if p.parameter_type == 'checkbox':
                new_params[str(p.id)] = 'Yes' if key in request.POST else ''
            elif key in request.POST:
                new_params[str(p.id)] = request.POST[key]

        report.parameters     = new_params
        report.signatory      = request.POST.get('signatory', '').strip()
        report.clinical_notes = request.POST.get('clinical_notes', '').strip()
        report.lab_notes      = request.POST.get('lab_notes', '').strip()
        report.save()

        messages.success(request, f'Report {report.report_number} updated.')
        return redirect('reports:detail', pk=report.pk)

    return render(request, 'reports/edit.html', {
        'report':     report,
        'param_list': param_list,
    })


# ── Print report ───────────────────────────────────────────────────────────────

@login_required
def report_print(request, pk):
    report = get_object_or_404(Report, pk=pk)

    parameters = ReportParameter.objects.filter(service=report.service)
    param_list = [
        {
            'name':         p.name,
            'value':        report.parameters.get(str(p.id), ''),
            'unit':         p.unit,
            'normal_range': p.normal_range,
        }
        for p in parameters
    ]

    centre = CentreProfile.get_profile()

    return render(request, 'reports/print.html', {
        'report':     report,
        'parameters': param_list,
        'centre':     centre,
    })


# ── AJAX: service parameters ───────────────────────────────────────────────────

@login_required
def get_service_parameters_api(request, service_id):
    try:
        params = ReportParameter.objects.filter(service_id=service_id)
        data   = [
            {
                'id':           p.id,
                'name':         p.name,
                'type':         p.parameter_type,
                'unit':         p.unit,
                'normal_range': p.normal_range,
                'options':      p.options,
                'required':     p.required,
            }
            for p in params
        ]
        return JsonResponse({'parameters': data})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=400)


# ── AJAX: invoice info ─────────────────────────────────────────────────────────

@login_required
def api_invoice_info(request, invoice_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id, status='PAID')
        items   = [
            {
                'id':           item.id,
                'service_id':   item.service_id,
                'service_name': item.service.name,
                'has_report':   item.reports.exists(),
            }
            for item in invoice.items.filter(service__requires_report=True)
        ]
        return JsonResponse({
            'client_name':     invoice.full_name,
            'age':             invoice.age,
            'sex':             invoice.get_sex_display(),
            'phone':           invoice.phone_number,
            'invoice_number':  invoice.invoice_number,
            'invoice_date':    invoice.created_at.strftime('%d/%m/%Y'),
            'items':           items,
        })
    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
