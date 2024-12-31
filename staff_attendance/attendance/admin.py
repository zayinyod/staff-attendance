from django.contrib import admin
from .models import (
    CodeMaster,
    Department,
    User,
    Clock,
    PaidLeave,
    ClockCorrect,
    Fare,
    PayPeriod,
)

@admin.register(CodeMaster)
class CodeMasterAdmin(admin.ModelAdmin):
    list_filter = ["code_type"]
    search_fields = ["code_type", "code", "description"]
    ordering = ["code_type", "code"]

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["id"]
admin.site.register(User)

@admin.register(Clock)
class ClockAdmin(admin.ModelAdmin):
    list_filter = ["user", "date_stamp", "clock", "location"]

admin.site.register(PaidLeave)
admin.site.register(ClockCorrect)
admin.site.register(Fare)
admin.site.register(PayPeriod)
