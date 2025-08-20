from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth import logout
from ..forms import LoginForm

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'login.html'

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'role'):
            if user.role == 'admin':
                return reverse_lazy('admin_dashboard')
            elif user.role == 'moderator':
                return reverse_lazy('moderator_dashboard')
            else:
                return reverse_lazy('user_dashboard')
        else:
            # Роль не задана, направим на user_dashboard или logout
            return reverse_lazy('user_dashboard')


def index(request):
    return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')