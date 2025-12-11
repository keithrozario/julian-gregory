from unittest.mock import MagicMock, patch
import datetime
from zoneinfo import ZoneInfo
from julian_gregory.tools import find_free_slots_for_multiple_users


@patch('julian_gregory.tools._get_calendar_and_time_info')
def test_find_free_slots_for_multiple_users_with_free_slots(mock_get_calendar_and_time_info):
    """Tests that the function finds free slots when there are some available."""
    # Mock ToolContext and calendar service
    tool_context = MagicMock()
    calendar_service = MagicMock()
    mock_get_calendar_and_time_info.return_value = (
        calendar_service, 
        ZoneInfo("UTC"), 
        datetime.datetime(2025, 12, 14, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    )

    # Mock user emails
    user_emails = ["user1@example.com", "user2@example.com"]

    # Mock free/busy result
    freebusy_result = {
        "calendars": {
            "user1@example.com": {
                "busy": [
                    {"start": "2025-12-15T10:00:00Z", "end": "2025-12-15T11:00:00Z"}
                ]
            },
            "user2@example.com": {
                "busy": [
                    {"start": "2025-12-15T14:00:00Z", "end": "2025-12-15T15:00:00Z"}
                ]
            }
        }
    }
    calendar_service.freebusy.return_value.query.return_value.execute.return_value = freebusy_result

    # Call the function
    free_slots = find_free_slots_for_multiple_users(tool_context, user_emails, slot_duration_minutes=60, time_delta_in_days=1, business_hours_start=9, business_hours_end=17)

    # Assertions
    assert len(free_slots) > 0

    # Check that there are no slots that overlap with the busy times
    for slot in free_slots:
        slot_start = datetime.datetime.fromisoformat(slot['start'])
        slot_end = datetime.datetime.fromisoformat(slot['end'])
        assert not (slot_start < datetime.datetime.fromisoformat("2025-12-15T11:00:00+00:00") and slot_end > datetime.datetime.fromisoformat("2025-12-15T10:00:00+00:00"))
        assert not (slot_start < datetime.datetime.fromisoformat("2025-12-15T15:00:00+00:00") and slot_end > datetime.datetime.fromisoformat("2025-12-15T14:00:00+00:00"))


@patch('julian_gregory.tools._get_calendar_and_time_info')
def test_find_free_slots_for_multiple_users_no_free_slots(mock_get_calendar_and_time_info):
    """Tests that the function returns an empty list when there are no free slots."""
    # Mock ToolContext and calendar service
    tool_context = MagicMock()
    calendar_service = MagicMock()
    mock_get_calendar_and_time_info.return_value = (
        calendar_service, 
        ZoneInfo("UTC"), 
        datetime.datetime(2025, 12, 14, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    )

    # Mock user emails
    user_emails = ["user1@example.com"]

    # Mock free/busy result
    freebusy_result = {
        "calendars": {
            "user1@example.com": {
                "busy": [
                    {"start": "2025-12-15T09:00:00Z", "end": "2025-12-15T17:00:00Z"}
                ]
            }
        }
    }
    calendar_service.freebusy.return_value.query.return_value.execute.return_value = freebusy_result

    # Call the function
    free_slots = find_free_slots_for_multiple_users(tool_context, user_emails, slot_duration_minutes=60, time_delta_in_days=1, business_hours_start=9, business_hours_end=17)

    # Assertions
    assert len(free_slots) == 0


@patch('julian_gregory.tools._get_calendar_and_time_info')
def test_find_free_slots_for_multiple_users_duration_too_long(mock_get_calendar_and_time_info):
    """Tests that the function returns an empty list when the duration is longer than any available slot."""
    # Mock ToolContext and calendar service
    tool_context = MagicMock()
    calendar_service = MagicMock()
    mock_get_calendar_and_time_info.return_value = (
        calendar_service, 
        ZoneInfo("UTC"), 
        datetime.datetime(2025, 12, 14, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    )

    # Mock user emails
    user_emails = ["user1@example.com"]

    # Mock free/busy result
    freebusy_result = {
        "calendars": {
            "user1@example.com": {
                "busy": []
            }
        }
    }
    calendar_service.freebusy.return_value.query.return_value.execute.return_value = freebusy_result

    # Call the function
    free_slots = find_free_slots_for_multiple_users(tool_context, user_emails, slot_duration_minutes=120, time_delta_in_days=1, business_hours_start=9, business_hours_end=10)

    # Assertions
    assert len(free_slots) == 0


@patch('julian_gregory.tools._get_calendar_and_time_info')
def test_find_free_slots_for_multiple_users_no_busy_slots(mock_get_calendar_and_time_info):
    """Tests that the function returns a full list of slots when there are no busy slots."""
    # Mock ToolContext and calendar service
    tool_context = MagicMock()
    calendar_service = MagicMock()
    mock_get_calendar_and_time_info.return_value = (
        calendar_service, 
        ZoneInfo("UTC"), 
        datetime.datetime(2025, 12, 14, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    )

    # Mock user emails
    user_emails = ["user1@example.com"]

    # Mock free/busy result
    freebusy_result = {
        "calendars": {
            "user1@example.com": {
                "busy": []
            }
        }
    }
    calendar_service.freebusy.return_value.query.return_value.execute.return_value = freebusy_result

    # Call the function
    free_slots = find_free_slots_for_multiple_users(tool_context, user_emails, slot_duration_minutes=60, time_delta_in_days=1, business_hours_start=9, business_hours_end=17)

    # Assertions
    assert len(free_slots) == 15 # 8 hours, 30 min increment, 60 min slot


@patch('julian_gregory.tools._get_calendar_and_time_info')
def test_find_free_slots_for_multiple_users_weekend(mock_get_calendar_and_time_info):
    """Tests that the function returns an empty list for a weekend day."""
    # Mock ToolContext and calendar service
    tool_context = MagicMock()
    calendar_service = MagicMock()
    mock_get_calendar_and_time_info.return_value = (
        calendar_service, 
        ZoneInfo("UTC"), 
        datetime.datetime(2025, 12, 12, 12, 0, 0, tzinfo=ZoneInfo("UTC")) # A Friday, so the next day is Saturday
    )

    # Mock user emails
    user_emails = ["user1@example.com"]

    # Mock free/busy result
    freebusy_result = {
        "calendars": {
            "user1@example.com": {
                "busy": []
            }
        }
    }
    calendar_service.freebusy.return_value.query.return_value.execute.return_value = freebusy_result

    # Call the function
    free_slots = find_free_slots_for_multiple_users(tool_context, user_emails, slot_duration_minutes=60, time_delta_in_days=1, business_hours_start=9, business_hours_end=17)

    # Assertions
    assert len(free_slots) == 0


@patch('julian_gregory.tools._get_calendar_and_time_info')
def test_find_free_slots_for_multiple_users_multiple_busy_slots(mock_get_calendar_and_time_info):
    """Tests that the function correctly handles multiple busy slots in a day."""
    # Mock ToolContext and calendar service
    tool_context = MagicMock()
    calendar_service = MagicMock()
    mock_get_calendar_and_time_info.return_value = (
        calendar_service, 
        ZoneInfo("UTC"), 
        datetime.datetime(2025, 12, 14, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
    )

    # Mock user emails
    user_emails = ["user1@example.com"]

    # Mock free/busy result
    freebusy_result = {
        "calendars": {
            "user1@example.com": {
                "busy": [
                    {"start": "2025-12-15T10:00:00Z", "end": "2025-12-15T11:00:00Z"},
                    {"start": "2025-12-15T13:00:00Z", "end": "2025-12-15T14:00:00Z"}
                ]
            }
        }
    }
    calendar_service.freebusy.return_value.query.return_value.execute.return_value = freebusy_result

    # Call the function
    free_slots = find_free_slots_for_multiple_users(tool_context, user_emails, slot_duration_minutes=60, time_delta_in_days=1, business_hours_start=9, business_hours_end=17)

    # Assertions
    assert len(free_slots) == 9
