from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Arrival, Rate, RoomLayout, Application, Relative


User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Подтвердите пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    birthdate = forms.DateField(
        label='Дата рождения', required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'last_name', 'first_name', 'patronymic',
            'position', 'birthdate', 'role'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Пароли не совпадают')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class UserEditForm(forms.ModelForm):
    birthdate = forms.DateField(
        label='Дата рождения', required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        )
    )
    class Meta:
        model = User
        fields = [
            'username', 'email', 'last_name', 'first_name', 'patronymic',
            'position', 'birthdate', 'role', 'is_active'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Эта строка — гарантирует что дата будет в ISO формате
        if self.instance and self.instance.birthdate:
            self.fields['birthdate'].initial = self.instance.birthdate.strftime('%Y-%m-%d')


class ArrivalForm(forms.ModelForm):

    application_start = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M'
        )
    )

    application_end = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M'
        )
    )

    class Meta:
        model = Arrival
        fields = [
            'name', 'status', 'start_date', 'end_date',
            'application_start', 'application_end', 'rate'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'application_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'application_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['application_start', 'application_end']:
            if self.instance and getattr(self.instance, f):
                self.fields[f].initial = getattr(self.instance, f).strftime('%Y-%m-%dT%H:%M')


class RateForm(forms.ModelForm):
    class Meta:
        model = Rate
        fields = ['name', 'price', 'vat', 'building_type', 'room_layout']


class RoomLayoutForm(forms.ModelForm):
    class Meta:
        model = RoomLayout
        fields = ['name', 'capacity', 'floor', 'building_type']


class ApplicationForm(forms.ModelForm):
    guests = forms.CharField(widget=forms.HiddenInput)
    class Meta:
        model = Application
        fields = [
            'arrival',         # Выбор заезда
            'guests',          # Список отдыхающих (текстовое поле)
            'rooms',           # Комнаты (текстовое поле)
            'document',        # Файл
        ]


class RelativeForm(forms.ModelForm):
    birthdate = forms.DateField(
        label='Дата рождения',
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d'
        ),
        required=True
    )

    class Meta:
        model = Relative
        fields = [
            'user', 'last_name', 'first_name', 'patronymic',
            'relation', 'birthdate', 'is_employee_child'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'relation': forms.TextInput(attrs={'class': 'form-control'}),
            'is_employee_child': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Гарантируем, что дата рождения корректно выводится для редактирования
        if self.instance and self.instance.birthdate:
            self.fields['birthdate'].initial = self.instance.birthdate.strftime('%Y-%m-%d')


