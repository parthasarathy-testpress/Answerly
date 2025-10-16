from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin

class SignupView(FormView):
    template_name = 'accounts/signup.html'
    form_class = UserRegisterForm
    success_url = '/'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Account created for {user.username}!')
        return super().form_valid(form)

class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    success_message = "Password reset email sent!"
