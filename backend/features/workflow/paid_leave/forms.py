from django import forms
from attendance.models import PaidLeave

class PaidLeaveRequestForm(forms.ModelForm):
    class Meta:
        model = PaidLeave

        fields = ["start_date", "end_date", "reason"]
        labels = {
            "start_date": "start date",
            "end_date": "end date",
            "reason": "provide the reason if necessary.",
        }
        widgets = {
            "start_date": forms.NumberInput(attrs={"type": "date"}),
            "end_date": forms.NumberInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.initialize_fields()

    def initialize_fields(self):
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "input",
                "placeholder": field.label,
            })
