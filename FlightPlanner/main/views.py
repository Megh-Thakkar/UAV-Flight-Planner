from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from .models import *
# Create your views here.

def upload_file(request):
    if request.method == 'POST':
        from django.core.files import File
        # try:
        k_file = request.FILES['k_file']
        new_k_file = File(k_file)
        kml_file = KMLFile.objects.create(name=str(KMLFile.objects.count()))
        kml_file.file_path.save('kmlfile{}.kml'.format(kml_file.name), new_k_file)
        return redirect(reverse("main:render_map", kwargs = {"name":kml_file.name}))
        # except:
        #     pass
    return render(request, 'main/upload_file.html')

def render_map(request, name):
    return render(request, 'main/render_map.html', {"name":'kmlfile' + name+'.kml'})