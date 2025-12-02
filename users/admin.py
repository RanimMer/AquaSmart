from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from .models import UserProfile, Farm

admin.site.unregister(Group)

class UserGroupInline(admin.TabularInline):
    model = User.groups.through          # M2M "User <-> Group"
    extra = 0
    verbose_name = "Utilisateur"
    verbose_name_plural = "Utilisateurs dans ce groupe"
    autocomplete_fields = ('user',)

@admin.register(Group)
class CustomGroupAdmin(BaseGroupAdmin):
    inlines = [UserGroupInline]
    list_display = ('name', 'get_users')

    def get_users(self, obj):
        return ", ".join(u.username for u in obj.user_set.all()) or "—"
    get_users.short_description = "Utilisateurs"

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
