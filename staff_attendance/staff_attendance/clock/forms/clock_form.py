from django import forms
from django.forms import ModelForm
from attendance.models import Clock
from decimal import Decimal
from ..usecases import ClockEntry

class ClockForm(ModelForm):
    clock_status = ClockEntry.clock_repository
    to_in = clock_status.to_in
    to_out = clock_status.to_out

    class Meta:
        STEP_NUMBER = "0.25"
        model = Clock

        fields = ["date_stamp", "time_stamp", "clock", "break_time", "location"]
        labels = {
            "date_stamp": "date",
            "time_stamp": "time",
            "clock": "in/out",
            "break_time": "break time",
            "location": "location",
        }
        widgets = {
            "date_stamp": forms.NumberInput(attrs={"type": "date"}),
            "time_stamp": forms.NumberInput(attrs={"type": "time"}),
            "break_time": forms.NumberInput(attrs={
                "step": STEP_NUMBER,
                "min": "0.00",
                "max": "24.00",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["clock"].label_from_instance = lambda obj: obj.description
        self.fields["location"].label_from_instance = lambda obj: obj.description

        self.initialize_fields()

    def initialize_fields(self):
        if self.user:
            break_time, location, has_in_record = ClockEntry.get_in_breaktime_and_location(self.user)
            self.fields["clock"].initial = self.to_out if has_in_record else self.to_in
            if has_in_record:
                self.fields["break_time"].initial = break_time
                self.fields["location"].initial = location

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "input",
                "placeholder": field.label,
            })

    def clean_break_time(self):
        break_time = self.cleaned_data.get("break_time")

        if break_time % Decimal(self.Meta.STEP_NUMBER) != 0:
            raise forms.ValidationError("`Break time` must be in increments of 0.25.")
        return break_time
