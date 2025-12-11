# Julian Gregory - The Calendar assistant

## What does it do?

The Calendar assistant can help:

1. Summarize the days meetings
2. Summarize the weeks meetings
3. Cancel all your meetings with an apology to participants (for when you have an emergency)
4. Book trainings into your calendar (perhaps after reading your email)
5. Adjust the trainings on your calendar (e.g. move everything by a week)
6. Create a Google Doc to prep for a meeting
7. Book an appointment (dental, car service, etc)

## How does it do it?

We cannot rely on Gemini Enterprise Assistant capability we instead of have to create a custom agent that oAuths into the Google Calendar and GMail Apis. Will have to figure out the oAuth works for Gemini Enterprise, which will be doubly fun ;)

## Why the name?

There is a batman villian called [Calendar Man](https://en.wikipedia.org/wiki/Calendar_Man), whose real name is Julian Gregory Day, named after the Julian and Gregorian calendars. I like to name my projects after quirky things!

## What I have so far

I've finally figured out how to OAuth with a custom agent in ADK and Gemini Enterprise.

If you're inside Google, the doc with more info is [here](https://docs.google.com/document/d/1unBzB5Wuqry_WRABrcSnE2R38pBvHogiv_pvqj2rVkY/edit?tab=t.0)

## Next steps

We'll actually have to build the agents with the right prompts for the feature set above.

## References

Google Calendar API - [Link](https://developers.google.com/workspace/calendar/api/guides/overview)

Google Mail API - [Link](https://developers.google.com/workspace/gmail/api/guides)
