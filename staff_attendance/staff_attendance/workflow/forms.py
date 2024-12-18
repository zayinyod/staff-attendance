from django import forms
from attendance.models import PaidLeave

class PaidLeaveRequestForm(forms.ModelForm):
    class Meta:
        model = PaidLeave
        fields = ["start_date", "end_date", "reason"]
