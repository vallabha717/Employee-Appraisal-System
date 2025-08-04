from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'department']
    list_filter = ['role', 'department', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'department', 'employee_id', 'phone', 'hire_date', 'manager')}),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']