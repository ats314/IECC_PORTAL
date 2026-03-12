# Teams Meeting App Setup

The IECC portal can run as a Microsoft Teams Meeting App — embedded directly in the meeting side panel so chairs don't need to switch windows.

## How It Works

- **Side Panel (280px):** The portal loads in a compact layout inside the Teams meeting. Chairs can manage the agenda, record votes, and stage actions.
- **Meeting Stage:** Chair clicks "Share to Stage" to display the Go Live view to all meeting participants (replaces screen sharing).
- **All the same data:** Same portal, same database, same HTMX interactions — just inside Teams.

## Prerequisites

- Microsoft 365 account with Teams
- VS Code with Dev Tunnels extension (for HTTPS tunnel)
- Teams admin must allow custom app sideloading (see Step 3)

## Step 1: Start the Portal

```
cd web
start.bat
```

Portal runs at `http://localhost:8080`.

## Step 2: Create a Dev Tunnel

You need a public HTTPS URL because Teams loads tabs from the cloud.

### Option A: VS Code Dev Tunnels (Recommended)

1. Open VS Code
2. Install the "Dev Tunnels" extension if not already installed
3. Press `Ctrl+Shift+P` → "Dev Tunnels: Create Tunnel"
4. Select "Allow anonymous access" (needed for Teams to reach it)
5. Forward port `8080`
6. Copy the HTTPS URL (e.g., `https://abc123.devtunnels.ms`)

### Option B: CLI

```bash
# Install if needed
winget install Microsoft.devtunnel

# Create and start tunnel
devtunnel create --allow-anonymous
devtunnel port create -p 8080
devtunnel host
```

Copy the HTTPS URL from the output.

## Step 3: Update the Manifest

Edit `web/teams-app/manifest.json`:

1. Replace ALL occurrences of `TUNNEL_DOMAIN` with your tunnel domain (without `https://`).
   Example: `abc123.devtunnels.ms`

2. Generate a new GUID for the `id` field (or use any online GUID generator).
   Replace `00000000-0000-0000-0000-000000000000` with your GUID.

## Step 4: Package the App

Create a ZIP containing exactly these 3 files:
- `manifest.json`
- `color.png`
- `outline.png`

```bash
cd web/teams-app
# On Windows:
powershell Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath iecc-portal.zip -Force
```

## Step 5: Enable Custom App Sideloading

Your Teams admin needs to enable these (one-time):

1. **Teams Admin Center** → Teams apps → Manage apps → Org-wide app settings
   → Toggle ON "Let users interact with custom apps in preview"

2. **Teams Admin Center** → Teams apps → Setup policies → Global (or your policy)
   → Toggle ON "Upload custom apps"

## Step 6: Sideload the App

1. Open Teams
2. Click **Apps** (left sidebar) → **Manage your apps** (bottom)
3. Click **Upload an app** → **Upload a custom app**
4. Select your `iecc-portal.zip` file
5. Click **Add**

## Step 7: Add to a Meeting

1. Open or create a Teams meeting
2. Click the **+** icon in the meeting tab bar
3. Search for "IECC Portal"
4. Click **Add** → **Save**
5. During the meeting, click the IECC Portal icon to open the side panel

## Using the App

### In the Side Panel
- Log in (cookie-based, same as the browser portal)
- Navigate to your meeting
- Open the portal — it automatically adapts to the narrow 280px layout
- Record votes, stage actions, enter modification text

### Sharing to Stage
- Click **Share to Stage** in the Teams toolbar at the top
- The Go Live view appears for all meeting participants
- Participants see the proposal details, vote tallies, and status
- Click **Stop Sharing** when done

## Troubleshooting

**"App not loading" in side panel:**
- Check that your Dev Tunnel is running and the URL is accessible
- Verify the tunnel domain matches `validDomains` in manifest.json
- Check browser console for CSP errors

**"Share to Stage" button not visible:**
- Only presenters and organizers can share to stage
- Attendees will not see this button

**Login issues in iframe:**
- Third-party cookies must be enabled in the browser for cookie-based auth in iframes
- In Teams desktop app, this should work by default
- For Teams web, check browser cookie settings

## Notes

- **No Azure AD app registration needed** for this basic tab integration. Azure AD is only required if you add SSO later.
- **The tunnel URL changes** when you restart Dev Tunnels (unless you use a persistent tunnel). You'll need to update manifest.json and re-upload.
- **Production deployment:** For permanent use, deploy the portal to Azure App Service or similar and use a fixed domain instead of a tunnel.
