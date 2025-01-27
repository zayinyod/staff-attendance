from django import forms
from datetime import date

class DashboardForm(forms.Form):
    year = forms.ChoiceField(
        choices=[(y, y) for y in range(2020, date.today().year + 1)],
        label="Year",
    )
    month = forms.ChoiceField(
        choices=[(m, f"{m:02}") for m in range(1, 13)],
        label="Month",
    )
