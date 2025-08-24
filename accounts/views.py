from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import RegisterForm

def signup(request):
  if request.method=='POST':
    forms=RegisterForm(request.POST)
    if forms.is_valid():
      forms.save()
      return render(request,'registration/sucess.html')
  else:
      forms=RegisterForm()
  return render(request,'registration/signup.html',{'form':forms})


def home(request):
  return render(request,'home.html')

