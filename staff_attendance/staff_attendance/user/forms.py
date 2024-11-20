from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .usecases import UserUseCase

User = get_user_model()

class UserEntryForm(UserCreationForm):
    email = forms.EmailField(
        label="email",
        required=True,
    )
    department = forms.ModelChoiceField(
        queryset=UserUseCase.get_all_department_names(),
        label="department",
        required=True,
        empty_label="department",
    )

    class Meta:
        model = User
        fields = ["username", "department", "email", "password1", "password2"]
        labels = {
            "username": "name",
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

    def clean_user_id(self):
        cleaned_data = super().clean()
        user_id = UserUseCase.generate_user_id()
        cleaned_data["user_id"] = user_id
        return cleaned_data
