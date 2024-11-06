from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm
from .models import Blacklist, MyBlacklist, CapturedPacket
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

def home(request):
    blacklists = Blacklist.objects.all()
    return render(request, 'home.html', {'blacklists': blacklists})

def login_user(request):
    if request.method == 'POST':
        email = request.POST['email_address']
        password = request.POST['password']

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

def myblacklist_view(request):
    if request.user.is_authenticated:
        myblacklists = MyBlacklist.objects.filter(user=request.user)
        return render(request, 'myblacklist.html', {'myblacklists': myblacklists})
    else:
        return redirect('login')

def add_to_my_blacklist(request, blacklist_id):
    if request.user.is_authenticated:
        blacklist_entry = get_object_or_404(Blacklist, id=blacklist_id)
        my_blacklist_entry, created = MyBlacklist.objects.get_or_create(
            user=request.user, blacklist_entry=blacklist_entry
        )
        if created:
            messages.success(request, 'Entry added to your MyBlacklist.')
        else:
            messages.info(request, 'This entry is already in your MyBlacklist.')
    else:
        messages.error(request, 'You need to be logged in to add entries to your MyBlacklist.')

    return redirect('central_blacklist')


def central_blacklist_view(request):
    if request.user.is_authenticated:
        central_blacklist = Blacklist.objects.all()
        user_blacklist_ids = MyBlacklist.objects.filter(user=request.user).values_list('blacklist_entry_id', flat=True)
        all_added = all(blacklist.id in user_blacklist_ids for blacklist in central_blacklist)
        return render(request, 'central_blacklist.html', {
            'central_blacklist': central_blacklist,
            'user_blacklist_ids': user_blacklist_ids, 
            'all_added': all_added,
        })
    else:
        messages.error(request, 'You need to login to view the central blacklist')
        return redirect('login')


def remove_from_my_blacklist(request, blacklist_id):
    if request.user.is_authenticated:
        blacklist_entry = get_object_or_404(Blacklist, id=blacklist_id)
        MyBlacklist.objects.filter(user=request.user, blacklist_entry=blacklist_entry).delete()
        messages.success(request, 'Entry removed from your MyBlacklist')
    else:
        messages.error(request, 'You need to be logged in to remove entries from your MyBlacklist.')
    
    return redirect('myblacklist')


def add_all_to_my_blacklist(request):
    if request.user.is_authenticated:
        all_blacklists = Blacklist.objects.all()
        for blacklist_entry in all_blacklists:
            MyBlacklist.objects.get_or_create(user=request.user, blacklist_entry=blacklist_entry)

        messages.success(request, 'All entries have been added to your MyBlacklist.')
    else:
        messages.error(request, 'You need to be logged in to add entries to your MyBlacklist.')
    
    return redirect('central_blacklist')

def remove_all_from_my_blacklist(request):
    if request.user.is_authenticated:
        MyBlacklist.objects.filter(user=request.user).delete()
        messages.success(request, 'All entries have been removed from your MyBlacklist.')
    else:
        messages.error(request, 'You need to be logged in to remove entries from your MyBlacklist.')
    
    return redirect('myblacklist')

def settings_myblacklist(request):
    if request.method == 'GET':
        try:
            user_id = request.GET.get('user_id')
            user = User.objects.get(id=user_id)

            myblacklists = MyBlacklist.objects.filter(user=user).values('blacklist_entry__ip', 'blacklist_entry__url')

            return JsonResponse({"myblacklists": list(myblacklists)}, status=200)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "GET request required."}, status=405)

@csrf_exempt  # Disable CSRF for this endpoint
def packet_capture(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ip = data.get('ip')
            url = data.get('url')
            user_id = data.get('user_id')
            
            if not ip and not url:
                return JsonResponse({"error": "IP or URL is required."}, status=400)

            user = User.objects.get(id=user_id) if user_id else None

            captured_packet = CapturedPacket.objects.create(
                user=user,
                ip=ip,
                url=url
            )

            return JsonResponse({"success": "Packet captured successfully.", "id": captured_packet.id}, status=201)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "POST request required."}, status=405)
        
            