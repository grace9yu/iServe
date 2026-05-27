from django.conf import settings
from django.db import models


class Office(models.Model):
	REGISTRAR = "registrar"
	GUIDANCE_OFFICE = "guidance_office"
	STUDENT_AFFAIRS = "student_affairs"
	PRODUCTION_OFFICE = "production_office"
	LIBRARY = "library"

	OFFICE_CHOICES = [
		(REGISTRAR, "Registrar"),
		(GUIDANCE_OFFICE, "Guidance Office"),
		(STUDENT_AFFAIRS, "Office of Students Affair and Services"),
		(PRODUCTION_OFFICE, "Production Office"),
		(LIBRARY, "Library"),
	]

	name = models.CharField(max_length=100, choices=OFFICE_CHOICES, unique=True)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.get_name_display()


class StaffOfficeAssignment(models.Model):
	staff = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="office_assignment")
	office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name="staff_members")
	assigned_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.staff.username} - {self.office.get_name_display()}"


class StaffRegistrationRequest(models.Model):
	STATUS_PENDING = "pending"
	STATUS_APPROVED = "approved"
	STATUS_REJECTED = "rejected"

	STATUS_CHOICES = [
		(STATUS_PENDING, "Pending"),
		(STATUS_APPROVED, "Approved"),
		(STATUS_REJECTED, "Rejected"),
	]

	username = models.CharField(max_length=150, unique=True)
	email = models.EmailField()
	password_hash = models.CharField(max_length=255)  # Hash of the password
	office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name="registration_requests")
	id_number = models.CharField(max_length=50, help_text="Employee/Staff ID")
	contact_number = models.CharField(max_length=20, help_text="Contact phone number")
	
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_registrations")
	approved_at = models.DateTimeField(null=True, blank=True)
	rejected_at = models.DateTimeField(null=True, blank=True)
	rejection_reason = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.username} - {self.office.get_name_display()} ({self.get_status_display()})"


class Appointment(models.Model):
	STATUS_PENDING = "pending"
	STATUS_PAYMENT_PENDING = "payment_pending"
	STATUS_PROCESSING = "processing"
	STATUS_DOCUMENT_PREP = "document_preparation"
	STATUS_READY_FOR_RELEASE = "ready_for_release"
	STATUS_COMPLETED = "completed"
	STATUS_INCOMPLETE = "incomplete"
	STATUS_CANCELLED = "cancelled"

	STATUS_CHOICES = [
		(STATUS_PENDING, "Pending"),
		(STATUS_PAYMENT_PENDING, "Awaiting Payment"),
		(STATUS_PROCESSING, "Processing Request"),
		(STATUS_DOCUMENT_PREP, "Document Preparation"),
		(STATUS_READY_FOR_RELEASE, "Ready For Release"),
		(STATUS_COMPLETED, "Completed"),
		(STATUS_INCOMPLETE, "Incomplete Requirements"),
		(STATUS_CANCELLED, "Cancelled"),
	]

	MODE_DIGITAL = "digital"
	MODE_PHYSICAL = "physical"
	RELEASE_MODE_CHOICES = [
		(MODE_DIGITAL, "Digital"),
		(MODE_PHYSICAL, "Physical"),
	]

	PAYMENT_NOT_REQUIRED = "not_required"
	PAYMENT_PENDING = "pending"
	PAYMENT_PAID = "paid"
	PAYMENT_FAILED = "failed"
	PAYMENT_STATUS_CHOICES = [
		(PAYMENT_NOT_REQUIRED, "Not Required"),
		(PAYMENT_PENDING, "Pending"),
		(PAYMENT_PAID, "Paid"),
		(PAYMENT_FAILED, "Failed"),
	]

	student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	office = models.ForeignKey(Office, on_delete=models.SET_NULL, related_name="appointments", null=True, blank=True)
	service_type = models.CharField(max_length=120)
	number_of_copies = models.IntegerField(default=1, help_text="Number of copies needed")
	semester_and_academic_year = models.CharField(max_length=50, blank=True, help_text="e.g., 1st Semester 2023-2024")
	scheduled_at = models.DateTimeField()
	status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
	release_mode = models.CharField(max_length=10, choices=RELEASE_MODE_CHOICES, default=MODE_DIGITAL)
	payment_required = models.BooleanField(default=False)
	payment_status = models.CharField(
		max_length=20,
		choices=PAYMENT_STATUS_CHOICES,
		default=PAYMENT_NOT_REQUIRED,
	)
	or_number = models.CharField(max_length=50, blank=True)
	tracking_note = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	completed_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.student.username} - {self.service_type} ({self.get_status_display()})"

class Notification(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
	message = models.CharField(max_length=255)
	link = models.CharField(max_length=255, blank=True)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.user.username} - {self.message}"

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

@receiver(post_save, sender=Appointment)
def create_appointment_notification(sender, instance, created, **kwargs):
	if created:
		Notification.objects.create(
			user=instance.student,
			message=f"You successfully scheduled an appointment for {instance.service_type}.",
		)
		admins = get_user_model().objects.filter(is_superuser=True)
		for admin in admins:
			Notification.objects.create(
				user=admin,
				message=f"New appointment request from {instance.student.username} for {instance.service_type}."
			)
		if instance.office:
			staffs = get_user_model().objects.filter(office_assignment__office=instance.office)
			for s in staffs:
				Notification.objects.create(
					user=s,
					message=f"New appointment mapped to your office: {instance.service_type}."
				)
	else:
		Notification.objects.create(
			user=instance.student,
			message=f"Your appointment for {instance.service_type} has been updated to {instance.get_status_display()}.",
		)

@receiver(post_save, sender=StaffRegistrationRequest)
def create_staff_reg_notification(sender, instance, created, **kwargs):
	if created:
		admins = get_user_model().objects.filter(is_superuser=True)
		for admin in admins:
			Notification.objects.create(
				user=admin,
				message=f"New staff registration request from {instance.username}."
			)
	else:
		user_qs = get_user_model().objects.filter(username=instance.username)
		if user_qs.exists():
			Notification.objects.create(
				user=user_qs.first(),
				message=f"Your staff registration request has been {instance.get_status_display()}."
			)

