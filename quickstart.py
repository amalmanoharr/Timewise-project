import datetime
import os.path
from sys import argv #inorder to access the command line arguments
import sqlite3


from dateutil import parser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
#With the https://www.googleapis.com/auth/calendar scope, your application can create, modify, and delete events in the user’s Google Calendar.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
  
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:

    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  if argv[1] == "add":
     duration = argv[2]
     description = argv[3]
     addEvent(creds, duration , description)
  if argv[1] == "commit":
     commitHours(creds)
  if argv[1] == "gethours":
     no_of_days = argv[2]
     gethours(no_of_days)
  

def commitHours(creds): 
    try:
        service = build("calendar", "v3", credentials=creds)#connect to calender api

        # Call the Calendar API
        today= datetime.date.today() # to get todays date
        timeStart = str(today) + "T00:00:00Z"
        timeEnd = str(today) + "T23:59:59Z"
        print("Getting todays's coding hours")
        events_result = (service.events().list(calendarId="7c2b9c467c79dbe6e8f0fc657a18a59a177c924cb8ccda76734baf8ea32cf14e@group.calendar.google.com",timeMin=timeStart,
            timeMax = timeEnd,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",).execute())
        #the above line will save the events
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return
        
        total_duration = datetime.timedelta(
           seconds = 0,
           minutes = 0,
           hours = 0,
        )
        id = 0
        print('CODING HOURS')
        
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event['end'].get('dateTime',event['end'].get('date'))

            start_formatted = parser.isoparse(start) #changing the start time to date time format
            end_formatted = parser.isoparse(end) #changing the endtime to date time format
            duration = end_formatted - start_formatted

            total_duration += duration
            print(f"{event['summary']}, duration :{duration}")
        print(f"Total coding time :{total_duration}")

        conn = sqlite3.connect('hours.db')
        cur = conn.cursor()
        print('opened database successfully')
        date = datetime.date.today()

        formatted_total_duration = total_duration.seconds/60/60
        coding_hours = (date, 'CODING', formatted_total_duration)
        cur.execute('INSERT INTO hours VALUES(?,?,?);', coding_hours)
        conn.commit()

    except HttpError as error:
        print(f"An error occurred: {error}")

def addEvent(creds, duration, description):
   start = datetime.datetime.utcnow()

   end = datetime.datetime.utcnow() + datetime.timedelta(hours=int(duration))
   start_formatted = start.isoformat() + 'Z'
   end_formatted = end.isoformat() + 'Z'

   event = {
      'summary':description,
      'start': {
         'dateTime':start_formatted,
         'timeZone':'Europe/London'
      },
      'end':{
         'dateTime':end_formatted,
         'timeZone':'Europe/London'
      },
   }
   service = build('calendar','v3',credentials=creds)
   event = service.events().insert(calendarId='7c2b9c467c79dbe6e8f0fc657a18a59a177c924cb8ccda76734baf8ea32cf14e@group.calendar.google.com',body=event).execute()
   print('Event created: %s' %(event.get('htmlLink')))

def gethours(no_of_days):
   #get todays date
   today = datetime.date.today()
   seven_days_ago = today + datetime.timedelta(days=-int(no_of_days))
   #get hours from db
   conn = sqlite3.connect("hours.db")
   cur = conn.cursor()
   cur.execute("SELECT DATE, HOURS from hours WHERE DATE between ? AND ?",(seven_days_ago,today))
   hours = cur.fetchall()

   totalhours = 0
   for element in hours:
      print(f"{element[0]}:{element[1]}")
      totalhours += element[1]
   print(f"Total hours : {totalhours}")
   print(f"Average hours : {totalhours/float(no_of_days)}")


if __name__ == "__main__":
  main()