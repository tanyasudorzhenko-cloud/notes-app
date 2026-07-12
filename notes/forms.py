from django import forms

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "text", "reminder", "category"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 5}),
            "reminder": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # щоб форма правильно розпізнавала дату/час, які надсилає браузер
        self.fields["reminder"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["reminder"].required = False
