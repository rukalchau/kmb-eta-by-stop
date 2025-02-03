from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path

class GoogleCalendarEvents:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        # Update to use service account
        self.CREDENTIALS_FILE = 'service-account.json'
        self.calendar_id = 'your-calendar-id@group.calendar.google.com'  # Update this
        self.creds = None

    def authenticate(self):
        try:
            self.creds = service_account.Credentials.from_service_account_file(
                self.CREDENTIALS_FILE, 
                scopes=self.SCOPES
            )
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def get_upcoming_events(self, max_results=10):
        """Get upcoming calendar events"""
        try:
            if not self.creds:
                if not self.authenticate():
                    return []

            service = build('calendar', 'v3', credentials=self.creds)
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            if not events:
                print('No upcoming events found.')
                return []

            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_event = {
                    'summary': event.get('summary', 'No title'),
                    'start': start,
                    'end': end,
                    'description': event.get('description', ''),
                    'location': event.get('location', '')
                }
                formatted_events.append(formatted_event)

            return formatted_events

        except Exception as e:
            print(f"Error fetching events: {e}")
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