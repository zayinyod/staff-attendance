from django import forms
from django.forms import ModelForm
from attendance.models import Clock
from decimal import Decimal
from .usecases import ClockUseCase

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
        super(ClockForm, self).__init__(*args, **kwargs)

        if self.user:
            break_time, location, has_in_record = ClockUseCase.get_in_breaktime_and_location(self.user)

            if has_in_record:
                self.fields["clock"].initial = "OUT"
                if break_time is not None:
                    self.fields["break_time"].initial = break_time
                if location is not None:
                    self.fields["location"].initial = location
            else:
                self.fields["clock"].initial = "IN"

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "input",
            })

    def clean_break_time(self):
        break_time = self.cleaned_data.get("break_time")
        if break_time % Decimal("0.25") != 0:
            raise forms.ValidationError("Enter in units of 0.25.")
        return break_time
