from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def WebProView(request):
    return render(request, 'webpro/index.html')