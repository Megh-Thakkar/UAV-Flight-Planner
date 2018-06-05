from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from .models import *
from django.conf import settings
import os
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
        import utm
        data = request.POST
        if (data['ne_lng'] == '' or data['ne_lat'] == '' or data['sw_lng'] == '' or data['sw_lat'] == ''):
            return redirect("main:input_map")
        ne_lng = float(data['ne_lng'])
        ne_lat = float(data['ne_lat'])
        sw_lng = float(data['sw_lng'])
        sw_lat = float(data['sw_lat'])
        x_resolution = int(data['x_res'])
        y_resolution = int(data['y_res'])
        GSD = float(data['gsd'])
        NE_UTM_X, NE_UTM_Y, NE_UTM_ZONE_NO, NE_UTM_NAME = utm.from_latlon(ne_lat, ne_lng)
        SW_UTM_X, SW_UTM_Y, SW_UTM_ZONE_NO, SW_UTM_NAME = utm.from_latlon(sw_lat, sw_lng)
        if(NE_UTM_NAME!=SW_UTM_NAME or NE_UTM_ZONE_NO!=SW_UTM_ZONE_NO):
            return HttpResponse("UTM Zones do not match. Select a smaller region.")
        else:
            return redirect(reverse("main:generate_csv", kwargs={"x_resolution":x_resolution, "y_resolution":y_resolution, "x1":NE_UTM_X, "y1":NE_UTM_Y, "x2":SW_UTM_X, "y3":SW_UTM_Y, "GSD":GSD, "zone_no":NE_UTM_ZONE_NO, "zone_name":NE_UTM_NAME}))
    else:
        return render(request, 'main/input_map.html')

def generate_csv(request, x_resolution, y_resolution, x1, y1, x2, y3,  GSD, zone_no, zone_name):
    line_path = pathline(mesh(x_resolution, y_resolution, x1, y1, x2, y3,  GSD, pixel_to_km=0.00001))
    i=0
    while(KMLFile.objects.get(name=i)):
        i += 1
    path = os.path.join(settings.MEDIA_ROOT, 'csv', str(i)+'.csv')
    with open(path, 'wb') as csvfile:
        csvfile.truncate()
        filewriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow('X', 'Y')
        for i in range(0, len(line_path)):
            filewriter.writerow([str(line_path[i]['X']), str(line_path[i]['Y'])])
    kml_file = KMLFile()
    kml_file.name = str(i)
    kml_file.csv_file.name = path
    kml_file.zone_name = zone_name
    kml_file.zone_no = zone_no
    kml_file.save()
    generate_kml(path, kml_file)
    return render(request, 'main/test.html', {'name':kml_file+'.kml'})
####################################    Main Functions    ####################################

import csv
import simplekml
import numpy as np

def generate_kml(filename, kml_file):
    import utm
    inputfile = csv.reader(open(filename,'r'))
    kml=simplekml.Kml()
    ls = kml.newlinestring(name="Journey path")
    zone_no = kml_file.zone_no
    zone_name = kml_file.zone_name
    inputfile.next()
    for row in inputfile:
        lat, lng = utm.to_latlon(row[0], row[1], zone_no, zone_name)
        ls.coords.addcoordinates([(lng, lat, get_elevation(lat, lng))])  #longitude, latitude
        # print row[2]
    ls.extrude = 1
    ls.tessellate = 1
    ls.altitudemode = simplekml.AltitudeMode.absolute
    ls.style.linestyle.color = '7f00ffff'   #aabbggrr
    ls.style.linestyle.width = 4
    ls.style.polystyle.color = '7f00ff00'
    kml_path = os.path.join(settings.MEDIA_ROOT, 'files', str(kml_file.name)+'.kml')
    kml.save(kml_path)
    kml_file.file_path.name = kml_path
    kml_file.save()

def get_elevation(lat, lng):
    import urllib, json
    response = urllib.urlopen("https://maps.googleapis.com/maps/api/elevation/json?locations=" + str(lat) + "," +
                            str(lng) + "&key=AIzaSyDTJkkx8M1hzY3OpG-lL66LmoBYoZRKMBg")
    return float(json.load(response)["results"][0]["elevation"])

def mesh(x_resolution, y_resolution, x1, y1, x2, y3, GSD, pixel_to_km=0.00001):
    centres = []
    per_X = GSD * x_resolution * pixel_to_km                        ### x3,y3-------x4,y4
    per_Y = GSD * y_resolution * pixel_to_km                        #    |            |
    lx = np.linspace(0, x2, int((x2 - x1) / per_X))                 #    |            |
    ly = np.linspace(0, y3, int((y3 - y1) / per_Y))                 ### x1,y1-------x2,y2
    kx, ky = np.meshgrid(lx, ly)

    for i in range(0, len(kx) - 1):
        y = (ky[i][0] + ky[i + 1][0]) / 2.00
        for j in range(0, len(kx[i]) - 1):
            centre = (kx[i][j] + kx[i][j + 1]) / 2.00
            centres.append({'X': centre, 'Y': y})

    return centres

def pathline(centres):
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

"""centres = mesh(1000, 1000, 0, 0, 1, 0, 1, 2, 0, 2, 5)
path = pathline(centres)
cfile(centres)
# for i in range(0,len(path)):
#	print path[i],"\n"
"""


