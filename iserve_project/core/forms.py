from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from .models import Appointment, Office, StaffOfficeAssignment, StaffRegistrationRequest


class AppointmentRequestForm(forms.ModelForm):
    service_type = forms.ChoiceField(
        choices=[("", "Select an office first")],
        required=True,
    )

    SERVICE_TYPE_CHOICES = {
        "registrar": [
            ("Transcript of Records", "Transcript of Records"),
            ("Certification Requests", "Certification Requests"),
            ("Document Authentication", "Document Authentication"),
            ("Appointment Scheduling", "Appointment Scheduling"),
            ("Other", "Other"),
        ],
        "guidance_office": [
            ("Counseling", "Counseling"),
            ("Mental Health Support", "Mental Health Support"),
            ("Certificates of Good Moral Character", "Certificates of Good Moral Character"),
            ("Assessment & Profiling", "Assessment & Profiling"),
            ("Application Career & Scholarship Support", "Application Career & Scholarship Support"),
            ("Psychological Exam", "Psychological Exam"),
            ("Exit Form Application", "Exit Form Application"),
        ],
        "student_affairs": [
            ("Student Support", "Student Support"),
            ("Student Records", "Student Records"),
            ("Enrollment Verification", "Enrollment Verification"),
            ("Other", "Other"),
        ],
        "production_office": [
            ("Document Production", "Document Production"),
            ("Printing Request", "Printing Request"),
            ("Other", "Other"),
        ],
        "library": [
            ("Book Reservation", "Book Reservation"),
            ("Library Account Assistance", "Library Account Assistance"),
            ("Other", "Other"),
        ],
    }

    class Meta:
        model = Appointment
        fields = ["office", "service_type", "number_of_copies", "semester_and_academic_year", "scheduled_at", "release_mode", "payment_required"]
        widgets = {
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "number_of_copies": forms.NumberInput(attrs={"type": "number", "min": "1", "max": "100", "value": "1"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service_type"].choices = [("", "Select an office first")]
        office_value = None

        if self.data.get("office"):
            office_value = self.data.get("office")
        elif self.initial.get("office"):
            office_value = self.initial.get("office")
        elif self.instance.pk and self.instance.office:
            office_value = self.instance.office.name

        if office_value:
            if office_value and str(office_value).isdigit():
                office_obj = Office.objects.filter(pk=office_value).first()
                office_value = office_obj.name if office_obj else None
            elif isinstance(office_value, Office):
                office_value = office_value.name

        if office_value:
            choices = self.SERVICE_TYPE_CHOICES.get(office_value, [("Other", "Other")])
            self.fields["service_type"].choices = [("", "Select a service type")] + choices


class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["status", "payment_status", "or_number", "tracking_note", "release_mode"]


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class StaffRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Enter a strong password with at least 8 characters"
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        help_text="Confirm your password"
    )
    email = forms.EmailField(required=True)

    class Meta:
        model = StaffRegistrationRequest
        fields = ("username", "email", "office", "id_number", "contact_number", "password1", "password2")
        labels = {
            "username": "Username",
            "email": "Email Address",
            "office": "Office Assignment",
            "id_number": "Employee/Staff ID",
            "contact_number": "Contact Phone Number",
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        instance.password_hash = make_password(password)
        if commit:
            instance.save()
        return instance

