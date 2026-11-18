# Mission Control phone view (Batch P0-2): set up and undo

Status: **NOT CHECKED on a phone or on the real server.** This page only describes what to do once the server route is approved. Nothing here has been installed or run anywhere.

## What it is

`dashboard.flow.json` is a Node-RED flow for the FlowFuse Dashboard 2 add-on (`@flowfuse/node-red-dashboard`). It has four pages: Home, Approvals, Flows and Agents. It reads one address only, the controller snapshot at `http://127.0.0.1:8765/snapshot`. It is a web app you add to your phone's home screen, not a new Android app.

The buttons on the Approvals page send a *request* and nothing more. They cannot merge, approve or close anything. Your own GitHub tap stays the only approval for protected files.

## Versions to record when you install

- Dashboard 2: `@flowfuse/node-red-dashboard@1.37.0` was the newest release seen when this was written. Write down the exact version you really install.
- Node-RED: write down the exact version you install.
- Do not use the old "node-red-dashboard" add-on (its nodes start with `ui_`). The flow checker refuses it.
- No FlowFuse hosted service is needed.

## Set up (when the server route is approved)

1. Install the Dashboard 2 add-on in Node-RED from its Manage palette screen.
2. Import `dashboard.flow.json` as a new flow. Open each "http request" node, choose bearer authentication and type the value there. It is stored in Node-RED's own credentials file, never in this flow.
3. Deploy, then open the dashboard address on your phone over a protected (HTTPS) connection.
4. In your phone browser's menu choose "Add to Home screen" or "Install app".

## What counts as accepted

Opening the address once is not acceptance. `check_p0_phone_acceptance` needs a receipt showing, each with an evidence reference: the page loaded, it was installed to the home screen, all four pages open, you were logged in, stale and offline states show, and it reconnects after a restart. Anything missing stays NOT CHECKED.

## Undo

1. Delete the imported flow in Node-RED and deploy.
2. Remove the home-screen icon from your phone.
3. Uninstall the Dashboard 2 add-on from the palette if you no longer want it.

Nothing else changes; the controller, queue and GitHub gates are untouched.
