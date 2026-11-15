from django import forms
from django.utils import timezone

class MonthSelectForm(forms.Form):
    """
    集計対象の年月を選択するフォーム
    """

    START_YEAR = 2020

    year = forms.ChoiceField(label="Year")
    month = forms.ChoiceField(
        choices=[(month, f"{month:02}") for month in range(1, 13)],
        label="Month",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 年の選択肢はインポート時ではなく生成時に評価する
        self.fields["year"].choices = [
            (year, year) for year in self.selectable_years()
        ]

        for field in self.fields.values():
            field.widget.attrs.update({"class": "input"})

    @classmethod
    def selectable_years(cls) -> range:
        return range(cls.START_YEAR, timezone.localdate().year + 1)
