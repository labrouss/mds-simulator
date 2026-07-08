# Lab 3: Diagnosing a VSAN Trunk Mismatch

## Objective
Configure two switches (via docker-compose two_switch_fabric example)
with intentionally mismatched `switchport trunk allowed vsan` lists and
diagnose the resulting partial VSAN isolation.

## Steps
1. `docker compose up --build`
2. On switch1 (port 12221): allow VSANs 1,10,20,30 on fc1/1 as TE-port.
3. On switch2 (port 12222): allow VSANs 1,10,40 on fc1/1 as TE-port.
4. Bring up both ports with `no shutdown`.
5. Run `show interface fc1/1 trunk` on both switches.

## Expected Observations
- Overall trunk status: TRUNKING (not down).
- VSAN 1 and 10: `up` on both sides (common to both).
- VSAN 20, 30: `isolated` on switch1 (not carried by switch2).
- VSAN 40: `isolated` on switch2 (not carried by switch1).
- Syslog: `%PORT-4-VSAN_ISOLATED` listing the isolated VSANs.

## Fix
Align `switchport trunk allowed vsan` on both sides to include all
needed VSANs, then re-check `show interface fc1/1 trunk` to confirm
all VSANs report `up`.
