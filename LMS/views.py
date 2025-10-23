from django.shortcuts import render
from django.http import HttpResponse

def About(request):
    return render(request, 'about.html')