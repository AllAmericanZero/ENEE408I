from twilio.rest import Client
import datetime
import time
import json
from tracking_func import speak
import pyttsx
weekdays = ("mon","tues","wed","thurs","fri","sat","sun")

account_sid = 'AC73b795f32902823dc799b09856fe41c9'
auth_token = 'c3beb617b2227f80e574a886461cae26'
client = Client(account_sid, auth_token)

engine  = pyttsx.init()

while True:
    curr_time = datetime.datetime.now()
    curr_day  = weekdays[curr_time.weekday()]
    with open('schedule.json') as json1_file:
        sched = json.loads(json1_file.read())
        json1_file.close()
        for pill in sched[curr_day]:
            if pill['hour'] == curr_time.hour and pill['min'] == curr_time.minute:
                print("Sending message!")
                message = client.messages \
                        .create(
                                body=pill['message'],
                                from_='+14436376388',
                                to='+14107393906'
                        )
                speak(engine,pill['message'])
        time.sleep(60)
    
        