from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    
    class Meta(UserCreationForm.Meta): # type: ignore
        model = User
        fields = ('username', 'email')
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

class UserEditForm(forms.ModelForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if user_qs.exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email
