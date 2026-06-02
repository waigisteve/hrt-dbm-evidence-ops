# Connecting pgAdmin on Windows to PostgreSQL Running in WSL

## Purpose

This document explains how to connect **pgAdmin running on Windows** to a **PostgreSQL database created inside WSL**.

In this setup:

- **pgAdmin** is installed on Windows.
- **PostgreSQL** is running inside Ubuntu on WSL.
- The target database is `hrt_prep`.

---

## Environment Summary

| Component | Value |
|---|---|
| Windows PostgreSQL version | PostgreSQL 17 |
| WSL PostgreSQL version | PostgreSQL 16 |
| WSL distribution | Ubuntu 24.04 LTS |
| WSL username | `waigisteve` |
| Target database | `hrt_prep` |
| PostgreSQL user | `postgres` |
| WSL PostgreSQL IP observed | `172.25.250.6` |
| PostgreSQL port | `5432` |
| Final working method | pgAdmin SSH tunnel into WSL |

---

## Problem Encountered

pgAdmin initially showed databases from the **Windows PostgreSQL instance**, not from the PostgreSQL instance running inside WSL.

This happened because there were two separate PostgreSQL environments:

```text
Windows PostgreSQL 17  -> visible from pgAdmin through Windows localhost
WSL PostgreSQL         -> contains the hrt_prep database
```

The `hrt_prep` database existed only inside WSL.

---

## Symptoms

When pgAdmin or Windows PowerShell attempted to connect using:

```text
Host: 127.0.0.1
Port: 5432
```

the connection failed with:

```text
server closed the connection unexpectedly
```

When connecting to:

```text
Host: ::1
Port: 5432
```

the connection worked, but it connected to the **Windows PostgreSQL instance**, where `hrt_prep` did not exist.

When trying to connect directly to the WSL IP:

```text
Host: 172.25.250.6
Port: 5432
```

Windows returned:

```text
Permission denied (0x0000271D/10013)
```

---

## Root Cause

The issue was caused by having:

1. PostgreSQL running on Windows.
2. PostgreSQL running inside WSL.
3. pgAdmin connecting to the Windows PostgreSQL instance when using localhost.
4. Windows networking blocking direct access to the WSL PostgreSQL IP.
5. The target database existing only inside WSL.

The correct PostgreSQL instance was inside WSL, but pgAdmin could not reach it directly through the WSL IP.

---

## Confirming the WSL PostgreSQL Database

Inside WSL, the database was confirmed using:

```bash
psql -h 172.25.250.6 -p 5432 -U postgres -d hrt_prep
```

Then inside `psql`:

```sql
SELECT
    inet_server_addr() AS server_ip,
    inet_server_port() AS server_port,
    current_database() AS database_name,
    current_user AS connected_user;
```

Expected output:

```text
server_ip     | server_port | database_name | connected_user
--------------+-------------+---------------+----------------
172.25.250.6  | 5432        | hrt_prep   | postgres
```

This confirmed that PostgreSQL inside WSL was healthy and that `hrt_prep` existed there.

---

## Checking the WSL IP Address

Inside WSL:

```bash
hostname -I
```

Example output:

```text
172.25.250.6
```

This was the IP address of the WSL Ubuntu environment.

---

## Checking PostgreSQL Listening Status in WSL

Inside WSL:

```bash
sudo ss -ltnp | grep 5432
```

Expected output:

```text
LISTEN 0 200 0.0.0.0:5432 0.0.0.0:* users:(("postgres",pid=...,fd=6))
LISTEN 0 200 [::]:5432    [::]:*    users:(("postgres",pid=...,fd=7))
```

This confirmed that PostgreSQL inside WSL was listening on port `5432`.

---

## Direct Windows Connection Failed

From Windows PowerShell:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h 172.25.250.6 -p 5432 -U postgres -d hrt_prep
```

Result:

```text
Permission denied (0x0000271D/10013)
```

This showed that Windows could not directly reach the WSL PostgreSQL service over the WSL IP.

---

## Port Proxy Attempt

A Windows port proxy was created:

```powershell
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=5433 connectaddress=172.25.250.6 connectport=5432
```

The proxy was confirmed with:

```powershell
netsh interface portproxy show all
```

Expected output:

```text
Listen on ipv4:             Connect to ipv4:

Address         Port        Address         Port
--------------- ----------  --------------- ----------
127.0.0.1       5433        172.25.250.6    5432
```

Connectivity test:

```powershell
Test-NetConnection 127.0.0.1 -Port 5433
```

Output showed:

```text
TcpTestSucceeded : True
```

However, the PostgreSQL session still failed:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h 127.0.0.1 -p 5433 -U postgres -d hrt_prep
```

Result:

```text
server closed the connection unexpectedly
```

Because the proxy path was unreliable in this environment, the final working solution used SSH tunneling.

---

# Final Working Solution: SSH Tunnel Through WSL

The working solution was to use **SSH tunneling** from pgAdmin into WSL.

This allows pgAdmin to connect to WSL first over SSH, then connect to PostgreSQL locally inside WSL.

The final connection path is:

```text
pgAdmin on Windows
    -> SSH to WSL through 127.0.0.1:22
    -> PostgreSQL inside WSL through 127.0.0.1:5432
    -> Database: hrt_prep
```

---

## Step 1: Install OpenSSH Server in WSL

Inside WSL:

```bash
sudo apt update
sudo apt install -y openssh-server
```

---

## Step 2: Start SSH Service in WSL

```bash
sudo service ssh start
```

Confirm SSH is listening:

```bash
sudo ss -ltnp | grep :22
```

Expected output:

```text
LISTEN 0 4096 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=...,fd=3))
LISTEN 0 4096 [::]:22    [::]:*    users:(("sshd",pid=...,fd=4))
```

---

## Step 3: Test SSH from Windows

From Windows PowerShell:

```powershell
Test-NetConnection 127.0.0.1 -Port 22
```

Expected result:

```text
TcpTestSucceeded : True
```

Then test SSH login:

```powershell
ssh waigisteve@127.0.0.1
```

Enter the WSL/Linux password for:

```text
waigisteve
```

Successful login shows:

```text
Welcome to Ubuntu 24.04 LTS
waigisteve@StephenWaigi:~$
```

---

## Step 4: Configure pgAdmin

Create a new server in pgAdmin.

### General Tab

```text
Name: HRT Prep - WSL SSH Tunnel
```

### Connection Tab

Use these settings:

```text
Host name/address: 127.0.0.1
Port: 5432
Maintenance database: hrt_prep
Username: postgres
Password: <PostgreSQL postgres password>
Role: blank
Kerberos authentication: OFF
```

Important:

```text
Host name/address = 127.0.0.1
```

This is correct because pgAdmin connects through the SSH tunnel. From inside WSL, `127.0.0.1:5432` points to PostgreSQL running inside WSL.

---

### SSH Tunnel Tab

Enable SSH tunneling.

Use these settings:

```text
Use SSH tunneling: ON
Tunnel host: 127.0.0.1
Tunnel port: 22
Username: waigisteve
Authentication: Password
Password: <WSL/Linux password>
```

---

## Password Clarification

There are two different passwords involved:

```text
SSH password        = WSL/Linux password for waigisteve
PostgreSQL password = PostgreSQL password for the postgres database user
```

Do not confuse the two.

---

## Final Working pgAdmin Setup

```text
Server name: HRT Prep - WSL SSH Tunnel

Connection:
Host: 127.0.0.1
Port: 5432
Database: hrt_prep
User: postgres

SSH Tunnel:
Tunnel host: 127.0.0.1
Tunnel port: 22
Tunnel user: waigisteve
Authentication: Password
```

---

## Recommended pgAdmin Server Names

To avoid confusion, rename pgAdmin server registrations clearly:

```text
PostgreSQL 17 - Windows
HRT Prep - WSL SSH Tunnel
```

This makes it clear which server points to Windows PostgreSQL and which one points to the WSL PostgreSQL database.

---

## Useful Verification Query

After connecting in pgAdmin or `psql`, run:

```sql
SELECT
    inet_server_addr() AS server_ip,
    inet_server_port() AS server_port,
    current_database() AS database_name,
    current_user AS connected_user;
```

When using SSH tunneling, PostgreSQL may show `127.0.0.1` as the server or client address because the connection is local inside WSL.

---

## Useful Database Test

```sql
SELECT COUNT(*) FROM public.incidents;
```

This confirms that the `hrt_prep` database is accessible and the expected tables are available.

---

## Notes

- `::1` connected to the Windows PostgreSQL instance, not the WSL PostgreSQL instance.
- `127.0.0.1:5432` from Windows was affected by Windows/WSL networking behavior.
- The WSL database was confirmed at `172.25.250.6:5432`.
- Direct Windows access to `172.25.250.6:5432` was blocked.
- SSH tunneling through `127.0.0.1:22` solved the issue cleanly.
- If WSL is restarted, the WSL IP may change, but SSH through `127.0.0.1` is easier to manage.
- If SSH is not running after a restart, start it again with:

```bash
sudo service ssh start
```

---

## Final Outcome

pgAdmin on Windows successfully connected to the PostgreSQL database running inside WSL using SSH tunneling.

The working database is:

```text
hrt_prep
```

The working approach is:

```text
pgAdmin -> SSH Tunnel -> WSL -> PostgreSQL -> hrt_prep
```
