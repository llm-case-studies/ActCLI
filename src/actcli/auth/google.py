from __future__ import annotations

from google_auth_oauthlib.flow import InstalledAppFlow

from .store import CredentialStore, Credentials

# Google's public CLI client ID (same as used by gcloud, etc.)
CLIENT_ID = "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com"

CLIENT_SECRETS = {
    "installed": {
        "client_id": CLIENT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    }
}


def login_with_google():
    """Initiate Google OAuth 2.0 PKCE login flow."""
    flow = InstalledAppFlow.from_client_config(
        CLIENT_SECRETS,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    creds = flow.run_local_server(port=0)

    store = CredentialStore()
    store.set(
        "google_oauth",
        Credentials(
            method="oauth",
            token=creds.token,
            info={
                "refresh_token": creds.refresh_token,
                "client_id": creds.client_id,
                "client_secret": getattr(creds, "client_secret", None),
            },
        ),
    )
    print("Successfully authenticated with Google.")
