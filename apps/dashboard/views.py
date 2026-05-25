from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone

from apps.invoices.models import Invoice, Payment
from apps.reports.models import Report
from apps.accounts.models import User


@login_required
def home(request):
    today = timezone.localdate()
    ctx   = {'today': today}

    # ── Admin dashboard ────────────────────────────────────────────────────────
    if request.user.is_admin:
        today_invoices = Invoice.objects.filter(created_at__date=today, status='PAID')
        today_payments = Payment.objects.filter(payment_date__date=today)

        today_rev  = today_payments.aggregate(t=Sum('amount'))['t'] or 0
        today_cash = today_payments.filter(payment_method='CASH').aggregate(t=Sum('amount'))['t'] or 0
        today_xfer = today_payments.filter(payment_method='TRANSFER').aggregate(t=Sum('amount'))['t'] or 0
        today_card = today_payments.filter(payment_method='CARD').aggregate(t=Sum('amount'))['t'] or 0

        ctx.update({
            'today_count':    today_invoices.count(),
            'today_revenue':  today_rev,
            'today_cash':     today_cash,
            'today_transfer': today_xfer,
            'today_card':     today_card,
            'reports_today':  Report.objects.filter(created_at__date=today).count(),
        })

        # Per-cashier breakdown for today
        cashier_stats = (
            Invoice.objects
            .filter(created_at__date=today, status='PAID')
            .values(
                'created_by__id',
                'created_by__first_name',
                'created_by__last_name',
                'created_by__username',
            )
            .annotate(
                invoice_count=Count('id'),
                total=Sum('total_amount'),
                cash=Sum('total_amount',     filter=Q(payment_method='CASH')),
                transfer=Sum('total_amount', filter=Q(payment_method='TRANSFER')),
                card=Sum('total_amount',     filter=Q(payment_method='CARD')),
            )
            .order_by('-total')
        )
        ctx['cashier_stats'] = list(cashier_stats)

        # Top 5 examinations today
        from apps.invoices.models import InvoiceItem
        ctx['top_services'] = (
            InvoiceItem.objects
            .filter(invoice__created_at__date=today, invoice__status='PAID')
            .values('service__name')
            .annotate(count=Count('id'), revenue=Sum('total_price'))
            .order_by('-count')[:5]
        )

        ctx['recent_invoices'] = (
            Invoice.objects
            .select_related('created_by', 'referral')
            .prefetch_related('items__service')
            .filter(status='PAID')
            .order_by('-created_at')[:10]
        )

    # ── Cashier dashboard ──────────────────────────────────────────────────────
    elif request.user.is_cashier:
        my_today_invoices = Invoice.objects.filter(
            created_by=request.user,
            created_at__date=today,
            status='PAID',
        )
        my_payments_today = Payment.objects.filter(
            received_by=request.user,
            payment_date__date=today,
        )

        my_rev   = my_payments_today.aggregate(t=Sum('amount'))['t'] or 0
        my_cash  = my_payments_today.filter(payment_method='CASH').aggregate(t=Sum('amount'))['t'] or 0
        my_xfer  = my_payments_today.filter(payment_method='TRANSFER').aggregate(t=Sum('amount'))['t'] or 0
        my_card  = my_payments_today.filter(payment_method='CARD').aggregate(t=Sum('amount'))['t'] or 0

        ctx.update({
            'today_count':    my_today_invoices.count(),
            'today_revenue':  my_rev,
            'today_cash':     my_cash,
            'today_transfer': my_xfer,
            'today_card':     my_card,
            'recent_invoices': (
                Invoice.objects
                .filter(created_by=request.user)
                .select_related('referral')
                .prefetch_related('items__service')
                .order_by('-created_at')[:10]
            ),
        })

    # ── Doctor dashboard ───────────────────────────────────────────────────────
    elif request.user.is_doctor:
        ctx.update({
            'total_reports':  Report.objects.count(),
            'reports_today':  Report.objects.filter(created_at__date=today).count(),
            'recent_reports': (
                Report.objects
                .select_related('invoice', 'service', 'created_by')
                .order_by('-created_at')[:10]
            ),
        })

    # ── Lab tech dashboard ─────────────────────────────────────────────────────
    elif request.user.is_lab_tech:
        ctx.update({
            'my_reports_today': Report.objects.filter(
                created_by=request.user, created_at__date=today
            ).count(),
            'my_reports_total': Report.objects.filter(created_by=request.user).count(),
            'recent_reports': (
                Report.objects
                .filter(created_by=request.user)
                .select_related('invoice', 'service')
                .order_by('-created_at')[:10]
            ),
        })

    return render(request, 'dashboard/home.html', ctx)
