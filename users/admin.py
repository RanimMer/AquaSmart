from django.contrib import admin
from .models import UserProfile, Farm

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "location", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "location", "owner__username", "owner__email")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "farm", "is_active", "created_at")
    list_filter = ("role", "is_active", "farm")
    search_fields = ("user__username", "user__email", "phone", "farm__name")
    autocomplete_fields = ("user", "farm")
