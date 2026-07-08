# Lab 1: Basic VSAN and Zoning

## Objective
Create a VSAN, assign an interface to it, create a zone and zoneset,
and activate it.

## Steps

1. Connect via SSH: `ssh admin@localhost -p 2222`
2. Enter config mode and create VSAN 10:
   ```
   configure terminal
   vsan database
   vsan 10 name PROD_FABRIC
   exit
   ```
3. Assign fc1/1 to VSAN 10:
   ```
   interface fc1/1
   vsan 10
   switchport mode F
   no shutdown
   exit
   ```
4. Verify: `show vsan`
5. Create a zone and zoneset:
   ```
   zone name HOST1_TO_ARRAY1 vsan 10
   member pwwn 21:00:00:00:00:00:01:01
   exit
   zoneset name PROD_ZONESET vsan 10
   member HOST1_TO_ARRAY1
   exit
   zoneset activate vsan 10 PROD_ZONESET
   ```
6. Verify: `show zoneset active vsan 10`

## Discussion Questions
- What real-world purpose does zoning serve in a SAN fabric?
- Why must a zoneset be explicitly activated after being created?
