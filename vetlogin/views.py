from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User

from .decorators import (
    siteowner_required, clinic_owner_required,
    doctor_or_clinic_owner_required,
    is_siteowner, is_clinic_owner, is_doctor, is_petshop
)
from .models import SiteOwnerProfile, ClinicOwnerProfile, DoctorProfile, PetshopProfile
from clinics.models import Clinic, SubscriptionPlan, ClinicSubscription


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
    from invoices.models import Invoice
    from django.utils import timezone
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth, TruncDate
    from datetime import timedelta
    import json

    today = timezone.localdate()
    this_month_start = today.replace(day=1)

    # Calculate last 6 months for charts
    months_labels = []
    months_starts = []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year - ((today.month - i - 1) // 12 + (1 if (today.month - i - 1) < 0 else 0))
        if today.month - i <= 0:
            y = today.year - 1
            m = 12 + (today.month - i)
        # Simpler: use relativedelta logic
        from datetime import date
        dt = date(today.year, today.month, 1)
        for _ in range(i):
            dt = (dt - timedelta(days=1)).replace(day=1)
        months_starts.append(dt)
        months_labels.append(dt.strftime('%b %Y'))

    # Siteowner sees platform-wide stats
    if is_siteowner(request.user):
        context = {
            'total_clinics': Clinic.objects.count(),
            'active_clinics': Clinic.objects.filter(is_active=True).count(),
            'total_users': User.objects.count(),
            'total_owners': Owner.objects.count(),
            'total_pets': Pet.objects.count(),
            'clinics': Clinic.objects.filter(is_active=True).order_by('name'),
            'total_revenue': Invoice.objects.aggregate(t=Sum('total_amount'))['t'] or 0,
            'total_invoices': Invoice.objects.count(),
        }
        return render(request, 'homepage/home.html', context)

    # Clinic-scoped staff see their clinic's data
    clinic = request.clinic
    if not clinic:
        messages.error(request, "Your account is not associated with any clinic.")
        return render(request, 'homepage/home.html', {})

    # Basic stats
    total_owners = Owner.objects.filter(clinic=clinic).count()
    total_pets = Pet.objects.filter(owner__clinic=clinic).count()
    total_visits = Visit.objects.filter(pet__owner__clinic=clinic).count()
    active_boardings = BoardingPet.objects.filter(
        pet__owner__clinic=clinic, end_date__isnull=True
    ).count()
    today_visits_count = Visit.objects.filter(
        pet__owner__clinic=clinic, next_visit_date=today
    ).count()
    open_tasks = Task.objects.filter(clinic=clinic, is_done=False).count()
    birthday_count = Pet.objects.filter(
        owner__clinic=clinic,
        birthdate__month=today.month,
        birthdate__day=today.day
    ).count()

    # Monthly analytics
    new_owners_this_month = Owner.objects.filter(
        clinic=clinic, joined_date__gte=this_month_start
    ).count()
    visits_this_month = Visit.objects.filter(
        pet__owner__clinic=clinic, visit_date__gte=this_month_start
    ).count()

    # Revenue this month
    revenue_this_month = Invoice.objects.filter(
        clinic=clinic, created_at__date__gte=this_month_start
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    invoices_this_month = Invoice.objects.filter(
        clinic=clinic, created_at__date__gte=this_month_start
    ).count()

    # Monthly visits chart (last 6 months)
    visits_by_month = []
    owners_by_month = []
    revenue_by_month = []
    for i, ms in enumerate(months_starts):
        if i < len(months_starts) - 1:
            me = months_starts[i + 1]
        else:
            me = today + timedelta(days=1)
        v_count = Visit.objects.filter(
            pet__owner__clinic=clinic,
            visit_date__gte=ms, visit_date__lt=me
        ).count()
        o_count = Owner.objects.filter(
            clinic=clinic,
            joined_date__gte=ms, joined_date__lt=me
        ).count()
        r_sum = Invoice.objects.filter(
            clinic=clinic,
            created_at__date__gte=ms, created_at__date__lt=me
        ).aggregate(t=Sum('total_amount'))['t'] or 0
        visits_by_month.append(v_count)
        owners_by_month.append(o_count)
        revenue_by_month.append(float(r_sum))

    # Daily visits last 14 days
    daily_visits_labels = []
    daily_visits_data = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        daily_visits_labels.append(d.strftime('%d %b'))
        daily_visits_data.append(
            Visit.objects.filter(
                pet__owner__clinic=clinic, visit_date=d
            ).count()
        )

    context = {
        'total_owners': total_owners,
        'total_pets': total_pets,
        'total_visits': total_visits,
        'active_boardings': active_boardings,
        'today_visits_count': today_visits_count,
        'open_tasks': open_tasks,
        'birthday_count': birthday_count,
        # Monthly
        'new_owners_this_month': new_owners_this_month,
        'visits_this_month': visits_this_month,
        'revenue_this_month': revenue_this_month,
        'invoices_this_month': invoices_this_month,
        # Charts
        'months_labels': json.dumps(months_labels),
        'visits_by_month': json.dumps(visits_by_month),
        'owners_by_month': json.dumps(owners_by_month),
        'revenue_by_month': json.dumps(revenue_by_month),
        'daily_visits_labels': json.dumps(daily_visits_labels),
        'daily_visits_data': json.dumps(daily_visits_data),
    }
    return render(request, 'homepage/home.html', context)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# User Management (Clinic Owners manage their staff)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@clinic_owner_required
def add_user(request):
    clinic = request.clinic
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role')
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        target_clinic_id = request.POST.get('clinic_id')

        errors = {}
        if not username:
            errors['username'] = 'Username is required.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'This username already exists.'
        if not password:
            errors['password'] = 'Password is required.'
        if not role:
            errors['role'] = 'Please select a role.'
        if not name:
            errors['name'] = 'Full name is required.'

        # Determine target clinic
        target_clinic = clinic
        if is_siteowner(request.user) and target_clinic_id:
            target_clinic = Clinic.objects.filter(id=target_clinic_id).first()
        if role in ('DOCTOR', 'PETSHOP', 'CLINIC_OWNER') and not target_clinic:
            errors['clinic_id'] = 'Please select a clinic.'

        # Validate: Doctor/Petshop require the clinic to have a Clinic Owner first
        if role in ('DOCTOR', 'PETSHOP') and target_clinic and not errors:
            has_owner = ClinicOwnerProfile.objects.filter(clinic=target_clinic).exists()
            if not has_owner:
                errors['clinic_id'] = f'"{target_clinic.name}" has no Clinic Owner yet. Please create a Clinic Owner first.'

        if errors:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': errors})
            # Fallback for non-AJAX: show first error as message
            for msg in errors.values():
                messages.error(request, msg)
                break
        else:
            user = User.objects.create_user(username=username, password=password)
            try:
                if role == 'CLINIC_OWNER':
                    ClinicOwnerProfile.objects.create(user=user, clinic=target_clinic, name=name, phone_number=phone)
                elif role == 'DOCTOR':
                    DoctorProfile.objects.create(user=user, clinic=target_clinic, name=name, phone_number=phone)
                elif role == 'PETSHOP':
                    PetshopProfile.objects.create(user=user, clinic=target_clinic, name=name, phone_number=phone)
                if is_ajax:
                    return JsonResponse({'success': True, 'message': f'User "{username}" created successfully.'})
                messages.success(request, f'User "{username}" created successfully.')
                return redirect('add_user')
            except Exception as e:
                user.delete()
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': {'__all__': str(e)}})
                messages.error(request, str(e))

    # Scope user list
    if is_siteowner(request.user):
        users = User.objects.all().select_related(
            'siteownerprofile', 'clinicownerprofile', 'clinicownerprofile__clinic',
            'doctorprofile', 'doctorprofile__clinic',
            'petshopprofile', 'petshopprofile__clinic'
        )
        clinics = Clinic.objects.filter(is_active=True)
    else:
        clinic_user_ids = set()
        clinic_user_ids.update(ClinicOwnerProfile.objects.filter(clinic=clinic).values_list('user_id', flat=True))
        clinic_user_ids.update(DoctorProfile.objects.filter(clinic=clinic).values_list('user_id', flat=True))
        clinic_user_ids.update(PetshopProfile.objects.filter(clinic=clinic).values_list('user_id', flat=True))
        users = User.objects.filter(id__in=clinic_user_ids).select_related(
            'clinicownerprofile', 'doctorprofile', 'petshopprofile'
        )
        clinics = None

    return render(request, 'vetlogin/add_user.html', {'users': users, 'clinics': clinics})


@clinic_owner_required
def delete_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return redirect('add_user')

    # Siteowner can delete anyone (except themselves)
    if is_siteowner(request.user):
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
        else:
            user.delete()
            messages.success(request, f'User "{user.username}" deleted.')
        return redirect('add_user')

    # Clinic owners can only delete users within their clinic
    clinic = request.clinic
    is_in_clinic = (
        ClinicOwnerProfile.objects.filter(user=user, clinic=clinic).exists() or
        DoctorProfile.objects.filter(user=user, clinic=clinic).exists() or
        PetshopProfile.objects.filter(user=user, clinic=clinic).exists()
    )
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
    elif is_in_clinic:
        user.delete()
        messages.success(request, f'User "{user.username}" deleted.')
    else:
        messages.error(request, "You can only delete users within your clinic.")
    return redirect('add_user')


@clinic_owner_required
def edit_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return redirect('add_user')

    # Clinic check (non-siteowner)
    if not is_siteowner(request.user):
        clinic = request.clinic
        is_in_clinic = (
            ClinicOwnerProfile.objects.filter(user=user, clinic=clinic).exists() or
            DoctorProfile.objects.filter(user=user, clinic=clinic).exists() or
            PetshopProfile.objects.filter(user=user, clinic=clinic).exists()
        )
        if not is_in_clinic:
            messages.error(request, "You can only edit users within your clinic.")
            return redirect('add_user')

    if request.method == 'POST':
        profile = (
            getattr(user, 'siteownerprofile', None) or
            getattr(user, 'clinicownerprofile', None) or
            getattr(user, 'doctorprofile', None) or
            getattr(user, 'petshopprofile', None)
        )
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Siteowner — Clinic Management
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@siteowner_required
def manage_clinics(request):
    clinics = Clinic.objects.all().order_by('name')
    # Get stats for each clinic
    from owners.models import Owner, Pet
    for c in clinics:
        c.owner_count = Owner.objects.filter(clinic=c).count()
        c.pet_count = Pet.objects.filter(owner__clinic=c).count()
        c.staff_count = (
            ClinicOwnerProfile.objects.filter(clinic=c).count() +
            DoctorProfile.objects.filter(clinic=c).count() +
            PetshopProfile.objects.filter(clinic=c).count()
        )
        # Attach subscription info
        try:
            c.sub = c.subscription
        except ClinicSubscription.DoesNotExist:
            c.sub = None
    return render(request, 'vetlogin/manage_clinics.html', {'clinics': clinics})


@siteowner_required
def add_clinic(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        logo = request.FILES.get('logo')
        
        if name:
            Clinic.objects.create(
                name=name,
                phone=phone or '',
                address=address or '',
                logo=logo,
            )
            messages.success(request, f'Clinic "{name}" created successfully.')
        else:
            messages.error(request, 'Clinic name is required.')
    return redirect('manage_clinics')


@siteowner_required
def edit_clinic(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        is_active = request.POST.get('is_active') == 'on'
        logo = request.FILES.get('logo')
        
        if name:
            clinic.name = name
            clinic.phone = phone or ''
            clinic.address = address or ''
            clinic.is_active = is_active
            if logo:
                clinic.logo = logo
            clinic.save()
            messages.success(request, f'Clinic "{name}" updated successfully.')
        else:
            messages.error(request, 'Clinic name is required.')
    return redirect('manage_clinics')


@siteowner_required
def delete_clinic(request, clinic_id):
    if request.method == 'POST':
        from owners.models import Owner
        clinic = get_object_or_404(Clinic, id=clinic_id)
        name = clinic.name

        # Check if clinic has any associated data
        has_staff = (
            ClinicOwnerProfile.objects.filter(clinic=clinic).exists() or
            DoctorProfile.objects.filter(clinic=clinic).exists() or
            PetshopProfile.objects.filter(clinic=clinic).exists()
        )
        has_owners = Owner.objects.filter(clinic=clinic).exists()

        if has_staff or has_owners:
            messages.error(
                request,
                f'Cannot delete "{name}" — it still has '
                f'associated staff or patient records. '
                f'Remove all staff and data first, or deactivate the clinic instead.'
            )
        else:
            clinic.delete()
            messages.success(request, f'Clinic "{name}" deleted successfully.')
    return redirect('manage_clinics')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Siteowner — Subscription Management
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@siteowner_required
def subscription_history(request):
    from django.utils import timezone
    today = timezone.localdate()

    plans = SubscriptionPlan.objects.all().order_by('days')
    subscriptions = ClinicSubscription.objects.select_related('clinic', 'plan').order_by('end_date')
    clinics_without_sub = Clinic.objects.exclude(
        id__in=subscriptions.values_list('clinic_id', flat=True)
    ).order_by('name')

    # Stats
    active_count = sum(1 for s in subscriptions if s.is_active)
    expired_count = len(subscriptions) - active_count
    expiring_soon = [s for s in subscriptions if s.is_active and s.days_remaining <= 14]

    context = {
        'plans': plans,
        'subscriptions': subscriptions,
        'clinics_without_sub': clinics_without_sub,
        'active_count': active_count,
        'expired_count': expired_count,
        'expiring_soon': expiring_soon,
        'today': today,
    }
    return render(request, 'vetlogin/subscription_history.html', context)


@siteowner_required
def add_subscription_plan(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '').strip()
        days = request.POST.get('days', '').strip()
        if name and price and days:
            try:
                SubscriptionPlan.objects.create(name=name, price=price, days=int(days))
                messages.success(request, f'Plan "{name}" created.')
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'All fields are required.')
    return redirect('subscription_history')


@siteowner_required
def edit_subscription_plan(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '').strip()
        days = request.POST.get('days', '').strip()
        if name and price and days:
            try:
                plan.name = name
                plan.price = price
                plan.days = int(days)
                plan.save()
                messages.success(request, f'Plan "{name}" updated.')
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'All fields are required.')
    return redirect('subscription_history')


@siteowner_required
def delete_subscription_plan(request, plan_id):
    if request.method == 'POST':
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        if plan.subscriptions.exists():
            messages.error(request, f'Cannot delete "{plan.name}" — it is assigned to one or more clinics.')
        else:
            plan.delete()
            messages.success(request, f'Plan "{plan.name}" deleted.')
    return redirect('subscription_history')


@siteowner_required
def assign_subscription(request):
    """Assign or update a clinic's subscription."""
    if request.method == 'POST':
        clinic_id = request.POST.get('clinic_id')
        plan_id = request.POST.get('plan_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None

        clinic = get_object_or_404(Clinic, id=clinic_id)
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        sub, created = ClinicSubscription.objects.get_or_create(clinic=clinic)
        sub.plan = plan
        sub.start_date = start_date
        sub.end_date = end_date  # will auto-calc if None via save()
        sub.save()

        action = 'assigned' if created else 'updated'
        messages.success(request, f'Subscription {action} for "{clinic.name}".')
    return redirect('subscription_history')


@siteowner_required
def revoke_subscription(request, clinic_id):
    if request.method == 'POST':
        sub = get_object_or_404(ClinicSubscription, clinic_id=clinic_id)
        clinic_name = sub.clinic.name
        sub.delete()
        messages.success(request, f'Subscription removed from "{clinic_name}".')
    return redirect('subscription_history')
