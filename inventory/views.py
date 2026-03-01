from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Min, Q
from vetlogin.decorators import admin_required, doctor_or_admin_required
from .models import Category, InventoryItem, InventoryBatch, InventoryPreference, UNIT_CHOICES
from datetime import timedelta
from django.utils import timezone


VALID_PER_PAGE = [10, 20, 50, 100]
DEFAULT_PER_PAGE = 50


@doctor_or_admin_required
def inventory_dashboard(request):
    prefs = InventoryPreference.get()
    categories = Category.objects.all()
    tab = request.GET.get('tab', 'items')

    # ── Search & filter params ────────────────────────────────────
    search_q = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    try:
        per_page = int(request.GET.get('per_page', DEFAULT_PER_PAGE))
        if per_page not in VALID_PER_PAGE:
            per_page = DEFAULT_PER_PAGE
    except (ValueError, TypeError):
        per_page = DEFAULT_PER_PAGE

    # ── Build items queryset with annotations ─────────────────────
    items_qs = InventoryItem.objects.select_related('category').annotate(
        total_qty=Sum('batches__quantity'),
        nearest_exp=Min('batches__expiration_date'),
    )

    today = timezone.now().date()
    warn_days = today + timedelta(days=prefs.expiry_warning_days)

    if status_filter == 'low_stock':
        items_qs = items_qs.exclude(category__is_infinite=True).filter(total_qty__lte=prefs.low_stock_threshold)
    elif status_filter == 'expiring_soon':
        items_qs = items_qs.exclude(category__is_infinite=True).filter(nearest_exp__isnull=False, nearest_exp__lte=warn_days)

    if search_q:
        items_qs = items_qs.filter(
            Q(name__icontains=search_q) | Q(notes__icontains=search_q)
        )
    if category_filter:
        items_qs = items_qs.filter(category_id=category_filter)

    items_qs = items_qs.order_by('category__name', 'name')

    # ── Warning counts (before pagination) ───────────────────────

    warning_count = 0
    for item in items_qs:
        total = item.total_qty or 0
        if not item.category.is_infinite:
            if total <= prefs.low_stock_threshold:
                warning_count += 1
            elif item.nearest_exp and item.nearest_exp <= warn_days:
                warning_count += 1

    # ── Paginate ──────────────────────────────────────────────────
    paginator = Paginator(items_qs, per_page)
    page_number = request.GET.get('page', 1)
    items_page = paginator.get_page(page_number)

    # ── Attach batch info for template ───────────────────────────
    items_with_batches = []
    for item in items_page:
        batches = list(item.batches.order_by('expiration_date', 'date_received'))
        total = item.total_qty or 0
        is_low = (not item.category.is_infinite) and (total <= prefs.low_stock_threshold)
        exp_status = None
        if item.nearest_exp and not item.category.is_infinite:
            if item.nearest_exp < today:
                exp_status = 'expired'
            elif item.nearest_exp <= warn_days:
                exp_status = 'warning'
            else:
                exp_status = 'ok'
        items_with_batches.append({
            'item': item,
            'batches': batches,
            'total_qty': total,
            'is_low_stock': is_low,
            'expiry_status': exp_status,
            'nearest_exp': item.nearest_exp,
        })

    try:
        category_filter_int = int(category_filter) if category_filter else None
    except (ValueError, TypeError):
        category_filter_int = None

    context = {
        'items_with_batches': items_with_batches,
        'items_page': items_page,
        'categories': categories,
        'prefs': prefs,
        'tab': tab,
        'search_q': search_q,
        'category_filter': category_filter,
        'unit_choices': UNIT_CHOICES,
        'category_filter_int': category_filter_int,
        'status_filter': status_filter,
        'per_page': per_page,
        'per_page_options': VALID_PER_PAGE,
        'warning_count': warning_count,
        'total_items': items_qs.count(),
    }
    return render(request, 'inventorypage/inventory.html', context)


# ── Category Views ────────────────────────────────────────────────

@admin_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_infinite = request.POST.get('is_infinite') == 'on'
        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f'A category named "{name}" already exists.')
        else:
            Category.objects.create(name=name, is_infinite=is_infinite)
            messages.success(request, f'Category "{name}" added.')
    return redirect('/inventory/?tab=categories')


@admin_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_infinite = request.POST.get('is_infinite') == 'on'
        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
            messages.error(request, f'A category named "{name}" already exists.')
        else:
            category.name = name
            category.is_infinite = is_infinite
            category.save()
            messages.success(request, f'Category "{name}" updated.')
    return redirect('/inventory/?tab=categories')


@admin_required
def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        if category.items.exists():
            messages.error(request, f'Cannot delete "{category.name}" — it still has items.')
        else:
            name = category.name
            category.delete()
            messages.success(request, f'Category "{name}" deleted.')
    return redirect('/inventory/?tab=categories')


# ── Item Views ────────────────────────────────────────────────────

@admin_required
def add_item(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        unit = request.POST.get('unit', '').strip() or None
        notes = request.POST.get('notes', '').strip() or None
        # First-batch fields
        batch_qty = request.POST.get('batch_quantity') or None
        batch_expiry = request.POST.get('batch_expiry') or None
        batch_notes = request.POST.get('batch_notes', '').strip() or None

        if not name or not category_id or not price:
            messages.error(request, 'Name, category, and price are required.')
            return redirect('/inventory/?tab=items')

        try:
            category = Category.objects.get(id=category_id)
            item = InventoryItem.objects.create(
                name=name, category=category, price=price, unit=unit, notes=notes
            )
            if not category.is_infinite and batch_qty:
                InventoryBatch.objects.create(
                    item=item,
                    quantity=int(batch_qty),
                    expiration_date=batch_expiry or None,
                    notes=batch_notes,
                )
            messages.success(request, f'Item "{name}" added to inventory.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('/inventory/?tab=items')


@admin_required
def edit_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        unit = request.POST.get('unit', '').strip() or None
        notes = request.POST.get('notes', '').strip() or None

        if not name or not category_id or not price:
            messages.error(request, 'Name, category, and price are required.')
            return redirect('/inventory/?tab=items')
        try:
            item.name = name
            item.category = Category.objects.get(id=category_id)
            item.price = price
            item.unit = unit
            item.notes = notes
            item.save()
            messages.success(request, f'Item "{name}" updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('/inventory/?tab=items')


@admin_required
def delete_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(InventoryItem, id=item_id)
        name = item.name
        item.delete()
        messages.success(request, f'Item "{name}" deleted.')
    return redirect('/inventory/?tab=items')


# ── Batch Views ───────────────────────────────────────────────────

@admin_required
def add_batch(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    if request.method == 'POST':
        qty = request.POST.get('quantity')
        expiry = request.POST.get('expiration_date') or None
        date_received = request.POST.get('date_received') or None
        batch_notes = request.POST.get('notes', '').strip() or None
        if not qty:
            messages.error(request, 'Quantity is required for a batch.')
        else:
            try:
                InventoryBatch.objects.create(
                    item=item,
                    quantity=int(qty),
                    expiration_date=expiry,
                    date_received=date_received or None,
                    notes=batch_notes,
                )
                messages.success(request, f'Batch added to "{item.name}".')
            except Exception as e:
                messages.error(request, f'Error: {e}')
    return redirect('/inventory/?tab=items')


@admin_required
def edit_batch(request, batch_id):
    batch = get_object_or_404(InventoryBatch, id=batch_id)
    if request.method == 'POST':
        qty = request.POST.get('quantity')
        expiry = request.POST.get('expiration_date') or None
        date_received = request.POST.get('date_received') or None
        batch_notes = request.POST.get('notes', '').strip() or None
        if not qty:
            messages.error(request, 'Quantity is required.')
        else:
            try:
                batch.quantity = int(qty)
                batch.expiration_date = expiry
                if date_received:
                    batch.date_received = date_received
                batch.notes = batch_notes
                batch.save()
                messages.success(request, 'Batch updated.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
    return redirect('/inventory/?tab=items')


@admin_required
def delete_batch(request, batch_id):
    if request.method == 'POST':
        batch = get_object_or_404(InventoryBatch, id=batch_id)
        item_name = batch.item.name
        batch.delete()
        messages.success(request, f'Batch removed from "{item_name}".')
    return redirect('/inventory/?tab=items')


# ── Preferences View ──────────────────────────────────────────────

@admin_required
def edit_preferences(request):
    if request.method == 'POST':
        prefs = InventoryPreference.get()
        try:
            prefs.low_stock_threshold = int(request.POST.get('low_stock_threshold', 10))
            prefs.expiry_warning_days = int(request.POST.get('expiry_warning_days', 30))
            prefs.save()
            messages.success(request, 'Preferences saved.')
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid value: {e}')
    return redirect('/inventory/?tab=preferences')
