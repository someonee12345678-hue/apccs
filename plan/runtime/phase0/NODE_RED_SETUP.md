# Node-RED setup for the Phase 0 controller (Batch P0-1)

Status: **NOT CHECKED on the real server.** This page only describes how to import the flow. Nothing here has been installed or run on any host.

## What this is

`node_red_controller.flow.json` is a small Node-RED flow made only of core nodes (tab, comment, inject, http request, debug). It calls the four loopback routes of the local controller in `code/apccs_p0_controller.py`: POST `/jobs`, POST `/claim`, POST `/dispatch` and GET `/snapshot` at `http://127.0.0.1:8765`. The flow holds no passwords or tokens. It contains no exec nodes, no function nodes and no listening (http in) nodes, and it can reach only those four loopback addresses.

## Version pins to record when you install

- Node-RED: record the exact version you install (use a current long-term-support release, per the official Node-RED docs).
- Dashboard 2 (FlowFuse): record the exact version. It is wired in Batch P0-2, not here.
- Python: 3.11 or newer for the controller.

## Import

1. Start the controller from code that builds `make_p0_controller_server` with your own authentication function (a bearer value kept outside every repository file).
2. In the Node-RED editor open the menu, choose Import, pick `node_red_controller.flow.json`, and import it as a new flow.
3. Open each "http request" node and choose bearer authentication; type the value there. Node-RED stores it in its own credentials file, not in the flow.
4. Deploy, then press a probe button. The debug sidebar shows the controller's reply.

## Required before the server counts as accepted

- Editor/admin login turned on in Node-RED settings.
- HTTP-node and dashboard authentication turned on.
- HTTPS or another protected transport in front of anything that is not loopback.
- Observed receipts for import, restart and these settings. `check_p0_node_red_bundle` returns `NOT_CHECKED` until they are supplied.

## Restart

Restart Node-RED and confirm the flow is still present and the probes still work. Record the receipt.

## Undo

Delete the imported flow tab in the editor and stop the controller process. The SQLite file keeps the append-only history; remove it only if you want to discard that history.
