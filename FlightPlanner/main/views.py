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


def generate_kml(filename, zone_no, zone_name):
    import utm
    inputfile = csv.reader(open(filename,'r'))
    kml=simplekml.Kml()
    ls = kml.newlinestring(name="Journey path")

    inputfile.next()
    for row in inputfile:
        lat, lng = utm.to_latlon(row[0], row[1], zone_no, zone_name)
        ls.coords.addcoordinates([(lng, lat, row[2])])  #longitude, latitude
        print row[2]
    ls.extrude = 1
    ls.tessellate = 1
    ls.altitudemode = simplekml.AltitudeMode.absolute
    ls.style.linestyle.color = '7f00ffff'   #aabbggrr
    ls.style.linestyle.width = 4
    ls.style.polystyle.color = '7f00ff00'
    kml.save('fooline.kml')



######################## changes and new fnc ###########

def get_elevation(lat, lng):
    import urllib, json
    response = urllib.urlopen("https://maps.googleapis.com/maps/api/elevation/json?locations=" + str(lat) + "," +
                            str(lng) + "&key=AIzaSyDTJkkx8M1hzY3OpG-lL66LmoBYoZRKMBg")
    return float(json.load(response)["results"][0]["elevation"])


centres = []
import numpy as np


def mesh(x_resolution, y_resolution, x1, y1, x2, y2, x3, y3, x4, y4, GSD, pixel_to_km=0.00001):
    per_X = GSD * x_resolution * pixel_to_km
    per_Y = GSD * y_resolution * pixel_to_km
    lx = np.linspace(0, x2, int((x2 - x1) / per_X))
    ly = np.linspace(0, y3, int((y3 - y1) / per_Y))
    kx, ky = np.meshgrid(lx, ly)

    for i in range(0, len(kx) - 1):
        y = (ky[i][0] + ky[i + 1][0]) / 2.00
        for j in range(0, len(kx[i]) - 1):
            centre = (kx[i][j] + kx[i][j + 1]) / 2.00
            centres.append({'X': centre, 'Y': y})


def pathline(centres=[]):
    path = []
    lineno = 0
    rev = []
    for i in range(0, len(centres) - 1):
        if ((float(centres[i]['Y']) == float(centres[i + 1]['Y'])) and lineno % 2 == 0):
            path.append(centres[i])

        elif ((float(centres[i]['Y']) == float(centres[i + 1]['Y'])) and lineno % 2 == 1):
            rev.append(centres[i])
        else:
            if (lineno % 2 == 0):
                path.append(centres[i])
            if (lineno % 2 == 1):
                rev.append(centres[i])
                # print rev, lineno
                rev.reverse()
                path = path + rev
                del (rev)
                rev = []
            lineno += 1
    return path


import csv


def cfile(centres=[]):
    with open('points.csv', 'wb') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow('X', 'Y')
        for i in range(0, len(centres)):
            filewriter.writerow([str(centres[i]['X']), str(centres[i]['Y'])])


"""mesh(1000, 1000, 0, 0, 1, 0, 1, 2, 0, 2, 5)
path = pathline(centres)
cfile(centres)
# for i in range(0,len(path)):
#	print path[i],"\n"
"""


