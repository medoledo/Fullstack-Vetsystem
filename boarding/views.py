from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from vetlogin.decorators import admin_required, doctor_or_admin_required
from django.utils import timezone
from datetime import datetime
from .models import Cage, BoardingType, BoardingPet
from owners.models import Pet, PetType, Owner

import json
import decimal
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, IntegerField, Value
from django.db.models.functions import Coalesce

@login_required
def boarding_dashboard(request):
    clinic = request.clinic
    if not clinic:
        return render(request, 'boardingpage/boarding.html', {})

    current_month = timezone.now().strftime('%Y-%m')
    selected_month = request.GET.get('month', current_month)
    
    try:
        year_str, month_str = selected_month.split('-')
        year = int(year_str)
        month = int(month_str)
    except (ValueError, TypeError):
        year = timezone.now().year
        month = timezone.now().month
        selected_month = current_month

    active_boardings = BoardingPet.objects.filter(
        pet__owner__clinic=clinic, end_date__isnull=True
    ).select_related(
        'pet', 'cage', 'boarding_type', 'checked_in_by', 'checked_out_by'
    ).order_by('-start_date')
    
    history_qs = BoardingPet.objects.filter(
        pet__owner__clinic=clinic,
        end_date__isnull=False,
        end_date__year=year,
        end_date__month=month
    ).select_related(
        'pet', 'pet__owner', 'cage', 'boarding_type', 'checked_in_by', 'checked_out_by'
    )

    income_agg = history_qs.aggregate(
        raw_sum=Sum(
            ExpressionWrapper(
                F('price_per_day'),
                output_field=DecimalField()
            )
        )
    )
    total_income = sum(
        b.amount_owed for b in BoardingPet.objects.filter(
            pet__owner__clinic=clinic,
            end_date__isnull=False,
            end_date__year=year,
            end_date__month=month
        ).only('start_date', 'end_date', 'price_per_day', 'discount')
        if b.amount_owed is not None
    )
    
    history_paginator = Paginator(history_qs.order_by('-end_date'), 15)
    history_page_number = request.GET.get('history_page')
    boarding_history = history_paginator.get_page(history_page_number)
    
    cages = Cage.objects.filter(clinic=clinic).prefetch_related('pet_types')
    boarding_types = BoardingType.objects.filter(clinic=clinic).prefetch_related('cages')
    
    pets = Pet.objects.filter(owner__clinic=clinic)[:200]
    owners = Owner.objects.filter(clinic=clinic)[:100]
    pet_types = PetType.objects.filter(clinic=clinic)

    occupied_cage_ids = set(active_boardings.values_list('cage_id', flat=True))
    cages_data = {}
    for c in cages:
        cages_data[c.id] = {
            'is_empty': c.id not in occupied_cage_ids,
            'pet_type_ids': list(c.pet_types.values_list('id', flat=True))
        }

    context = {
        'selected_month': selected_month,
        'active_boardings': active_boardings,
        'boarding_history': boarding_history,
        'history_page_obj': boarding_history,
        'cages': cages,
        'boarding_types': boarding_types,
        'pets': pets,
        'pet_types': pet_types,
        'owners': owners,
        'cages_data_json': json.dumps(cages_data),
        'total_income': total_income
    }
    return render(request, 'boardingpage/boarding.html', context)

@admin_required
def add_cage(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        pet_type_ids = request.POST.getlist('pet_types')
        
        try:
            cage = Cage.objects.create(name=name, clinic=request.clinic)
            if pet_type_ids:
                cage.pet_types.set(pet_type_ids)
            messages.success(request, f"Cage '{name}' added successfully.")
        except Exception as e:
            messages.error(request, f"Error adding cage: {str(e)}")
            
    return redirect('/boarding/#tab-config')

@admin_required
def add_boarding_type(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price_per_day')
        cages_ids = request.POST.getlist('cages')
        
        try:
            b_type = BoardingType.objects.create(name=name, price_per_day=price, clinic=request.clinic)
            if cages_ids:
                b_type.cages.set(cages_ids)
            messages.success(request, f"Boarding type '{name}' created.")
        except Exception as e:
            messages.error(request, f"Error creating boarding type: {str(e)}")
            
    return redirect('/boarding/#tab-config')

@doctor_or_admin_required
def board_pet(request):
    if request.method == 'POST':
        pet_id = request.POST.get('pet')
        cage_id = request.POST.get('cage')
        btype_id = request.POST.get('boarding_type')
        start_date = request.POST.get('start_date')
        
        try:
            pet = Pet.objects.get(id=pet_id, owner__clinic=request.clinic)
            cage = Cage.objects.get(id=cage_id, clinic=request.clinic)
            btype = BoardingType.objects.get(id=btype_id, clinic=request.clinic)
            
            if BoardingPet.objects.filter(cage=cage, end_date__isnull=True).exists():
                messages.error(request, f"Cage {cage.name} is currently occupied.")
                return redirect('boarding_dashboard')
                
            if cage.pet_types.exists() and pet.pet_type not in cage.pet_types.all():
                messages.error(request, f"Cage {cage.name} does not accept {pet.pet_type.name}s.")
                return redirect('boarding_dashboard')
                
            BoardingPet.objects.create(
                pet=pet,
                cage=cage,
                boarding_type=btype,
                start_date=start_date or timezone.now(),
                checked_in_by=request.user
            )
            messages.success(request, f"{pet.name} has been checked into boarding.")
        except Exception as e:
            messages.error(request, f"Error boarding pet: {str(e)}")
            
    return redirect('boarding_dashboard')

@doctor_or_admin_required
def end_boarding(request, boarding_id):
    if request.method == 'POST':
        boarding = get_object_or_404(BoardingPet, id=boarding_id, pet__owner__clinic=request.clinic)
        
        end_date_str = request.POST.get('end_date')
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()
        else:
            end_date = timezone.now().date()
            
        discount_str = request.POST.get('discount', '0')
        try:
            discount = Decimal(discount_str)
        except (ValueError, TypeError, decimal.InvalidOperation):
            discount = Decimal('0')
            
        try:
            boarding.end_date = end_date
            boarding.discount = discount
            boarding.checked_out_by = request.user
            boarding.save()
            messages.success(request, f"Boarding ended. Amount due: ${boarding.amount_owed}")
        except Exception as e:
            messages.error(request, f"Error ending boarding: {str(e)}")
            
    return redirect('boarding_dashboard')


@admin_required
def edit_cage(request, cage_id):
    cage = get_object_or_404(Cage, id=cage_id, clinic=request.clinic)
    if request.method == 'POST':
        name = request.POST.get('name')
        pet_type_ids = request.POST.getlist('pet_types')
        
        try:
            cage.name = name
            cage.save()
            cage.pet_types.clear()
            if pet_type_ids:
                cage.pet_types.set(pet_type_ids)
            messages.success(request, f"Cage '{name}' updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating cage: {str(e)}")
            
    return redirect('/boarding/#tab-config')

@admin_required
def delete_cage(request, cage_id):
    if request.method == 'POST':
        cage = get_object_or_404(Cage, id=cage_id, clinic=request.clinic)
        if BoardingPet.objects.filter(cage=cage, end_date__isnull=True).exists():
            messages.error(request, f"Cannot delete cage '{cage.name}' because it is currently occupied.")
        else:
            name = cage.name
            cage.delete()
            messages.success(request, f"Cage '{name}' deleted successfully.")
    return redirect('/boarding/#tab-config')

@admin_required
def edit_boarding_type(request, type_id):
    b_type = get_object_or_404(BoardingType, id=type_id, clinic=request.clinic)
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price_per_day')
        cages_ids = request.POST.getlist('cages')
        
        try:
            b_type.name = name
            b_type.price_per_day = price
            b_type.save()
            
            b_type.cages.clear()
            if cages_ids:
                b_type.cages.set(cages_ids)
            messages.success(request, f"Boarding type '{name}' updated.")
        except Exception as e:
            messages.error(request, f"Error updating boarding type: {str(e)}")
            
    return redirect('/boarding/#tab-config')

@admin_required
def delete_boarding_type(request, type_id):
    if request.method == 'POST':
        b_type = get_object_or_404(BoardingType, id=type_id, clinic=request.clinic)
        if BoardingPet.objects.filter(boarding_type=b_type, end_date__isnull=True).exists():
            messages.error(request, f"Cannot delete package '{b_type.name}' because pets are currently using it.")
        else:
            name = b_type.name
            b_type.delete()
            messages.success(request, f"Boarding type '{name}' deleted.")
    return redirect('/boarding/#tab-config')
