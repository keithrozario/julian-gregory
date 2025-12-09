from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools.agent_tool import AgentTool
from .tools import get_todays_events, decline_all_todays_events

summary_agent = Agent(
    name="summary_agent",
    model="gemini-2.0-flash",
    description=("An agent that provides a summary of the day's events"),
    instruction=(
"""
You are a helpful assistant that will summarize the days meetings for a user. 

Look through the events for the day and provide a useful summary of:

1. All meetings and events taking place today
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
    tools=[get_todays_events],
)

cancel_todays_meeting_agent = Agent(
    name="cancel_todays_events",
    model="gemini-2.0-flash",
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
    tools=[decline_all_todays_events],

)

root_agent = Agent(
    name="julian_gregory_day",
    model="gemini-2.0-flash",
    description=("Julian is an agent that helps users with their Calendars"),
    instruction=(
        "You are a helpful calendar agent. You help users organize their calendars using the tools and subagents at your disposal." \
        "If you call other agents, provide back the user the original answer from the agent."
    ),
    tools=[
        AgentTool(agent=summary_agent),
        AgentTool(agent=cancel_todays_meeting_agent)
    ],
)


app = App(root_agent=root_agent, name="julian_gregory")