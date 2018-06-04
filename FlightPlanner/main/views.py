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

####################################    Main Functions    ####################################

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


import geocoding_for_kml.py
import csv
import xml.dom.minidom
import sys


def extractAddress(row):
    return '%s,%s,%s,%s,%s' % (row['placemark_number'], row['latitude'],
                               row['longitude'], row['zone'], row['computed_elevation'])


def createKML(csvReader, fileName, order):
    # This constructs the KML document from the CSV file.
    kmlDoc = xml.dom.minidom.Document()
    kmlElement = kmlDoc.createElementNS('http://earth.google.com/kml/2.2 ', 'kml')  # url to be added
    kmlElement.setAttribute('xmlns', 'http://earth.google.com/kml/2.2')  # uurl to be added
    kmlElement = kmlDoc.appendChild(kmlElement)
    documentElement = kmlDoc.createElement('Document')
    documentElement = kmlElement.appendChild(documentElement)

    csvReader.next()
    for row in csvReader:
        placemarkElement = createPlacemark(kmlDoc, row, num)
        documentElement.appendChild(placemarkElement)
    kmlFile = open(fileName, 'w')
    kmlFile.write(kmlDoc.toprettyxml('  ', newl='\n', encoding='utf-8'))


def createPlacemark(kmlDoc, row, num):
    placemarkElement = kmlDoc.createElement('Placemark')
    extElement = kmlDoc.createElement('ExtendedData')
    placemarkElement.appendChild(extElement)
    for key in num:
        if row[key]:
            dataElement = kmlDoc.createElement('Data')
            dataElement.setAttribute('name', key)
            valueElement = kmlDoc.createElement('value')
            dataElement.appendChild(valueElement)
            valueText = kmlDoc.createTextNode(row[key])
            valueElement.appendChild(valueText)
            extElement.appendChild(dataElement)

    pointElement = kmlDoc.createElement('Point')
    placemarkElement.appendChild(pointElement)
    coordinates = geocoding_for_kml.geocode(extractAddress(row))
    coorElement = kmlDoc.createElement('coordinates')
    coorElement.appendChild(kmlDoc.createTextNode(coordinates))
    pointElement.appendChild(coorElement)
    return placemarkElement



######################## changes and new fnc ###########
centres=[]
import numpy as np
def mesh(x_resolution,y_resolution,x1,y1,x2,y2,x3,y3,x4,y4,GSD,pixel_to_km=0.00001):
	per_X=GSD*x_resolution*pixel_to_km
	per_Y=GSD*y_resolution*pixel_to_km
	lx=np.linspace(0,x2,int((x2-x1)/per_X))
	ly=np.linspace(0,y3,int((y3-y1)/per_Y))
	kx,ky=np.meshgrid(lx,ly)

	for i in range(0,len(kx)-1):
		y=(ky[i][0]+ky[i+1][0])/2.00
		for j in range(0,len(kx[i])-1):
			centre=(kx[i][j]+kx[i][j+1])/2.00
			centres.append({'X':centre,'Y':y})
			

def pathline(centres=[]):
	path=[]
	lineno=0
	rev = []
	for i in range(0,len(centres)-1):
		if((float(centres[i]['Y'])==float(centres[i+1]['Y'])) and lineno%2==0):
			path.append(centres[i])
		
		elif ((float(centres[i]['Y'])==float(centres[i+1]['Y'])) and lineno%2==1) :
			rev.append(centres[i])
		else:
			if(lineno%2==0):
				path.append(centres[i])
			if(lineno%2==1):
				rev.append(centres[i])
				#print rev, lineno
				rev.reverse()
				path=path + rev
				del(rev)
				rev = []
			lineno+=1
	return path

			

mesh(1000,1000,0,0,1,0,1,2,0,2,5)
path=pathline(centres)
for i in range(0,len(path)):
	print path[i],"\n"
