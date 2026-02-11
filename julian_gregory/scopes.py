# This is the scopes for the agent
# both the local credential process in tools.get_creds()
# and the deploy_to_ge script will referene this.

AUTHORIZER_NAME = "julian-authorizer"
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
    "https://mail.google.com/",
]

