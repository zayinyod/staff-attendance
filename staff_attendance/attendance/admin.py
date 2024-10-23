from django.contrib import admin
from .models import Department, User, Clock

class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["id"]

admin.site.register(Department, DepartmentAdmin)
admin.site.register(User)
admin.site.register(Clock)
