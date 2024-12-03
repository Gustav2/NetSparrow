from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm
from .models import Blacklist, MyBlacklist, CapturedPacket, MySettings
import json
from django.http import JsonResponse
#from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

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
            user = form.save()
            token, created = Token.objects.get_or_create(user=user)
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

def mysettings(request):
    if request.user.is_authenticated:
        settings, created = MySettings.objects.get_or_create(user=request.user)
        return render(request, 'mysettings.html', {'settings': settings})
    return redirect('login')

def update_settings(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            settings, created = MySettings.objects.get_or_create(user=request.user)

            settings.auto_add_blacklist = 'auto_add_blacklist' in request.POST
            settings.log_suspicious_packets = 'log_suspicious_packets' in request.POST
            settings.enable_ip_blocking = 'enable_ip_blocking' in request.POST
            settings.dark_mode = 'dark_mode' in request.POST
            settings.notify_blacklist_updates = 'notify_blacklist_updates' in request.POST
            settings.notify_suspicious_activity = 'notify_suspicious_activity' in request.POST

            settings.save()

            messages.success(request, 'Settings updated successfully')

            return redirect('mysettings')
        return redirect('mysettings')
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

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def settings_myblacklist(request):
    if request.method == 'GET':
        try:
            user = request.user

            myblacklists = MyBlacklist.objects.filter(user=user).values(
                'blacklist_entry__capturedpacket_entry__ip',
                'blacklist_entry__capturedpacket_entry__url'
            )

            return JsonResponse({"myblacklists": list(myblacklists)}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "GET request required."}, status=405)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def packet_capture(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip = data.get('ip')
            url = data.get('url')

            user = request.user

            if not ip and not url:
                return JsonResponse({"error": "IP or URL is required."}, status=400)

            if CapturedPacket.objects.filter(user=user, ip=ip, url=url).exists():
                return JsonResponse({"error": "Duplicate packet for this user."}, status=400)

            captured_packet = CapturedPacket.objects.create(
                user=user,
                ip=ip,
                url=url
            )

            return JsonResponse({"success": "Packet captured successfully.", "id": captured_packet.id}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST request required."}, status=405)

# API view for getting the central blacklist - GET
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def settings_centralblacklist(request):
    if request.method == 'GET':
        try:

            central_blacklist_entries = Blacklist.objects.all().values(
                'capturedpacket_entry__ip',
                'capturedpacket_entry__url'
            )

            return JsonResponse({"central_blacklist": list(central_blacklist_entries)}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "GET request required."}, status=405)


# api; for adding to my blacklist, from existing central blacklist entries - POST
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def settings_add_to_myblacklist(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip = data.get('ip')
            url = data.get('url')

            user = request.user

            if not ip and not url:
                return JsonResponse({"error": "IP or URL is required."}, status=400)

            captured_packets = CapturedPacket.objects.filter(ip=ip, url=url)

            for captured_packet in captured_packets:
                try:
                    blacklist_entry = Blacklist.objects.get(capturedpacket_entry=captured_packet)

                    my_blacklist_entry, created = MyBlacklist.objects.get_or_create(
                        user=user, blacklist_entry=blacklist_entry
                    )

                    if created:
                        return JsonResponse({"success": "Entry added to your MyBlacklist."}, status=200)
                    else:
                        return JsonResponse({"info": "Entry already exists in your MyBlacklist."}, status=200)

                except Blacklist.DoesNotExist:
                    continue

            return JsonResponse({"error": "No matching central blacklist entry found."}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST request required."}, status=405)


# api; for removing from my blacklist - DELETE
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def settings_remove_from_myblacklist(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            ip = data.get('ip')
            url = data.get('url')

            user = request.user

            if not ip and not url:
                return JsonResponse({"error": "IP or URL is required."}, status=400)

            captured_packets = CapturedPacket.objects.filter(ip=ip, url=url)

            for captured_packet in captured_packets:
                try:
                    blacklist_entry = Blacklist.objects.get(capturedpacket_entry=captured_packet)
                    my_blacklist_entry = MyBlacklist.objects.filter(user=user, blacklist_entry=blacklist_entry)

                    if my_blacklist_entry.exists():
                        my_blacklist_entry.delete()
                        return JsonResponse({"success": "Entry removed from your MyBlacklist."}, status=200)
                except Blacklist.DoesNotExist:
                    continue

            return JsonResponse({"error": "Entry not found in your MyBlacklist."}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "DELETE request required."}, status=405)

# api; for updating settings - PUT
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def settings_update(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            user = request.user

            settings, created = MySettings.objects.get_or_create(user=user)

            settings.auto_add_blacklist = data.get('auto_add_blacklist', settings.auto_add_blacklist)
            settings.log_suspicious_packets = data.get('log_suspicious_packets', settings.log_suspicious_packets)
            settings.enable_ip_blocking = data.get('enable_ip_blocking', settings.enable_ip_blocking)
            settings.dark_mode = data.get('dark_mode', settings.dark_mode)
            settings.notify_blacklist_updates = data.get('notify_blacklist_updates', settings.notify_blacklist_updates)
            settings.notify_suspicious_activity = data.get('notify_suspicious_activity', settings.notify_suspicious_activity)
            settings.ml_caution = data.get('mlCaution', settings.ml_caution)
            settings.ml_percentage = data.get('mlPercentage', settings.ml_percentage)

            settings.save()

            return JsonResponse({"success": "Settings updated successfully."}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "PUT request required."}, status=405)

# api; for getting settings - GET
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def settings_get(request):
    if request.method == 'GET':
        try:
            user = request.user

            settings, created = MySettings.objects.get_or_create(user=user)

            return JsonResponse({
                "auto_add_blacklist": settings.auto_add_blacklist,
                "log_suspicious_packets": settings.log_suspicious_packets,
                "enable_ip_blocking": settings.enable_ip_blocking,
                "dark_mode": settings.dark_mode,
                "notify_blacklist_updates": settings.notify_blacklist_updates,
                "notify_suspicious_activity": settings.notify_suspicious_activity,
                "mlPercentage": settings.ml_percentage,
                "mlCaution": settings.ml_caution
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "GET request required."}, status=405)

# api; for getting pi specific settings
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def settings_pi(request):
    if request.method == 'GET':
        try:
            user = request.user

            settings, created = MySettings.objects.get_or_create(user=user)

            return JsonResponse({
                "mlPercentage": settings.ml_percentage,
                "mlCaution": settings.ml_caution
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "GET request required."}, status=405)
