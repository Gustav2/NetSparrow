from django.shortcuts import render, redirect, get_object_or_404
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

def add_to_my_blacklist(request, blacklist_id):
    blacklist_entry = get_object_or_404(Blacklist, id=blacklist_id)
    MyBlacklist.objects.get_or_create(user=request.user, blacklist_entry=blacklist_entry)
    messages.success(request, 'Entry added to your MyBlacklist')
    return redirect('central_blacklist')

def central_blacklist_view(request):
    central_blacklist = Blacklist.objects.all()
    user_blacklist_ids = MyBlacklist.objects.filter(user=request.user).values_list('blacklist_entry_id', flat=True)
    return render(request, 'central_blacklist.html', {
        'central_blacklist': central_blacklist,
        'user_blacklist_ids': user_blacklist_ids
    })

def remove_from_my_blacklist(request, blacklist_id):
    blacklist_entry = get_object_or_404(Blacklist, id=blacklist_id)
    MyBlacklist.objects.filter(user=request.user, blacklist_entry=blacklist_entry).delete()
    messages.success(request, 'Entry removed from your MyBlacklist')
    return redirect('myblacklist')