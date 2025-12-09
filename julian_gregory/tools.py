from google.adk.tools.tool_context import ToolContext
import datetime
from zoneinfo import ZoneInfo
from .helper_funcs import get_service, get_user_info


def set_weather(city: str, weather: str, tool_context: ToolContext) -> dict:
    """
    Sets a calendar entry for the weather.
    """

    calendar_service, gmail_service = get_service(tool_context)
    timezone = calendar_service.calendarList().get(calendarId="primary").execute()['timeZone']
    event = {
        "summary": "Weather Update",
        "location": city,
        "description": weather,
        "start": {
            "dateTime": "2025-12-05T09:00:00",
            "timeZone": timezone

        },
        "end": {
            "dateTime": "2025-12-05T17:00:00",
            "timeZone": timezone
        },
    }
    
    event = calendar_service.events().insert(calendarId="primary", body=event).execute()
    return {
        "status": "success",
        "report": "All done"
    }


def get_todays_events(tool_context: ToolContext) -> list[dict]:
    """
    Gets a list of events for today. 
    Today is inferred between the system time and timeZone set on the calendar.

    returns:
        events: List of Dicts of the events
    """


    calendar_service, _ = get_service(tool_context)
    time_zone = calendar_service.calendars().get(calendarId="primary").execute()['timeZone']
    today = datetime.datetime.now(ZoneInfo(time_zone))

    start_of_today = datetime.datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=ZoneInfo(time_zone))
    start_of_tomorrow = start_of_today + datetime.timedelta(days=1)

    # Format as RFC3339 timestamps
    time_min = start_of_today.isoformat()
    time_max = start_of_tomorrow.isoformat()

    # Call the Calendar API events.list method
    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result['items']

    return events


def get_weeks_events(tool_context: ToolContext) -> list[dict]:
    """
    Gets a list of events for the week. 
    The week is inferred between the system time and timeZone set on the calendar.

    returns:
        events: List of Dicts of the events
    """


    calendar_service, _ = get_service(tool_context)
    time_zone = calendar_service.calendars().get(calendarId="primary").execute()['timeZone']
    today = datetime.datetime.now(ZoneInfo(time_zone))

    start_of_today = datetime.datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=ZoneInfo(time_zone))

    # Calculate the number of days until the next Sunday (where Sunday is weekday 6, Monday is 0)
    days_until_this_sunday = 6 - today.weekday()
    time_min = start_of_today.isoformat()
    time_max = (start_of_today + datetime.timedelta(days=days_until_this_sunday)).isoformat()

    # Call the Calendar API events.list method
    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    return events

def set_calendar_entry(location: str, summary: str, description: str, start_date_time: datetime.datetime, end_date_time: datetime.datetime,
                     tool_context: ToolContext) -> dict:
    """
    Sets a calendar entry
    """

    calendar_service, gmail_service = get_service(tool_context)
    timezone = calendar_service.calendarList().get(calendarId="primary").execute()['timeZone']

    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_date_time.isoformat(),
            "timeZone": timezone

        },
        "end": {
            "dateTime": end_date_time.isoformat(),
            "timeZone": timezone
        },
    }
    
    event = calendar_service.events().insert(calendarId="primary", body=event).execute()
    return {
        "status": "success",
        "report": "All done"
    }


def decline_all_todays_events(tool_context: ToolContext):
    """
    Declines or cancels all of todays events.
    """


    calendar_service, _ = get_service(tool_context)
    events = get_todays_events(tool_context)
    user_email = get_user_info(tool_context)['email']

    for event in events:
        try:
            for attendee in event['attendees']:
                if attendee['email'] == user_email:
                    attendee['responseStatus'] = 'declined'
                    attendee['comment'] = "declined by Julian"
                calendar_service.events().patch(calendarId='primary', eventId=event['id'], body=event).execute()
        except KeyError:
            pass # events without attendees don't need to be declined
    
    events = get_todays_events(tool_context)
    summarized_events = [{"Event Title": event['summary'], "start": event['start']['dateTime'], "end": event['end']['dateTime']} for event in events]
                
    return summarized_events