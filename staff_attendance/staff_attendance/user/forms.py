from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from attendance.models import Department

User = get_user_model()

class UserEntryForm(UserCreationForm):
    email = forms.EmailField(
        label="your email",
        required=True,
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label="your department",
        required=True,
        empty_label="select department",
    )

    class Meta:
        model = User
        fields = ["username", "department", "email", "password1", "password2"]
        labels = {
            "username": "your name",
        }

    def __init__(self, *args, **kwargs):
        super(UserEntryForm, self).__init__(*args, **kwargs)

        self.fields["password1"].label = "password"
        self.fields["password2"].label = "password again"
        self.fields["department"].label_from_instance = lambda obj: obj.name

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "input",
                "placeholder": field.label,
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.department = self.cleaned_data["department"]
        if commit:
            user.save()
        return user
