# Lab 2: Diagnosing a Link Failure

## Objective
Use the instructor fault-injection API to simulate an SFP removal and
practice diagnosing it from the CLI, as you would on real hardware.

## Setup
1. Bring up fc1/1 as an F-port and confirm it reaches FLOGI_PENDING/UP.
2. Have the instructor (or yourself, out-of-band) run:
   ```
   curl -X POST http://localhost:8000/faults/unplug_sfp \
     -H "Content-Type: application/json" -d '{"port": "fc1/1"}'
   ```
3. From the student SSH session, run:
   ```
   show interface brief
   show interface fc1/1 transceiver
   show logging
   ```

## Expected Observations
- Port status changes to OFFLINE/LINK_DOWN.
- `show interface transceiver` reports "SFP not present".
- Syslog shows `%PORT-5-IF_DOWN_SFP_ABSENT`.

## Follow-up
Re-insert a 32G SFP via the instructor API and bring the port back up:
```
curl -X POST http://localhost:8000/faults/insert_sfp \
  -H "Content-Type: application/json" -d '{"port": "fc1/1", "sfp_type": "32G_SW"}'
```
Then from CLI: `switchport speed 32000`, `no shutdown`.
