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
#pixel=0.00001km
coordinates = []
height_change = []
len_no=[]


def get_grid_list(x_resolution, y_resolution, x1, y1, x2, y2, x3, y3, x4, y4, GSD, pixel_to_km=0.001, img_overlap=0.2):

    per_X = GSD * x_resolution * pixel_to_km
    per_Y = GSD * y_resolution * pixel_to_km
    y = y1

    h_no=1
    while (y <= y3):
        x = x4
        l_no = 0
        x_prev=x
        while (x <= x2):
            coordinates.append({'X':x, 'Y':y})
            x_prev=x
            x = x - img_overlap + per_X
            l_no+=1
        len_no.append(l_no)
        y_prev=y
        y = y - img_overlap + per_Y
        #h_no+=1
        height_change.append({'X': x_prev,'Y': y_prev})
hori_center_main=[]

def hori_center(coordinates=[],len_no=[],height_change=[]):
	#print height_change,len_no
	for j in range(len(height_change)):
		center = []
		for i in range((len_no[j])-1):
			cen=(coordinates[i]['X']+coordinates[i+1]['X'])/2.0
			#print cen
			center.append({'X':cen,'Y':height_change[j]['Y']})
		hori_center_main.append(center)
verti_center_main=[]
def verti_center(coordinates=[],height_change=[],len_no=[]):
	for i in range(len(height_change)-1):
		center=[]
		for j in range(len_no[i]):		
			#x_cen=coordinates[j+i]['X']+coordinates[j+i+1]['X']/2.0
			y_cen = (coordinates[i]['Y'] + coordinates[i+1]['Y']) / 2.0
			center.append({'X':coordinates[j]['X'],'Y':y_cen})
		verti_center_main.append(center)
elevat_centers=[]
def intersection(verti_center_main=[],hori_center_main=[]):	
	lines1=[]
	lines2=[]
	from sympy.geometry import Point, Line,intersection
	for i in range(len(hori_center_main)-1):
		for j in range(len(hori_center_main[i])):
			p1=Point(hori_center_main[i][j]['X'],hori_center_main[i][j]['Y'])
			p2=Point(hori_center_main[i+1][j]['X'],hori_center_main[i+1][j]['Y'])
			print p1
			l1=Line(p1,p2)
			lines1.append(l1)
	print len(lines1)
	for i in range(len(verti_center_main)-1):
		for j in range(len(verti_center_main[i])):
			p3=Point(verti_center_main[i][j]['X'],verti_center_main[i][j]['Y'])
			p4=Point(verti_center_main[i+1][j]['X'],verti_center_main[i+1][j]['Y'])
			l2=Line(p3,p4)
			lines2.append(l2)
	print(len(lines2))
	for i in range(len(lines1)):
		p=intersection(lines1[i], lines2[i])
		elevat_centers.append(p)			



get_grid_list(1000,1000,0,0,10,0,10,20,0,20,5)

hori_center(coordinates,len_no,height_change)
verti_center(coordinates,height_change,len_no)
print verti_center_main,"\n"
print len(verti_center_main),"\n"
print len(hori_center_main),"\n"
print hori_center_main,"\n"
intersection(verti_center_main,hori_center_main)
print elevat_centers,"\n"


