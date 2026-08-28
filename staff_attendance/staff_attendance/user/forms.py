from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .usecases import UserUseCase

class UserEntryForm(UserCreationForm):
    user_usecase = UserUseCase()

    email = forms.EmailField(
        label="email",
        required=True,
    )
    department = forms.ModelChoiceField(
        queryset=user_usecase.get_all_department_names(),
        label="department",
        required=True,
        empty_label="Select department",
    )

    class Meta:
        model = get_user_model()
        fields = ["username", "department", "email", "password1", "password2"]
        labels = {"username": "name"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].label = "password"
        self.fields["password2"].label = "password again"
        self.fields["department"].label_from_instance = lambda obj: obj.name

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "input",
                "placeholder": field.label,
            })
