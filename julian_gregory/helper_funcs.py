import os.path

from google.adk.tools.tool_context import ToolContext
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .scopes import SCOPES, AUTHORIZER_NAME


def get_local_creds():
    """
    Gets the Google API credentials
    This function is only executed when running locally. It should never be needed when running on Agent Engine
    There's a difference between Google CLoud auth tokens and GWS auth tokens, they're not interchangeable :(
    """
    token_path = "./token_and_creds/token.json"
    local_credentials_json = "./token_and_creds/credentials_local.json"

    creds = False
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(local_credentials_json, SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    if not creds:
        raise Exception("Unable to get Google Credentials")

    return creds

def get_creds(tool_context: ToolContext):
    """
    Returns the Credentials object for either Gemini Enterprise or Local Host execution
    """
    try:
        oauth_token = tool_context.state[AUTHORIZER_NAME]
        creds = Credentials(token=oauth_token)
    except KeyError:  ## if the AUTHORIZER doesn't exists, then we're on a local machine testing
        creds = get_local_creds()

    return creds

def get_calendar_service(tool_context: ToolContext):
    """
    Returns the Google Calendar service for API interaction
    """
    creds = get_creds(tool_context)
    return build("calendar", "v3", credentials=creds)


def get_gmail_service(tool_context: ToolContext):
    """
    Returns the Google Gmail service for API interaction
    """
    creds = get_creds(tool_context)
    return build("gmail", "v1", credentials=creds)

def get_user_info(tool_context: ToolContext)->dict:
    """
    Returns the user-info object that contains the email and userid of the user.
    We infer the user from the token provided
    """
    creds = get_creds(tool_context)
    user_info_service = build('oauth2','v2',credentials=creds)
    user_info = user_info_service.userinfo().get().execute()
    return user_info

