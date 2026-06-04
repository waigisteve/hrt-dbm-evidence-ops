"""Connection helper that selects a least-privilege PostgreSQL role.

The scripts no longer hard-code "run as the postgres superuser". Each script
asks for the role it needs ('etl' = read-only reporting, 'app' = OLTP
read/write) and this helper builds the psql invocation:

- If HRT_<ROLE>_USER is set, connect over TCP as that dedicated, least-privilege
  role (created by sql/roles_and_security.sql), using HRT_PG_HOST / HRT_PG_PORT
  and the matching HRT_<ROLE>_PASSWORD. This is the recommended posture.
- Otherwise, fall back to the original demo default of `sudo -u postgres psql`
  (peer/trust auth) so the out-of-the-box quick start keeps working.

Passwords are read from the environment only; they are never placed on the
command line (psql reads PGPASSWORD), so they do not leak via the process list.
"""

from __future__ import annotations

import os


DEFAULT_DB = os.getenv("HRT_PG_DB", "hrt_prep")


def psql_command(role: str) -> tuple[list[str], dict[str, str]]:
    """Return (command, env) for a named connection role ('etl' or 'app')."""
    prefix = role.upper()
    env = dict(os.environ)
    user = os.getenv(f"HRT_{prefix}_USER")
    if user:
        host = os.getenv("HRT_PG_HOST", "127.0.0.1")
        port = os.getenv("HRT_PG_PORT", "5432")
        password = os.getenv(f"HRT_{prefix}_PASSWORD", "")
        if password:
            env["PGPASSWORD"] = password
        return (["psql", "-h", host, "-p", port, "-U", user, "-d", DEFAULT_DB], env)
    return (["sudo", "-u", "postgres", "psql", "-d", DEFAULT_DB], env)
