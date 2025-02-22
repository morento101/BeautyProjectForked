"""Configuration for admin."""

from api.models import (CustomUser, Order, Service, Position,
                        Business, Review, Invitation, Location)
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import (UserAdmin as BaseUserAdmin,
                                       GroupAdmin as BaseGroupAdmin)
from api.forms import CustomUserChangeForm, CustomUserCreationForm


class CustomUserAdmin(BaseUserAdmin):
    """Class for specifing CustomUser fields in admin."""
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ("email", "is_admin", "first_name", "last_name",
                    "phone_number", "is_active", "id")
    list_filter = ("is_admin", "groups")
    fieldsets = (
        (None, {"fields": ("email", "password", "groups")}),
        ("Personal info", {"fields": ("first_name", "last_name", "patronymic",
                                      "phone_number", "bio", "avatar")}),
        ("Permissions", {"fields": ("is_admin", "is_active")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "phone_number", "groups",
                       "avatar", "password1", "password2"),
        }),
    )
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()


class CustomUserInline(admin.TabularInline):
    """Class allows to add CustomUser in Group admin page."""
    model = CustomUser.groups.through
    extra = 1


class CustomGroupAdmin(BaseGroupAdmin):
    """Extends BaseGroupAdmin class adding CustomUserInline class."""
    inlines = [
        CustomUserInline,
    ]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
admin.site.register(Order)
admin.site.register(Service)
admin.site.register(Position)


class BusinessAdmin(admin.ModelAdmin):
    search_fields = ("name", "owner", "type")

    list_display = ("name", "owner", "business_type")
    list_filter = ("is_active",)
    ordering = ("name",)

    fieldsets = (
        ("Required", {
            "fields": (
                ("name", "business_type"),
                "owner",
                "description",
            ),
        }),
        ("Additional", {
            "fields": (
                ("logo", "location",),
                ("working_time", "is_active"),
            )
        })
    )


admin.site.register(Business, BusinessAdmin)
admin.site.register(Review)
admin.site.register(Invitation)
admin.site.register(Location)
