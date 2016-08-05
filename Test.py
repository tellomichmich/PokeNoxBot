# -*- coding: utf-8 -*-

import json
import time

import random
import sys
import os.path
import base64

from PIL import Image

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
    else:
        #print "%f, %f, %f" % (new_lat, new_lon, new_alt)
        travel_geo_points.append([new_lat, new_lon, new_alt])
    return travel_geo_points

def geo_point_from_kml(kml_filename, speed):
    geo_points = []
    f = open(kml_filename)
    for line in f:
        if re.match(".*,.*,.*", line):
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
    Command = "adb shell input tap %d %d" % (x, y)
    os.system(Command)

def Swipe(x1, y1, x2, y2):
    Command = "adb shell input swipe %d %d %d %d " % (x1, y1, x2, y2)
    os.system(Command)
    
def SwipeTime(x1, y1, x2, y2, t):
    Command = "adb shell input swipe %d %d %d %d %d" % (x1, y1, x2, y2, t)
    print Command
    os.system(Command)


def TakePngScreenshot():
    TempPngScreenshot = "TempPngScreenshot"
    Command = "adb shell \"screencap -p | busybox base64\" >  " + TempPngScreenshot
    os.system(Command)
    f = open(TempPngScreenshot, 'rb')
    PngScreenshotData = f.read()
    PngScreenshotData = base64.b64decode(PngScreenshotData)
    f.close()
    os.remove(TempPngScreenshot)
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
                
def GetMeanColor(img, x, y):
    MeanColor = [0, 0, 0]
    pixdata = img.load()
    for xr in range(x-5, x+5):
        for yr in range(y-5, y+5):
            MeanColor[0] = MeanColor[0] + pixdata[xr, yr][0]
            MeanColor[1] = MeanColor[1] + pixdata[xr, yr][1]
            MeanColor[2] = MeanColor[2] + pixdata[xr, yr][2]
            #pixdata[xr, yr] = (0, 0, 255)
    MeanColor[0] = MeanColor[0]/100
    MeanColor[1] = MeanColor[1]/100
    MeanColor[2] = MeanColor[2]/100
    return MeanColor
    
def FindClick(img, x, y, xs, ys):
    pixdata = img.load()
    for xr in range(x, x+xs-10):
        for yr in range(y, y+ys-10):
            MeanColor = GetMeanColor(img, xr, yr)
            if IsColorInCeil(MeanColor, [42, 172, 255], 0.2):
            #if IsColorInCeil(MeanColor, [87, 255, 255], 0.2):
                return [xr+5, yr+5]
    return None

def GetImgFromScreenShot():
    Screenshot = TakePngScreenshot()
    f = open("output.png", 'wb')
    f.write(Screenshot)
    f.close()
               
    img = Image.open("output.png")
    img = img.convert("RGB")
    return img
    
def GetImgFromFile(File):               
    img = Image.open(File)
    img = img.convert("RGB")
    return img
    
def IsOpenPokestop():
    img = GetImgFromScreenShot()
    MeanColor = GetMeanColor(img, 234, 780)
    print MeanColor
    if IsColorInCeil(MeanColor, [31, 164, 255], 0.3):
        return True
    return False
 
def SpinPokestop():
    Swipe(432, 424, 109, 432)
    
def IsSpinnedPokestop():
    img = GetImgFromScreenShot()
    MeanColor = GetMeanColor(img, 234, 780)
    if IsColorInCeil(MeanColor, [140, 100, 240], 0.6):
        return True
    return False
     
def ClosePokestop():
    Tap(236, 736)

def FindPokestop(img):
    ColorBlackList = []
    #Night
    #RemoveColor(img, (104, 137, 177), 0.1)
    #Night Road
    #RemoveColor(img, (44, 78, 123), 0.2)
    #Night Road Border
    #RemoveColor(img, (186, 203, 137), 0.1)
    #RemoveColor(img, (13, 38, 79), 0.1)
    #RemoveColor(img, (69, 134, 101), 0.1)
    #RemoveColor(img, (6, 95, 141), 0.1)
    #RemoveColor(img, (2, 88, 130), 0.1)
    #RemoveColor(img, (54, 161, 157), 0.1)
    #Green
    #RemoveColor(img, (82, 135, 142), 0.1)
    #RemoveColor(img, (76, 162, 188), 0.1)
    #Circle 
    #RemoveColor(img, (154, 132, 204), 0.1)
    #Remove the Player
    #RemoveInSquare(img, 259, 536, 24, 42)
    #RemoveNotInSquare(img, 200-50, 514-50, 137+100, 119+100)
    #Safe values : 165, 455, 110, 100
    ClickPosition = FindClick(img, 165, 455, 110, 100)
    return ClickPosition
    
def BlackOrWhite(img):
    pixdata = img.load()
    for yr in xrange(img.size[1]):
        for xr in xrange(img.size[0]):
            if pixdata[xr, yr] != (255, 255, 255):
               pixdata[xr, yr] = (0, 0, 0)

def FindPokemonPosition(img):
    for xr in range(5, img.size[0]-5):
        for yr in range(5, img.size[1]-5):
            FalsePositiv = GetMeanColor(img, xr, yr)
            Score = (FalsePositiv[0]+FalsePositiv[1]+FalsePositiv[2])/3
            if Score < 60:
                return [xr, yr]
    return None
               
def FindPokemon():
    img = GetImgFromScreenShot()
    ColorBlackList = []
    #Remove the Player
    #RemoveInSquare(img, 259, 536, 24, 42)
    #RemoveNotInSquare(img, 200-50, 514-50, 137+100, 119+100)
    #ClickPosition = FindClick(img, 165, 455, 110, 100)
    Frame = img.crop(((135, 438, 135+200, 438+150)))
    bIsDay = False
    if bIsDay == True:
        #Day Road
        RemoveColor(Frame, (86, 162, 151), 0.1)
        #Day Road Border
        RemoveColor(Frame, (242, 255, 139), 0.1)
        #Day Green    
        RemoveColor(Frame, (153, 255, 140), 0.1)
        RemoveColor(Frame, (161, 249, 170), 0.1)
        RemoveColor(Frame, (109, 255, 110), 0.1)
        #Day Building    
        RemoveColor(Frame, (109, 244, 160), 0.1)
        RemoveColor(Frame, (189, 255, 173), 0.1)
        #Day Building + Road Border
        RemoveColor(Frame, (216, 249, 154), 0.1)
        #Day Parc
        RemoveColor(Frame, (4, 173, 141), 0.3)
        #Day Water
        RemoveColor(Frame, (27, 137, 217), 0.1)
    else:
        #Night Road
        RemoveColor(Frame, (44, 85, 144), 0.1)
        #Night Road + Building
        RemoveColor(Frame, (44, 130, 184), 0.1)
        #Night Road Border
        RemoveColor(Frame, (186, 203, 137), 0.1)
        #Green
        RemoveColor(Frame, (69, 134, 101), 0.1)
        RemoveColor(Frame, (54, 161, 157), 0.1)
        #Green
        RemoveColor(Frame, (82, 135, 142), 0.15)
        #Park
        RemoveColor(Frame, (3, 91, 134), 0.15)
        #Night Building
        RemoveColor(Frame, (103, 146, 203), 0.1)
        #Night Water
        RemoveColor(Frame, (14, 71, 205), 0.1)
        
    
    #PokeStop
    #RemoveColor(Frame, (42, 172, 255), 0.1)
    #RemoveColor(Frame, (87, 255, 255), 0.2)
    #RemoveColor(Frame, (35, 202, 255), 0.1)
    #RemoveColor(Frame, (35, 202, 255), 0.1)
    RemoveColor(Frame, (32, 137, 245), 0.1)
    #PokeStop Circle
    #RemoveColor(Frame, (177, 248, 255), 0.1)
    RemoveBlue(Frame, 254)
    
    #SpinnedPokeStop
    RemoveColor(Frame, (192, 115, 248), 0.1)
    RemoveColor(Frame, (154, 103, 234), 0.1)
  
    #Remove player
    RemoveInSquare(Frame, 91, 44, 23, 37)
    
    #Convert to Black And White
    BlackOrWhite(Frame)
    
    PokemonPosition = FindPokemonPosition(Frame)
    if not PokemonPosition is None:
        PokemonPosition[0] += 135
        PokemonPosition[1] += 438
    Frame.save("OUT.png")
    return PokemonPosition

def ThrowPokeball():
    #Near 200
    SwipeTime(236, 780, 236, 400, 190)

def IsPokemonFightOpen():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    return IsColorInCeil(pixdata[426, 67], (241, 249, 241), 0.01)
 
def IsOnMap():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    return IsColorInCeil(pixdata[237, 703], (255, 57, 69), 0.01)
    
def IsCatchSucess():
    img = GetImgFromScreenShot()
    #img = GetImgFromFile("CatchSuccess.png")
    pixdata = img.load()
    return IsColorInCeil(pixdata[44, 227], (254, 255, 254), 0.01)
    
def CatchPokemon(PokemonPosition):
    print PokemonPosition
    Tap(PokemonPosition[0], PokemonPosition[1])

    bIsPokemonFightOpened = False
    for i in range(0, 10):
        #time.sleep(1)
        if IsPokemonFightOpen() == True:
            bIsPokemonFightOpened = True
            break;
        print "Wait for Pokemon fight..."
    
    if bIsPokemonFightOpened == False:
        return False

    while True:
        time.sleep(1)
        ThrowPokeball()
        time.sleep(1)
        bIsPokemonFightOpened = False
        bIsCatchSuccess = False
        bIsOnMap = False
        while True:
            if IsPokemonFightOpen() == True:
                bIsPokemonFightOpened = True
                break
            if IsCatchSucess() == True:
                bIsCatchSuccess = True
                break
            if IsOnMap() == True:
                bIsOnMap = True
                break
            print "[!] #STRESS..."
        if bIsCatchSuccess == True:
            print "[!] Pokemon captured !"
            break
        if bIsOnMap == True:
            print "[!] Pokemon leaved !"
            return False
    
    Tap(239, 526)
    time.sleep(1)
    Tap(239, 740)
    while IsOnMap() == False:
        print "[!] Waiting return to the map"
    return True
    
    #sys.exit(0)

#Tap(272, 800)
#Swipe(539, 200, 0, 200)
#Tap(490, 128)


#img = GetImgFromFile("CatchSucess.png")
#PokemonPosition = FindPokemon(img)
#PokeStopPosition = FindPokestop(img)
#img = GetImgFromScreenShot()
#print FindPokemon(img)
#img.save("OUT.png")
#print PokemonPosition
#print IsCatchSucess()
#CatchPokemon([376, 512])
#sys.exit(0)

Speed = 10

#pokeball 260 800 260 400 200
loop_geo_points = geo_point_from_kml("Levalois.kml", Speed)

#Searching for the nearest point 
if os.path.isfile("saved_position.txt"):
    f = open("saved_position.txt", 'r')
    line = f.read().strip()
    if re.match(".*,.*,.*", line):
        saved_position = line.split(',')
        saved_position[0] = float(saved_position[0])
        saved_position[1] = float(saved_position[1])
        saved_position[2] = float(saved_position[2])
        min_distance = 99999999
        min_distance_index = 0
        current_index = 0
        for geo_point in loop_geo_points:
            distance_to_saved_point = geo_distance(saved_position[0], saved_position[1], geo_point[1], geo_point[0])
            if distance_to_saved_point < min_distance:
                min_distance_index = current_index
                min_distance = distance_to_saved_point
            current_index += 1
        loop_geo_points = rotate_list(loop_geo_points, (-1 * min_distance_index))
		#Teleport Security

Count = 0
while True:
    for geo_point in loop_geo_points:
        Count += 1
        #Command = "adb shell am startservice -a com.incorporateapps.fakegps.ENGAGE --ef lat %f --ef lng %f --activity-single-top --activity-brought-to-front --activity-brought-to-front --debug-log-resolution" % (geo_point[1], geo_point[0])
        Command = "adb shell gps fix %f %f " % (geo_point[0], geo_point[1])
        #Saved position
        f = open("saved_position.txt", "w")
        f.write("%f,%f,%f" % (geo_point[1], geo_point[0], geo_point[2]))
        f.close()
        os.system(Command)
        if Count%(50/Speed)==0:
            print "[!] Looking around..."
            time.sleep(3)
            print "[!] Looking for Pokestop"
            while True:
                img = GetImgFromScreenShot()
                PokeStopPosition = None
                PokeStopPosition = FindPokestop(img)
                if PokeStopPosition is None:
                    print "[!] No more Pokestop found."
                    break
                    
                print "PokeStopPosition %d %d" % (PokeStopPosition[0], PokeStopPosition[1])
                Tap(PokeStopPosition[0], PokeStopPosition[1])
                bOpenPokestopSuccess = False
                for i in range(0, 5):
                    if IsOpenPokestop() == True:
                        bOpenPokestopSuccess = True
                        break
                    print "Wait for open pokestop"
                    
                if bOpenPokestopSuccess == True:
                    SpinPokestop()
                    while IsSpinnedPokestop() == False:
                        print "Wait for spinned pokestop"
                    ClosePokestop()
                    while IsOnMap() == False:
                        print "[!] Waiting return to the map"
                else:
                    print "Failed to OpenPokestop"
            
            print "[!] Looking for pokemon"
            while True:
                PokemonPosition = FindPokemon()
                if PokemonPosition is None:
                    print "[!] No more Pokemon not found."
                    break
                CatchPokemon(PokemonPosition)