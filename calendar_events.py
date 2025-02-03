from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
import pickle

class GoogleCalendarEvents:
    def __init__(self):
        # Update scopes to be more specific
        self.SCOPES = [
            'https://www.googleapis.com/auth/calendar.events.readonly',
            'https://www.googleapis.com/auth/calendar.readonly'
        ]
        self.creds = None
        # Update the credentials file name to match your file
        self.CREDENTIALS_FILE = 'client_secret_302310932458-v0m30pv9tghcqo823upui4phcv4nkp0d.apps.googleusercontent.com.json'

    def authenticate(self):
        # Check if token.pickle exists with saved credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        # If credentials are not valid or don't exist, get new ones
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, 
                    self.SCOPES,
                    redirect_uri='http://localhost:8080/callback'
                )
                self.creds = flow.run_local_server(
                    port=8080,
                    success_message='Authentication successful! You can close this window.'
                )
            
            # Save credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

    def get_upcoming_events(self, max_results=20):
        """Get upcoming calendar events."""
        try:
            self.authenticate()
            service = build('calendar', 'v3', credentials=self.creds)

            # Get current time
            now = datetime.utcnow().isoformat() + 'Z'
            
            # Set time max to 3 days from now
            three_days_from_now = datetime.utcnow() + timedelta(days=3)
            time_max = three_days_from_now.isoformat() + 'Z'

            # Call the Calendar API
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])

            if not events:
                print('No upcoming events found.')
                return []

            # Format and return events
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_event = {
                    'summary': event.get('summary', 'No title'),
                    'start': start,
                    'end': end,
                    'description': event.get('description', 'No description'),
                    'location': event.get('location', 'No location')
                }
                formatted_events.append(formatted_event)

            return formatted_events

        except Exception as e:
            print(f"An error occurred: {e}")
            return []

def main():
    # Example usage
    calendar = GoogleCalendarEvents()
    events = calendar.get_upcoming_events(max_results=5)
    
    # Display events
    for event in events:
        print("\n=== Event ===")
        print(f"Title: {event['summary']}")
        print(f"Start: {event['start']}")
        print(f"End: {event['end']}")
        print(f"Location: {event['location']}")
        print(f"Description: {event['description']}")

if __name__ == '__main__':
    main() 