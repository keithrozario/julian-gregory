"""
This script deploys an agent_engine agent into Gemini Enterprise, with a configured authorizer and the scopes.
Currently the script only handles Google Workspace authorizations
"""

import json
import requests
import google.auth
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request

auth_id = "julian-gregory-authorizer"
gemini_app_id = "agentspace-1759116549124_1759116549124"
credentials_file = "credentials_web.json"
deployment_metadata_file = "deployment_metadata.json"
scopes = [
    "https://www.googleapis.com/auth/calendar",
    "https://mail.google.com",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


with open(deployment_metadata_file, "r") as f:
    deployment_metadata = json.loads(f.read())
reasoningEngine = deployment_metadata["remote_agent_engine_id"]

with open(credentials_file, "r") as credential_file:
    client_credentials = json.loads(credential_file.read())["installed"]
client_id = client_credentials["client_id"]
client_secret = client_credentials["client_secret"]
token_uri = client_credentials["token_uri"]
project_id = client_credentials["project_id"]
auth_name = f"projects/{project_id}/locations/global/authorizations/{auth_id}"
authorizer_gcp_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/authorizations/{auth_id}"

flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    credentials_file, scopes=scopes
)
authorization_url, state = flow.authorization_url(
    access_type="offline",
    include_granted_scopes="true",
    prompt="consent",
)

gcp_credentials, _ = google.auth.default()
gcp_credentials.refresh(Request())  # pyright: ignore[reportAttributeAccessIssue]
access_token = gcp_credentials.token  # pyright: ignore[reportAttributeAccessIssue]
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "X-Goog-User-Project": project_id,
}
data = {
    "name": auth_name,
    "serverSideOauth2": {
        "clientId": client_id,
        "clientSecret": client_secret,
        "authorizationUri": authorization_url,
        "tokenUri": token_uri,
    },
    "displayName": auth_id,
}
endpoint = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/authorizations?authorizationId={auth_id}"


requests.delete(
    url=authorizer_gcp_url, headers=headers
)  ## delete the authorizer if it exists.
requests.post(url=endpoint, data=json.dumps(data), headers=headers)
r = requests.get(url=authorizer_gcp_url, headers=headers)
if r.status_code == 200:
    print(r.text)
    auth_name_with_project_number = json.loads(r.text)["name"]
else:
    print(f"ERROR: failed to create {auth_id} in {project_id}")
    raise Exception("Unable to create authorizer")


agent_registration_endpoint = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{gemini_app_id}/assistants/default_assistant/agents"
data = {
    "displayName": "Julian Gregory",
    "description": "The Calendar Assistant",
    "adkAgentDefinition": {
        "toolSettings": {"toolDescription": "An Agent to manage my calendar"},
        "provisionedReasoningEngine": {"reasoningEngine": reasoningEngine},
    },
    "authorizationConfig": {"toolAuthorizations": [auth_name_with_project_number]},
}

try:
    with open(".agents_deployed", "r") as agent_file:
        agent_resource_url = json.loads(agent_file.read())["agent_resource_url"]
    agent_endpoint_url = (
        f"https://discoveryengine.googleapis.com/v1alpha/{agent_resource_url}"
    )
    r = requests.delete(url=agent_endpoint_url, headers=headers)
except (FileNotFoundError, KeyError):
    pass  # NO previous agents deployed

r = requests.post(
    url=agent_registration_endpoint, data=json.dumps(data), headers=headers
)
agent_resource_url = json.loads(r.text)["name"]

# Save agent url to allow us to delete it when we re-run this script (idempotency)
with open(".agents_deployed", "w") as agent_file:
    agent_file.write(json.dumps({"agent_resource_url": agent_resource_url}))

