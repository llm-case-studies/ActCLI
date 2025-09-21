# ActCLI Authentication Flow

This document describes the authentication flow for ActCLI, including the different authentication methods, the `auth` command, and how credentials are stored.

## Overview

ActCLI supports two authentication methods for accessing AI models:

1.  **API Keys:** Users can provide an API key for a specific provider by setting an environment variable (e.g., `OPENAI_API_KEY`, `GOOGLE_API_KEY`). This is a simple and effective method for users who are familiar with API keys.

2.  **OAuth 2.0:** For providers that support it, ActCLI uses the OAuth 2.0 protocol to allow users to authenticate with their provider accounts. This is a more user-friendly and secure method, as it doesn't require users to manage API keys manually.

## Google OAuth 2.0 Flow (Desktop App)

For Google authentication, ActCLI uses the same public client ID as the official Gemini CLI and other Google Cloud tools. This means that you don't need to create your own OAuth 2.0 client ID in the Google API Console. This simplifies the setup process and makes it easier for users to get started.

The flow works as follows:

1.  **Initiate Login:** The user runs the `actcli auth login google` command.

2.  **Create Flow:** ActCLI creates an `InstalledAppFlow` object from the `google-auth-oauthlib` library. This object is configured with the client ID and scopes required for the Gemini API.

3.  **Open Browser:** ActCLI opens the user's default web browser to a Google consent screen. The user is asked to log in with their Google account and grant permission for ActCLI to access their user information and the Gemini API.

4.  **Handle Redirect:** After the user grants permission, Google redirects the browser to a local web server that ActCLI is running on a random port. The redirect URL contains an authorization code.

5.  **Fetch Token:** ActCLI extracts the authorization code from the redirect URL and uses it to fetch an access token and a refresh token from Google's token endpoint.

6.  **Store Credentials:** The access token, refresh token, and other credential information are stored securely using the `keyring` library.

## Commands

The `auth` command is used to manage authentication with AI providers.

*   `actcli auth login <provider>`: Initiates the login flow for the specified provider.
*   `actcli auth logout <provider>`: Logs out of the specified provider and removes the stored credentials.
*   `actcli auth status`: Shows the current authentication status for all providers.

## Credential Storage

ActCLI uses the `keyring` library to store credentials securely in the user's system keychain. This is a more secure alternative to storing credentials in a plain text file.

The `CredentialStore` class in `src/actcli/auth/store.py` provides an abstraction for storing and retrieving credentials from the keychain.

## Future Enhancement: Named Accounts

To make it easier for users to switch between multiple accounts for the same provider (e.g., a personal account and a work account), a future enhancement could be to support "named accounts."

### Use Cases

*   A consultant who works with multiple clients and needs to use different API keys or accounts for each client.
*   A developer who wants to test the application with different accounts without having to log out and log in every time.

### Proposed Commands

*   `actcli auth login <provider> --as <name>`: Logs in to the specified provider and saves the credentials under the given name.
*   `actcli auth use <name>`: Sets the specified named account as the active account for the provider.
*   `actcli auth list`: Lists all the configured named accounts.
*   `actcli auth remove <name>`: Removes a named account.

### Data Model

The `CredentialStore` would need to be updated to store multiple credentials for the same provider. The credentials could be stored in the keychain with a service name that includes the provider and the account name (e.g., `actcli:google:personal`, `actcli:google:work`).

## Testing

### Unit Tests

*   Test the `CredentialStore` to ensure that it can store and retrieve credentials correctly.
*   Test the `auth` command to ensure that it calls the correct functions for each subcommand.
*   Mock the `InstalledAppFlow` and test the `login_with_google` function to ensure that it handles the OAuth flow correctly.

### Integration Tests

*   Write an integration test that runs the `actcli auth login google` command and uses a mock OAuth server to simulate the Google login flow.
*   Write an integration test that uses a real AI provider (with a test account) to test the end-to-end authentication and API call flow.
