from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth.forms import PasswordResetForm
from django.views import View
from django.shortcuts import render, redirect
from django.conf import settings

class SignupView(FormView):
    template_name = 'accounts/signup.html'
    form_class = UserRegisterForm
    success_url = '/'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Account created for {user.username}!')
        return super().form_valid(form)

class CustomPasswordResetView(View):
    template_name = 'registration/password_reset_form.html'

    def get(self, request):
        form = PasswordResetForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name='registration/password_reset_email.txt',
                html_email_template_name='registration/password_reset_email.html',
            )
            messages.success(request, "Password reset email sent!")
            return redirect(reverse_lazy('password_reset_done'))
        return render(request, self.template_name, {'form': form})
