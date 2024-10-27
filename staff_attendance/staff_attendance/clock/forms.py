from django import forms
from django.forms import ModelForm
from attendance.models import Clock
from decimal import Decimal

class ClockForm(ModelForm):
    class Meta:
        model = Clock
        fields = ["user", "date_stamp", "time_stamp", "clock", "break_time", "location"]
        labels = {
            "user": "user",
            "date_stamp": "date",
            "time_stamp": "time",
            "clock": "in/out",
            "break_time": "breaktime",
            "location": "location",
        }
        widgets = {
            "break_time": forms.NumberInput(attrs={
                "placeholder": "break time",
                "step": "0.25",
                "min": "0.00",
                "max": "24.00",
            }),
        }

    def __init__(self, *args, **kwargs):
        super(ClockForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "input",
            })

    def clean_break_time(self):
        break_time = self.cleaned_data.get("break_time")
        if break_time % Decimal("0.25") != 0:
            raise forms.ValidationError("Enter in units of 0.25.")
        return break_time
