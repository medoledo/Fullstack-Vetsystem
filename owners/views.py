from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from vetlogin.decorators import admin_required, doctor_or_admin_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Owner, Pet, PetType
from .forms import OwnerForm, PetForm, PetTypeForm
import pandas as pd


from django.db.models import Q, Exists, OuterRef, Value
from django.core.paginator import Paginator
from django.http import JsonResponse
from boarding.models import BoardingPet

@doctor_or_admin_required
def api_search_owners(request):
    """AJAX endpoint for searching owners dynamically via TomSelect"""
    query = request.GET.get('q', '').strip()
    qs = Owner.objects.all()
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(phone_number__icontains=query))
    
    qs = qs[:50] # Limit to 50 to ensure high performance
    results = [{'id': o.id, 'text': f"{o.name} - {o.phone_number}"} for o in qs]
    return JsonResponse({'items': results})
@doctor_or_admin_required
def api_get_owner_pets(request, owner_id):
    """AJAX endpoint to load pets belonging to a specific owner with optimized check for active boarding"""
    active_boardings = BoardingPet.objects.filter(
        pet=OuterRef('pk'), 
        end_date__isnull=True
    )
    
    pets = Pet.objects.filter(owner_id=owner_id).annotate(
        is_boarded=Exists(active_boardings)
    ).values('id', 'name', 'code', 'is_boarded', 'pet_type_id')
    
    results = [
        {
            'id': p['id'], 
            'text': f"{p['name']} ({p['code']})", 
            'is_boarded': p['is_boarded'],
            'pet_type_id': p['pet_type_id']
        } for p in pets
    ]
    return JsonResponse({'items': results})

@doctor_or_admin_required
def owners(request):
    search_query = request.GET.get('search', '').strip()

    qs = Owner.objects.all().prefetch_related('pets').order_by('-joined_date', '-id')

    if search_query:
        qs = qs.filter(
            Q(name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    # Pagination: dynamic page size based on user selection (default 10)
    try:
        limit = int(request.GET.get('limit', 10))
    except ValueError:
        limit = 10
        
    # Ensure limit is one of the allowed options
    if limit not in [10, 20, 50, 100]:
        limit = 10

    paginator = Paginator(qs, limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'ownerspage/owners.html', {
        'owners': page_obj,  # Pass the paginated object as 'owners' for compatibility with the existing loop
        'page_obj': page_obj,
        'search_query': search_query,
        'limit': str(limit),
    })


@doctor_or_admin_required
def add_owner(request):
    if request.method == 'POST':
        form = OwnerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Owner added successfully.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    return redirect(request.META.get('HTTP_REFERER', 'owners'))


@doctor_or_admin_required
def edit_owner(request, owner_id):
    owner = get_object_or_404(Owner, id=owner_id)
    if request.method == 'POST':
        form = OwnerForm(request.POST, instance=owner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Owner updated.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    return redirect(request.META.get('HTTP_REFERER', 'owners'))


@admin_required
def delete_owner(request, owner_id):
    owner = get_object_or_404(Owner, id=owner_id)
    if request.method == 'POST':
        owner.delete()
        messages.success(request, 'Owner deleted.')
    return redirect('owners')


@doctor_or_admin_required
def owner_detail(request, owner_id):
    owner = get_object_or_404(Owner, id=owner_id)
    pets = owner.pets.select_related('pet_type')
    pet_types = PetType.objects.all()
    return render(request, 'ownerspage/owner_detail.html', {'owner': owner, 'pets': pets, 'pet_types': pet_types})


@doctor_or_admin_required
def download_owners(request):
    search_name = request.GET.get('search_name', '')
    search_number = request.GET.get('search_number', '')

    qs = Owner.objects.all().select_related()
    if search_name:
        qs = qs.filter(name__icontains=search_name)
    if search_number:
        qs = qs.filter(phone_number__icontains=search_number)

    data = qs.values('name', 'phone_number', 'joined_date')
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=owners.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')
    return response


@doctor_or_admin_required
def todays_birthdays(request):
    import urllib.parse
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Get all active pets born on this month and day
    birthday_pets = Pet.objects.filter(
        birthdate__month=today.month,
        birthdate__day=today.day
    ).select_related('owner', 'pet_type')
    
    # Process WhatsApp message for each pet
    pets_data = []
    for pet in birthday_pets:
        # Generate the Egyptian Arabic message
        msg = f"كل سنة و {pet.name} طيب وبخير! 🎉 حابين نشارككم فرحة عيد ميلاد {pet.name} الـ {pet.age} النهارده من عيادة كوين سنتر 🐾"
        
        # Clean phone number (remove leading zeros, ensure country code)
        phone = pet.owner.phone_number.strip()
        if phone.startswith('0'):
            phone = '2' + phone
        elif not phone.startswith('+') and not phone.startswith('20'):
            # Fallback if no country code (assumes Egypt)
            phone = '20' + phone
            
        whatsapp_url = f"https://web.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(msg)}"
        
        pets_data.append({
            'pet': pet,
            'whatsapp_url': whatsapp_url
        })
        
    return render(request, 'ownerspage/birthdays.html', {
        'pets_data': pets_data,
        'today': today
    })


# ── Pet Type ──────────────────────────────────────────────
@admin_required
def pet_types(request):
    types = PetType.objects.all()
    form = PetTypeForm()
    if request.method == 'POST':
        form = PetTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pet type added.')
            return redirect('pet_types')
    return render(request, 'ownerspage/pet_types.html', {'types': types, 'form': form})


@admin_required
def delete_pet_type(request, type_id):
    pet_type = get_object_or_404(PetType, id=type_id)
    if request.method == 'POST':
        try:
            pet_type.delete()
            messages.success(request, 'Pet type deleted.')
        except Exception:
            messages.error(request, 'Cannot delete — pets of this type still exist.')
    return redirect('pet_types')


# ── Pets ──────────────────────────────────────────────────
@doctor_or_admin_required
def add_pet(request, owner_id):
    owner = get_object_or_404(Owner, id=owner_id)
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = owner
            pet.save()
            messages.success(request, f'Pet "{pet.name}" added with code {pet.code}.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    return redirect('owner_detail', owner_id=owner.id)


@doctor_or_admin_required
def edit_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pet updated.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    return redirect('owner_detail', owner_id=pet.owner.id)


@doctor_or_admin_required
def delete_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    owner_id = pet.owner.id
    if request.method == 'POST':
        pet.delete()
        messages.success(request, 'Pet deleted.')
        return redirect('owner_detail', owner_id=owner_id)
    return render(request, 'ownerspage/confirm_delete_pet.html', {'pet': pet})


@doctor_or_admin_required
def pet_detail(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    return render(request, 'ownerspage/pet_detail.html', {'pet': pet})
