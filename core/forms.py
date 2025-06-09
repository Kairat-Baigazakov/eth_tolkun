from django import forms
from .models import Application, Relative

class ApplicationForm(forms.ModelForm):
    relatives = forms.ModelMultipleChoiceField(
        queryset=Relative.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Application
        fields = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ApplicationForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['relatives'].queryset = Relative.objects.filter(owner=user.employee)
