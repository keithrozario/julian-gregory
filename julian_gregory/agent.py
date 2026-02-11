from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools.agent_tool import AgentTool

from functools import cached_property
import os
from google.adk.models import Gemini
from google.genai import Client, types

from . import tools

class Gemini3(Gemini):

    # https://github.com/google/adk-python/issues/3628#issuecomment-3595215761
    
    @cached_property
    def api_client(self) -> Client:
        """Provides the api client with explicit configuration.

        Returns:
        The api client initialized with specific location and http_options.
        """
        # Ensure project ID is retrieved, falling back to a placeholder or raising an error if needed.
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "xxxxx")
        

        return Client(
            project=project,
            location="global",
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
            )
        )


summary_agent = Agent(
    name="summary_agent",
    model=Gemini3(model="gemini-3-pro-image-preview"),
    description=("An agent that provides a summary of the day's events"),
    instruction=(
"""
You are a helpful assistant that will summarize the days meetings for a user. 

Look through the events for the day or week and provide a useful summary of:

1. All meetings and events taking place todayor this week
2. Any free slots and time that are in the calendar
3. Any last minute meetings that were booked after 5pm yesterday should be flagged.

Here's an example summary:

Summary: You have a busy day ahead with many back-2-back meetings. Remember to hydrate and take breaks.

Meetings:

1. Meeting with Brad. 9-10pm, <link to meeting>
2. Project ABC team huddle 10.30-11am, <link to meeting>
3. Lunch with Randy, <link to meeting>
4. .....

Late last night an invite for quick huddle at 2pm today was booked into your calendar by Edmund. You may not have read the invite.

"""
    ),
    tools=[tools.get_todays_events],
)

find_free_slots = Agent(
    name="find_free_slots",
    model="gemini-2.5-flash",
    description=("An agent to find free slots available in the calendar"),
    instruction=(
"""
You are a helpful assistant that will find free slots in the users calendar

You will provide the user a list of 1-hour free slots in their calendar that meet user specified criteria including:

1. Duration of the slots, assume 1 hour slot. If not specified assume 1 hour.
2. Time of the slot (morning, afternoon, evening). If not specified assume it is in the morning.
3. Timeline (when the slots should be, e.g. within the week, within the month, etc). Assume within the next 3 days if not specified.

Do not provide slots when user is on Holiday, do not provide slots for non business hours. 

Provide only 5 slots maximum. Prioritise earlier slots over later slots, but not more than 2 slots on the same day.

"""
    ),
    tools=[tools.get_upcoming_events, tools.find_free_slots],
)

cancel_todays_meeting_agent = Agent(
    name="cancel_todays_events",
    model="gemini-2.5-flash",
    description=("An agent to cancel all meetings for today"),
    instruction=(
"""
You are a calendar assistant that helps the user manage their calendar.

You will cancel all events for the day, and report back to the user all events that were cancelled.

Here's an example response:

I have declined all the meetings below for today.

Meetings:

1. Meeting with Brad. 9-10pm, <link to meeting>
2. Project ABC team huddle 10.30-11am, <link to meeting>
3. Lunch with Randy, <link to meeting>
4. .....
"""
    ),
    tools=[tools.decline_all_todays_events],
)

move_meeting_agent = Agent(
    name="move_meeting_agent",
    model="gemini-2.5-flash",
    description=("An agent to help move a meeting from one time to another"),
    instruction=(
""" 
You are a helpful assistant, and tasked to move a meeting from one time to another.

Use the tools at your disposal to find a suitable time to move a meeting.

1. First determine the actual event the user is asking for by looking at upcoming events
2. Then determine the next available free slot in the timeline the user provided that is free for all attendees
3. Ask the user which slot works best
4. If the user is the organizer reschedule the event, move the event to the new time
5. If the user is not the organizer, decline the event and propose the new time in a comment

"""
    ),
    tools=[
        tools.find_free_slots_for_multiple_users,
        tools.get_upcoming_events,
        tools.decline_event,
        tools.reschedule_event,
        tools.get_now,
           ],
)

root_agent = Agent(
    name="julian_gregory_day",
    model=Gemini3(model="gemini-3-pro-preview"),
    description=("Julian is an agent that helps users with their Calendars"),
    instruction=(
"""
You are a helpful calendar agent. You help users organize their calendars using the tools and subagents at your disposal.
If you call other agents, provide back the user the original answer from the agent.

You can also help arrange for meetings with multiple attendees. If a user asks to setup a meeting with other attendees, perform the following actions:

1. Check for free slots with the users
2. Propose a maximum of 3 slots to the users and seek their confirmation
3. Set a calendar entry for the user and add the attendees.

Always check todays date, do not book meetings before now, or meetings more than 6 months into the future.
"""
    ),
    tools=[
        AgentTool(agent=summary_agent),
        AgentTool(agent=cancel_todays_meeting_agent),
        AgentTool(find_free_slots),
        tools.set_calendar_entry,
        tools.add_attendees_to_event,
        tools.find_free_slots_for_multiple_users,
        tools.get_now
    ],
    sub_agents=[move_meeting_agent]
)


app = App(root_agent=root_agent, name="julian_gregory")