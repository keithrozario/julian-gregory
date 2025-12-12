from google.adk.tools.tool_context import ToolContext
import datetime
from zoneinfo import ZoneInfo
from .helper_funcs import get_calendar_service, get_user_info


def _get_calendar_and_time_info(tool_context: ToolContext):
    """Helper to get calendar service, timezone, and current time."""
    calendar_service = get_calendar_service(tool_context)
    time_zone_str = calendar_service.calendars().get(calendarId="primary").execute()['timeZone']
    time_zone = ZoneInfo(time_zone_str)
    now = datetime.datetime.now(time_zone)
    return calendar_service, time_zone, now


def get_upcoming_events(tool_context: ToolContext, time_delta_in_days: int=7) -> list[dict]:
    """
    Returns all events from now until time_delta_in_days into the future
    Args:
        time_delta_in_days: The number of days to look into the future
    returns
        events: List of Dicts of the events
    """
    calendar_service, time_zone, now = _get_calendar_and_time_info(tool_context)
    start_of_today = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=time_zone)
    end_time = start_of_today + datetime.timedelta(days=time_delta_in_days)
    
    time_min = now.isoformat()
    time_max = end_time.isoformat()

    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get("items", [])

    return events


def get_todays_events(tool_context: ToolContext) -> list[dict]:
    """
    Gets a list of events for today. 
    Today is inferred between the system time and timeZone set on the calendar.

    returns:
        events: List of Dicts of the events
    """

    calendar_service, time_zone, now = _get_calendar_and_time_info(tool_context)
    
    start_of_today = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=time_zone)
    start_of_tomorrow = start_of_today + datetime.timedelta(days=1)
    
    time_min = start_of_today.isoformat()
    time_max = start_of_tomorrow.isoformat()

    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get("items", [])

    return events


def get_weeks_events(tool_context: ToolContext) -> list[dict]:
    """
    Gets a list of events for the week. 
    The week is inferred between the system time and timeZone set on the calendar.

    returns:
        events: List of Dicts of the events
    """

    calendar_service, time_zone, now = _get_calendar_and_time_info(tool_context)

    start_of_today = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=time_zone)
    days_until_end_of_week = 7 - now.weekday()
    
    time_min = start_of_today.isoformat()
    time_max = (start_of_today + datetime.timedelta(days=days_until_end_of_week)).isoformat()

    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get("items", [])

    return events


def find_free_slots(tool_context: ToolContext, slot_duration_minutes: int = 60, time_delta_in_days: int = 14, business_hours_start: int = 8, business_hours_end: int = 17) -> list[dict]:
    """
    Finds all free time slots of a given duration in the next specified number of days during business hours.
    Business hours are Monday to Friday.
    """
    _, time_zone, now = _get_calendar_and_time_info(tool_context)
    
    events = get_upcoming_events(tool_context, time_delta_in_days=time_delta_in_days)
    
    def parse_datetime_from_event(event_time_dict):
        dt_str = event_time_dict.get('dateTime')
        if dt_str:
            return datetime.datetime.fromisoformat(dt_str)
        return None

    busy_intervals = []
    for event in events:
        start = parse_datetime_from_event(event.get('start', {}))
        end = parse_datetime_from_event(event.get('end', {}))
        if start and end:
            busy_intervals.append((start.astimezone(time_zone), end.astimezone(time_zone)))

    # Sort intervals by start time
    busy_intervals.sort()

    # Merge overlapping intervals
    # The result is a clean list of non-overlapping intervals representing all the busy periods.
    if not busy_intervals:
        merged_busy_intervals = []
    else:
        merged_busy_intervals = [busy_intervals[0]]
        for current_start, current_end in busy_intervals[1:]:
            last_start, last_end = merged_busy_intervals[-1]
            if current_start < last_end:
                merged_busy_intervals[-1] = (last_start, max(last_end, current_end))
            else:
                merged_busy_intervals.append((current_start, current_end))

    free_slots = []
    slot_duration = datetime.timedelta(minutes=slot_duration_minutes)
    increment = datetime.timedelta(minutes=30) # Check for a new slot every 30 minutes
    
    start_date = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(time_delta_in_days):
        current_day = start_date + datetime.timedelta(days=day_offset)

        if current_day.weekday() >= 5:  # Skip weekends
            continue
        
        day_start = current_day.replace(hour=business_hours_start, minute=0, second=0, microsecond=0)
        day_end = current_day.replace(hour=business_hours_end, minute=0, second=0, microsecond=0)

        potential_slot_start = day_start
        while potential_slot_start + slot_duration <= day_end:
            potential_slot_end = potential_slot_start + slot_duration
            
            is_overlapping = False
            for busy_start, busy_end in merged_busy_intervals:
                if max(potential_slot_start, busy_start) < min(potential_slot_end, busy_end):
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                free_slots.append({
                    "start": potential_slot_start.isoformat(),
                    "end": potential_slot_end.isoformat(),
                })
            
            potential_slot_start += increment
            
    return free_slots


def find_free_slots_for_multiple_users(tool_context: ToolContext, user_emails: list[str], slot_duration_minutes: int = 60, time_delta_in_days: int = 14, business_hours_start: int = 8, business_hours_end: int = 17) -> list[dict]:
    """
    Finds all free time slots of a given duration for multiple users in the next specified number of days during business hours.
    Business hours are Monday to Friday.
    """
    calendar_service, time_zone, now = _get_calendar_and_time_info(tool_context)
    
    time_min = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    time_max = (now + datetime.timedelta(days=time_delta_in_days)).replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    calendar_ids = [{"id": email} for email in user_emails]

    freebusy_query = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": calendar_ids
    }

    freebusy_result = calendar_service.freebusy().query(body=freebusy_query).execute()
    
    busy_intervals = []
    for calendar_id, data in freebusy_result['calendars'].items():
        for busy_period in data['busy']:
            busy_intervals.append((
                datetime.datetime.fromisoformat(busy_period['start']).astimezone(time_zone),
                datetime.datetime.fromisoformat(busy_period['end']).astimezone(time_zone)
            ))

    # Sort intervals by start time
    busy_intervals.sort()

    # Merge overlapping intervals
    if not busy_intervals:
        merged_busy_intervals = []
    else:
        merged_busy_intervals = [busy_intervals[0]]
        for current_start, current_end in busy_intervals[1:]:
            last_start, last_end = merged_busy_intervals[-1]
            if current_start < last_end:
                merged_busy_intervals[-1] = (last_start, max(last_end, current_end))
            else:
                merged_busy_intervals.append((current_start, current_end))

    free_slots = []
    slot_duration = datetime.timedelta(minutes=slot_duration_minutes)
    increment = datetime.timedelta(minutes=30) # Check for a new slot every 30 minutes
    
    start_date = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(time_delta_in_days):
        current_day = start_date + datetime.timedelta(days=day_offset)

        if current_day.weekday() >= 5:  # Skip weekends
            continue
        
        day_start = current_day.replace(hour=business_hours_start, minute=0, second=0, microsecond=0, tzinfo=time_zone)
        day_end = current_day.replace(hour=business_hours_end, minute=0, second=0, microsecond=0, tzinfo=time_zone)

        potential_slot_start = day_start
        while potential_slot_start + slot_duration <= day_end:
            potential_slot_end = potential_slot_start + slot_duration
            
            is_overlapping = False
            for busy_start, busy_end in merged_busy_intervals:
                if max(potential_slot_start, busy_start) < min(potential_slot_end, busy_end):
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                free_slots.append({
                    "start": potential_slot_start.isoformat(),
                    "end": potential_slot_end.isoformat(),
                })
            
            potential_slot_start += increment
            
    return free_slots


def set_calendar_entry(location: str, summary: str, description: str, start_datetime_isoformat: str, end_datetime_isoformat: str,
                     tool_context: ToolContext) -> dict:
    """
    Sets a calendar entry. The agents uses strings to call the function even when type hints suggest datetime objects.

    So I set this to strings instead.

    Args: 
        start_datetime_isoformat: The start time of the meeting
        end_datetime_isoformat: The end time of the meeting
    """

    calendar_service, time_zone, _ = _get_calendar_and_time_info(tool_context)
    time_zone_str = str(time_zone)

    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_datetime_isoformat,
            "timeZone": time_zone_str

        },
        "end": {
            "dateTime": end_datetime_isoformat,
            "timeZone": time_zone_str
        },
    }
    
    event = calendar_service.events().insert(calendarId="primary", body=event).execute()
    # Return the created event object, which contains the ID, link, etc.
    return event


def decline_all_todays_events(tool_context: ToolContext):
    """
    Declines all of todays events.
    Sets the responseStatus to decline
    """

    calendar_service, _, _ = _get_calendar_and_time_info(tool_context)
    events = get_todays_events(tool_context)
    user_email = get_user_info(tool_context)['email']
    declined_events = []

    for event in events:
        # Skip events without attendees or where the user is not an attendee
        if 'attendees' not in event:
            continue

        user_as_attendee = next((att for att in event['attendees'] if att.get('email') == user_email), None)

        # If the user is an attendee and their status is not already declined
        if user_as_attendee and user_as_attendee.get('responseStatus') != 'declined':
            user_as_attendee['responseStatus'] = 'declined'
            user_as_attendee['comment'] = "Declined by Julian"
            
            # Patch the event with the updated attendee list once per event
            calendar_service.events().patch(calendarId='primary', eventId=event['id'], body=event).execute()
            declined_events.append({
                "Event Title": event.get('summary', 'No Title'),
                "start": event.get('start', {}).get('dateTime'),
                "end": event.get('end', {}).get('dateTime')
            })

    return declined_events


def add_attendees_to_event(tool_context: ToolContext, event_id: str, attendees: list[str]) -> dict:
    """
    Adds a list of attendees to an existing event.
    """
    calendar_service, _, _ = _get_calendar_and_time_info(tool_context)
    event = calendar_service.events().get(calendarId='primary', eventId=event_id).execute()

    if 'attendees' not in event:
        event['attendees'] = []

    for attendee_email in attendees:
        event['attendees'].append({'email': attendee_email})

    updated_event = calendar_service.events().patch(calendarId='primary', eventId=event['id'], body=event, sendUpdates='all').execute()

    return updated_event

def get_now(tool_context: ToolContext):
    """
    Returns the current time according to the timezone of the users primary calendar's timezone
    """
    _, _, now = _get_calendar_and_time_info(tool_context)
    return now.isoformat()


def reschedule_event(tool_context: ToolContext, event_id: str, new_start_datetime_isoformat: str, new_end_datetime_isoformat: str):
    """
    Receives and event id, and new time, and reschedules and event
    Args:
        event_id: Event id of the event to reschedule
        new_start_datetime_isoformat: The new startime of the event
        new_end_datetime_isoformat: The new endtime of the event
    """

    calendar_service, _, _ = _get_calendar_and_time_info(tool_context)
    event = calendar_service.events().get(calendarId='primary', eventId=event_id).execute()
    event['start']['dateTime'] = new_start_datetime_isoformat
    event['end']['dateTime'] = new_end_datetime_isoformat
    updated_event = calendar_service.events().patch(calendarId='primary', eventId=event['id'], body=event, sendUpdates='all').execute()

    return updated_event


def decline_event(tool_context: ToolContext, event_id: str, decline_comment: str="Declined by Julian"):
    """
    Declines an event with a message
    
    Args:
        event_id: The Event id of the event to reschedule
        decline_message: A message to decline
    """
    calendar_service, _, _ = _get_calendar_and_time_info(tool_context)
    user_email = get_user_info(tool_context)['email']
    event = calendar_service.events().get(calendarId='primary', eventId=event_id).execute()
    user_as_attendee = next((att for att in event['attendees'] if att.get('email') == user_email), None)

    if user_as_attendee:
        user_as_attendee['responseStatus'] = 'declined'
        user_as_attendee['comment'] = decline_comment
        calendar_service.events().patch(calendarId='primary', eventId=event['id'], body=event).execute()

    return event