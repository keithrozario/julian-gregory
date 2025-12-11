import pytest
import pytest_asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.invocation_context import InvocationContext

from julian_gregory.agent import root_agent
from julian_gregory.tools import decline_all_todays_events

async def create_tool_context(user_id: str | None = "user@user.com"):
    """Helper to create a ToolContext manually."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="test_app", user_id="test_user")
    invocation_context = InvocationContext(
        session_service=session_service,
        session=session,
        invocation_id="123",
        agent=root_agent,
    )
    return ToolContext(invocation_context)

@pytest_asyncio.fixture
async def tool_context_factory():
    async def _factory(user_id: str | None):
        return await create_tool_context(user_id)
    return _factory

@pytest.mark.asyncio
async def test_decline_all_todays_events(tool_context_factory):
    auth_user_context = await tool_context_factory("user@user.com")
    # decline_all_todays_events is synchronous
    result = decline_all_todays_events(tool_context=auth_user_context)
    print(result)