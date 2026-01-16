# How to Enable Google Generative Language API (Veo/Gemini)

This guide will help you enable the necessary API on your Google Cloud account so that your AI application can generate videos using the Veo model.

## Step 1: Open the Google Cloud Console
1.  Click the following direct link to visit the Google Cloud Console API page for your project:
    👉 **[Google Cloud Console: Enable Generative Language API](https://console.developers.google.com/apis/api/generativelanguage.googleapis.com/overview?project=542708778979)**

    *(Note: This link is pre-configured for your specific project ID: `542708778979`)*

2.  If asked, sign in with the Google Account you used to create the API Key/Project.

## Step 2: Enable the API
1.  Once the page loads, look for a blue button near the top left or center labelled **"ENABLE"**.
2.  **Click the "ENABLE" button**.
3.  The page may spin for 30-60 seconds while it activates.
4.  Once finished, the button will change to say **"MANAGE"** or "DISABLE". This means it is active.

## Step 3: Verify Billing (If Required)
*   Some generative AI models require a billing account to be linked, even if they have a free tier.
*   If you see a banner asking to "Enable Billing", click it and follow the prompts to link a valid credit card or billing account.

## Step 4: Test Your Application
1.  **Delete Old Files**: Go to your `media/videos/` folder and delete any `.mp4` files there (they are likely corrupt error files from before).
2.  **Restart Server**: It's good practice to restart your Django server (`Ctrl+C` then `run.py`).
3.  **Generate a Video**: Go to your frontend/app and request a new video generation.
4.  **Success**: You should now see a playable video file appear in your media folder.

---

### Troubleshooting
*   **"Permission Denied" Error**: This means the API is still not enabled. Double check Step 2.
*   **"Quota Exceeded"**: This means you have hit the free limit for the day. You may need to upgrade your Google Cloud billing or wait 24 hours.
