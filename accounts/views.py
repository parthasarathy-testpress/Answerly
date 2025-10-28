from django.urls import reverse_lazy
from django.views.generic.edit import FormView,UpdateView
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegisterForm,UserEditForm
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin

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
    html_email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    success_message = "Password reset email sent!"

class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('question_list')
    success_message = "Your profile was updated successfully!"

    def get_object(self, queryset=None):
        return self.request.user
