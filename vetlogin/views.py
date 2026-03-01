from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.models import User

def vetlogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'vetlogin/login.html')


def logout_view(request):
    logout(request)
    return redirect('vetlogin')


@login_required
def home(request):
    from owners.models import Owner, Pet
    from visits.models import Visit
    from boarding.models import BoardingPet
    from tasks.models import Task
    from django.utils import timezone
    today = timezone.localdate()
    context = {
        'total_owners': Owner.objects.count(),
        'total_pets': Pet.objects.count(),
        'total_visits': Visit.objects.count(),
        'active_boardings': BoardingPet.objects.filter(end_date__isnull=True).count(),
        'today_visits_count': Visit.objects.filter(next_visit_date=today).count(),
        'open_tasks': Task.objects.filter(is_done=False).count(),
        'birthday_count': Pet.objects.filter(birthdate__month=today.month, birthdate__day=today.day).count(),
    }
    return render(request, 'homepage/home.html', context)

from .decorators import admin_required
from .models import AdminProfile, DoctorProfile, PetshopProfile

@admin_required
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        name = request.POST.get('name')
        phone = request.POST.get('phone_number')

        if username and password and role and name:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'This username already exists. Please choose a different one.')
            else:
                user = User.objects.create_user(username=username, password=password)
                if role == 'ADMIN':
                    AdminProfile.objects.create(user=user, name=name, phone_number=phone)
                elif role == 'DOCTOR':
                    DoctorProfile.objects.create(user=user, name=name, phone_number=phone)
                elif role == 'PETSHOP':
                    PetshopProfile.objects.create(user=user, name=name, phone_number=phone)
                messages.success(request, 'User created successfully.')
                return redirect('add_user')
        else:
            messages.error(request, 'Please fill in all required fields.')

    users = User.objects.all().select_related('adminprofile', 'doctorprofile', 'petshopprofile')
    return render(request, 'vetlogin/add_user.html', {'users': users})

@admin_required
def delete_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user and user != request.user:
        user.delete()
        messages.success(request, f'User "{user.username}" deleted.')
    elif user == request.user:
        messages.error(request, "You cannot delete your own account.")
    return redirect('add_user')

@admin_required
def edit_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return redirect('add_user')

    if request.method == 'POST':
        profile = getattr(user, 'adminprofile', None) or getattr(user, 'doctorprofile', None) or getattr(user, 'petshopprofile', None)
        name = request.POST.get('name')
        phone = request.POST.get('phone_number')
        if name and profile:
            profile.name = name
            profile.phone_number = phone
            profile.save()
            
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'User profile updated successfully.')
        elif name and profile:
            messages.success(request, 'User profile updated successfully.')

    return redirect('add_user')

def custom_csrf_failure(request, reason=""):
    """
    Handle CSRF failures gracefully. This usually happens when a user 
    logs out, hits the back button to the login page, and tries to log in again.
    """
    return render(request, 'vetlogin/login.html', {'messages': ['Your session token expired. Please try logging in again.']})


