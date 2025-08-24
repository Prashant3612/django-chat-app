from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('', views.signup, name='signup'),
    path('login',auth_views.LoginView.as_view(template_name='registration/login.html'),name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name="registration/success_logout.html"), name='logout'),

    
    # path('home/', views.home, name='home'),
    # path('login/',views.login,name='login')
    # other routes...
]