from django.urls import path, include
from .views import SignupView,CustomPasswordResetView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('', include('django.contrib.auth.urls')),
]
