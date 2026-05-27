from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from .forms import AppointmentRequestForm, AppointmentUpdateForm, StaffRegistrationForm, StudentRegistrationForm
from .models import Appointment, Office, StaffRegistrationRequest, StaffOfficeAssignment


SERVICES = [
    {
        "name": "Transcript of Records",
        "description": "Request official transcript processing with appointment-based release.",
        "release": "Physical or digital release",
    },
    {
        "name": "Certification Requests",
        "description": "Generate enrollment, graduation, and good moral certificates.",
        "release": "Usually same workflow with optional payment",
    },
    {
        "name": "Document Authentication",
        "description": "Submit academic documents for verification and release tracking.",
        "release": "Physical claim or downloadable file",
    },
    {
        "name": "Appointment Scheduling",
        "description": "Choose a release schedule and track request completion in real time.",
        "release": "Aligned to staff processing dashboard",
    },
]


def _dashboard_route(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return "superadmin_dashboard"
    return "admin_dashboard" if user.is_staff else "student_dashboard"


def home(request):
    if request.user.is_authenticated:
        return redirect(_dashboard_route(request.user))
    
    return render(
        request,
        "home.html",
        {
            "services": SERVICES[:3],
            "dashboard_route": _dashboard_route(request.user),
        },
    )


def student_services(request):
    if request.user.is_authenticated:
        return redirect(_dashboard_route(request.user))
        
    return render(
        request,
        "student_services.html",
        {
            "services": SERVICES,
            "dashboard_route": _dashboard_route(request.user),
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect(_dashboard_route(request.user) or "home")

    register_type = request.GET.get("type", None)

    if register_type == "staff":
        form = StaffRegistrationForm(request.POST or None)
        template = "registration/register.html"
        title = "Staff Registration"
        if request.method == "POST" and form.is_valid():
            # Create a registration request instead of directly creating a user
            form.save()
            messages.success(request, "Staff registration request submitted. Please wait for superadmin approval.")
            return redirect("home")
    elif register_type == "student":
        form = StudentRegistrationForm(request.POST or None)
        template = "registration/register.html"
        title = "Student Registration"
        if request.method == "POST" and form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful. Welcome to iServe.")
            return redirect("student_dashboard")
    else:
        form = None
        template = "registration/register.html"
        title = "Register"

    context = {"form": form, "register_type": register_type, "title": title}
    return render(request, template, context)


@login_required
def student_dashboard(request):
    appointments = Appointment.objects.filter(student=request.user)
    context = {
        "appointments": appointments,
        "active_count": appointments.exclude(
            status__in=[Appointment.STATUS_COMPLETED, Appointment.STATUS_CANCELLED]
        ).count(),
        "ready_count": appointments.filter(status=Appointment.STATUS_READY_FOR_RELEASE).count(),
        "payment_pending_count": appointments.filter(
            payment_status=Appointment.PAYMENT_PENDING
        ).count(),
    }
    return render(request, "student_dashboard.html", context)


@login_required
def create_appointment(request):
    form = AppointmentRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        appointment = form.save(commit=False)
        appointment.student = request.user
        if appointment.payment_required:
            appointment.payment_status = Appointment.PAYMENT_PENDING
            appointment.status = Appointment.STATUS_PAYMENT_PENDING
        appointment.save()
        messages.success(request, "Appointment request submitted.")
        return redirect("student_dashboard")
    return render(request, "create_appointment.html", {"form": form})


def _is_staff_user(user):
    return user.is_staff


def _is_superadmin(user):
    return user.is_superuser


@login_required
@user_passes_test(_is_superadmin)
def superadmin_dashboard(request):
    """Superadmin dashboard to manage staff registrations"""
    pending_registrations = StaffRegistrationRequest.objects.filter(status=StaffRegistrationRequest.STATUS_PENDING).order_by("-created_at")
    approved_registrations = StaffRegistrationRequest.objects.filter(status=StaffRegistrationRequest.STATUS_APPROVED).order_by("-approved_at")
    rejected_registrations = StaffRegistrationRequest.objects.filter(status=StaffRegistrationRequest.STATUS_REJECTED).order_by("-rejected_at")
    
    context = {
        "pending_count": pending_registrations.count(),
        "approved_count": approved_registrations.count(),
        "rejected_count": rejected_registrations.count(),
        "pending_registrations": pending_registrations,
        "approved_registrations": approved_registrations,
        "rejected_registrations": rejected_registrations,
    }
    return render(request, "superadmin_dashboard.html", context)


@login_required
@user_passes_test(_is_superadmin)
def approve_staff_registration(request, registration_id):
    """Approve a staff registration request"""
    registration = get_object_or_404(StaffRegistrationRequest, id=registration_id)
    
    if registration.status != StaffRegistrationRequest.STATUS_PENDING:
        messages.warning(request, "This registration has already been processed.")
        return redirect("superadmin_dashboard")
    
    if request.method == "POST":
        # Create the staff user account
        user = User.objects.create_user(
            username=registration.username,
            email=registration.email,
            password=None  # We need to set password after
        )
        user.is_staff = True
        user.save()
        
        # Set the password from the hashed password in the registration request
        user.password = registration.password_hash
        user.save()
        
        # Create office assignment
        StaffOfficeAssignment.objects.create(staff=user, office=registration.office)
        
        # Update registration status
        registration.status = StaffRegistrationRequest.STATUS_APPROVED
        registration.approved_by = request.user
        registration.approved_at = timezone.now()
        registration.save()
        
        messages.success(request, f"Staff account for {registration.username} has been approved and created.")
        return redirect("superadmin_dashboard")
    
    return render(request, "approve_staff_registration.html", {"registration": registration})


@login_required
@user_passes_test(_is_superadmin)
def reject_staff_registration(request, registration_id):
    """Reject a staff registration request"""
    registration = get_object_or_404(StaffRegistrationRequest, id=registration_id)
    
    if registration.status != StaffRegistrationRequest.STATUS_PENDING:
        messages.warning(request, "This registration has already been processed.")
        return redirect("superadmin_dashboard")
    
    if request.method == "POST":
        rejection_reason = request.POST.get("rejection_reason", "")
        if not rejection_reason:
            messages.error(request, "Please provide a reason for rejection.")
            return render(request, "reject_staff_registration.html", {"registration": registration})
        
        registration.status = StaffRegistrationRequest.STATUS_REJECTED
        registration.rejected_at = timezone.now()
        registration.rejection_reason = rejection_reason
        registration.save()
        
        messages.success(request, f"Staff registration for {registration.username} has been rejected.")
        return redirect("superadmin_dashboard")
    
    return render(request, "reject_staff_registration.html", {"registration": registration})



def admin_dashboard(request):
    # Get the staff member's office assignment
    try:
        staff_office = request.user.office_assignment.office
        appointments = Appointment.objects.filter(office=staff_office).select_related("student")
        office_name = staff_office.get_name_display()
    except:
        # If no office assignment, show all (for superusers without assignment)
        appointments = Appointment.objects.select_related("student")
        office_name = "All Offices"
    
    context = {
        "appointments": appointments,
        "total_count": appointments.count(),
        "processing_count": appointments.filter(status=Appointment.STATUS_PROCESSING).count(),
        "ready_count": appointments.filter(status=Appointment.STATUS_READY_FOR_RELEASE).count(),
        "incomplete_count": appointments.filter(status=Appointment.STATUS_INCOMPLETE).count(),
        "office_name": office_name,
    }
    return render(request, "admin_dashboard.html", context)


@login_required
@user_passes_test(_is_staff_user)
def update_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    form = AppointmentUpdateForm(request.POST or None, instance=appointment)

    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)

        if updated.status == Appointment.STATUS_COMPLETED and not updated.completed_at:
            updated.completed_at = timezone.now()

        if updated.payment_status == Appointment.PAYMENT_PAID and updated.status == Appointment.STATUS_PAYMENT_PENDING:
            updated.status = Appointment.STATUS_PROCESSING

        updated.save()
        messages.success(request, f"Appointment #{updated.id} updated.")
        return redirect("admin_dashboard")

    return render(
        request,
        "update_appointment.html",
        {"form": form, "appointment": appointment},
    )