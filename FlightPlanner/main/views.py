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
numpy.set_printoptions(threshold=numpy.nan)


# Solar constants

rad = pi / 180.0
epochStart = datetime(1970, 1, 1)
J1970 = 2440588
J2000 = 2451545
dayMs = 24 * 60 * 60 * 1000
e = rad * 23.4397 # obliquity of the Earth

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
            # return HttpResponse("UTM Zones do not match. Select a smaller region.")
            return render(request, 'main/test.html', {'name':kml_file.name+'.kml'})
    else:
        return render(request, 'main/input_map.html')

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
    t = datetime.now()
    dev = get_projection_north_deviation(heightmap.proj, heightmap.lat,heightmap.lng)
    sunpos = solar_position(t, heightmap.lat, heightmap.lng)
    sun_x = -sin(sunpos['azimuth'] - dev) * cos(sunpos['altitude'])
    sun_y = -cos(sunpos['azimuth'] - dev) * cos(sunpos['altitude'])
    sun_z = sin(sunpos['altitude'])
    shadowmap = ShadowMap(centre_lat, centre_lon, x_resolution, y_resolution, heightmap.size_x, heightmap.size_y, heightmap.proj, pixel_to_km, GSD, x1, y1, x2, y3, sun_x, sun_y, sun_z, heightmap, 1.5)
    render_matrix = shadowmap.render()
    kml_file = KMLFile()
    kml_file.name = str(name_int)
    kml_file.csv_file.name = path
    kml_file.zone_name = zone_name
    kml_file.zone_no = zone_no
    kml_file.save()
    generate_kml(path, kml_file)
    # print heightmap.heights
    print render_matrix
    return kml_file
####################################    Main Functions    ####################################

import csv
import simplekml
import numpy as np

def generate_kml(filename, kml_file):
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
    for row in inputfile:
        # print row[0], row[1]
        lat, lng = utm.to_latlon(float(row[0]), float(row[1]), zone_no, zone_name)
        ls.coords.addcoordinates([(lng, lat, float(row[2]) + 100.00)])  #longitude, latitude
        pnt = fol.newpoint(coords=[(lng,lat, float(row[2]) + 100.00)])
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
    kml_file.file_path.name = kml_path
    kml_file.save()

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

'''
rasterio

import rasterio
import numpy as np
import csv
filename = 'img.tif'
with rasterio.open(filename) as src:
    #read image
    image= src.read()
    # transform image
    bands,rows,cols = np.shape(image)
    image1 = image.reshape (rows*cols,bands)
    print image1
    print(np.shape(image1))
    # bounding box of image
    l,b,r,t = src.bounds
    #resolution of image
    res = src.res
    print 'Resolution: ', res
    print 'Bounds: ', src.bounds
    # meshgrid of X and Y
    x = np.arange(l,r, float((r-l)/rows))
    y = np.arange(t,b, float((b-t)/cols))
    X,Y = np.meshgrid(x,y)
    print (np.shape(X))
    # flatten X and Y
    newX = np.array(X.flatten(1))
    newY = np.array(Y.flatten(1))
    print (np.shape(newX))
    print (np.shape(newY))
    print newX
    print newY
    # join XY and Z information
    export = np.column_stack((newX, newY, image1))
    fname='XYZ.csv'
    with open(fname, 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerows(export)
        fp.close() # close file

'''

