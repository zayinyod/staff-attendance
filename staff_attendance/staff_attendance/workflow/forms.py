from django import forms
from attendance.models import PaidLeave

class PaidLeaveRequestForm(forms.ModelForm):
    class Meta:
        model = PaidLeave
        fields = ["start_date", "end_date", "reason"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.initialize_fields()

    def initialize_fields(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")
