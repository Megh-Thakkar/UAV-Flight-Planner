from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from .models import *
import utm
# Create your views here.

def upload_file(request):
    if request.method == 'POST':
        from django.core.files import File
        try:
            k_file = request.FILES['k_file']
            new_k_file = File(k_file)
            kml_file = KMLFile.objects.create(name=str(KMLFile.objects.count()))
            kml_file.file_path.save('kmlfile{}.kml'.format(kml_file.name), new_k_file)
            return redirect(reverse("main:render_map", kwargs = {"name":kml_file.name}))
        except:
            pass
    return render(request, 'main/upload_file.html')

def render_map(request, name):
    return render(request, 'main/render_map.html', {"name":'kmlfile' + name+'.kml'})

def test(request):
    return render(request, 'main/test.html')

def input_map(request):
    if request.method == 'POST':
        data = request.POST
        if (data['ne_lng'] == '' or data['ne_lat'] == '' or data['sw_lng'] == '' or data['sw_lat'] == ''):
            return redirect("main:input_map")
        ne_lng = float(data['ne_lng'])
        ne_lat = float(data['ne_lat'])
        sw_lng = float(data['sw_lng'])
        sw_lat = float(data['sw_lat'])

        import utm
        NE_UTM = utm.from_latlon(ne_lat, ne_lng)
        SW_UTM = utm.from_latlon(sw_lat, sw_lng)
        print NE_UTM, SW_UTM
        return HttpResponse('Coords printed')
    else:
        return render(request, 'main/input_map.html')

####################################    Main Functions    ####################################

import csv
import simplekml


def get_grid_list(x_resolution, y_resolution, x1, y1, x2, y2, x3, y3, x4, y4, GSD, pixel_to_km=0.00001, img_overlap=0.2):
    coordinates = []
    per_X = GSD * x_resolution * pixel_to_km
    per_Y = GSD * y_resolution * pixel_to_km
    y = y1
    while (y <= y3):
        x = x4
        while (x <= x2):
            coordinates.append({'X':x, 'Y':y})
            x = x - img_overlap + per_X
        y = y - img_overlap + per_Y


def generate_kml(filename):
    inputfile = csv.reader(open('coords.csv','r'))
    kml=simplekml.Kml()
    ls = kml.newlinestring(name="Journey path")

    inputfile.next()
    for row in inputfile:
        ls.coords.addcoordinates([(row[0],row[1],row[2])])
        print row[2]
    ls.extrude = 1
    ls.tessellate = 1
    ls.altitudemode = simplekml.AltitudeMode.absolute
    ls.style.linestyle.color = '7f00ffff'   #aabbggrr
    ls.style.linestyle.width = 4
    ls.style.polystyle.color = '7f00ff00'
    kml.save('fooline.kml')



######################## changes and new fnc ###########
"""given the area of interest we need to divide that in smaller areas and get the center of each area and then using thet estimate
height at which the drone will fly"""
#pixel=0.00001km
coordinates = []
height_change = []
len_no=[]

def get_grid_list(x_resolution, y_resolution, x1, y1, x2, y2, x3, y3, x4, y4, GSD, pixel_to_km=0.00001, img_overlap=0.2):

    per_X = GSD * x_resolution * pixel_to_km
    per_Y = GSD * y_resolution * pixel_to_km
    y = y1

    h_no=1
    while (y <= y3):
        x = x4
        l_no = 0
        while (x <= x2):
            coordinates[i].append({'X':x, 'Y':y})
            x = x - img_overlap + per_X
            l_no+=1
        len_no.append(l_no)
        y = y - img_overlap + per_Y
        #h_no+=1
        height_change.append({'X': x, 'Y': y})
hori_center_main=[]
def hori_center(coordinates=[],len_no=[]):
    center = []
    for j in range(len(len_no)):
        for i in range((len_no[j])-1):
            cen=(coordinates[i]['X']+coordinates[i+1]['X'])/2.0
            center.append({'X':cen,'Y':y})
        hori_center_main.append(center)
verti_center_main=[]
def verti_center(coordinates=[],height_change=[]):
    center=[]
    for i in range(len(height_change)-1):
        for j in range(len(len_no[i])):
            x_cen=coordinates[j+i]['X']+coordinates[j+i+1]['X']/2.0
            y_cen = coordinates[j+i]['Y'] + coordinates[j+i + 1]['Y'] / 2.0
            center.append({'X':x_cen,'Y':y_cen})
    verti_center_main.append(center)





