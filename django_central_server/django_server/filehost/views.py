from django.http import FileResponse, HttpResponseForbidden
import os
from django.conf import settings

#ALLOWED_IPS = ['123.123.123.123']  # Replace with your allowed server IP(s)

def download_file(request):
    token = request.GET.get('token') or request.headers.get('Authorization')
    client_ip = request.META.get('REMOTE_ADDR')

    if token != settings.ACCESS_TOKEN: #or client_ip not in ALLOWED_IPS:
        return HttpResponseForbidden("Access denied.")

    file_path = os.path.join(settings.BASE_DIR, 'filehost', 'files', 'my-blocklist.txt')
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='my-blocklist.txt')
