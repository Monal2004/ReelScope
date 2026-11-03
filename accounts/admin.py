from django.contrib import admin

from .models import EmailVerification


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "expires_at", "used_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["token", "created_at", "expires_at", "used_at"]
