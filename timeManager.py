from __future__ import print_function

import datetime
import os.path
from sys import argv

import sqlite3
from dateutil import parser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
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
  if argv[1] == 'add':
    duration = argv[2]
    description = argv[3]
    addEvent(creds, duration, description) 
  if argv[1] == 'commit':  
    commitHours(creds)  
   

def commitHours(creds):
  try:
    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    today = datetime.date.today()
    timeStart = str(today) + "T00:00:00Z"
    timeEnd = str(today) + "T23:59:59Z"
    print("Getting today's coding hours")
    events_result = (service.events().list(calendarId="7b2c30dbeacd99e2e494e8e1f563163b1ca5a4b8580cb8ae042b515fc37039a3@group.calendar.google.com", timeMin=timeStart, timeMax=timeEnd, singleEvents=True, orderBy="startTime", timeZone="Asia/Kolkata").execute())
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return
    
    total_duration = datetime.timedelta(
      seconds=0,
      minutes=0,
      hours=0,
    )
    
    print("CODING HOURS:")
    for event in events:
      start = event['start'].get('dateTime', event['start'].get('date'))
      end = event['end'].get('dateTime', event['end'].get('date'))

      start_formatted = parser.isoparse(start)
      end_formatted = parser.isoparse(end)
      duration = end_formatted - start_formatted

      total_duration += duration
      print(f"{event['summary']}, duration: {duration}")
    print(f"Total coding time:{total_duration}")

    conn = sqlite3.connect('hours.db')
    cur = conn.cursor()
    print("Opened database successfully")
    date = datetime.date.today()

    formatted_total_duration = total_duration.seconds/60/60
    coding_hours = (date, 'CODING', formatted_total_duration)
    cur.execute("INSERT INTO hours VALUES(?, ?, ?);", coding_hours)
    conn.commit()
    print("Coding hours added to database successfully")
  
  except HttpError as error:
   print('An error occured: %s' % error)

def addEvent(creds, duration, description):
  start = datetime.datetime.now()
  
  end = datetime.datetime.now() + datetime.timedelta(hours=int(duration))
  start_formatted = start.isoformat() + 'Z'
  end_formatted = end.isoformat() + 'Z'
  
  event ={
  'summary': description,
  'start': {
    'dateTime': start_formatted,
    'timeZone': 'Asia/Kolkata',
  },
  'end': {
    'dateTime': end_formatted,
    'timeZone': 'Asia/Kolkata',
  },
}
  
  service = build('calendar', 'v3', credentials=creds)
  event = service.events().insert(calendarId="7b2c30dbeacd99e2e494e8e1f563163b1ca5a4b8580cb8ae042b515fc37039a3@group.calendar.google.com",body=event).execute()
  print('Event created: %s' %(event.get('htmlLink')))

if __name__ == "__main__":
  main()