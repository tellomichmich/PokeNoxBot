import json
import time
import io
import random
import sys
import os.path
import base64
import datetime
import PokemonIVCalculator
import math
import fileinput
import traceback
from PIL import Image, ImageOps, ImageDraw, ImageChops, ImageFilter
from math import ceil, radians, cos, sin, asin, sqrt
import re

#Rotate a python list
def rotate_list(l,n):
    return l[-n:] + l[:-n]

def geo_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = sin(dlon/2)**2 + cos(lon1) * cos(lon2) * sin(dlat/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 
    return (c * r)*1000
    
def geo_walk_to(speed, lat1, lon1, alt1, lat2, lon2, alt2):
    new_lat = lat1
    new_lon = lon1
    new_alt = alt1
    
    travel_geo_points = []
    
    dist = geo_distance(lat1, lon1, lat2, lon2)
    steps = (float(dist))/(float(speed))
    if steps >= 1:
        dLat = (lat2 - lat1) / steps
        dLon = (lon2 - lon1) / steps
        dAlt = (alt2 - alt1) / steps
        for i in range(0, int(steps)):
            new_lat = lat1 + (dLat * (i+1))
            new_lon = lon1 + (dLon * (i+1))
            new_alt = alt1 + (dAlt * (i+1))
            #print "%f, %f, %f" % (new_lat, new_lon, new_alt)
            travel_geo_points.append([new_lat, new_lon, new_alt])
    #else:
        #print "%f, %f, %f" % (new_lat, new_lon, new_alt)
    #    travel_geo_points.append([new_lat, new_lon, new_alt])
    return travel_geo_points

def geo_point_from_kml(kml_filename, speed):
    geo_points = []
    f = open(kml_filename)
    for line in f:
        if re.match("[-+]?[0-9]*\.?[0-9]+,[-+]?[0-9]*\.?[0-9]+,[-+]?[0-9]*\.?[0-9]+", line):
            geo_point = line.strip().split(',')
            geo_points.append([float(geo_point[0]), float(geo_point[1]), float(geo_point[2])])
    f.close()

    loop_geo_points = []

    last_geo_point = None
    for cur_geo_point in geo_points:
        if not last_geo_point is None:
            loop_geo_points = loop_geo_points + geo_walk_to(speed, last_geo_point[0], last_geo_point[1], last_geo_point[2], cur_geo_point[0], cur_geo_point[1], cur_geo_point[2])
        last_geo_point = cur_geo_point
    loop_geo_points = loop_geo_points + geo_walk_to(speed, last_geo_point[0], last_geo_point[1], last_geo_point[2], geo_points[0][0], geo_points[0][1], geo_points[0][2])
    return loop_geo_points

def Tap(x, y):
    Command = "bin\\adb.exe shell input tap %d %d" % (x, y)
    os.system(Command)

def Swipe(x1, y1, x2, y2):
    Command = "bin\\adb.exe shell input swipe %d %d %d %d " % (x1, y1, x2, y2)
    os.system(Command)
    
def SwipeTime(x1, y1, x2, y2, t):
    Command = "bin\\adb.exe shell input swipe %d %d %d %d %d" % (x1, y1, x2, y2, t)
    os.system(Command)
    
def KeyEscap():
    Command = "bin\\adb.exe shell input keyevent 4"
    os.system(Command)

def TakePngScreenshot():
    while True:
        try:
            Command = "bin\\adb.exe shell \"screencap -p | busybox base64\""
            PngScreenshotData = os.popen(Command).read()
            PngScreenshotData = base64.b64decode(PngScreenshotData)
            break;
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print "[!] Failed to get screen"
    return PngScreenshotData
 
def IsColorInCeil(ColorToCheck, RefColor, Ceil):
    if (RefColor[0]+(255*Ceil)) > ColorToCheck[0] > (RefColor[0]-(255*Ceil)):
        if (RefColor[1]+(255*Ceil)) > ColorToCheck[1] > (RefColor[1]-(255*Ceil)):
            if (RefColor[2]+(255*Ceil)) > ColorToCheck[2] > (RefColor[2]-(255*Ceil)):
                return True
    return False

def RemoveColor(img, Color, Ceil):
    pixdata = img.load()
    for y in xrange(img.size[1]):
        for x in xrange(img.size[0]):
            if IsColorInCeil(pixdata[x, y], Color, Ceil):
                pixdata[x, y] = (255, 255, 255)
               
def RemoveBlue(img, Limit):
    pixdata = img.load()
    for y in xrange(img.size[1]):
        for x in xrange(img.size[0]):
            if pixdata[x, y][2] > Limit:
                pixdata[x, y] = (255, 255, 255)
                        
def RemoveInSquare(img, x, y, xs, ys):
    pixdata = img.load()
    for yr in xrange(img.size[1]):
        for xr in xrange(img.size[0]):
            if (x+xs >= xr >= x) and (y+ys >= yr >= y):
                pixdata[xr, yr] = (255, 255, 255)
                
def RemoveNotInSquare(img, x, y, xs, ys):
    pixdata = img.load()
    for yr in xrange(img.size[1]):
        for xr in xrange(img.size[0]):
            if not((x+xs >= xr >= x) and (y+ys >= yr >= y)):
                pixdata[xr, yr] = (255, 255, 255)
                
def GetMeanColor(img, x, y, size=10):
    MeanColor = [0, 0, 0]
    pixdata = img.load()
    for xr in range(x-(size/2), x+(size/2)):
        for yr in range(y-(size/2), y+(size/2)):
            MeanColor[0] = MeanColor[0] + pixdata[xr, yr][0]
            MeanColor[1] = MeanColor[1] + pixdata[xr, yr][1]
            MeanColor[2] = MeanColor[2] + pixdata[xr, yr][2]
    MeanColor[0] = MeanColor[0]/(size**2)
    MeanColor[1] = MeanColor[1]/(size**2)
    MeanColor[2] = MeanColor[2]/(size**2)
    return MeanColor

def GetImgFromScreenShot():
    Screenshot = TakePngScreenshot()
    img = Image.open(io.BytesIO(Screenshot))
    img = img.convert("RGB")
    return img
    
def HighContrast(img, Limit=126):
    pixdata1 = img.load()
    for xr in xrange(img.size[0]):
        for yr in xrange(img.size[1]):
            if pixdata1[xr, yr] >= Limit:
                pixdata1[xr, yr] = 255
            else:
                pixdata1[xr, yr] = 0

def OnlyPureWhite(img1):
    pixdata1 = img1.load()
    output = img1.copy()
    pixdataout = output.load()
    for xr in xrange(img1.size[0]):
        for yr in xrange(img1.size[1]):
            if pixdata1[xr, yr] != (255, 255, 255):
                pixdataout[xr, yr] = (255, 255, 255)
            else:
                pixdataout[xr, yr] = (0, 0, 0)
    return output
    
def GetImgFromFile(File):               
    img = Image.open(File)
    img = img.convert("RGB")
    return img
    
#END OF UTILS
    
def BlackOrWhite(img):
    BlackCount = 0.0
    pixdata = img.load()
    for xr in xrange(img.size[0]):
        for yr in xrange(img.size[1]):
            if pixdata[xr, yr] != (255, 255, 255):
               pixdata[xr, yr] = (0, 0, 0)
               BlackCount += 1
    return (BlackCount/(img.size[0]*img.size[1]))*100
    
def RemoveColorList(img, ColorList):
    pixdata = img.load()
    for x in xrange(img.size[0]):
        for y in xrange(img.size[1]):
            if pixdata[x, y] in ColorList:
                pixdata[x, y] = (255, 255, 255)
                
def random_lat_long_delta():
    return ((random.random() * 0.00001) - 0.000005) * 3
    
def ImgToString(img, CharSet=None):
    img.save("tmp\\ocr.png")
    Command = "bin\\tesseract.exe --tessdata-dir bin\\tessdata tmp\\ocr.png tmp\\ocr "
    if CharSet != None:
        Command += "-c tessedit_char_whitelist="+CharSet+" "
    Command += "-psm 7 "
    Command += "> nul 2>&1"
    #print Command
    os.system(Command)
    #TODO: Remove this, as we psm 7
    #Get the largest line in txt
    with open("tmp\\ocr.txt") as f:
        content = f.read().splitlines()
    OutputLine = ""
    for line in content:
        line = line.strip()
        if len(line) > len(OutputLine):
            OutputLine = line
    return OutputLine
    
#Todo: Take a while...
def ZoomOut():
    ZoomOutFix()
    Command = "bin\\adb.exe push bin\\Zoomout.txt /sdcard/Zoomout.txt"
    os.system(Command)
    Command = "bin\\adb.exe shell sh /sdcard/Zoomout.txt"
    os.system(Command)

#Check the correct input
def GetEvent():
    Command = "bin\\adb.exe shell cat /proc/bus/input/devices >tmp\\inputs.log"
    os.system(Command)
    a = 'N: Name="Android Input"'
    line_num = 0
    x = 0
    with open("tmp\\inputs.log") as f:
        content = f.read().splitlines()
        for line in content:
            line_num += 1
            if a in line:
                x = line_num+4
            elif line_num == x:
                result = line.replace(line[:36], '')
                return result

#Change the file whit the correct event number
def ZoomOutFix():
    x = GetEvent()
    array = []
    array.append("#!/bin/sh")
    with open("bin\\Zoomout.txt") as f:
        content = f.read().splitlines()
        for line in content:
            if "event" in line:
                line = re.sub(r"event[0-9]", x, line)
                array.append(line)
    f.close()
    array.append("exit")
    g = open("bin\\Zoomout.txt", 'w')
    g.write("\n".join(array))
    g.close()

def LevenshteinDistance(first, second):
    """Find the Levenshtein distance between two strings."""
    if len(first) > len(second):
        first, second = second, first
    if len(second) == 0:
        return len(first)
    first_length = len(first) + 1
    second_length = len(second) + 1
    distance_matrix = [[0] * second_length for x in range(first_length)]
    for i in range(first_length):
       distance_matrix[i][0] = i
    for j in range(second_length):
       distance_matrix[0][j]=j
    for i in xrange(1, first_length):
        for j in range(1, second_length):
            deletion = distance_matrix[i-1][j] + 1
            insertion = distance_matrix[i][j-1] + 1
            substitution = distance_matrix[i-1][j-1]
            if first[i-1] != second[j-1]:
                substitution += 1
            distance_matrix[i][j] = min(insertion, deletion, substitution)
    return distance_matrix[first_length-1][second_length-1]
    
def ERROR_LOG(String):
    print("\033[0;91m"+"[#] "+String+"\033[00m")
   
def WARNING_LOG(String):
    print("\033[0;93m"+"[!] "+String+"\033[00m")
    
def COOL_LOG(String):
    print("\033[0;92m"+"[*] "+String+"\033[00m")
 
def DEBUG_LOG(String):
    print("\033[0;94m"+"[@] "+String+"\033[00m")
    
def INFO_LOG(String):
    print("[+] "+String)

def WriteAppend(Filename, Content):
    f = open(Filename, "a")
    f.write(Content)
    f.close()

def DiffImgPercent(img1, img2):
    pixdata1 = img1.load()
    pixdata2 = img2.load()
    DiffCount = 0
    for xr in xrange(img1.size[0]):
        for yr in xrange(img1.size[1]):
            if pixdata1[xr, yr] != pixdata2[xr, yr]:
            	DiffCount += 1

    return (DiffCount*1.0) / (img1.size[0]*img1.size[1])
