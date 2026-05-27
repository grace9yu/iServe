from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import StaffOfficeAssignment

User = get_user_model()


class StaffApprovalBackend(ModelBackend):
    """
    Custom authentication backend that ensures approved staff can log in
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user and user.is_staff:
            # Check if staff member is approved
            try:
                StaffOfficeAssignment.objects.get(staff=user)
            except StaffOfficeAssignment.DoesNotExist:
                # Staff is not approved yet
                return None
        
        return user
