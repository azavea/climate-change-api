from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from user_management.models import ClimateUser, UserProfile


# Define an inline admin descriptor for the UserProfile model
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Throttling', {'fields': ('burst_rate', 'sustained_rate')}),
    )
    inlines = (UserProfileInline, )
    ordering = ('email', )
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')


# Overwrite default user settings
admin.site.unregister([Group, ], )
admin.site.register(ClimateUser, UserAdmin, )
