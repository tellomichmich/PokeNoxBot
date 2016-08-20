# -*- coding: utf-8 -*-

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
import traceback
from Utils import *
from PIL import Image, ImageOps, ImageDraw, ImageChops, ImageFilter
from math import ceil, radians, cos, sin, asin, sqrt
import re

assert sys.version_info >= (2,7)
assert sys.version_info < (3,0)

#TODO: Class !
config = {}
IVCalculator = PokemonIVCalculator.PokemonIVCalculator()
#TODO: class !!!
img = None
#TODO: We really need class !!
TotalExperience = 0
#TODO: A CLASS IS REALLY NEEDED !
TrainerLevel = -1
               
#This is a best effort implementation !            
def GetPokemonFightNameCP():
    for i in range(5):
        PokemonName = None
        PokemonCP = None
        img1 = GetScreen()
        Frame = img1.crop(((65, 190, 65+320, 190+80)))
        Frame = ImageOps.posterize(Frame, 6)
        RemoveColor(Frame, (255, 255, 255), 0.20)
        Frame = OnlyPureWhite(Frame)
        PokemonNameCP = ImgToString(Frame, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789♀♂?")
        PokemonNameCP = PokemonNameCP.split(' ')
        print PokemonNameCP
        #New pokenom don't have the pokeball in front of name
        #['BLABLA', 'CP123'] 
        if len(PokemonNameCP) == 2:
            CPMark = PokemonNameCP[1][:2]
            if CPMark == "CP":
                PokemonName = PokemonNameCP[0]
                PokemonCP = PokemonNameCP[1][2:]
        #@ is the pokeball
        #['@', 'BLABLA', 'CP123']
        elif len(PokemonNameCP) == 3:
            CPMark = PokemonNameCP[2][:2]
            if CPMark == "CP":
                PokemonName = PokemonNameCP[1]
                PokemonCP = PokemonNameCP[2][2:]
            else:
                #New pokenom don't have the pokeball in front of name
                #['BLABLA', 'CP', '123']
                CPMark = PokemonNameCP[1]
                if CPMark == "CP":
                    PokemonName = PokemonNameCP[0]
                    PokemonCP = PokemonNameCP[2]
        #['@', 'BLABLA', 'CP', '123']
        elif len(PokemonNameCP) == 4:
            CPMark = PokemonNameCP[2]
            if CPMark == "CP":
                PokemonName = PokemonNameCP[1]
                PokemonCP = PokemonNameCP[3]
        #print "-> %s %s" % (PokemonName, PokemonCP)
        if PokemonCP != None and PokemonName != None:
            #Little correction
            PokemonCP = PokemonCP.replace('O', '0')
            PokemonCP = PokemonCP.replace('L', '1')
            PokemonCP = PokemonCP.replace('l', '1')
            PokemonCP = PokemonCP.replace('Z', '2')
            PokemonCP = PokemonCP.replace('/', '7')
            PokemonCP = PokemonCP.replace('S', '5')
            PokemonCP = PokemonCP.replace('R', '8')
            if PokemonCP == "???":
                PokemonCP = "9999"
            try:
                PokemonCP = int(PokemonCP)
                PokemonName = FindRealPokemonName(PokemonName)
                
                #img1.save("tmp\\DEBUG_POKEFIGHT_%s_%d.png" % (PokemonName, PokemonCP))      
                return (PokemonName, PokemonCP)
            except:
                pass
        ClearScreen()
    return ("Unknown", 9999)

def AddExperience(ExperienceCount):
    global TotalExperience
    TotalExperience += ExperienceCount

def GetExperience():
    global TotalExperience
    return TotalExperience

def GetScreen():
    global img
    if img == None:
        img = GetImgFromScreenShot()
    return img
 
def ClearScreen():
    global img
    img = None
    
def IsPokestopOpened():
    img = GetScreen()
    #Outer
    MeanColor = GetMeanColor(img, 234, 780)
    #print MeanColor
    if MeanColor[0] < 150 and MeanColor[1] < 235 and MeanColor[2] > 240:
        return True
    #Inner border
    MeanColor = GetMeanColor(img, 180, 745)
    #print MeanColor
    if MeanColor[0] < 150 and MeanColor[1] < 235 and MeanColor[2] > 240:
        return True
    return False
 
def SpinPokestop():
    Swipe(432, 424, 109, 432)
    time.sleep(0.5)
    ClearScreen()
    
def IsPokestopSpinned():
    img = GetScreen()
    #Outer
    MeanColor = GetMeanColor(img, 234, 780)
    if MeanColor[0] > 150 and MeanColor[1] < 150 and MeanColor[2] > 200:
        return True
    #Inner border
    MeanColor = GetMeanColor(img, 180, 745)
    #print MeanColor
    if MeanColor[0] > 150 and MeanColor[1] < 150 and MeanColor[2] > 200:
        return True
    return False
    
def ClosePokestop():
    #Tap(236, 736)
    KeyEscap()
    time.sleep(1)
    ClearScreen()

def CloseGym():
    #Tap(236, 736)
    KeyEscap()
    time.sleep(0.2)
    ClearScreen()
    
def FindPokestop():
    ReturnToMap()
    img = GetScreen().copy()
    #Apply a mask to keep only "Pokestop zone"
    PokeStopZone = (135, 420, 195, 180)
    mask = Image.new('L', (480, 800), 255)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((PokeStopZone[0],PokeStopZone[1],PokeStopZone[0]+PokeStopZone[2],PokeStopZone[1]+PokeStopZone[3]) , fill=0)
    img.paste((255, 255, 255), mask=mask)

    x, y, xs, ys = PokeStopZone
    #Remove Lured pokestop circle
    Frame = img.crop(((x, y, x+xs, y+ys)))
    RemoveColor(Frame, (179, 250, 255), 0.05)
    #Frame.save("tmp\\OUT_POKESTOP.png")
    pixdata = Frame.load()
    SquareSize = 8
    for xr in range((SquareSize/2), xs-(SquareSize/2)):
        for yr in range((SquareSize/2), ys-(SquareSize/2)):
            #Only on blue like pixel
            if pixdata[xr, yr] != (255, 255, 255) and pixdata[xr, yr][2] > 230:
                MeanColor = GetMeanColor(Frame, xr, yr, SquareSize)
                if IsColorInCeil(MeanColor, [87, 255, 255], 0.05):
                    return [xr+(SquareSize/2)+x, yr+(SquareSize/2)+y]
                if IsColorInCeil(MeanColor, [64, 227, 252], 0.15):
                    return [xr+(SquareSize/2)+x, yr+(SquareSize/2)+y]
    return None
    
def IsDay():
    Hour = datetime.datetime.now().hour  
    if Hour >= 7 and Hour < 19:
        return True
    return False
                
def FindPokemonPosition(img, SquareSize=4):
    pixdata = img.load()
    for xr in range(SquareSize/2, img.size[0]-(SquareSize/2)):
        for yr in range(SquareSize/2, img.size[1]-(SquareSize/2)):
            if pixdata[xr, yr] == (0, 0, 0):
                FalsePositiv = GetMeanColor(img, xr, yr, SquareSize)
                Score = (FalsePositiv[0]+FalsePositiv[1]+FalsePositiv[2])/3
                if Score < 70:
                    return [xr, yr]
    return None
    
def FindPokemon():
    ReturnToMap();
    #TestFindPokemon()
    img = GetScreen().copy()
    #Remove the player
    RemoveInSquare(img, 227, 482, 22, 40)
    #Remove the Experience notification
    RemoveInSquare(img, 24, 600, 115, 70)
    
    #Apply amask to keep only "Pokemon zone"
    mask = Image.new('L', (480, 800), 255)
    draw = ImageDraw.Draw(mask)
    PokemonZone = (65, 420, 135+300, 438+250)
    draw.ellipse(PokemonZone, fill=0)
    img.paste((255, 255, 255), mask=mask)
    
    Frame = img.crop((PokemonZone))
    Frame = ImageOps.posterize(Frame, 2)
    
    ColorBlackList = []
    if IsDay() == True:
        #Day Road
        ColorBlackList.append((64, 128, 128))
        ColorBlackList.append((0, 128, 128))
        #Green
        ColorBlackList.append((0, 192, 128))
        ColorBlackList.append((128, 192, 128))
        ColorBlackList.append((128, 192, 64))
        ColorBlackList.append((64, 192, 128))
        ColorBlackList.append((64, 192, 64))
        #Day Road Boarder
        ColorBlackList.append((192, 192, 128))
    else:
        #Road
        ColorBlackList.append((64, 128, 192))
        #Green
        ColorBlackList.append((64, 128, 128))
        ColorBlackList.append((0, 128, 128))
        ColorBlackList.append((0, 64, 128))
        ColorBlackList.append((0, 64, 64))
        ColorBlackList.append((64, 128, 64))
        #Night Road Boarder
        ColorBlackList.append((128, 128, 128))
        
    #Spinned Pokestop 
    ColorBlackList.append((192, 128, 192))
    ColorBlackList.append((64, 64, 192))
    ColorBlackList.append((128, 64, 192))
    #Lured Pokestop 
    ColorBlackList.append((192, 64, 192))
    #Pokestop 
    ColorBlackList.append((0, 128, 192))
    ColorBlackList.append((64, 192, 192))
    ColorBlackList.append((0, 192, 192))
    ColorBlackList.append((0, 64, 192))
    #Lured Pokestop Circle
    ColorBlackList.append((128, 192, 192))
    #Lured Pokestop Flowers
    ColorBlackList.append((192, 192, 192))
    #Green rustles
    ColorBlackList.append((0, 128, 64))
    ColorBlackList.append((128, 128, 64))
    ColorBlackList.append((128, 192, 128))
    ColorBlackList.append((0, 192, 0))
    ColorBlackList.append((128, 192, 0))
    ColorBlackList.append((0, 64, 0))
    ColorBlackList.append((64, 192, 0))
    ColorBlackList.append((64, 192, 128))
    ColorBlackList.append((0, 128, 0))
    
    RemoveColorList(Frame, ColorBlackList)
    BlackOrWhite(Frame)
    #Search for big Pokemon before small one
    for i in range(10, 2, -2):
        PokemonPosition = FindPokemonPosition(Frame, i)
        if not PokemonPosition is None:
            PokemonPosition[0] += PokemonZone[0]
            PokemonPosition[1] += PokemonZone[1]
            return PokemonPosition

    return None

def ThrowPokeball(Power):
    #Far 100
    #Near 400
    SwipeTime(236, 780, 236, Power, 200)
    ClearScreen()

def IsPokemonFightOpen():
    img = GetScreen()
    pixdata = img.load()
    return IsColorInCeil(pixdata[426, 67], (241, 249, 241), 0.01)
 
def IsGymOpen():
    img = GetScreen()
    pixdata = img.load()
    #White part of the "plateau"
    if IsColorInCeil(pixdata[403, 560], (255, 255, 255), 0.01) == False:
        return False
    #Close cross
    if IsColorInCeil(pixdata[240, 740], (34, 136, 153), 0.01) == False:
        return False
    return True
    
def IsOnMap():
    img = GetScreen()
    pixdata = img.load()
    return IsColorInCeil(pixdata[237, 703], (255, 57, 69), 0.01)
    
def IsCatchSucess():
    img = GetScreen()
    pixdata = img.load()
    if IsColorInCeil(pixdata[44, 227], (254, 255, 254), 0.005) and IsColorInCeil(pixdata[22, 518], (247, 255, 245), 0.01):
        return True
    return False
    
def GetPokeballLeft():
    img = GetScreen()
    img = img.crop(((297, 755, 297+28, 755+19)))
    RemoveColor(img, (255, 255, 255), 0.1)
    img = OnlyPureWhite(img)
    return int(ImgToString(img, "0123456789"))
    
def IsNoMorePokeBall():
    img = GetScreen()
    pixdata = img.load()
    return pixdata[283, 737] == (179, 251, 165)
    
def PokemonWorker(PokemonPosition):
    print "[!] Going to fight with %d %d !" % (PokemonPosition[0], PokemonPosition[1])
    Tap(PokemonPosition[0], PokemonPosition[1])
    ClearScreen()
    time.sleep(0.3)
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
        if IsPokestopOpened() == True:
            print "[!] Holy... This is a Pokestop"
            PokestopWorker([0,0])
            break
        if IsPokestopSpinned() == True:
            print "[!] Holy... This is a Spinned Pokestop"
            ClosePokestop()
            break
        if IsPokeBoxFull() == True:
            print "[!] The PokeBox is full !"
            #Close the pop-up
            KeyEscap()
            time.sleep(0.5)
            ClearScreen()
            TransferLowCPPokemons(10)
            #Return true to refight the pokemon
            return True
        print "[!] Wait for Pokemon fight..."
        time.sleep(0.5)
        ClearScreen()
    
    if bIsPokemonFightOpened == False:  
        #This is a big fail maybe a gym detected as Pokemon
        return None
        
    if IsNoMorePokeBall() == True:
        print "[!] No more pokeball... leaving fight !"
        ClosePokemonFight()
        return None
    
    #Get the Name and the CP of this Pokemon
    (PokemonName, PokemonCP) = GetPokemonFightNameCP()
    print "[!] Seems to be a %s at %d" % (PokemonName, PokemonCP)
    
    #Select the right Poke Ball
    SelectedPokeball = "Poke Ball"
    if PokemonCP >= config['UltraBallCPLimit'] and GetTrainerLevel() >= 20:
        print "[!] Using a Ultra Ball %d > %d" % (PokemonCP, config['UltraBallCPLimit'])
        if UseUltraBall() == False:
            if UseGreatBall() == True:
                SelectedPokeball = "Great Ball" 
        else:
           SelectedPokeball = "Ultra Ball" 
    elif PokemonCP >= config['GreatBallCPLimit'] and GetTrainerLevel() >= 12:
        print "[!] Using a Great Ball %d > %d" % (PokemonCP, config['GreatBallCPLimit'])
        if UseGreatBall() == True:
            SelectedPokeball = "Great Ball"
            
    #Do this after the pokeball selection
    PokeBallLeft = GetPokeballLeft()

    #Use a Razz Berry if one
    if PokemonCP >= config['RazzBerryCPLimit'] and GetTrainerLevel() >= 8:
        if UseRazzBerry() == True:
            print "[!] Using Razz Berry"

    bIsPokemonHitted = False
    ThrowCount = 0
    while True:
        print "[!] %d %s left" % (PokeBallLeft, SelectedPokeball)
        if PokeBallLeft == 0:
            if IsNoMorePokeBall() == True:
                print "[!] No more pokeball... leaving fight !"
                ClosePokemonFight()
                return None
            
            PokeBallLeft = GetPokeballLeft()
        
        if bIsPokemonHitted == False:
            LastPower = random.randint(10,500)
        else:
            print "[!] Using last "+SelectedPokeball+" power"
        if ThrowCount > 30 :
            print "[!] Pokemon too hard, exiting the fight !"
            ClosePokemonFight()
            #Return false to avoid refight this pokemon
            return False
        #TODO Detect pokemon distance
        print "[!] Throwing a "+SelectedPokeball+" (%d)" % LastPower
        ThrowPokeball(LastPower)
        ThrowCount += 1
        time.sleep(1)
        bIsPokemonFightOpened = False
        bIsCatchSuccess = False
        bIsOnMap = False
        StressCount = 0
        for i in range(30):
            if IsPokemonFightOpen() == True:
                bIsPokemonFightOpened = True
                break
            if IsCatchSucess() == True:
                bIsCatchSuccess = True
                break
            if IsOnMap() == True:
                bIsOnMap = True
                break
            if IsGameCrashed() == True:
                return None
            print "[!] #STRESS..."
            StressCount += 1
            ClearScreen()
            
        if bIsCatchSuccess == True:
            print "[!] Pokemon caught !"
            break
            
        if bIsOnMap == True:
            print "[!] Pokemon flee !"
            return False
            
        if StressCount >= 4:
            bIsPokemonHitted = True
        else:
            bIsPokemonHitted = False
        
        PokeBallLeft -= 1

    #Let the popup to fully open
    time.sleep(0.5)
    #Close "sucess" Pop-up
    Tap(239, 526)
    time.sleep(0.5)
    ClearScreen()
    while IsPokemonOpen() == False:
        #Tap anywhere will close the sucess pop-up
        Tap(50,50)
        time.sleep(0.5)
        ClearScreen()
    print "[!] Getting Pokemon information"
    #Waiting Rewards to disappear
    time.sleep(2)
    ClearScreen()
    #We are here on the pokemon statistics
    PokemonName = GetPokemonName()
    PokemonCP = GetPokemonCP()
    print "[!] This is a %s CP:%d" % (PokemonName, PokemonCP)
    PokemonIV = GetPokemonIV(PokemonName, PokemonCP)
    print PokemonIV
    if (not PokemonIV is None) and PokemonIV['perfection'] >= config['IVLimit']:
        ClosePokemon()
    elif PokemonName in config['EvolveList']:
        EvolvePokemon()
        TransferPokemon()
    elif PokemonCP < config['TransferCPLimit'] and (not PokemonName in config['KeepList']):
        TransferPokemon()
    else:
        ClosePokemon()
        
    AddExperience(100)
    print "[!] Waiting return to map..."
    ReturnToMap()
    return True

def ClosePokemon():
    KeyEscap()
    time.sleep(0.3)
    ClearScreen()
    
def PokestopWorker(PokeStopPosition):
    print "[!] Working on Pokestop %d %d" % (PokeStopPosition[0], PokeStopPosition[1])
    Tap(PokeStopPosition[0], PokeStopPosition[1])
    time.sleep(0.6)
    ClearScreen()
    if IsOnMap() == True:
        print "[!] Click failed !"
        return False
    bOpenPokestopSuccess = False
    for i in range(5):
        if IsPokestopTooFar() == True:
            print "[!] Pokestop is too far !"
            ClosePokestop()
            break
        if IsPokestopOpened() == True:
            bOpenPokestopSuccess = True
            break
        if IsPokestopSpinned() == True:
            print "[!] Pokestop already spinned... Something wrong..."
            ClosePokestop()
            break
        if IsPokemonFightOpen():
            print "[!] Holy... This is a pokemon !"
            PokemonWorker([0,0])
            break
        if IsGymOpen():
            print "[!] Holy... This is a Gym"
            CloseGym()
        print "[!] Wait for open pokestop"
        ClearScreen()
            
    if bOpenPokestopSuccess == True:
        SpinPokestop()
        bIsPokestopSpinned = False
        for i in range(3):
            if IsPokestopSpinned() == True:
                bIsPokestopSpinned = True
                break
            print "[!] Wait for spinned pokestop"
            ClearScreen()
        
        bIsBagFull = IsBagFull()
        
        ClosePokestop()
        bIsOnMap = False
        for i in range(10):
            if IsOnMap() == True:
                bIsOnMap = True
                break
            print "[!] Waiting return to the map"
            ClearScreen()
            
        if bIsOnMap == False:
            return False

        if bIsBagFull == True:
            print "[!] The bag is full..."
            CleanInventory()
         
        if bIsPokestopSpinned == True:
            AddExperience(50)

        bOpenPokestopSuccess = bIsPokestopSpinned
    return bOpenPokestopSuccess

def SetPosition(Position):
    Position[1] += random_lat_long_delta()
    Position[0] += random_lat_long_delta()
    Command = "bin\\adb.exe shell \"setprop persist.nox.gps.longitude %f && setprop persist.nox.gps.latitude %f && setprop persist.nox.gps.altitude %f\"" % (Position[0], Position[1], Position[2])
    #Saved position
    f = open("tmp/saved_position.txt", "w")
    f.write("%f,%f,%f" % (Position[1], Position[0], Position[2]))
    f.close()
    os.system(Command)
    ClearScreen()
    
def TransferPokemon():
    if IsPokemonOpen() == False:
        return False
    #Options
    Tap(418, 741)
    time.sleep(0.1)
    #Tap Transfert
    Tap(423, 651)
    time.sleep(0.1)
    #Validation
    #Tap(236,452) #0.31
    Tap(240, 500) #0.33
    time.sleep(1)
    
def OpenPokemonMenu():
    if IsOnMap() == False:
        print "[!] Not on the map !"
        return False
    #Open Menu
    Tap(236, 736)
    time.sleep(0.1)
    #Open Pokemon Menu
    Tap(104, 659)
    time.sleep(0.2)
    return True

def CloseMenu():
    KeyEscap()
    time.sleep(0.3)
    ClearScreen()
    
def TransferLowCPPokemons(Number):
    print "[!] Low CP pokemon will be transfered..."
    if OpenPokemonMenu() == False:
        print "[!] Failed to OpenPokemonMenu"
        return False
    #Tap CP
    Tap(415, 742) 
    time.sleep(0.1)
    #Select CP
    #Tap(414, 631)#0.310
    Tap(415, 650) #0.33.0
    time.sleep(0.1)
    #ScrollDown
    SwipeTime(461, 123, 461, 12000, 300)
    
    for i in range(0, Number):
        print "[!] Transfering a low CP pokemon (%d/%d)" % (i+1, Number)
        #Tap Down Left pokemon
        Tap(83,619)
        time.sleep(0.5)
        ClearScreen()
        if GetPokemonName() in EvolveList:
            EvolvePokemon()
        #    ClosePokemon()
        #else:
        TransferPokemon()
    
    #Close Menu
    CloseMenu()
    #Wait to be on the map
    time.sleep(1)
    ClearScreen()
    
def IsGameCrashed():
    img = GetScreen()
    pixdata = img.load()
    if IsColorInCeil(pixdata[112, 451], (0, 0, 0), 0.01) and IsColorInCeil(pixdata[372, 449], (0, 0, 0), 0.01):
        return True
    if IsColorInCeil(pixdata[112, 451], (40, 40, 40), 0.01) and IsColorInCeil(pixdata[372, 449], (40, 40, 40), 0.01):
        return True
    MeanColor = GetMeanColor(img, 334, 291, 10)
    if IsColorInCeil(MeanColor, [159, 156, 155], 0.01):
        return True
    return False
    
def IsPokeBoxFull():
    img = GetScreen()
    pixdata = img.load()
    return IsColorInCeil(pixdata[345, 419], (54, 206, 167), 0.005)

def IsPokestopTooFar():
    img = GetScreen()
    pixdata = img.load()
    return IsColorInCeil(pixdata[379,653], (229, 127, 179), 0.005)

def IsBagFull():
    img = GetScreen()
    pixdata = img.load()
    return IsColorInCeil(pixdata[310, 398], (228, 127, 177), 0.005)

def ClosePokemonFight():
    Tap(53, 65)
    ClearScreen()
    
def RestartApplication():
    #Close the game
    Command = "bin\\adb shell am force-stop com.nianticlabs.pokemongo"
    os.system(Command)
    #Start the game
    Command = "bin\\adb shell monkey -p com.nianticlabs.pokemongo -c android.intent.category.LAUNCHER 1"
    os.system(Command)
    while IsOnMap() == False:
        Tap(235, 457)
        ClearScreen()
        print "[!] Waiting for map..."
        time.sleep(1)
    #Sometime got a "flash" map
    time.sleep(2)
    ClearScreen()
    while IsOnMap() == False:
        Tap(235, 457)
        ClearScreen()
        print "[!] Waiting for map..."
        time.sleep(1)
    ZoomOut()
    ClearScreen()

#TODO: Handle multiple egg incubators
def AddEggInIncubator():
    if OpenPokemonMenu() == False:
        print "[!] Failed to OpenPokemonMenu"
        return False
    time.sleep(0.5)
    #Tap on EGGS
    Tap(357, 85)
    time.sleep(0.2)
    #Tap on Upper left Egg
    Tap(80, 217)
    time.sleep(0.2)
    #Tap on START INCUBATION
    Tap(231, 507)
    time.sleep(0.2)
    #Tap on first incubator (always a free when a free incubator is available)
    Tap(67, 619)
    time.sleep(0.2)
    #Close Egg Screen
    #ClosePokestop()
    KeyEscap()
    #Close Eggs Screen
    ClosePokemonMemu()
    KeyEscap()
    return True
    
#TODO !
def ReturnToMap():
    for i in range(4):
        if IsOnMap() == True:
            return True
        #Sometime got a crash of pokemongo
        if IsGameCrashed():
            RestartApplication()
            return True
        #This is shit !
        if IsPokemonFightOpen():
            PokemonWorker([0,0])
            #No need to close
            return True
        if IsEggHatched() == True:
            print "[!] EGG HATCHED !!!!!!!!!!"
            #Tap anywhere on screen
            Tap(200, 440)
            ClearScreen()
            print "[!] Waiting end of animation"
            while IsPokemonOpen() == False:
                ClearScreen()
            AddExperience(500)
            ClosePokemon()
            time.sleep(2)
            ClearScreen()
            #Be sur in case we have multiple egg at the same time
            if IsOnMap() == True:
                AddEggInIncubator()
            return True
        if IsPokestopTooFar():
            ClosePokestop()
            return True
        if IsPokestopSpinned():
            ClosePokestop()
            return True
        if IsPokestopOpened():
            PokestopWorker([0,0])
            #No need to close, this is close by PokestopWorker
            return True
        if IsGymOpen():
            CloseGym()
            return True
        if IsPokeBoxFull():
            #Close the pop-up
            Tap(345, 419)
            ClearScreen()
            time.sleep(0.5)
            TransferLowCPPokemons(50)
            return True
        time.sleep(0.5)
        #Last Hope... medals,...
        if i == 2:
            print "[!] LAST HOPE TO ESCAPE !"
            for j in range(4):
                KeyEscap()
            Tap(0, 0)
            ClosePokestop()
            #Close speed alert
            Tap(236, 536)
            time.sleep(1)
        ClearScreen()
    print "[!] Don't know where we are.... Exiting"
    img = GetScreen()
    img.save("OUT_FAIL.png")
    RestartApplication()
    return False

def GetPokemonName():
    img = GetScreen()
    PokeNameZone = (24, 353, 24+430, 353+52)
    Frame = img.crop(((PokeNameZone)))
    PokemonName = ImgToString(Frame, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz♀♂")
    return FindRealPokemonName(PokemonName)
    
def IsEvolvable():
    img = GetScreen()
    pixdata = img.load()
    return IsColorInCeil(pixdata[218, 703], (36, 204, 170), 0.005)
 
def IsPokemonOpen():
    img = GetScreen()
    pixdata = img.load()
    return (pixdata[33, 331] == (250, 250, 250) and pixdata[448, 675] == (250, 250, 250))
    
def EvolvePokemon():
    if IsPokemonOpen() == False:
        print "[!] Not on a Pokemon !"
        return False
    if IsEvolvable() == False:
        print "[!] This Pokemon is not evolvable !"
        return False
    #Evolve !
    Tap(144, 707)
    time.sleep(0.2)
    #Validation
    Tap(239, 420)
    ClearScreen()
    print "[!] Waiting end of evolution..."
    time.sleep(10)
    while IsPokemonOpen() == False:
        ClearScreen()
        time.sleep(1)
    AddExperience(500)
    print "[!] Evolution done !"
    return True
    
def IsEggHatched():
    img = GetScreen()
    pixdata = img.load()
    #print pixdata[18, 780]
    return IsColorInCeil(pixdata[18, 780], (204, 245, 237), 0.005)
    
def FindRealItemName(ItemName):
    ItemNameList = [
                    "Potion",
                    "Super Potion",
                    "Hyper Potion",
                    "Max Potion",
                    "Incense",
                    "Revive",
                    "Max Revive",
                    "Egg Incubator",
                    "Camera",
                    "Poke Ball",
                    "Great Ball",
                    "Ultra Ball",
                    "Lure Module",
                    "Lucky Egg",
                    "Razz Berry"]
    RealItemName = ""
    MinScore = 9999
    for i in ItemNameList:
        CurrentScore = LevenshteinDistance(ItemName, i)
        if CurrentScore < MinScore:
            MinScore = CurrentScore
            RealItemName = i
    return RealItemName
                 
def CleanInventory():
    print "[!] Clean inventory..."
    if IsOnMap() == False:
        print "[!] Not on the map !"
        return False
    Tap(236, 736)
    time.sleep(1)
    Tap(372, 651)
    time.sleep(1)
    ClearScreen()
    while True:
        bIsDroppedItem = False
        img = GetScreen()
        for i in range(3, -1, -1):
            ItemNameZone = (152, 140+(170*i), 152+272, 140+(170*i)+39)
            Frame = img.crop(((ItemNameZone)))
            #TODO: use user-patterns
            ItemName = ImgToString(Frame,"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzé")
            if len(ItemName) < 4 or len(ItemName) > 20:
                #Close Inventory
                Tap(236, 736)
                ClearScreen()
                return False
            ItemName = FindRealItemName(ItemName)
            if ItemName in config['ItemToDropList']:
                print "[!] Dropping %s " % (ItemName)
                #Tap on trash
                Tap(440, 140+(170*i))
                time.sleep(1)
                #1sec for 20 elements
                SwipeTime(351, 355, 351, 355, 4000)
                #Tap OK
                Tap(236, 511)
                time.sleep(0.5)
                bIsDroppedItem = True
        if bIsDroppedItem == False:
            SwipeTime(399, 790, 399, 799-(116*4), 1000)
            time.sleep(2)
        ClearScreen()
    #Close Inventory
    KeyEscap()
    ClearScreen()
    return False
 
def CloseBackPack():
    KeyEscap()
    ClearScreen()
    
def UseItem(ItemToUseName):
    img = GetScreen()
    for i in range(4):
        ItemNameZone = (152, 140+(170*i), 152+272, 140+(170*i)+39)
        Frame = img.crop(((ItemNameZone)))
        ItemName = ImgToString(Frame, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
        if len(ItemName) < 4 or len(ItemName) > 30:
            break
        ItemName = FindRealItemName(ItemName)
        if ItemName == ItemToUseName:
            Tap(152, 140+(170*i))
            time.sleep(0.5)
            ClearScreen()
            return True
    #Same position as Pokestop
    CloseBackPack()
    time.sleep(0.5)
    return False

def GetPokemonCP():
    #Need to that because of some Pokemon animation
    for i in range(5):
        img = GetScreen()
        Frame = img.crop(((160, 49, 160+121, 49+38)))
        RemoveColor(Frame, (255, 255, 255), 0.2)
        BlackOrWhite(Frame)
        PokemonCP = ImgToString(Frame, "CP01234567890").upper()
        #print PokemonCP
        if PokemonCP[:2] == "CP":
            try:  
                return int(PokemonCP[2:])
            except:
                pass
        ClearScreen()
    return 9999
        
def OpenBackPack():
    #Tap on Back Pack
    Tap(418, 737)
    time.sleep(0.5)
    ClearScreen()
    
def UseRazzBerry():
    if IsPokemonFightOpen() == False:
        print "[!] Impossible to use Razz Berry here !"
        return False
    OpenBackPack()
    if UseItem("Razz Berry") == True:
        #Tap on Razz Berry to really use it
        Tap(237, 600)
        #Animation of Razz Berry
        time.sleep(1.5)
        ClearScreen()
        return True
    return False
    
def UseGreatBall():
    if IsPokemonFightOpen() == False:
        print "[!] Impossible to use Great Ball here !"
        return False
    OpenBackPack()
    if UseItem("Great Ball") == True:
        #Animation of Great Ball
        time.sleep(0.2)
        ClearScreen()
        return True
    return False

def UseUltraBall():
    if IsPokemonFightOpen() == False:
        print "[!] Impossible to use Ultra Ball here !"
        return False
    OpenBackPack()
    if UseItem("Ultra Ball") == True:
        #Animation of Great Ball
        time.sleep(0.2)
        ClearScreen()
        return True
    return False

def ClosePokemonMemu():
    KeyEscap()
    ClearScreen()
    
#TODO: Optimize this!
def CleanAllPokemon():
    OpenPokemonMenu()
    #Tap on Top Left Pokemon
    Tap(77, 239)
    time.sleep(0.5)
    ClearScreen()
    for i in range(250):
        #print GetPokemonCP()
        PokemonIV = GetPokemonIV()
        print PokemonIV
        if (not PokemonIV is None) and PokemonIV['perfection'] <= config['IVLimit']:
            bIsForwardNeeded = False
            if IsEvolvable() == True and GetPokemonName() in config['EvolveList']:
                EvolvePokemon()
                ClosePokemon()
                bIsForwardNeeded = True
            elif GetPokemonCP() < config['TransferCPLimit']:
                TransferPokemon()
                bIsForwardNeeded = True
                
            if bIsForwardNeeded == True:
                #Tap on Upper Top Pokemon
                Tap(77, 239)
                time.sleep(0.5)
                #This is not optimized at all !
                for j in range(i-1):
                    #Go to Next Pokemon
                    Tap(460, 200)
        #Go to Next Pokemon
        Tap(460, 200)
        time.sleep(1)
        ClearScreen()
    ClosePokemon()
    ClosePokemonMenu()
    
def GetPokemonLevel():
    arcCenter = 240
    arcInitialY = 285
    radius = 183
    img = GetScreen()
    pixdata = img.load()
    trainerLevel = GetTrainerLevel()*2
    estimatedPokemonLevel = trainerLevel + 3;

    for estPokemonLevel in range(estimatedPokemonLevel, 2, -1):
        angleInDegrees = (IVCalculator.levels[int(estPokemonLevel - 1)]['cpScalar'] - 0.094) * 202.037116 / IVCalculator.levels[trainerLevel - 1]['cpScalar']
        if (angleInDegrees > 1.0 and trainerLevel < 60) :
            angleInDegrees -= 0.5
        elif (trainerLevel >= 60):
            angleInDegrees += 0.5
        angleInRadians = (angleInDegrees + 180) * math.pi / 180.0;
        x = int(arcCenter + (radius * math.cos(angleInRadians)));
        y = int(arcInitialY + (radius * math.sin(angleInRadians)));
        if pixdata[x, y] == (255, 255, 255):
            return estPokemonLevel
    return 0

def GetTrainerLevel():
    global TrainerLevel
    return TrainerLevel
    
def SetTrainerLevel(NewTrainerLevel):
    global TrainerLevel
    TrainerLevel = NewTrainerLevel
    
def UpdateTrainerLevel():
    img = GetScreen()
    TrainerLevelZone = (65, 730, 65+45, 730+25)
    img = img.crop((TrainerLevelZone))
    img = ImageOps.grayscale(img)
    HighContrast(img, 220)
    img = ImageChops.invert(img)
    NewTrainerLevel = ImgToString(img, "0123456789")
    try:
        NewTrainerLevel = int(NewTrainerLevel)
        if NewTrainerLevel >= 1 and NewTrainerLevel <= 40 and NewTrainerLevel >= GetTrainerLevel():
            SetTrainerLevel(NewTrainerLevel)
            return True
    except:
        pass
    return False
    
def GetPokemonHP():
    img = GetScreen()
    PokeHPZone = (129, 418, 223+129, 31+418)
    img = img.crop((PokeHPZone))
    PokemonHP = ImgToString(img, "HP01234567890/")
    PokemonHP = int(PokemonHP.split('/')[1])
    return PokemonHP
    
def GetPokemonStarDust():
    img = GetScreen()
    PokeHPZone = (262, 635, 262+66, 635+21)
    img = img.crop((PokeHPZone))
    PokemonStartDust = ImgToString(img, "0123456789")
    PokemonStartDust = int(PokemonStartDust)
    return PokemonStartDust    
  
def GetPokemonIV(PokemonName=None, PokemonCP=None):
    PokemonLevel = GetPokemonLevel()
    if PokemonName == None:
        PokemonName = GetPokemonName()
    if PokemonCP == None:
        PokemonCP = GetPokemonCP()
    PokemonHP = GetPokemonHP()
    PokemonStarDust = GetPokemonStarDust()
    return IVCalculator.EvaluatePokemon(PokemonName, PokemonCP, PokemonHP, PokemonStarDust, True, PokemonLevel)
    
def FindRealPokemonName(PokemonName):
    MinScore = 9999
    RealPokemonName = None
    for pokemon in IVCalculator.PokemonInfoList:
        CurrentScore = LevenshteinDistance(PokemonName, pokemon['name'])
        if CurrentScore < MinScore:
            MinScore = CurrentScore
            RealPokemonName = pokemon['name']
    return RealPokemonName
    
#Core...
if __name__ == '__main__':
    #Load config file
    with open('config.json', 'r') as f:
        config = json.load(f)

    #Load KML File and extrapol geo point
    loop_geo_points = geo_point_from_kml(config['KMLFile'], config['Speed'])

    #Searching for the nearest point 
    if os.path.isfile("tmp/saved_position.txt"):
        f = open("tmp/saved_position.txt", 'r')
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

    StepCount = 0
    #Set Initial position
    SetPosition(loop_geo_points[0])
    StartTime = time.time()
    while True:
        for geo_point in loop_geo_points:
            #Check for Pokemon and Pokestop every 50 meters
            if StepCount%(config['CheckRadius']/config['Speed'])==0:
                ReturnToMap()
                UpdateTrainerLevel()
                SetPosition(geo_point)
                #Waiting for end of running...
                time.sleep(4.5)
                ClearScreen()
                print "[!] Looking around..."
                
                #Pokestop first to grab some pokeball
                while config['ProcessPokestop']:
                    print "[!] Looking for Pokestop"
                    PokeStopPosition = FindPokestop()
                    if PokeStopPosition is None:
                        print "[!] No more Pokestop found."
                        break
                    if PokestopWorker(PokeStopPosition) == False:
                        print "[!] Something failed..."
                        break
                
                while config['ProcessPokemon']:
                    print "[!] Looking for pokemon"
                    #Clearing the screen because PokestopWorker can be long...
                    ClearScreen()
                    PokemonPosition = FindPokemon()
                    if PokemonPosition == False:
                        print "[!] This place is near a Gym !"
                        break
                    if PokemonPosition is None:
                        print "[!] No more Pokemon not found."
                        break
                    PokemonWorkerReturn = PokemonWorker(PokemonPosition)
                    if PokemonWorkerReturn == None:
                        print "[!] This place is near a Gym ?"
                        break
                    if PokemonWorkerReturn == False:
                        if IsGymOpen() == True:
                            CloseGym()
                            print "[!] This place is near a Gym !"
                            break
                #Print estimated exprience for kikoo-time !
                print "[!] ~%d Exp/h" % ((GetExperience()/(time.time()-StartTime))*60*60)
            StepCount += 1
            #SetPosition(geo_point)