from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def is_admin(user):
    return hasattr(user, 'adminprofile')

def is_doctor(user):
    return hasattr(user, 'doctorprofile')

def is_petshop(user):
    return hasattr(user, 'petshopprofile')

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('vetlogin')
        if is_admin(request.user):
            return view_func(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access that page.")
        return redirect('home')
    return _wrapped_view

def doctor_or_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('vetlogin')
        if is_admin(request.user) or is_doctor(request.user):
            return view_func(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access that page.")
        return redirect('home')
    return _wrapped_view
