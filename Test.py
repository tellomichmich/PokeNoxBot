# -*- coding: utf-8 -*-

import json
import time
import io

import random
import sys
import os.path
import base64
import datetime

from PIL import Image

from math import ceil, radians, cos, sin, asin, sqrt
import re

assert sys.version_info >= (2,7)
assert sys.version_info < (3,0)


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
    Command = "adb shell input tap %d %d" % (x, y)
    os.system(Command)

def Swipe(x1, y1, x2, y2):
    Command = "adb shell input swipe %d %d %d %d " % (x1, y1, x2, y2)
    os.system(Command)
    
def SwipeTime(x1, y1, x2, y2, t):
    Command = "adb shell input swipe %d %d %d %d %d" % (x1, y1, x2, y2, t)
    os.system(Command)

def TakePngScreenshot():
    while True:
        try:
            Command = "adb shell \"screencap -p | busybox base64\""
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
    
def GetImgFromFile(File):               
    img = Image.open(File)
    img = img.convert("RGB")
    return img
    
def IsOpenPokestop():
    img = GetImgFromScreenShot()
    MeanColor = GetMeanColor(img, 234, 780)
    #print MeanColor
    if IsColorInCeil(MeanColor, [31, 164, 255], 0.3):
        return True
    return False
 
def SpinPokestop():
    Swipe(432, 424, 109, 432)
    time.sleep(0.2)
    
def IsSpinnedPokestop():
    img = GetImgFromScreenShot()
    MeanColor = GetMeanColor(img, 234, 780)
    if MeanColor[0] > 80 and MeanColor[1] > 80:
        return True
    # if IsColorInCeil(MeanColor, [140, 100, 240], 0.1):
        # return True
    # if IsColorInCeil(MeanColor, [184, 116, 249], 0.1):
        # return True
    # if IsColorInCeil(MeanColor, [211, 116, 249], 0.1):
        # return True
    return False
     
def ClosePokestop():
    Tap(236, 736)
    time.sleep(0.7)

def CloseGym():
    Tap(236, 736)
    time.sleep(0.2)
    
#TODO !
def ReturnToMap():
    if IsOnMap() == False:
        #This is shit !
        if IsPokemonFightOpen():
            ClosePokemonFight()
            return True
        if IsOpenPokestop():
            ClosePokestop()
            return True
        if IsSpinnedPokestop():
            ClosePokestop()
            return True
        if IsGymOpen():
            CloseGym()
            return True
        if IsPokeBoxFull():
            #Close the pop-up
            Tap(345, 419)
            time.sleep(0.5)
            TransfertPokemon(10)
            return True
        if IsPokestopTooFar():
            ClosePokestop()
            return True
        print "[!] Don't know where we are.... Exiting"
        sys.exit(0)
    return True
    
def FindPokestop():
    ReturnToMap();    
    img = GetImgFromScreenShot()
    pixdata = img.load()
    x, y, xs, ys = (188, 456, 128, 130)
    SquareSize = 10
    for xr in range(x+(SquareSize/2), x+xs-(SquareSize/2)):
        for yr in range(y+(SquareSize/2), y+ys-(SquareSize/2)):
            MeanColor = GetMeanColor(img, xr, yr, SquareSize)
            #if IsColorInCeil(MeanColor, [42, 172, 255], 0.15):
            #    return [xr+(SquareSize/2), yr+(SquareSize/2)]
            if IsColorInCeil(MeanColor, [87, 255, 255], 0.05):
                return [xr+(SquareSize/2), yr+(SquareSize/2)]
            if IsColorInCeil(MeanColor, [64, 227, 252], 0.15):
                return [xr+(SquareSize/2), yr+(SquareSize/2)]
    #img.save("OUT_POKESTOP.png")
    #sys.exit(0)
    return None
    
def BlackOrWhite(img):
    BlackCount = 0.0
    pixdata = img.load()
    for xr in xrange(img.size[0]):
        for yr in xrange(img.size[1]):
            if pixdata[xr, yr] != (255, 255, 255):
               pixdata[xr, yr] = (0, 0, 0)
               BlackCount += 1
    return (BlackCount/(img.size[0]*img.size[1]))*100

def FindPokemonPosition(img):
    SquareSize = 7
    for xr in range(SquareSize/2, img.size[0]-(SquareSize/2)):
        for yr in range(SquareSize/2, img.size[1]-(SquareSize/2)):
            FalsePositiv = GetMeanColor(img, xr, yr, SquareSize)
            Score = (FalsePositiv[0]+FalsePositiv[1]+FalsePositiv[2])/3
            if Score < 2:
                return [xr, yr]
    return None
    
def IsDay():
    Hour = datetime.datetime.now().hour  
    if Hour > 7 and Hour < 19:
        return True
    return False
    
def FindPokemon():
    ReturnToMap(); 
    #img = GetImgFromFile("output.png")
    img = GetImgFromScreenShot()
    Frame = img.crop(((135, 438, 135+200, 438+150)))
    if IsDay() == True:
        #Day Road
        RemoveColor(Frame, (86, 162, 151), 0.1)
        #Day Road Border
        RemoveColor(Frame, (242, 255, 139), 0.1)
        #Day Green    
        RemoveColor(Frame, (153, 255, 140), 0.1)
        RemoveColor(Frame, (161, 249, 170), 0.1)
        RemoveColor(Frame, (109, 255, 110), 0.1)
        RemoveColor(Frame, (118, 239, 186), 0.1)
        RemoveColor(Frame, (140, 255, 111), 0.1)
        RemoveColor(Frame, (150, 242, 198), 0.1)
        #Day Building    
        RemoveColor(Frame, (109, 244, 160), 0.1)
        RemoveColor(Frame, (189, 255, 173), 0.1)
        RemoveColor(Frame, (82, 240, 161), 0.1)
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
        RemoveColor(Frame, (18, 130, 174), 0.1)
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
    RemoveColor(Frame, (102, 87, 217), 0.1)
    #SpinnedPokeStop foot
    RemoveColor(Frame, (205, 186, 254), 0.1)
  
    #Remove player
    RemoveInSquare(Frame, 91, 44, 23, 37)
    
    #Convert to Black And White
    Frame.save("OUT_COLOR.png")
    BlackRatio = BlackOrWhite(Frame)
    #print BlackRatio
    if BlackRatio > 14:
        #Too many information on screen !
        print "[!] Too many information on map..."
        return False
    PokemonPosition = FindPokemonPosition(Frame)
    if not PokemonPosition is None:
        PokemonPosition[0] += 135
        PokemonPosition[1] += 438
    Frame.save("OUT.png")
    return PokemonPosition

def ThrowPokeball(Power):
    #Far 100
    #Near 400
    print "[!] Throw a Pokeball (%d)" % (100+Power)
    SwipeTime(236, 780, 236, 100+Power, 200)

def IsPokemonFightOpen():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    return IsColorInCeil(pixdata[426, 67], (241, 249, 241), 0.01)
 
def IsGymOpen():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    #White part of the "plateau"
    if IsColorInCeil(pixdata[403, 560], (255, 255, 255), 0.01) == False:
        return False
    #Close cross
    if IsColorInCeil(pixdata[240, 740], (34, 136, 153), 0.01) == False:
        return False
    return True
    
    
def IsOnMap():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    return IsColorInCeil(pixdata[237, 703], (255, 57, 69), 0.01)
    
def IsCatchSucess():
    img = GetImgFromScreenShot()
    #img = GetImgFromFile("CatchSuccess.png")
    pixdata = img.load()
    if IsColorInCeil(pixdata[44, 227], (254, 255, 254), 0.005) and IsColorInCeil(pixdata[22, 518], (247, 255, 245), 0.01):
        return True
    return False

    
def PokemonWorker(PokemonPosition):
    print "[!] Going to fight with %d %d !" % (PokemonPosition[0], PokemonPosition[1])
    Tap(PokemonPosition[0], PokemonPosition[1])
    time.sleep(0.2)
    bIsPokemonFightOpened = False
    #Check if the click successed
    if IsOnMap() == True:
        print "[!] Click failed !"
        return None
    
    #Wait for fight
    for i in range(0, 5):
        #time.sleep(1)
        if IsPokemonFightOpen() == True:
            bIsPokemonFightOpened = True
            break;
            
        if IsGymOpen() == True:
            print "[!] Holy... This is a Gym"
            CloseGym()
            break

        #We maybe clicked on a PokeStop...
        if IsOpenPokestop() == True:
            print "[!] Holy... This is a Pokestop"
            PokestopWorker(PokemonPosition)
            break
        
        if IsPokeBoxFull() == True:
            print "[!] The PokeBox is full !"
            #Close the pop-up
            Tap(345, 419)
            time.sleep(0.5)
            TransfertPokemon(10)
            #Return true to refight the pokemon
            return True
        print "[!] Wait for Pokemon fight..."
    
    if bIsPokemonFightOpened == False:  
        #This is a big fail maybe a gym detected as Pokemon
        return None

    bIsPokemonHitted = False
    while True:
        if bIsPokemonHitted == False:
            LastPower = random.randint(0,300)
        else:
            print "[!] Using last pokeball power"
        #TODO Detect pokemon distance
        ThrowPokeball(LastPower)
        time.sleep(1)
        bIsPokemonFightOpened = False
        bIsCatchSuccess = False
        bIsOnMap = False
        StressCount = 0
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
            StressCount += 1
            
        if bIsCatchSuccess == True:
            print "[!] Pokemon captured !"
            break
            
        if bIsOnMap == True:
            print "[!] Pokemon flee !"
            return False
            
        if StressCount >= 3:
            bIsPokemonHitted = True
        else:
            bIsPokemonHitted = False

    #Close "sucess" Pop-up
    Tap(239, 526)
    
    while IsOnMap() == False:
        #Close pokemon statistics
        Tap(239, 740)
        time.sleep(1)
        print "[!] Waiting return to the map"
    return True
    
def CleanInventory():
    print "[!] Clean inventory..."
    if IsOnMap() == False:
        print "[!] Not on the map !"
        return False
    Tap(236, 736)
    time.sleep(1)
    Tap(372, 651)
    time.sleep(1)
    while True:
        img = GetImgFromScreenShot()
        FirstObjectColor = GetMeanColor(img, 80, 200)
        print FirstObjectColor
        if IsColorInCeil(FirstObjectColor, [240, 79, 238], 0.01):
            print "[!] Lot of Potions will be dropped !"
        elif IsColorInCeil(FirstObjectColor, [253, 217, 55], 0.01):
            print "[!] Lot of Super Potions will be dropped !"
        elif IsColorInCeil(FirstObjectColor, [251, 228, 218], 0.01):
            print "[!] Lot of Hyper Potions will be dropped !"
        elif IsColorInCeil(FirstObjectColor, [254, 224, 96], 0.01):
            print "[!] Lot of Revives will be dropped !"
        else:
            print "[!] Nothing to drop !"
            break
        #Remove this object
        Tap(438, 150)
        time.sleep(1)
        #1sec for 25 elements
        SwipeTime(351,355,351,355,1000)
        Tap(236, 511)
        time.sleep(0.5)
    #Close Inventory
    Tap(236, 736)
    
SpinnedPokeStopCount = 0
def PokestopWorker(PokeStopPosition):
    global SpinnedPokeStopCount
    print "[!] Working on Pokestop %d %d" % (PokeStopPosition[0], PokeStopPosition[1])
    Tap(PokeStopPosition[0], PokeStopPosition[1])
    time.sleep(0.2)
    if IsOnMap() == True:
        print "[!] Click failed !"
        return False
    bOpenPokestopSuccess = False
    for i in range(5):
        if IsOpenPokestop() == True:
            bOpenPokestopSuccess = True
            break
        if IsSpinnedPokestop() == True:
            print "[!] Pokestop already spinned... Something wrong..."
            ClosePokestop()
            break
        if IsPokemonFightOpen():
            print "[!] Holy... This is a pokemon !"
            PokemonWorker(PokeStopPosition)
            break
        print "[!] Wait for open pokestop"
            
    if bOpenPokestopSuccess == True:
        SpinPokestop()
        bIsSpinnedPokestop = False
        for i in range(5):
            if IsSpinnedPokestop() == True:
                bIsSpinnedPokestop = True
                break
            print "[!] Wait for spinned pokestop"
        
        bIsBagFull = IsBagFull()

        ClosePokestop()
        while IsOnMap() == False:
            print "[!] Waiting return to the map"

        if bIsBagFull == True:
            print "[!] The bag is full..."
            CleanInventory()

        bOpenPokestopSuccess = bIsSpinnedPokestop
    return bOpenPokestopSuccess
        
def SetPosition(Position):
    Command = "adb shell \"setprop persist.nox.gps.longitude %f && setprop persist.nox.gps.latitude %f && setprop persist.nox.gps.altitude %f\"" % (Position[0], Position[1], Position[2])
    #Saved position
    f = open("saved_position.txt", "w")
    f.write("%f,%f,%f" % (Position[1], Position[0], Position[2]))
    f.close()
    os.system(Command)
    
def TransfertPokemon(Number):
    print "[!] Low CP pokemon will be transfered..."
    if IsOnMap() == False:
        print "[!] Not on the map !"
        return False
    #Open Menu
    Tap(236, 736)
    time.sleep(0.1)
    Tap(104, 659)
    time.sleep(0.2)
    #Tap CP
    Tap(415, 742)
    time.sleep(0.1)
    #Select CP
    Tap(414, 631)
    time.sleep(0.1)
    #ScrollDown
    SwipeTime(461, 123, 461, 12000, 300)
    
    for i in range(0, Number):
        print "[!] Transfering a low CP pokemon (%d/%d)" % (i, Number)
        #Tap Down Right pokemon
        Tap(83,619)
        time.sleep(0.5)
        #Options
        Tap(418, 741)
        time.sleep(0.1)
        #Tap Transfert
        Tap(423, 651)
        time.sleep(0.1)
        #Validation
        Tap(236,452)
        time.sleep(1)
    
    #Close Menu
    Tap(236, 736)
    #Wait to be on the map
    time.sleep(1)
    
def IsGameCrashed():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    if IsColorInCeil(pixdata[214, 410], (0, 0, 0), 0.01):
        return True
    if IsColorInCeil(pixdata[214, 410], (40, 40, 40), 0.01):
        return True
    return False
    
def IsPokeBoxFull():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    return IsColorInCeil(pixdata[345, 419], (54, 206, 167), 0.005)
    
def IsPokestopTooFar():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    return IsColorInCeil(pixdata[379,653], (229, 127, 179), 0.005)

def IsBagFull():
    img = GetImgFromScreenShot()
    pixdata = img.load()
    return IsColorInCeil(pixdata[310, 398], (228, 127, 177), 0.005)

def ClosePokemonFight():
    Tap(53, 65)

#Todo: Take a while...
def ZoomOut():
    Command = "adb push Zoomout.txt /sdcard/Zoomout.txt"
    os.system(Command)
    Command = "adb shell sh /sdcard/Zoomout.txt"
    os.system(Command)
    
def CheckApplicationAlive():
    if IsGameCrashed():
        Tap(240, 444)
        time.sleep(0.5)
        #Start the game
        Tap(334, 291)
        while IsOnMap() == False:
            print "[!] Waiting for map..."
            Tap(235, 457)
        #Sometime got a "flash" map
        time.sleep(2)
        while IsOnMap() == False:
            print "[!] Waiting for map..."
            Tap(235, 457)
        ZoomOut()
   

    
#Core...


#Tap(272, 800)
#Swipe(539, 200, 0, 200)
#Tap(490, 128)


#img = GetImgFromFile("output.png")
#PokemonPosition = FindPokemon()
#PokeStopPosition = FindPokestop(img)
#img = GetImgFromScreenShot()
#FindPokemon()
#print GetMeanColor(img, 251, 478 )
#print FindPokemon(img)
#img.save("OUT.png")
#print PokemonPosition
#print IsCatchSucess()
#CatchPokemon([376, 512])
#CleanInventory()
#print IsCatchSucess()
#TransfertPokemon(30)

#print IsBagFull()
#print IsGymOpen()
#sys.exit(0)



Speed = 10
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
SpinnedPokeStopCount = 0
while True:
    for geo_point in loop_geo_points:
        if Count%(50/Speed)==0:
            #Sometime got a crash of pokemongo
            CheckApplicationAlive()
            ReturnToMap()
            print "[!] Looking around..."
            time.sleep(3)
            while True:
                print "[!] Looking for Pokestop"
                PokeStopPosition = FindPokestop()
                if PokeStopPosition is None:
                    print "[!] No more Pokestop found."
                    break
                if PokestopWorker(PokeStopPosition) == False:
                    print "[!] Something is strange... go away (Soft-ban?)!"
                    break
            
            while True:
                print "[!] Looking for pokemon"
                PokemonPosition = FindPokemon()
                if PokemonPosition == False:
                    print "[!] This place is near a Gym !"
                    break
                if PokemonPosition is None:
                    print "[!] No more Pokemon not found."
                    break
                PokemonWorkerReturn = PokemonWorker(PokemonPosition)
                if PokemonWorkerReturn == False:
                    if IsGymOpen() == True:
                        CloseGym()
                        print "[!] This place is near a Gym !"
                        break
                if PokemonWorkerReturn == None:
                    print "[!] This place is near a Gym ?"
                    break
        Count += 1
        SetPosition(geo_point)