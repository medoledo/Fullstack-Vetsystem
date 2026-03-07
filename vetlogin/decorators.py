from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def is_siteowner(user):
    return hasattr(user, 'siteownerprofile')


def is_clinic_owner(user):
    return hasattr(user, 'clinicownerprofile')


# Backward-compatible alias
def is_admin(user):
    return is_clinic_owner(user)


def is_doctor(user):
    return hasattr(user, 'doctorprofile')


def is_petshop(user):
    return hasattr(user, 'petshopprofile')


def get_user_role(user):
    """Return the role string for a user."""
    if is_siteowner(user):
        return 'siteowner'
    if is_clinic_owner(user):
        return 'clinic_owner'
    if is_doctor(user):
        return 'doctor'
    if is_petshop(user):
        return 'petshop'
    return None


def siteowner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('vetlogin')
        if is_siteowner(request.user):
            return view_func(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access that page.")
        return redirect('home')
    return _wrapped_view


def clinic_owner_required(view_func):
    """Allows Clinic Owners and Site Owners."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('vetlogin')
        if is_siteowner(request.user) or is_clinic_owner(request.user):
            return view_func(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access that page.")
        return redirect('home')
    return _wrapped_view


# Backward-compatible alias
admin_required = clinic_owner_required


def doctor_or_clinic_owner_required(view_func):
    """Allows Doctors, Clinic Owners, and Site Owners."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('vetlogin')
        if is_siteowner(request.user) or is_clinic_owner(request.user) or is_doctor(request.user):
            return view_func(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access that page.")
        return redirect('home')
    return _wrapped_view


# Backward-compatible alias
doctor_or_admin_required = doctor_or_clinic_owner_required
