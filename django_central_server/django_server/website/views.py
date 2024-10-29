from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def home(request):
    # check if user is authenticated
    if request.method == 'POST':
        email = request.POST['email_address']
        password = request.POST['password']

        # authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in')
            return redirect('login')
        else:
            messages.success(request, 'Invalid username or password')
            return redirect('login')
    else:
        return render(request, 'home.html', {})

def login_user(request):
    return render(request, 'login.html', {})

def logout_user(request):
    pass
