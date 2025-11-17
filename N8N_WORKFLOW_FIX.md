# How to Fix the n8n Workflow Schedule

## Problem
Your n8n instance has a workflow calling the Google Sheets sync endpoint **every minute**, which is excessive since the data only needs daily updates.

## Solution Options

### Option 1: Let the Rate Limiter Handle It (Recommended)
With the recent fixes:
- External calls now get proper `429 Too Many Requests` responses
- The backend scheduler handles daily sync at 2 AM automatically
- The n8n workflow will hit rate limits and should eventually stop retrying so aggressively

**Action needed**: None - the system will self-regulate

### Option 2: Update n8n Workflow Schedule (Manual)

1. **Access n8n Dashboard**:
   - URL: https://n8n-hah4.onrender.com
   - Note: The service may take 1-2 minutes to wake up (Render free tier spins down when idle)

2. **Find the Workflow**:
   - Look for a workflow with these characteristics:
     - Schedule trigger set to "Every 1 minute" or similar
     - HTTP Request node calling your backend
     - URL contains `/sheet-integration/sync-wgp-sheet`

3. **Update the Schedule**:
   - Click on the Schedule Trigger node
   - Change from "Every 1 minute" to:
     - **"Every Day"** at a specific time (e.g., 3:00 AM)
     - OR **"Once a week"** if daily is still too frequent

4. **Alternative: Disable the Workflow**:
   - If you don't need n8n to trigger syncs at all (since the backend now handles it):
     - Click the workflow toggle to **Inactive**
     - The backend scheduler will handle all syncs automatically

5. **Save Changes**:
   - Click "Save" in the top right
   - The workflow will now run on the new schedule

### Option 3: Delete the n8n Workflow
If you no longer need n8n to handle sheet syncing:

1. Go to the workflow in n8n
2. Click the "..." menu (more options)
3. Select "Delete"
4. Confirm deletion

The backend scheduler will continue to work independently.

## Verifying the Fix

After making changes, check that the external calls stop:

```bash
# Watch the logs for the next few minutes
# You should see the 429 responses stop appearing
```

Or check your Render logs:
1. Go to https://dashboard.render.com
2. Select your wolf-goat-pig service
3. View logs
4. Look for requests from IP 192.69.186.162
5. They should either:
   - Stop appearing (workflow disabled/deleted)
   - Appear much less frequently (schedule changed)
   - Get 429 responses but not retry so aggressively

## Backend Scheduler Status

To verify the backend scheduler is working:

```bash
curl https://wolf-goat-pig.onrender.com/email/scheduler-status
```

Expected response:
```json
{
  "initialized": true,
  "running": true,
  "message": "Scheduler running"
}
```

## When the Sync Runs

- **n8n workflow**: Whatever schedule you set (or disabled)
- **Backend scheduler**: Daily at 2:00 AM Pacific Time
- **Manual trigger**: Call the endpoint with `X-Scheduled-Job: true` header to bypass rate limits

## Need Help?

If n8n continues to cause issues:
1. You can safely disable/delete the workflow
2. The backend scheduler will handle all syncing automatically
3. The data will stay fresh with daily updates at 2 AM
