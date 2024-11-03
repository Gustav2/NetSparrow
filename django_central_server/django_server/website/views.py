from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm
from .models import Blacklist, MyBlacklist

def home(request):
    blacklists = Blacklist.objects.all()
    return render(request, 'home.html', {'blacklists': blacklists})

def login_user(request):
    # check if user is authenticated
    if request.method == 'POST':
        email = request.POST['email_address']
        password = request.POST['password']

        # authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in')
            return redirect('home')
        else:
            messages.success(request, 'Invalid username or password')
            return redirect('login')
    else:
        return render(request, 'login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully logged out')
    return redirect('home')

def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # Authenticate and login user
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=email, password=password)
            login(request, user)
            messages.success(request, 'You have successfully registered')
            return redirect('home')
    else:
        form = SignUpForm()
        return render(request, 'register.html', {'form': form})

    return render(request, 'register.html', {'form': form})

def myblacklist(request):
    if request.user.is_authenticated:
        user_blacklists = MyBlacklist.objects.filter(user=request.user)
        return render(request, 'myblacklist.html', {'myblacklists': user_blacklists, 'user': request.user})
    else:
        messages.success(request, 'You need to login to view your blacklist')
        return redirect('login')




#def add_to_my_blacklist(request, blacklist_id):
#    blacklist_entry = get_object_or_404(Blacklist, id=blacklist_id)
#    MyBlacklist.objects.get_or_create(user=request.user, blacklist_entry=blacklist_entry)
#    return redirect('myblacklist')

