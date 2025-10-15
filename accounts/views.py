from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegisterForm

class SignupView(FormView):
    template_name = 'accounts/signup.html'
    form_class = UserRegisterForm
    success_url = '/'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Account created for {user.username}!')
        return super().form_valid(form)
