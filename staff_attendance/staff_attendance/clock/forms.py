from django import forms
from django.forms import ModelForm
from attendance.models import Clock
from decimal import Decimal
from .usecases import ClockEntry

class ClockForm(ModelForm):
    class Meta:
        model = Clock
        fields = ["date_stamp", "time_stamp", "clock", "break_time", "location"]
        labels = {
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
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.initialize_fields()

    def initialize_fields(self):
        if self.user:
            break_time, location, has_in_record = ClockEntry.get_in_breaktime_and_location(self.user)
            self.fields["clock"].initial = "OUT" if has_in_record else "IN"
            if has_in_record:
                self.fields["break_time"].initial = break_time
                self.fields["location"].initial = location

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")

    def clean_break_time(self):
        break_time = self.cleaned_data.get("break_time")
        if break_time % Decimal("0.25") != 0:
            raise forms.ValidationError("Break time must be in increments of 0.25.")
        return break_time
