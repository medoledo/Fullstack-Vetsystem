import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from django.utils import timezone

from vetlogin.decorators import (
    doctor_or_clinic_owner_required, clinic_owner_required,
    is_siteowner, is_clinic_owner, is_doctor, is_petshop
)
from .models import Invoice, InvoiceItem
from inventory.models import InventoryItem


@doctor_or_clinic_owner_required
def create_invoice(request):
    """Create a new invoice with line items. Deducts from inventory automatically."""
    clinic = request.clinic
    if not clinic:
        messages.error(request, "No clinic associated with your account.")
        return redirect('home')

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip() or 'Walk-in Customer'
        source = request.POST.get('source', 'clinic')
        notes = request.POST.get('notes', '').strip()

        # Parse line items from JSON
        items_json = request.POST.get('items_json', '[]')
        try:
            items_data = json.loads(items_json)
        except json.JSONDecodeError:
            messages.error(request, 'Invalid items data.')
            return redirect('create_invoice')

        if not items_data:
            messages.error(request, 'Please add at least one item to the invoice.')
            return redirect('create_invoice')

        # Create invoice
        invoice = Invoice.objects.create(
            clinic=clinic,
            source=source,
            created_by=request.user,
            customer_name=customer_name,
            notes=notes,
        )

        errors = []
        for item_data in items_data:
            inv_item_id = item_data.get('inventory_item_id')
            name = item_data.get('name', 'Item')
            try:
                qty = int(item_data.get('quantity', 1))
                unit_price = Decimal(str(item_data.get('unit_price', 0)))
            except (ValueError, InvalidOperation):
                errors.append(f'Invalid quantity or price for "{name}".')
                continue

            inv_item = None
            if inv_item_id:
                inv_item = InventoryItem.objects.filter(id=inv_item_id, clinic=clinic).first()
                if inv_item and not inv_item.category.is_infinite:
                    try:
                        inv_item.consume(qty)
                    except ValueError as e:
                        errors.append(str(e))
                        continue

            InvoiceItem.objects.create(
                invoice=invoice,
                inventory_item=inv_item,
                name=name,
                quantity=qty,
                unit_price=unit_price,
            )

        invoice.recalculate_total()

        if errors:
            for err in errors:
                messages.warning(request, err)

        messages.success(request, f'Invoice {invoice.reference} created — Total: ${invoice.total_amount}')
        return redirect('invoice_detail', invoice_id=invoice.id)

    # GET — show create form
    items = InventoryItem.objects.filter(clinic=clinic).select_related('category').order_by('name')
    source_choices = Invoice.SOURCE_CHOICES

    return render(request, 'invoices/create_invoice.html', {
        'inventory_items': items,
        'source_choices': source_choices,
    })


@doctor_or_clinic_owner_required
def invoice_detail(request, invoice_id):
    """View a single invoice."""
    clinic = request.clinic
    if is_siteowner(request.user):
        invoice = get_object_or_404(Invoice, id=invoice_id)
    else:
        invoice = get_object_or_404(Invoice, id=invoice_id, clinic=clinic)
    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})


@doctor_or_clinic_owner_required
def invoice_list(request):
    """Paginated list of invoices."""
    clinic = request.clinic
    if is_siteowner(request.user):
        qs = Invoice.objects.all()
    else:
        qs = Invoice.objects.filter(clinic=clinic)

    # Filters
    search = request.GET.get('q', '').strip()
    source_filter = request.GET.get('source', '')
    if search:
        qs = qs.filter(Q(reference__icontains=search) | Q(customer_name__icontains=search))
    if source_filter:
        qs = qs.filter(source=source_filter)

    qs = qs.select_related('clinic', 'created_by')
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'invoices/invoice_list.html', {
        'page': page,
        'search': search,
        'source_filter': source_filter,
        'source_choices': Invoice.SOURCE_CHOICES,
    })


@doctor_or_clinic_owner_required
def history(request):
    """Revenue history and analytics. Full analytics for admin, limited for doctor/petshop."""
    clinic = request.clinic
    today = timezone.localdate()
    user = request.user

    is_limited = is_doctor(user) or is_petshop(user)

    if is_siteowner(user):
        base_qs = Invoice.objects.all()
    else:
        base_qs = Invoice.objects.filter(clinic=clinic)

    if is_limited:
        # Only today and yesterday
        yesterday = today - timedelta(days=1)
        base_qs = base_qs.filter(created_at__date__gte=yesterday)
    else:
        # Date range filters
        date_from = request.GET.get('from', '')
        date_to = request.GET.get('to', '')
        if date_from:
            base_qs = base_qs.filter(created_at__date__gte=date_from)
        if date_to:
            base_qs = base_qs.filter(created_at__date__lte=date_to)

    # Source filter
    source_filter = request.GET.get('source', '')
    if source_filter:
        base_qs = base_qs.filter(source=source_filter)

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        base_qs = base_qs.filter(Q(reference__icontains=search) | Q(customer_name__icontains=search))

    # Sort
    sort = request.GET.get('sort', '-created_at')
    valid_sorts = ['created_at', '-created_at', 'total_amount', '-total_amount']
    if sort not in valid_sorts:
        sort = '-created_at'
    invoices_qs = base_qs.order_by(sort).select_related('clinic', 'created_by')

    paginator = Paginator(invoices_qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    # Analytics (admin only)
    analytics = {}
    if not is_limited:
        analytics['total_revenue'] = base_qs.aggregate(t=Sum('total_amount'))['t'] or 0
        analytics['invoice_count'] = base_qs.count()
        analytics['avg_ticket'] = (
            round(analytics['total_revenue'] / analytics['invoice_count'], 2)
            if analytics['invoice_count'] > 0 else 0
        )

        # Revenue by day (last 30 days)
        thirty_days_ago = today - timedelta(days=30)
        daily_rev = (
            base_qs.filter(created_at__date__gte=thirty_days_ago)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(revenue=Sum('total_amount'), count=Count('id'))
            .order_by('day')
        )
        analytics['daily_labels'] = [d['day'].strftime('%d %b') for d in daily_rev]
        analytics['daily_data'] = [float(d['revenue']) for d in daily_rev]

        # Revenue by source
        by_source = base_qs.values('source').annotate(total=Sum('total_amount')).order_by('-total')
        source_map = dict(Invoice.SOURCE_CHOICES)
        analytics['source_labels'] = [source_map.get(s['source'], s['source']) for s in by_source]
        analytics['source_data'] = [float(s['total']) for s in by_source]

        # Top selling items
        top_items = (
            InvoiceItem.objects.filter(invoice__in=base_qs)
            .values('name')
            .annotate(
                total_qty=Sum('quantity'),
                total_revenue=Sum('line_total')
            )
            .order_by('-total_revenue')[:10]
        )
        analytics['top_items'] = list(top_items)

    return render(request, 'invoices/history.html', {
        'page': page,
        'is_limited': is_limited,
        'analytics': analytics,
        'search': search,
        'source_filter': source_filter,
        'source_choices': Invoice.SOURCE_CHOICES,
        'sort': sort,
        'date_from': request.GET.get('from', ''),
        'date_to': request.GET.get('to', ''),
    })


@doctor_or_clinic_owner_required
def get_inventory_items_json(request):
    """Return inventory items as JSON for invoice creation autocomplete."""
    clinic = request.clinic
    if not clinic:
        return JsonResponse({'items': []})
    items = InventoryItem.objects.filter(clinic=clinic).select_related('category').order_by('name')
    data = [{
        'id': item.id,
        'name': item.name,
        'price': str(item.price),
        'unit': item.get_unit_display() if item.unit else '',
        'category': item.category.name,
        'stock': item.total_quantity if not item.category.is_infinite else 'Unlimited',
        'is_infinite': item.category.is_infinite,
    } for item in items]
    return JsonResponse({'items': data})
