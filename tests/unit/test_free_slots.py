import unittest
from unittest.mock import patch, MagicMock
import datetime
from zoneinfo import ZoneInfo

from julian_gregory.tools import find_free_slots

class TestFindFreeSlots(unittest.TestCase):

    def setUp(self):
        # Default timezone for tests
        self.time_zone = ZoneInfo("America/Los_Angeles")
        
        # A fixed point in time for consistent tests. Let's say it's a Monday.
        self.now = datetime.datetime(2025, 12, 8, 10, 0, 0, tzinfo=self.time_zone) # Monday

    @patch('julian_gregory.tools.get_upcoming_events')
    @patch('julian_gregory.tools._get_calendar_and_time_info')
    def test_basic_free_slots(self, mock_get_calendar_info, mock_get_upcoming_events):
        """Tests finding free slots on a day with a single event."""
        
        # Mock the helper functions
        mock_get_calendar_info.return_value = (None, self.time_zone, self.now)
        
        # A single event on Tuesday from 10am to 11am
        tuesday = self.now.date() + datetime.timedelta(days=1)
        event_start = datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 10, 0, 0, tzinfo=self.time_zone)
        event_end = event_start + datetime.timedelta(hours=1)
        
        mock_get_upcoming_events.return_value = [
            {
                'start': {'dateTime': event_start.isoformat()},
                'end': {'dateTime': event_end.isoformat()}
            }
        ]
        
        # Create a mock ToolContext
        mock_tool_context = MagicMock()
        
        free_slots = find_free_slots(mock_tool_context)
        
        # No slot should overlap with the 10-11 event
        for slot in free_slots:
            slot_start = datetime.datetime.fromisoformat(slot['start'])
            slot_end = datetime.datetime.fromisoformat(slot['end'])
            # Check only for slots on that Tuesday
            if slot_start.date() == tuesday:
                self.assertFalse(max(slot_start, event_start) < min(slot_end, event_end))

        # Check that we find a slot that should be free, e.g., 8am-9am on Tuesday
        expected_slot_start = datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 8, 0, 0, tzinfo=self.time_zone)
        expected_slot_end = expected_slot_start + datetime.timedelta(hours=1)
        self.assertIn({
            'start': expected_slot_start.isoformat(),
            'end': expected_slot_end.isoformat()
        }, free_slots)
        
        # Check a slot after the event
        expected_slot_start_after = datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 11, 0, 0, tzinfo=self.time_zone)
        expected_slot_end_after = expected_slot_start_after + datetime.timedelta(hours=1)
        self.assertIn({
            'start': expected_slot_start_after.isoformat(),
            'end': expected_slot_end_after.isoformat()
        }, free_slots)


    @patch('julian_gregory.tools.get_upcoming_events')
    @patch('julian_gregory.tools._get_calendar_and_time_info')
    def test_no_events(self, mock_get_calendar_info, mock_get_upcoming_events):
        """Tests a day with no events, should return all slots."""
        mock_get_calendar_info.return_value = (None, self.time_zone, self.now)
        mock_get_upcoming_events.return_value = [] # No events
        
        mock_tool_context = MagicMock()
        
        # Find slots for the next day (Tuesday)
        free_slots = find_free_slots(mock_tool_context, time_delta_in_days=1)

        tuesday = self.now.date() + datetime.timedelta(days=1)
        
        # Expected number of 1-hour slots from 8am to 5pm, incrementing by 30 mins
        # 8:00, 8:30, 9:00, 9:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00
        # The last slot starts at 16:00 to end at 17:00. That's 17 slots.
        self.assertEqual(len(free_slots), 17)
        
        # Check the first and last slots
        first_slot_start = datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 8, 0, 0, tzinfo=self.time_zone)
        self.assertEqual(free_slots[0]['start'], first_slot_start.isoformat())
        
        last_slot_start = datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 16, 0, 0, tzinfo=self.time_zone)
        self.assertEqual(free_slots[-1]['start'], last_slot_start.isoformat())


    @patch('julian_gregory.tools.get_upcoming_events')
    @patch('julian_gregory.tools._get_calendar_and_time_info')
    def test_weekend_day(self, mock_get_calendar_info, mock_get_upcoming_events):
        """Tests that no slots are returned for a weekend."""
        # Set 'now' to a Friday, so the next 2 days are Saturday and Sunday
        friday_now = datetime.datetime(2025, 12, 12, 10, 0, 0, tzinfo=self.time_zone)
        mock_get_calendar_info.return_value = (None, self.time_zone, friday_now)
        mock_get_upcoming_events.return_value = []

        mock_tool_context = MagicMock()
        
        # Search over the next 2 days (Saturday, Sunday)
        free_slots = find_free_slots(mock_tool_context, time_delta_in_days=2)
        
        self.assertEqual(len(free_slots), 0)

    @patch('julian_gregory.tools.get_upcoming_events')
    @patch('julian_gregory.tools._get_calendar_and_time_info')
    def test_overlapping_events(self, mock_get_calendar_info, mock_get_upcoming_events):
        """Tests that overlapping events are merged correctly."""
        mock_get_calendar_info.return_value = (None, self.time_zone, self.now)
        
        tuesday = self.now.date() + datetime.timedelta(days=1)
        
        # Event 1: 9:00 - 10:30
        event1_start = datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 9, 0, 0, tzinfo=self.time_zone)
        event1_end = event1_start + datetime.timedelta(minutes=90)
        # Event 2: 10:00 - 11:00 (overlaps with event 1)
        event2_start = datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 10, 0, 0, tzinfo=self.time_zone)
        event2_end = event2_start + datetime.timedelta(hours=1)
        
        mock_get_upcoming_events.return_value = [
            {'start': {'dateTime': event1_start.isoformat()}, 'end': {'dateTime': event1_end.isoformat()}},
            {'start': {'dateTime': event2_start.isoformat()}, 'end': {'dateTime': event2_end.isoformat()}},
        ]
        
        mock_tool_context = MagicMock()
        free_slots = find_free_slots(mock_tool_context, time_delta_in_days=1)

        # The merged busy slot should be from 9:00 to 11:00
        merged_busy_start = event1_start
        merged_busy_end = event2_end

        # Check that no free slots are found inside the merged busy period
        for slot in free_slots:
            slot_start = datetime.datetime.fromisoformat(slot['start'])
            slot_end = datetime.datetime.fromisoformat(slot['end'])
            self.assertFalse(max(slot_start, merged_busy_start) < min(slot_end, merged_busy_end))
            
        # Check that a slot right before is found
        expected_slot_before = {
            'start': datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 8, 0, 0, tzinfo=self.time_zone).isoformat(),
            'end': datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 9, 0, 0, tzinfo=self.time_zone).isoformat()
        }
        self.assertIn(expected_slot_before, free_slots)
        
        # Check that a slot right after is found
        expected_slot_after = {
            'start': datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 11, 0, 0, tzinfo=self.time_zone).isoformat(),
            'end': datetime.datetime(tuesday.year, tuesday.month, tuesday.day, 12, 0, 0, tzinfo=self.time_zone).isoformat()
        }
        self.assertIn(expected_slot_after, free_slots)

if __name__ == '__main__':
    unittest.main()
