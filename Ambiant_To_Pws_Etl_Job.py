'''
Written for:
Python 3.6.5
Requires the requests lib

Publishers:
PWSweather.com 
AmbientWeather.net

About:
This script pulls data from the ambient weather api and sends it to PWS.
This script is intended to help support Rachio Sprinklers with a local ambient Weather Station

Usage:
Set the following variables for your usage:
ambAppkey = from ambient weather, need to send a request to support
ambApiKey = from the ambientweather.net user interface
pwsStation = not the name but the ID when you set up your station
pwsPassword = your PWS weather account password
intervalMinutes = minutes delay between pushes
loglevel = change to ERROR to get less data, INFO, for a quick "it worked log", or DEBUG for tons of data

After you set the variables, execute the script, it will continue to run until killed

Author:
Steven Kuzmich

Date:
May 2018
v1.9
'''

import requests
import json
import base64
import logging
from logging.handlers import RotatingFileHandler
import datetime
'''use this if you get an error
from urllib import urlencode'''
from urllib.parse import urlencode
import time

#USER REQUIRED DATA SEE NOTES above
ambAppkey = ''
ambApiKey = ''
pwsStation = ''
pwsPassword = ''
intervalMinutes = 10
loglevel=logging.INFO 

#do not change
FORMAT = '%Y-%m-%d %H:%M:%S'
AW_URI = 'https://api.ambientweather.net/v1/devices/'
PSW_URI = 'http://www.pwsweather.com/pwsupdate/pwsupdate.php'
MAX_LOG_FILES = 5
MAX_LOG_MB = 2

#setup rotating file log
aw_logger = logging.getLogger('__name__')
aw_logger.setLevel(loglevel)
handler = RotatingFileHandler(
    'ambient_To_Pws_Etl_Job.log',
    maxBytes=MAX_LOG_MB*1024*1024,
    backupCount=MAX_LOG_FILES)
handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
aw_logger.addHandler(handler)

#GETS DATA FROM AMBIENT WEATHER
def grabFromAw():
    response = requests.get(AW_URI+'?apiKey='+ambApiKey+'&applicationKey='+ambAppkey+'')
    #print (response.url)
    aw_logger.debug(response.url)
    data = response.json()

    awDataResult=None
    if len(data) == 1:
        awDataResult=data[0]['lastData']
        
    #print (awDataResult)
    aw_logger.debug(str(awDataResult))
    return awDataResult

#PUSH DATA TO PWS WEATHER
def pushToPws(awDataResult):
    #converts aw timestamp string to pw timestamp string
    datetime_object = datetime.datetime.strptime(awDataResult['date'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime(FORMAT)
    
    #prep pws params
    args = {'ID':pwsStation,
            'PASSWORD':pwsPassword,
            'dateutc':datetime_object, 
            'winddir':awDataResult['winddir'],
            'windgustmph':awDataResult['windgustmph'],
            'windspeedmph':awDataResult['windspeedmph'],
            'tempf':awDataResult['tempf'],
            'rainin':awDataResult['hourlyrainin'],
            'dailyrainin':awDataResult['dailyrainin'],
            'monthrainin':awDataResult['monthlyrainin'],
            'baromin':awDataResult['baromrelin'],
            'dewptf':awDataResult['dewPoint'],
            'humidity':awDataResult['humidity'],
            'solarradiation':awDataResult['solarradiation'],
            'UV':awDataResult['uv'],
            'softwaretype':'PyambientWeather2PWS',
            'action':'updateraw'    
    }
    
    #SEND DATA TO PWS
    push = requests.get(PSW_URI,params=args)
    aw_logger.debug(push.url)
    #print(push.url)
    
    status="Failure to post data to PWS."
    #checks if the resulting page has the "success" message
    if push.text.find("Data Logged and posted in METAR mirror.") != -1:
        status ="Post to PWS Successful."
    else:
        aw_logger.error(status+' URL:'+push.url)

    return (status+' Outside Temp: '+str(awDataResult['tempf'])+'f')


#RUNNER LOOP
aw_logger.info('Job Started, transfers will occur every '+str(intervalMinutes)+' min')
while True:
    awDataResult = grabFromAw()
    if awDataResult != None:
        #print (awDataResult)
        result = pushToPws(awDataResult)
    else:
        result = "No data from AW service."
        aw_logger.error(result)

    #print (timeran+' - '+result)
    aw_logger.info(result)
    time.sleep(intervalMinutes*60)


