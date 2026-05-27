from django.contrib import admin
from .models import Appointment, Office, StaffOfficeAssignment, StaffRegistrationRequest


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
	list_display = ("name", "created_at")
	search_fields = ("name",)


@admin.register(StaffOfficeAssignment)
class StaffOfficeAssignmentAdmin(admin.ModelAdmin):
	list_display = ("staff", "office", "assigned_at")
	search_fields = ("staff__username", "office__name")
	raw_id_fields = ("staff", "office")


@admin.register(StaffRegistrationRequest)
class StaffRegistrationRequestAdmin(admin.ModelAdmin):
	list_display = ("username", "office", "contact_number", "status", "created_at", "approved_at")
	list_filter = ("status", "office", "created_at")
	search_fields = ("username", "email", "id_number", "contact_number")
	readonly_fields = ("password_hash", "created_at", "updated_at", "approved_at", "rejected_at")
	
	fieldsets = (
		("Personal Information", {
			"fields": ("username", "email", "id_number", "contact_number")
		}),
		("Office Assignment", {
			"fields": ("office",)
		}),
		("Security", {
			"fields": ("password_hash",),
			"classes": ("collapse",)
		}),
		("Status", {
			"fields": ("status", "approved_by", "approved_at", "rejection_reason", "rejected_at")
		}),
		("Timestamps", {
			"fields": ("created_at", "updated_at"),
			"classes": ("collapse",)
		}),
	)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"student",
		"office",
		"service_type",
		"status",
		"payment_status",
		"release_mode",
		"scheduled_at",
		"updated_at",
	)
	list_filter = ("office", "status", "payment_status", "release_mode", "payment_required")
	search_fields = ("student__username", "service_type", "or_number")
	raw_id_fields = ("student", "office")
