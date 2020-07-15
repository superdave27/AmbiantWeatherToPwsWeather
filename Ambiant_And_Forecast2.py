'''
Written for:
Python 3.6.5
Requires the requests lib

Publishers:
AmbientWeather.net

About:
This script pulls data from the ambient weather api and NWS


Usage:
Set the following variables for your usage in the config.txt file:
ambAppkey = from ambient weather, need to send a request to support
ambApiKey = from the ambientweather.net user interface
intervalMinutes = minutes delay between pushes
loglevel = change to ERROR to get less data, INFO, for a quick "it worked log", or DEBUG for tons of data

After you set the variables, execute the script, it will continue to run until killed
pip install pillow
pip install requests
pip install tkinter

Author:
Steven Kuzmich

Date:
May 2020
v6.0
'''
from tkinter import *
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
import base64
import logging
from logging.handlers import RotatingFileHandler
import datetime
'''use this if you get an error
from urllib import urlencode'''
from urllib.parse import urlencode
from urllib.request import urlopen
from PIL import Image, ImageTk
import io
import time
import configparser


root=Tk()
root.title('weather ux')
#root.resizable(width=FALSE, height=FALSE)
root.geometry('{}x{}'.format(800, 600))

configParser = configparser.RawConfigParser()   
configFilePath = 'config.txt'
configParser.read(configFilePath)

#USER REQUIRED DATA FROM Config file
ambAppkey = configParser.get('AMB', 'ambAppkey')
ambApiKey = configParser.get('AMB', 'ambApiKey')
owmId=configParser.get('AMB', 'owmId')
intervalMinutes = int(configParser.get('AMB', 'intervalMinutes'))
loglevel=logging.INFO


#do not change
FORMAT = '%Y-%m-%d %H:%M:%S'
OWM_URI= 'http://api.openweathermap.org/data/2.5/'
AW_URI = 'https://api.ambientweather.net/v1/devices/'
MAX_LOG_FILES = 5
MAX_LOG_MB = 2
awDataResult=None

labelfont = ('aerial', 22, 'bold')
bgdefault=StringVar()
fontColor=StringVar()
solr=DoubleVar()
solrTrend=StringVar()
condition=StringVar()
windSpeed=DoubleVar()
windTrend=StringVar()
tempNow=DoubleVar()
tempNowTrend=StringVar()
tempH=DoubleVar()
tempL=DoubleVar()
windH=DoubleVar()
windA=DoubleVar()
pres=DoubleVar()
presTrend=StringVar()
dew=DoubleVar()
humidity=DoubleVar()
humidityTrend=StringVar()
uv=DoubleVar()
uvTrend=StringVar()
rainRate=DoubleVar()
rainDaily=DoubleVar()
updated=StringVar()
isfull=False

global forecastData
forecastData=[None, None, None, None, None, None, None]

bgdefault.set('azure')
fontColor.set('black')
root.configure(background=bgdefault.get())
class WxLine:
    title=None
    varible=None
    trendvar=None
    image=None
    units=None
    def __init__(self, new_title, new_varible, new_trendvar=None, new_image=None, new_units=None):
        self.title=new_title
        self.varible=new_varible
        self.trendvar=new_trendvar
        self.image=new_image
        self.units=new_units

class ForecastLine:
    forecastDate=None
    forecastTemps=None
    forecastDay=None
    forecastNight=None
    forecastWind=None
    forecastWindNight=None
    dayLen=0
    nightLen=0
    lblDay=None
    lblNight=None
    imageDayUrl=None
    imageDay=None
    imageNightUrl=None
    imageNight=None
    def __init__(self, new_date, new_temps, new_forecastDay, new_forecastNight=None, new_forecastWind=None, new_forecastWindNight=None, new_dayLen=None, new_nightLen=None, ):
        self.forecastDate=StringVar()
        self.forecastTemps=StringVar()
        self.forecastDay=StringVar()
        self.forecastNight=StringVar()
        self.forecastWind=StringVar()
        self.forecastWindNight=StringVar()
        self.forecastDate.set(new_date)
        self.forecastTemps.set(new_temps)
        self.forecastDay.set(new_forecastDay)
        self.forecastNight.set(new_forecastNight)
        self.forecastWind.set(new_forecastWind)
        self.forecastWindNight.set(new_forecastWindNight)
        self.dayLen=new_dayLen
        self.nightLen=new_nightLen

        
#setup the rotating file log
aw_logger = logging.getLogger('__name__')
aw_logger.setLevel(loglevel)
handler = RotatingFileHandler(
    'Ambient_Job.log',
    maxBytes=MAX_LOG_MB*1024*1024,
    backupCount=MAX_LOG_FILES)
handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
aw_logger.addHandler(handler)

#GETS DATA FROM AMBIENT WEATHER
def grabFromAw():
    data = None
    try:
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        aws_full_url= AW_URI+'?apiKey='+ambApiKey+'&applicationKey='+ambAppkey+''
        #aws_full_url="http://www.google.com"
        response = session.get(aws_full_url)
        #print (response.url)
        aw_logger.debug(response.url)
        data = response.json()
        #print (str(data))
    except requests.ConnectionError as e:
        print("Connection Error AWS. Make sure you are connected to Internet. Technical Details given below.\n")
        aw_logger.error("Connection Error AWS. Make sure you are connected to Internet. Technical Details given below.\n")
        aw_logger.error(str(e))            
    except requests.Timeout as e:
        aw_logger.error("Timeout Error AWS")
        aw_logger.error(str(e))       
    except requests.RequestException as e:
        aw_logger.error("General Error AWS")
        aw_logger.error(str(e))
    except ValueError as e:
        aw_logger.error("Json Error AWS")
        aw_logger.error(str(e))
    awDataResult=None
    if data is not None and len(data) > 0 and isinstance(data, list) and data[0] is not None and 'lastData' in data[0]:
        awDataResult=data[0]['lastData']
        
    #print (awDataResult)
    aw_logger.debug(str(awDataResult))
    return awDataResult

def grabFromNWS():
    #https://www.weather.gov/documentation/services-web-api
    #NEEDS UPDATE https://api.weather.gov/gridpoints/BOU/60,92/forecast
    #https://api.weather.gov/points/40.4250602%2C-105.1222288/forecast
    nws_url = "https://api.weather.gov/points/"+configParser.get('NWS', 'forecastLocation')+"/forecast"
    #print (nws_url)
    nwsDataForecast=None
    try:
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        #session.headers.update({'accept': 'application/ld+json'})
        session.headers.update({'useragent': 'personalPiWeatherStationDisplay'})
        response = session.get(nws_url)
        data = response.json()
        nwsDataForecast=data['properties']['periods']
    except requests.ConnectionError as e:
        print("Connection Error NWS. Make sure you are connected to Internet. Technical Details given below.\n")
        aw_logger.error("Connection Error Yahoo. Make sure you are connected to Internet. Technical Details given below.\n")
        aw_logger.error(str(e))            
    except requests.Timeout as e:
        aw_logger.error("Timeout Error NWS")
        aw_logger.error(str(e))       
    except requests.RequestException as e:
        aw_logger.error("General Error NWS")
        aw_logger.error(str(e))
    except ValueError as e:
        aw_logger.error("Json Error NWS")
        aw_logger.error(str(e))
    except:
        aw_logger.error("Unknown error NWS")
    #print(data)
    return nwsDataForecast
    

#not in use
def screen_off():
    command1 = "echo 1"
    command2 = "/usr/bin/sudo tee /sys/class/backlight/rpi_backlight/bl_power"
    process1 = subprocess.Popen(command1.split(), stdout=subprocess.PIPE)
    process2 = subprocess.Popen(command2.split(), stdin=process1.stdout, stdout=subprocess.PIPE)
    output = process2.communicate()[0]
    #print(output)
def minwindow():
    root.attributes('-fullscreen', False)
    root.overrideredirect(False)
    root.geometry('{}x{}'.format(800, 600))
    global isfull
    isfull=False
def maxwindow():
    root.attributes('-fullscreen', True)
    root.overrideredirect(True)
    root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
    global isfull
    isfull=True
def trendMark(past, present):
    trendUp='▴'
    trendDown='▾'
    trendNutral='-'
    marker=None
    if past < present:
        marker=trendUp
    elif past == present:
        marker=trendNutral
    else:
       marker=trendDown
    return marker
def quitApp():
    root.destroy()
    
def update_value():
    awDataResult = grabFromAw()
    if awDataResult is not None:      
        result="Success"
    else:
        result = "No data from AW service."
        aw_logger.error(result)

    print (datetime.datetime.now().strftime(FORMAT)+ ' - ' +result)
    aw_logger.info(result)
    
    updateDisplay(awDataResult, result)

    
def setColors():
    #print("solr value "+str(solr.get()))
    #solr.set(100)
    if solr.get() <= 10:
        bgdefault.set('gray25')
        fontColor.set('white')
    elif solr.get() > 10 and solr.get() <= 100:
        bgdefault.set('gray45')
        fontColor.set('black')
    elif solr.get() > 100 and solr.get() <= 200:
        bgdefault.set('gray75')
        fontColor.set('black')
    elif solr.get() > 200 and solr.get() <= 300:
        bgdefault.set('gray85')
        fontColor.set('black')
    elif solr.get() > 300:
        bgdefault.set('grey95')
        fontColor.set('black')

    root.configure(background=bgdefault.get())  
    #spins through all widgets and sets colors
    listw = root.winfo_children()
    for item in listw :
        if item.winfo_children() :
            listw.extend(item.winfo_children())
        #print(item.image())
        #if item.winfo_class()=="Label" and item.image is None:
        item.configure(background=bgdefault.get())
        item.configure(foreground=fontColor.get())
    '''if solr.get() <= 0:
        updcode.configure(background="LightSkyBlue4")
        updcode1.configure(background="LightSkyBlue4")
        updcode2.configure(background="LightSkyBlue4")
        updcode3.configure(background="LightSkyBlue4")
        updcode4.configure(background="LightSkyBlue4")'''

def resetData():
    condition.set("Calm")
    tempNow.set(0)
    windH.set(0)
    windA.set(0)
    tempH.set(0)
    tempL.set(10000)
    pres.set(0)
    solr.set(1000)
    dew.set(0)
    humidity.set(0)
    uv.set(0)
    updated.set("NA")
    setColors()
    seed=0
    for x in range(len(forecastData)):
        forecastDate = ("Load")
        forecastTemps =""
        forecastDay =""
        forecastWind = ""
        forecastNight=""
        forecastWindNight=""
        forecastData[x]=ForecastLine(forecastDate, forecastTemps, forecastDay, forecastNight, forecastWind, forecastWindNight,0,0)
        

def getDirs(d):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = int((d + 11.25)/22.5 - 0.02)
    return dirs[ix % 16]

def getIcon(code):
    #http://erikflowers.github.io/weather-icons/
    #https://developer.yahoo.com/weather/documentation.html
    #print('CODE '+ str(code))
    icon=None
    if code == 0: 
        icon="wi-tornado"
    elif code == 1: 
        icon="wi-hurricane" # tropical storm
    elif code == 2: 
        icon="wi-hurricane" #hurricane
    elif code == 3: 
        icon="wi-thunderstorm" #severe thunderstorms
    elif code in[4, 45, 47]: 
        icon="wi-storm-showers" #thunderstorms, thundershowers
    elif code == 5: 
        icon="wi-rain-mix" # mixed rain and snow
    elif code in[6,7,18]: 
        icon="wi-sleet" # mixed rain and sleet,mixed snow and sleet, sleet
    elif code == 4: 
        icon="wi-thunderstorm"
    elif code in[8,10,12,14,16]: 
        icon="wi-snow" #freezing drizzle, drizzle, freezing rain,snow flurries,light snow showers,snow
    elif code in[9,11,12]: 
        icon="wi-sprinkle" #drizzle,showers, showers
    elif code in[15]: 
        icon="wi-snow-wind" #blowing snow
    elif code in[17,35]: 
        icon="wi-hail" #hail, rain hail
    elif code in[19]: 
        icon="wi-dust" #dust
    elif code in[20]: 
        icon="wi-fog" #fog
    elif code in[20,21]: 
        icon="wi-day-haze" #haze    
    elif code in[22]: 
        icon="wi-smoke" #smoky
    elif code in[23]: 
        icon="wi-strong-wind" #blustery
    elif code in[24]: 
        icon="wi-windy" #windy
    elif code in[25]: 
        icon="wi-snowflake-cold" #cold    
    elif code in[26,44]: 
        icon="wi-cloudy" #cloudy
    elif code in[27]: 
        icon="wi-night-alt-cloudy" #mostly cloudy night
    elif code in[28]: 
        icon="wi-day-cloudy" #mostly cloudy day
    elif code in[29]: 
        icon="wi-night-alt-partly-cloudy" #partly cloudy night
    elif code in[30]: 
        icon="wi-day-sunny-overcast" #partly cloudy day
    elif code in[31]: 
        icon="wi-night-clear" #night clear
    elif code in[33]: 
        icon="wi-night-alt-cloudy-high" #night fair
    elif code in[32]: 
        icon="wi-day-sunny" #sunny
    elif code in[34]: 
        icon="wi-day-cloudy-high" #day fair
    elif code in[36]: 
        icon="wi-hot" #hot
    elif code in[37,38,39]: 
        icon="wi-storm-showers" #isolated thunderstorms,scattered thunderstorms,scattered thunderstorms
    elif code in[40]: 
        icon="wi-sprinkley" #scattered showers
    elif code in[41,42,43, 46]: 
        icon="wi-snow" #heavy snow,scattered snow showers,heavy snow, snow showers
    elif code == -1: 
        icon="wi-thermometer" #heavy snow,scattered snow showers,heavy snow, snow showers
    else: 
        icon="wi-na" #other
    #print(str(code)+' '+icon)
    icon='wx-icons/small/'+icon+'.svg.png'
    
    img=PhotoImage(file=icon)
    
    return img



def updateDisplay(awDataResult, result):
    if awDataResult is not None:
              
        #print(datetime_object)
        conditions="Calm"
        if awDataResult['hourlyrainin']>0:
            conditions = "Raining"

        elif awDataResult['windspeedmph']>0:
            conditions =str(awDataResult['windspeedmph']) + '-' + getDirs(int(awDataResult['winddir']))
            
        condition.set(conditions)
        windTrend.set(trendMark(windSpeed.get(),awDataResult['windspeedmph'] ))
        windSpeed.set(awDataResult['windspeedmph'])
        
        tempNowTrend.set(trendMark(tempNow.get(),awDataResult['tempf'] ))
        tempNow.set(awDataResult['tempf'])
        if awDataResult['tempf'] > tempH.get():     
            tempH.set(awDataResult['tempf'])
            
        if awDataResult['tempf'] < tempL.get():     
            tempL.set(awDataResult['tempf'])

        presTrend.set(trendMark(pres.get(),awDataResult['baromrelin'] ))
        pres.set(awDataResult['baromrelin'])
        
        dew.set(awDataResult['dewPoint'])
        humidityTrend.set(trendMark(humidity.get(),awDataResult['humidity'] ))
        humidity.set(awDataResult['humidity'])
        
        rainRate.set(awDataResult['hourlyrainin'])
        rainDaily.set(awDataResult['dailyrainin'])
        
        uvTrend.set(trendMark(uv.get(),awDataResult['uv'] )) 
        uv.set(str(awDataResult['uv']))

        solrTrend.set(trendMark(solr.get(),awDataResult['solarradiation'] ))
        solr.set(awDataResult['solarradiation'])
                         

        if awDataResult['windspeedmph'] > windH.get():
            windH.set(awDataResult['windspeedmph'])

        if awDataResult['windgustmph'] > windA.get():    
            windA.set(awDataResult['windgustmph'])

        #forecastdata
        forecastWeather=grabFromNWS()
        if forecastWeather is not None and len(forecastWeather) > 0 and forecastWeather[0] is not None and forecastWeather[0].get('temperature', None)is not None:
            seed = 0 #array index counter to adjust for am pm changes in data payload


            for x in range(len(forecastData)):
                forecastData[x].forecastDate.set("Data Prep")
                forecastData[x].forecastTemps.set("")
                forecastData[x].forecastDay.set("")
                forecastData[x].forecastWind.set("")
                forecastData[x].forecastDay.set("")
                forecastData[x].forecastNight.set("")
                forecastData[x].forecastWindNight.set("")
                if x==0:
                    if forecastWeather[0]['isDaytime'] == False:
                        forecastData[x].forecastDate.set("Night")
                        forecastData[x].forecastTemps.set(str(forecastWeather[seed]['temperature'])+"°f")
                        forecastData[x].forecastNight.set(forecastWeather[seed]['detailedForecast'])
                        #forecastData[x].nightLen=len(forecastWeather[seed]['shortForecast'])
                        forecastData[x].forecastWindNight.set(forecastWeather[seed]['windSpeed'])
                        forecastData[x].imageNightUrl=forecastWeather[seed]['icon']
                        forecastData[x].imageDayUrl=None
                        seed+=1
                    else:
                        forecastData[x].forecastDate.set("Day")
                        forecastData[x].forecastTemps.set(str(forecastWeather[seed]['temperature'])+' / '+str(forecastWeather[seed+1]['temperature'])+"°f")
                        forecastData[x].forecastDay.set(forecastWeather[seed]['detailedForecast'])
                        #forecastData[x].dayLen=len(forecastWeather[seed]['shortForecast'])
                        forecastData[x].forecastWind.set(forecastWeather[seed]['windSpeed'])
                        forecastData[x].imageDayUrl=forecastWeather[seed]['icon']
                        forecastData[x].forecastNight.set(forecastWeather[seed+1]['detailedForecast'])
                        #forecastData[x].nightLen=len(forecastWeather[seed+1]['shortForecast'])
                        forecastData[x].forecastWindNight.set(forecastWeather[seed+1]['windSpeed'])
                        forecastData[x].imageNightUrl=forecastWeather[seed+1]['icon']
                        seed+=2
                        
                        
                else:
                    forecastData[x].forecastDate.set(forecastWeather[seed]['name'][:3] + '.')
                    forecastData[x].forecastTemps.set(str(forecastWeather[seed]['temperature'])+' / '+str(forecastWeather[seed+1]['temperature'])+"°f")
                    forecastData[x].forecastDay.set(forecastWeather[seed]['detailedForecast'])
                    #forecastData[x].dayLen=len(forecastWeather[seed]['shortForecast'])
                    forecastData[x].forecastWind.set(forecastWeather[seed]['windSpeed'])
                    forecastData[x].imageDayUrl=forecastWeather[seed]['icon']
                    forecastData[x].forecastNight.set(forecastWeather[seed+1]['detailedForecast'])
                    #forecastData[x].nightLen=len(forecastWeather[seed+1]['shortForecast'])
                    forecastData[x].forecastWindNight.set(forecastWeather[seed+1]['windSpeed'])
                    forecastData[x].imageNightUrl=forecastWeather[seed+1]['icon']
                    #FIX THIS, use the ones from reset and set the vals instead of new ones forecastData[x]=ForecastLine(forecastDate, forecastTemps, forecastDay, forecastNight, forecastWind, forecastWindNight)
                    seed+=2
                
                #labelFontSmall=('aerial', 9,)
                #labelFontLarge=('aerial', 12, 'bold')
                #if forecastData[x].dayLen>20:
                #    forecastData[x].lblDay.config(font=labelFontSmall)
                #else:
                #    forecastData[x].lblDay.config(font=labelFontLarge)
                    
                #if forecastData[x].nightLen>20:
                #    forecastData[x].lblNight.config(font=labelFontSmall)
                #else:
                #    forecastData[x].lblNight.config(font=labelFontLarge)
                
                if forecastData[x].imageDayUrl is not None:
                    #print(forecastData[x].imageDayUrl)
                    raw_data = urlopen(forecastData[x].imageDayUrl).read()
                    im = Image.open(io.BytesIO(raw_data))
                    img = ImageTk.PhotoImage(im)
                    forecastData[x].imageDay=img
                    forecastData[x].lblDay.config(image=forecastData[x].imageDay)
                    forecastData[x].lblDay.bind("<Button>", lambda event, data=forecastData[x].forecastDay.get(): on_click(data))

                if forecastData[x].imageNightUrl is not None:
                    #print(forecastData[x].imageNightUrl)
                    raw_data = urlopen(forecastData[x].imageNightUrl).read()
                    imn = Image.open(io.BytesIO(raw_data))
                    imgn = ImageTk.PhotoImage(imn)
                    forecastData[x].imageNight=imgn
                    forecastData[x].lblNight.config(image=forecastData[x].imageNight)
                    forecastData[x].lblNight.bind("<Button>", lambda event, data=forecastData[x].forecastNight.get(), : on_click(data))
        else:
            forecastData[0].forecastDate.set("ERROR")
    
        updated.set(datetime.datetime.now().strftime(FORMAT)+"\n"+result)
        
    else:
        updated.set(datetime.datetime.now().strftime(FORMAT)+"\n"+"ERROR OCCURED")
        
    setColors()
    root.update_idletasks()
    root.after(intervalMinutes*60*1000, update_value)

def wxWidgetMaker(groupName, dataList):
    labelFont3=('aerial', 16, 'bold')
    labelFont4=('aerial', 10, 'bold')
    widget = LabelFrame(root, text=groupName, bd=2, bg=bgdefault.get(), foreground=fontColor.get())
    
    for i, dataItem in enumerate(dataList):
        v1l=Label(widget, text=dataItem.title,font=labelFont3, bg=bgdefault.get(), foreground=fontColor.get())
        v1d=Label(widget, textvariable = dataItem.varible,font=labelFont3, bg=bgdefault.get(), foreground=fontColor.get())
        v1l.grid(row=i, column=1, sticky=W)
        v1d.grid(row=i, column=3, sticky=E)
        if dataItem.trendvar is not None:
            v2d=Label(widget, textvariable = dataItem.trendvar,font=labelFont3, bg=bgdefault.get(), foreground=fontColor.get())
            v2d.grid(row=i, column=2, sticky=E)
        if dataItem.image is not None:
            v2d=Label(widget, text="Provided By", image = dataItem.image)
            v2d.grid(row=i, column=0, sticky=E)
        if dataItem.units is not None:
            v2d=Label(widget, text=dataItem.units,font=labelFont4 )
            v2d.grid(row=i, column=4, sticky=W)
    for c in range(4):
        widget.columnconfigure(c, weight=1)
    return widget

def on_click(data):
    # `command=` calls function without argument
    # `bind` calls function with one argument
    #print("image clicked")
    #print(data)
    popup = Toplevel()
    popup.wm_title("Forecast Details")
    popup.configure(background=bgdefault.get())
    for r in range(2):
        popup.rowconfigure(r, weight=1)    
    for c in range(1):
        popup.columnconfigure(c, weight=1)
    l = Label(popup, text=data, font=('aerial', 28), wraplength=800, bg=bgdefault.get(), foreground=fontColor.get())
    l.grid(row=0, column=0, sticky=N, padx=10, pady=10)
    b = Button(popup, text="Okay", command=popup.destroy, font=('aerial', 20, 'bold'), bg=bgdefault.get(), foreground=fontColor.get())
    b.grid(row=1, column=0, sticky=S, padx=10, pady=50)
    

    popup.geometry(str(root.winfo_width())+"x"+str(root.winfo_height())+"+"+str(root.winfo_x())+"+"+str(root.winfo_y()))
    if isfull:
        popup.attributes('-fullscreen', True)
        popup.overrideredirect(True)
 

def forecastWidgetMaker(forecastData,icons):

    labelFont2=('aerial', 20, 'bold')
    labelFont1=('aerial', 14, 'bold')
    boxfor = LabelFrame(root, text="Forecast from the National Weather Service API", bd=2, bg=bgdefault.get(), foreground=fontColor.get())
    
    upddateL=Label(boxfor, text="Day", image=icons["time"])
    upddateL.grid(row=0, column=0,  sticky=W)
    
    updtempL=Label(boxfor, text="H/L", image=icons["tmp"])
    updtempL.grid(row=1, column=0,  sticky=W)

    updtextL=Label(boxfor, text="AM", image=icons["sun"])
    updtextL.grid(row=2, column=0, sticky=W)

    updcodeL=Label(boxfor, text="PM", image=icons["moon"])
    updcodeL.grid(row=3, column=0, sticky=W)
   

    for x in range(len(forecastData)):
        #forcastFont=labelFont1
        upddate=Label(boxfor, textvariable=forecastData[x].forecastDate, font=labelFont2, bg=bgdefault.get(), foreground=fontColor.get())
        upddate.grid(row=0, column=x+1,  sticky=N)
        updtemp=Label(boxfor, textvariable=forecastData[x].forecastTemps, font=labelFont1, bg=bgdefault.get(), foreground=fontColor.get())
        updtemp.grid(row=1, column=x+1,  sticky=N)

        updtext=Label(boxfor, textvariable=forecastData[x].forecastDay, font=labelFont1, bg=bgdefault.get(), foreground=fontColor.get(), wraplength=180)
        forecastData[x].lblDay=updtext
        updtext.grid(row=2, column=x+1, sticky=N)
        
        updcode=Label(boxfor, textvariable=forecastData[x].forecastNight, font=labelFont1, bg=bgdefault.get(), foreground=fontColor.get())
        forecastData[x].lblNight=updcode
        updcode.grid(row=3, column=x+1, sticky=N)
        
    for r in range(4):
        boxfor.rowconfigure(r, weight=1)    
    for c in range(len(forecastData)+1):
        boxfor.columnconfigure(c, weight=1)
    return boxfor
aw_logger.info('Job Started, transfers will occur every '+str(intervalMinutes)+' min')



icons={"tmp":PhotoImage(file='wx-icons/small/wi-thermometer.svg.png'),
"humid":PhotoImage(file='wx-icons/small/wi-humidity.svg.png'),
"bar":PhotoImage(file='wx-icons/small/wi-barometer.svg.png'),
"horizon":PhotoImage(file='wx-icons/small/wi-horizon-alt.svg.png'),
"umbrella":PhotoImage(file='wx-icons/small/wi-umbrella.svg.png'),
"tmpExt":PhotoImage(file='wx-icons/small/wi-thermometer-exterior.svg.png'),
"windy":PhotoImage(file='wx-icons/small/wi-windy.svg.png'),
"strongWind":PhotoImage(file='wx-icons/small/wi-strong-wind.svg.png'),
"raindrop":PhotoImage(file='wx-icons/small/wi-raindrop.svg.png'),
"raindrops":PhotoImage(file='wx-icons/small/wi-raindrops.svg.png'),
"sun":PhotoImage(file='wx-icons/small/wi-day-sunny.svg.png'),
"moon":PhotoImage(file='wx-icons/small/wi-night-clear.svg.png'),
"time":PhotoImage(file='wx-icons/small/wi-time-2.svg.png')
}
#initiate data download
#update_value()
resetData()
#stats
conditionData=[WxLine("Temp", tempNow,tempNowTrend,icons["tmp"], "°f"),
               WxLine("Wind", condition, windTrend,icons["strongWind"],"mph" ),
               WxLine("Humidity", humidity,humidityTrend,icons["humid"],"%"),
               WxLine("Pressure", pres, presTrend,icons["bar"],"inHg"),
               WxLine("Solar", solr, solrTrend,icons["horizon"],"W/m²"),
               WxLine("UV Index", uv, uvTrend,icons["umbrella"])]

tempData=[WxLine("Temp H", tempH, None, icons["tmp"], "°f"),
          WxLine("Temp L", tempL, None, icons["tmpExt"], "°f"),
          WxLine("Wind Max", windH, None, icons["windy"],"mph"),
          WxLine("Wind Gust", windA, None, icons["strongWind"],"mph"),
          WxLine("Hourly Rain", rainRate, None, icons["raindrop"],"in"),
          WxLine("Daily Rain", rainDaily, None, icons["raindrops"],"in")]


boxnow = wxWidgetMaker("Now" , conditionData)

boxtemps = wxWidgetMaker("Ranges" , tempData)
boxfor= forecastWidgetMaker(forecastData,icons)


#job update info ui
boxupdated =LabelFrame(root, text="Updated", bd=2, bg=bgdefault.get(), foreground=fontColor.get())
for r in range(1):
    boxupdated.rowconfigure(r, weight=1)    
for c in range(2):
    boxupdated.columnconfigure(c, weight=1)
updt=Label(boxupdated, textvariable=updated,font=('aerial', 15, 'bold'), bg=bgdefault.get(), foreground=fontColor.get())
updt.grid(row=0, column=0, columnspan=2, sticky=W+E+N+S)

#buttons
controls =LabelFrame(root, text="Controls", bd=2, bg=bgdefault.get(), foreground=fontColor.get())
for r in range(1):
    controls.rowconfigure(r, weight=1)    
for c in range(5):
    controls.columnconfigure(c, weight=1)
brefresh = Button(controls, text="Refresh", command=update_value)
breset = Button(controls, text="Re-Set", command=resetData)
bquit = Button(controls, text="Quit", command=quitApp)
bmin = Button(controls, text="Min", command=minwindow)
bmax = Button(controls, text="Max", command=maxwindow)
bmin.grid(row=0, column=0, sticky=W+E+N+S,padx=5, pady=5)
bmax.grid(row=0, column=1, sticky=W+E+N+S,padx=5, pady=5)
brefresh.grid(row=0, column=2, sticky=W+E+N+S,padx=5, pady=5)
breset.grid(row=0, column=3, sticky=W+E+N+S,padx=5, pady=5)
bquit.grid(row=0, column=4, sticky=W+E+N+S,padx=5, pady=5)

#layout app
for r in range(2):
    root.rowconfigure(r, weight=1)    
for c in range(2):
    root.columnconfigure(c, weight=1)
boxnow.grid(row=0, column=0, sticky=W+E+N+S,padx=5, pady=5)
boxtemps.grid(row=0, column=1, sticky=W+E+N+S, padx=5, pady=5)
boxfor.grid(row=1, column=0, columnspan=2, sticky=W+E+N+S, padx=5, pady=5)
boxupdated.grid(row=2, column=0, sticky=W+E+N+S ,padx=5, pady=5)
controls.grid(row=2, column=1, sticky=W+E+N+S ,padx=5, pady=5)



    
#update_value()
root.after(100, update_value)
root.mainloop()    



