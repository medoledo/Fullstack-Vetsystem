from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Min, Q
from vetlogin.decorators import admin_required, doctor_or_admin_required, is_petshop, is_clinic_owner, is_siteowner
from .models import Category, InventoryItem, InventoryBatch, InventoryPreference, UNIT_CHOICES, INVENTORY_TYPE_CHOICES
from datetime import timedelta
from django.utils import timezone


VALID_PER_PAGE = [10, 20, 50, 100]
DEFAULT_PER_PAGE = 50


@doctor_or_admin_required
def inventory_dashboard(request):
    clinic = request.clinic
    if not clinic:
        return render(request, 'inventorypage/inventory.html', {})

    prefs = InventoryPreference.get_for_clinic(clinic)
    tab = request.GET.get('tab', 'items')
    categories = Category.objects.filter(clinic=clinic)

    # ── filters ────────────────────────────────────────────────────
    search_q = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')

    items_qs = InventoryItem.objects.filter(clinic=clinic).select_related('category').prefetch_related('batches')

    # Role-based inventory type filtering
    if is_petshop(request.user):
        inv_type = 'petshop'
    elif is_clinic_owner(request.user) or is_siteowner(request.user):
        inv_type = request.GET.get('inv_type', '')  # clinic owners can see both
    else:
        inv_type = 'clinic'  # doctors see clinic only

    if inv_type:
        categories = categories.filter(inventory_type=inv_type)
        items_qs = items_qs.filter(category__inventory_type=inv_type)

    if cat_filter:
        items_qs = items_qs.filter(category_id=cat_filter)
    if search_q:
        items_qs = items_qs.filter(Q(name__icontains=search_q))

    # materialise list so we can use computed properties
    items_list = list(items_qs)

    if status_filter == 'low':
        items_list = [i for i in items_list if i.is_low_stock]
    elif status_filter == 'expired':
        items_list = [i for i in items_list if i.expiry_status == 'expired']
    elif status_filter == 'warning':
        items_list = [i for i in items_list if i.expiry_status == 'warning']

    # ── pagination ─────────────────────────────────────────────────
    try:
        per_page = int(request.GET.get('per_page', DEFAULT_PER_PAGE))
    except ValueError:
        per_page = DEFAULT_PER_PAGE
    if per_page not in VALID_PER_PAGE:
        per_page = DEFAULT_PER_PAGE

    paginator = Paginator(items_list, per_page)
    items_page = paginator.get_page(request.GET.get('page'))

    items_with_batches = []
    for item in items_page:
        batches = list(item.batches.all().order_by('expiration_date'))
        items_with_batches.append({'item': item, 'batches': batches, 'expiry_status': item.expiry_status, 'total_stock': item.total_stock})


    context = {
        'tab': tab,
        'items_page': items_page,
        'items_with_batches': items_with_batches,
        'categories': categories,
        'unit_choices': UNIT_CHOICES,
        'inventory_type_choices': INVENTORY_TYPE_CHOICES,
        'prefs': prefs,
        # keep filter state
        'selected_category': cat_filter,
        'search_q': search_q,
        'category_filter': cat_filter,
        'selected_status': status_filter,
        'selected_inv_type': inv_type if inv_type else '',
        'per_page': per_page,
        'per_page_options': [10, 20, 50, 100],
        # summary
        'total_items': len(items_list),
        'warning_count': sum(1 for i in list(InventoryItem.objects.filter(clinic=clinic).prefetch_related('batches')) if i.is_low_stock or i.expiry_status in ('expired', 'warning')),
        'is_petshop_user': is_petshop(request.user),
        'is_clinic_owner_user': is_clinic_owner(request.user) or is_siteowner(request.user),
    }
    return render(request, 'inventorypage/inventory.html', context)


# ── Category Views ────────────────────────────────────────────────

@admin_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_infinite = request.POST.get('is_infinite') == 'on'
        inventory_type = request.POST.get('inventory_type', 'clinic')
        if inventory_type not in ('clinic', 'petshop'):
            inventory_type = 'clinic'
        if name:
            Category.objects.create(
                name=name, is_infinite=is_infinite,
                inventory_type=inventory_type, clinic=request.clinic
            )
            messages.success(request, f'Category "{name}" created.')
        else:
            messages.error(request, 'Category name is required.')
    return redirect('inventory_dashboard')


@admin_required
def edit_category(request, category_id):
    cat = get_object_or_404(Category, id=category_id, clinic=request.clinic)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_infinite = request.POST.get('is_infinite') == 'on'
        inventory_type = request.POST.get('inventory_type', cat.inventory_type)
        if inventory_type not in ('clinic', 'petshop'):
            inventory_type = cat.inventory_type
        if name:
            cat.name = name
            cat.is_infinite = is_infinite
            cat.inventory_type = inventory_type
            cat.save()
            messages.success(request, f'Category "{name}" updated.')
        else:
            messages.error(request, 'Category name is required.')
    return redirect('inventory_dashboard')


@admin_required
def delete_category(request, category_id):
    cat = get_object_or_404(Category, id=category_id, clinic=request.clinic)
    if request.method == 'POST':
        try:
            cat.delete()
            messages.success(request, 'Category deleted.')
        except Exception:
            messages.error(request, 'Cannot delete — items still belong to this category.')
    return redirect('inventory_dashboard')


# ── Item Views ────────────────────────────────────────────────────

@admin_required
def add_item(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        cat_id = request.POST.get('category')
        unit = request.POST.get('unit', '')
        price = request.POST.get('price', 0)
        notes = request.POST.get('notes', '')

        # optional first-batch fields
        qty = request.POST.get('quantity')
        exp = request.POST.get('expiration_date') or None

        if name and cat_id:
            cat = get_object_or_404(Category, id=cat_id, clinic=request.clinic)
            item = InventoryItem.objects.create(
                name=name, category=cat, unit=unit,
                price=price, notes=notes, clinic=request.clinic,
            )
            # Create an initial batch if qty was provided
            if qty:
                try:
                    InventoryBatch.objects.create(
                        item=item, quantity=int(qty),
                        expiration_date=exp,
                    )
                except (ValueError, TypeError):
                    pass
            messages.success(request, f'Item "{name}" added.')
        else:
            messages.error(request, 'Name and category are required.')
    return redirect('inventory_dashboard')


@admin_required
def edit_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id, clinic=request.clinic)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        cat_id = request.POST.get('category')
        unit = request.POST.get('unit', '')
        price = request.POST.get('price', 0)
        notes = request.POST.get('notes', '')

        if name and cat_id:
            cat = get_object_or_404(Category, id=cat_id, clinic=request.clinic)
            item.name = name
            item.category = cat
            item.unit = unit
            item.price = price
            item.notes = notes
            item.save()
            messages.success(request, f'Item "{name}" updated.')
        else:
            messages.error(request, 'Name and category are required.')
    return redirect('inventory_dashboard')


@admin_required
def delete_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id, clinic=request.clinic)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted.')
    return redirect('inventory_dashboard')


# ── Batch Views ───────────────────────────────────────────────────

@admin_required
def add_batch(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id, clinic=request.clinic)
    if request.method == 'POST':
        qty = request.POST.get('quantity')
        exp = request.POST.get('expiration_date') or None
        notes = request.POST.get('notes', '')

        if qty:
            try:
                InventoryBatch.objects.create(
                    item=item, quantity=int(qty),
                    expiration_date=exp, notes=notes,
                )
                messages.success(request, f'Batch added to "{item.name}".')
            except (ValueError, TypeError):
                messages.error(request, 'Invalid quantity.')
        else:
            messages.error(request, 'Quantity is required.')
    return redirect('inventory_dashboard')


@admin_required
def edit_batch(request, batch_id):
    batch = get_object_or_404(InventoryBatch, id=batch_id, item__clinic=request.clinic)
    if request.method == 'POST':
        qty = request.POST.get('quantity')
        exp = request.POST.get('expiration_date') or None
        notes = request.POST.get('notes', '')

        if qty:
            try:
                batch.quantity = int(qty)
                batch.expiration_date = exp
                batch.notes = notes
                batch.save()
                messages.success(request, 'Batch updated.')
            except (ValueError, TypeError):
                messages.error(request, 'Invalid quantity.')
        else:
            messages.error(request, 'Quantity is required.')
    return redirect('inventory_dashboard')


@admin_required
def delete_batch(request, batch_id):
    batch = get_object_or_404(InventoryBatch, id=batch_id, item__clinic=request.clinic)
    if request.method == 'POST':
        batch.delete()
        messages.success(request, 'Batch deleted.')
    return redirect('inventory_dashboard')


# ── Preferences View ──────────────────────────────────────────────

@admin_required
def edit_preferences(request):
    clinic = request.clinic
    if not clinic:
        return redirect('inventory_dashboard')
    
    prefs = InventoryPreference.get_for_clinic(clinic)
    if request.method == 'POST':
        try:
            prefs.low_stock_threshold = int(request.POST.get('low_stock_threshold', 10))
            prefs.expiry_warning_days = int(request.POST.get('expiry_warning_days', 30))
            prefs.save()
            messages.success(request, 'Preferences updated.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid values.')
    return redirect('inventory_dashboard')
