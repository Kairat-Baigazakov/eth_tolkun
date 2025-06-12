from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Arrival, Rate, RoomLayout, Application, Relative


User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтвердите пароль', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'role')

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
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_active']


class ArrivalForm(forms.ModelForm):
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


class RateForm(forms.ModelForm):
    class Meta:
        model = Rate
        fields = ['name', 'price', 'vat', 'building_type', 'room_layout']


class RoomLayoutForm(forms.ModelForm):
    class Meta:
        model = RoomLayout
        fields = ['name', 'capacity', 'floor', 'building_type']


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            'arrival',         # Выбор заезда
            'guests',          # Список отдыхающих (текстовое поле)
            'rooms',           # Комнаты (текстовое поле)
            'document',        # Файл
        ]
        widgets = {
            'guests': forms.CharField(widget=forms.HiddenInput),
        }


class RelativeForm(forms.ModelForm):
    class Meta:
        model = Relative
        fields = ['user', 'last_name', 'first_name', 'patronymic', 'relation', 'date_of_birth', 'is_employee_child']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


