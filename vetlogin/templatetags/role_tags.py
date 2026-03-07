from django import template

register = template.Library()

@register.filter
def is_siteowner(user):
    return hasattr(user, 'siteownerprofile')

@register.filter
def is_clinic_owner(user):
    return hasattr(user, 'clinicownerprofile')

# Backward-compatible alias
@register.filter
def is_admin(user):
    return hasattr(user, 'clinicownerprofile')

@register.filter
def is_doctor(user):
    return hasattr(user, 'doctorprofile')

@register.filter
def is_petshop(user):
    return hasattr(user, 'petshopprofile')

@register.filter
def profile_name(user):
    """Returns the name from the user's profile."""
    if not user.is_authenticated:
        return user.username
        
    try:
        if hasattr(user, 'siteownerprofile'):
            return user.siteownerprofile.name
        elif hasattr(user, 'clinicownerprofile'):
            return user.clinicownerprofile.name
        elif hasattr(user, 'doctorprofile'):
            return user.doctorprofile.name
        elif hasattr(user, 'petshopprofile'):
            return user.petshopprofile.name
    except Exception:
        pass
        
    return user.username

@register.filter
def user_role_display(user):
    """Returns a human-readable role label."""
    if not user.is_authenticated:
        return 'Unknown'
    if hasattr(user, 'siteownerprofile'):
        return 'Site Owner'
    if hasattr(user, 'clinicownerprofile'):
        return 'Clinic Owner'
    if hasattr(user, 'doctorprofile'):
        return 'Doctor'
    if hasattr(user, 'petshopprofile'):
        return 'Petshop'
    return 'SuperUser'
