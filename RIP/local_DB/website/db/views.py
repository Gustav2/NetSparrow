from django.shortcuts import render, HttpResponse

# Create your views here.
def home(request):
    return HttpResponse("wauw det virker")

def db(request):
    return HttpResponse("her er en database")

def testplate(request):
    return render(request, 'index.html', {})
