from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from .models import *
from django.conf import settings
import os
from heightmap import *
from pyproj import Proj
from suncalc import solar_position
from datetime import datetime
from shadowmap import ShadowMap, get_projection_north_deviation
from math import sin, cos, tan, asin, atan2, pi
import ephem
import math
from django.core.files import File
# from io import BytesIO
numpy.set_printoptions(threshold=numpy.nan)

# Solar constants
rad = pi / 180.0
epochStart = datetime(1970, 1, 1)
J1970 = 2440588
J2000 = 2451545
dayMs = 24 * 60 * 60 * 1000
e = rad * 23.4397 # obliquity of the Earth

_MONTHNAMES = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Create your views here.
def render_map(request, name):
    return render(request, 'main/render_map.html', {"name":'kmlfile' + name+'.kml'})

def test(request):
    return render(request, 'main/test.html')

def input_map(request):
    if request.method == 'POST':
        import utm
        data = request.POST
        # print data
        if (data['ne_lng'] == '' or data['ne_lat'] == '' or data['sw_lng'] == '' or data['sw_lat'] == ''):
            return redirect("main:input_map")
        ne_lng = float(data['ne_lng'])
        ne_lat = float(data['ne_lat'])
        sw_lng = float(data['sw_lng'])
        sw_lat = float(data['sw_lat'])
        try:
            x_resolution = int(data['x_res'])
            y_resolution = int(data['y_res'])
            GSD = float(data['gsd'])
            pixel_to_km = float(data['pixel_to_km'])
            if (x_resolution == 0 or y_resolution == 0 or GSD == 0 or pixel_to_km == 0):
                raise Exception
        except:
            return render(request, 'main/input_map.html')
        # print ne_lng, sw_lat, ne_lat, sw_lng
        NE_UTM_X, NE_UTM_Y, NE_UTM_ZONE_NO, NE_UTM_NAME = utm.from_latlon(ne_lat, ne_lng)
        SW_UTM_X, SW_UTM_Y, SW_UTM_ZONE_NO, SW_UTM_NAME = utm.from_latlon(sw_lat, sw_lng)
        # print NE_UTM_X, NE_UTM_Y, NE_UTM_ZONE_NO, NE_UTM_NAME
        # print SW_UTM_X, SW_UTM_Y, SW_UTM_ZONE_NO, SW_UTM_NAME
        if(NE_UTM_NAME!=SW_UTM_NAME or NE_UTM_ZONE_NO!=SW_UTM_ZONE_NO):
            return HttpResponse("UTM Zones do not match. Select a smaller region.")
        else:
            kml_file = generate_csv(x_resolution, y_resolution, SW_UTM_X, SW_UTM_Y, NE_UTM_X, NE_UTM_Y,  GSD, NE_UTM_ZONE_NO, NE_UTM_NAME, pixel_to_km)
            try:
                name = kml_file.name
            except:
                return kml_file
            # print kml_file.file_path.url
            kml_url = request.build_absolute_uri(kml_file.file_path.url)
            # print kml_file.name
            # return HttpResponse("UTM Zones do not match. Select a smaller region.")
            return render(request, 'main/test.html', {'kml_file':kml_file, 'kml_url':kml_url})
    else:
        return render(request, 'main/input_map.html')

def download_csv(request, name):
    kml_file = KMLFile.objects.get(name=name)
    response = HttpResponse(kml_file.csv_file, content_type="application/csv")
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % name
    return response

def generate_csv(x_resolution, y_resolution, x1, y1, x2, y3,  GSD, zone_no, zone_name, pixel_to_km):
    import utm
    # print x_resolution, y_resolution, x1, y1, x2, y3,  GSD, zone_no, zone_name
    centres = mesh(x_resolution, y_resolution, x1, y1, x2, y3,  GSD, pixel_to_km)
    # print centres, 'centres'
    line_path = pathline(centres)
    name_int=0
    centre_lat, centre_lon = utm.to_latlon((x1+x2)/2, (y1+y3)/2, zone_no, zone_name)
    while(1):
        try:
            temp_file = KMLFile.objects.get(name=str(name_int))
            name_int += 1
            # print name_int
            continue
        except:
            break
    path = os.path.join(settings.MEDIA_ROOT, 'csv', 'csv' + str(name_int) + '.csv')
    # print path
    proj = Proj(proj='utm', zone=zone_no, ellps='WGS84')
    elevation_dir = os.path.join(settings.MEDIA_ROOT, 'hgt')
    heightmap = SrtmHeightMap(centre_lat, centre_lon, 
                    x_resolution, y_resolution, proj, pixel_to_km, GSD, x1, y1, x2, y3,elevation_dir)
    csvfile = open(str(path), "w+b")
    filewriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['X', 'Y', 'Elevation'])
    tiles = {}
    for i in range(0, len(line_path)):
        lat, lng = utm.to_latlon((line_path[i]['X']), (line_path[i]['Y']), zone_no, zone_name)
        tile_key = SrtmHeightMap._tileKey(lat, lng)
        if not tiles.has_key(tile_key):
            try:
                tiles[tile_key] = SrtmHeightMap._loadTile(heightmap.data_dir, lat, lng)
            except:
                return HttpResponse("HGT data does not exist. Please copy %s file in the media/hgt folder."%(SrtmHeightMap._tileKey(lat, lng)))
            # print 'Loaded tile', tile_key
        v = tiles[tile_key].getAltitudeFromLatLon(lat, lng)
        # print line_path[i]['X'], line_path[i]['Y']
        filewriter.writerow([str(line_path[i]['X']), str(line_path[i]['Y']), v])   # , str(get_elevation(utm.to_latlon((line_path[i]['X']), (line_path[i]['Y']), zone_no, zone_name)))
    csvfile.close()
    # t = datetime.now()
    # print t
    dev = get_projection_north_deviation(heightmap.proj, heightmap.lat,heightmap.lng)
    gatech = ephem.Observer()
    gatech.lon, gatech.lat = '%.2f'%heightmap.lng, '%.2f'%heightmap.lat
    # month_index = _MONTHNAMES.index(t.strftime("%b"))
    # gatech.date = "%s/%02d/%s %s:%s:%s"%(t.strftime("%Y"), month_index, t.strftime("%d"), t.strftime("%H"), t.strftime("%M"), t.strftime("%S"))
    # print gatech.date
    # gatech.date = '2018/7/9 06:00:00'
    # print gatech.date
    sun = ephem.Sun()
    # print gatech.date, heightmap.lng, heightmap.lat
    # print gatech.lon, gatech.lat
    sun.compute(gatech)
    # print("%s %s" % (sun.alt, sun.az))
    azimuth = sun.az
    altitude = sun.alt
    sunpos = {
        'azimuth' : degree_to_rad(azimuth),
        'altitude' : degree_to_rad(altitude)
    }
    sun_x = -sin(sunpos['azimuth'] - dev) * cos(sunpos['altitude'])
    sun_y = -cos(sunpos['azimuth'] - dev) * cos(sunpos['altitude'])
    sun_z = sin(sunpos['altitude'])
    shadowmap = ShadowMap(centre_lat, centre_lon, x_resolution, y_resolution, heightmap.size_x, heightmap.size_y, heightmap.proj, pixel_to_km, GSD, x1, y1, x2, y3, sun_x, sun_y, sun_z, heightmap, 1.5)
    render_matrix = shadowmap.render()
    print render_matrix
    # print shadowmap.size_y, shadowmap.size_x
    # struct_time = time.strptime("30 Nov 00", "%d %b %y")
    #print render_matrix
    s = ephem.Sun()
    s.compute()
    o = ephem.Observer()
    o.lat = '%0.2f'%heightmap.lat
    o.lon = '%0.2f'%heightmap.lng
    # print o.lat, o.lon
    # print 'O', o.date
    # print render_matrix
    render_matrix=rever(render_matrix, shadowmap) 
    # print o.next_rising(s), o.previous_setting(s)
    next_rising = ephem_to_datetime(o.next_rising(s))
    previous_setting = ephem_to_datetime(o.previous_setting(s))
    current_time = ephem_to_datetime(o.date)
    # print previous_setting, current_time, next_rising
    # if next_rising.day == previous_setting.day: # Sun is set
    #     for i in xrange(0, len(render_matrix)):
    #         render_matrix[i] = 0
    kml_file = KMLFile()
    kml_file.name = str(name_int)
    f = open(path)
    kml_file.csv_file.save(str(kml_file.name)+'.csv', File(f))
    # kml_file.file_path.name = kml_path
    kml_file.save()
    kml_file.zone_name = zone_name
    kml_file.zone_no = zone_no
    kml_file.save()
    print '######################'
    # print len(centres) == len(render_matrix)
    generate_kml(path, kml_file, render_matrix)
    # print heightmap.heights
    # print render_matrix
    # print len(render_matrix) == shadowmap.size_x * shadowmap.size_y
    return kml_file

def degree_to_rad(degrees):
    degree_str = str(degrees).split(':')
    return math.radians(float(degree_str[0]) + float(degree_str[1])/60 + float(degree_str[2])/3600)

def ephem_to_datetime(ephem_date):
    ephem_date_list = str(ephem_date).split('/')
    ephem_date_list[1] = _MONTHNAMES[int(ephem_date_list[1])]
    ephem_date = '/'.join(ephem_date_list)
    return datetime.strptime(str(ephem_date), "%Y/%b/%d %H:%M:%S")
####################################    Main Functions    ####################################

import csv
import simplekml
import numpy as np

def generate_kml(filename, kml_file, render_matrix):
    import utm
    # print filename
    inputfile = csv.reader(open(filename,'r'))
    kml=simplekml.Kml()
    ls = kml.newlinestring(name="Journey path")
    fol = kml.newfolder(name="Points")
    zone_no = kml_file.zone_no
    zone_name = kml_file.zone_name
    header = inputfile.next()
    i = 1
    prev_val = None
    for row in inputfile:
        # print row[0], row[1]
        lat, lng = utm.to_latlon(float(row[0]), float(row[1]), zone_no, zone_name)
        try:
            ls.coords.addcoordinates([(lng, lat, float(row[2]) + 100.00)])  #longitude, latitude
            prev_val = float(row[2])
            if render_matrix[i] != 0:
                pnt = fol.newpoint(coords=[(lng,lat, float(row[2]) + 100.00)])
                pnt.style.iconstyle.color = simplekml.Color.red
                pnt.style.iconstyle.scale = 0.05
        except:
            ls.coords.addcoordinates([(lng, lat, float(prev_val) + 100.00)])
            if render_matrix[i] != 0:
                pnt = fol.newpoint(coords=[(lng,lat, float(prev_val) + 100.00)])
                pnt.style.iconstyle.color = simplekml.Color.red
                pnt.style.iconstyle.scale = 0.05
        i += 1
        # print row[2]
    ls.extrude = 1
    ls.tessellate = 1
    ls.altitudemode = simplekml.AltitudeMode.absolute
    ls.style.linestyle.color = '7f00ffff'   #aabbggrr
    ls.style.linestyle.width = 4
    ls.style.polystyle.color = '7f00ff00'
    kml_path = os.path.join(settings.MEDIA_ROOT, 'files', str(kml_file.name)+'.kml')
    kml.save(kml_path)
    f = open(kml_path)
    kml_file.file_path.save(str(kml_file.name)+'.kml', File(f))
    kml_file.save()
    os.remove(kml_path)

# def get_elevation(lat, lng):
#     import urllib, json
#     response = urllib.urlopen("https://maps.googleapis.com/maps/api/elevation/json?locations=" + str(lat) + "," +
#                             str(lng) + "&key=AIzaSyDTJkkx8M1hzY3OpG-lL66LmoBYoZRKMBg")
#     return float(json.load(response)["results"][0]["elevation"])

def mesh(x_resolution, y_resolution, x1, y1, x2, y3, GSD, pixel_to_km):

    centres = []
    per_X = GSD * x_resolution * pixel_to_km                        ### x3,y3-------x4,y4
    per_Y = GSD * y_resolution * pixel_to_km                        #    |            |
    # print x_resolution, y_resolution, x1, y1, x2, y3, GSD, pixel_to_km
    lx = np.linspace(x1, x2, int((x2 - x1) / per_X))                 #    |            |
    # print per_X
    ly = np.linspace(y1, y3, int((y3 - y1) / per_Y))                 ### x1,y1-------x2,y2
    kx, ky = np.meshgrid(lx, ly)
    # print kx, ky
    for i in range(0, len(kx) - 1):
        y = (ky[i][0] + ky[i + 1][0]) / 2.00
        for j in range(0, len(kx[i]) - 1):
            centre = (kx[i][j] + kx[i][j + 1]) / 2.00
            centres.append({'X': centre, 'Y': y})
    # print 'meshgrid', centres
    # print len(lx), len(ly)
    # print len(kx[0]), len(kx)
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


def rever(render_matrix, shadowmap):
    # lineno=0
    rev=[]
    path=[]
    # print shadowmap.size_x, shadowmap.size_y
    for i in range(0,shadowmap.size_y):
        if(i%2==0):
            path += render_matrix[i][:shadowmap.size_x].tolist()
        else:
            li=render_matrix[i][:shadowmap.size_x]
            li=li.tolist()
            li.reverse()
            path = path + li
    return path