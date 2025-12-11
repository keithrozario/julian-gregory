# Token and Creds

This directory holds the json files with the tokens and credentials.

When you create oAuth2.0 client ids in GCP via [here](https://console.cloud.google.com/auth/clients) you will get a list of credentials which include the cliend id and secret that you can download in json format.

You will need to create two clients, one for Web Application Client for Gemini Enterprise, and one Desktop Client for local testing (unless you don't plan on doing testing locally which is bad! idea).

Save those credentials into:

* `credentials_local.json`
* `credentials_web.json` respectively.

`credentials_local.json` is used for local testing, whenever the code determines that we're running locally, it should happen seamlessly. `credentials_web.json` is never used in the code, we use this [script](deploy_to_gemini_enterprise/deploy_to_ge.py) to setup the authorizer in Gemini Enterprise using the creds in `credentials_web.json`. 

The `.gitignore` in this repo automatically ignores the credentials files for security reasons. The client secret should be a secret, so please ensure you do not commit your either credential files to your repo :)

