from django import template

register = template.Library()

@register.filter
def is_admin(user):
    return hasattr(user, 'adminprofile')

@register.filter
def is_doctor(user):
    return hasattr(user, 'doctorprofile')

@register.filter
def is_petshop(user):
    return hasattr(user, 'petshopprofile')

@register.filter
def profile_name(user):
    """Returns the name from the user's profile (Admin, Doctor, or Petshop)"""
    if not user.is_authenticated:
        return user.username
        
    try:
        # Check all possible profile types
        if hasattr(user, 'adminprofile'):
            return user.adminprofile.name
        elif hasattr(user, 'doctorprofile'):
            return user.doctorprofile.name
        elif hasattr(user, 'petshopprofile'):
            return user.petshopprofile.name
    except Exception:
        pass
        
    return user.username
