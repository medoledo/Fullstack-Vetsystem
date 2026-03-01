from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import urllib.parse
from owners.models import Pet
from .models import Visit
from django.contrib import messages
from django.core.paginator import Paginator

@login_required
def pet_visits(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    
    if request.method == 'POST':
        visit_date = request.POST.get('visit_date')
        weight = request.POST.get('weight')
        weight_unit = request.POST.get('weight_unit')
        diagnosis = request.POST.get('diagnosis')
        treatment_protocol = request.POST.get('treatment_protocol')
        next_visit_date = request.POST.get('next_visit_date') or None
        temperature = request.POST.get('temperature') or None
        
        try:
            doctor_name = request.user.username
            if hasattr(request.user, 'adminprofile'):
                doctor_name = request.user.adminprofile.name
            elif hasattr(request.user, 'doctorprofile'):
                doctor_name = request.user.doctorprofile.name
            elif hasattr(request.user, 'petshopprofile'):
                doctor_name = request.user.petshopprofile.name

            Visit.objects.create(
                pet=pet, doctor=request.user, doctor_name_snapshot=doctor_name,
                visit_date=visit_date, weight=float(weight), weight_unit=weight_unit,
                temperature=float(temperature) if temperature else None,
                diagnosis=diagnosis, treatment_protocol=treatment_protocol,
                next_visit_date=next_visit_date
            )
            messages.success(request, f"New visit recorded for {pet.name}.")
            return redirect('pet_visits', pet_id=pet.id)
        except Exception as e:
            messages.error(request, f"Error saving visit: {str(e)}")
            
    # Pagination for pet visits
    visits_qs = pet.visits.all().order_by('-visit_date')
    paginator = Paginator(visits_qs, 10) # 10 visits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'pet': pet,
        'visits': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'visitspage/pet_visits.html', context)

@login_required
def expected_visits(request):
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    
    # Use select_related to avoid N+1 per pet
    today_visits = Visit.objects.filter(next_visit_date=today).select_related('pet').order_by('pet__name')
    tomorrow_visits = Visit.objects.filter(next_visit_date=tomorrow).select_related('pet').order_by('pet__name')
    
    for v in today_visits:
        msg = f"السلام عليكم\nبنفكركم ان النهاردة بتاريخ {today.strftime('%Y-%m-%d')} معاد زيارة حيوانكم الاليف ( {v.pet.name} ) لمتابعه الحاله\nشكرا لكم"
        v.whatsapp_msg = urllib.parse.quote(msg)
        
    for v in tomorrow_visits:
        msg = f"السلام عليكم\nبنفكركم ان بكرا بتاريخ {tomorrow.strftime('%Y-%m-%d')} معاد زيارة حيوانكم الاليف ( {v.pet.name} ) لمتابعه الحاله\nشكرا لكم"
        v.whatsapp_msg = urllib.parse.quote(msg)

    context = {
        'today_visits': today_visits,
        'tomorrow_visits': tomorrow_visits,
    }
    return render(request, 'visitspage/expected_visits.html', context)
