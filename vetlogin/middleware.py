from django.shortcuts import redirect


class ClinicMiddleware:
    """
    Injects `request.clinic` and `request.user_role` for every authenticated user.
    - SiteOwnerProfile → request.clinic = None, request.user_role = 'siteowner'
    - ClinicOwnerProfile → request.clinic = profile.clinic, request.user_role = 'clinic_owner'
    - DoctorProfile → request.clinic = profile.clinic, request.user_role = 'doctor'
    - PetshopProfile → request.clinic = profile.clinic, request.user_role = 'petshop'
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.clinic = None
        request.user_role = None

        if request.user.is_authenticated:
            if hasattr(request.user, 'siteownerprofile'):
                request.clinic = None  # Siteowner sees all
                request.user_role = 'siteowner'
            elif hasattr(request.user, 'clinicownerprofile'):
                request.clinic = request.user.clinicownerprofile.clinic
                request.user_role = 'clinic_owner'
            elif hasattr(request.user, 'doctorprofile'):
                request.clinic = request.user.doctorprofile.clinic
                request.user_role = 'doctor'
            elif hasattr(request.user, 'petshopprofile'):
                request.clinic = request.user.petshopprofile.clinic
                request.user_role = 'petshop'
            elif request.user.is_superuser:
                request.user_role = 'superuser'

        response = self.get_response(request)
        return response
