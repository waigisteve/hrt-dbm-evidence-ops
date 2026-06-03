# Auth and RBAC Implementation

## Implemented Local Proof of Concept

The project now has backend role enforcement for stakeholder dashboard reads.

Implemented flow:

```text
dashboard/app.js
  -> POST /api/auth/demo-login
  -> receives local demo Bearer token
  -> GET /api/dashboard/{role} with Authorization header
  -> API verifies token signature, expiry, and role match
  -> API returns role-shaped dashboard data or rejects access
```

Protected route:

```text
GET /api/dashboard/{role}
```

Public local routes:

```text
GET /api/health
GET /api/openapi.json
GET /api/docs
```

Demo token controls:

- Tokens are signed with HMAC-SHA256 using `HRT_DEMO_TOKEN_SECRET`.
- Tokens expire after `HRT_DEMO_TOKEN_TTL_SECONDS`, default `3600`.
- Token role must match the requested `{role}`.
- Wrong-role access returns `403`.
- Missing or invalid tokens return `401`.

This is intentionally not production authentication. It proves the control point: the browser no longer decides access alone; the API enforces the stakeholder role.

## Production Recommendation

Recommended lowest-headwind production path:

1. Use **Microsoft Entra ID** if the organisation already uses Microsoft 365, Azure, Teams, SharePoint, or Outlook.
2. Use **Keycloak** if license cost must be near-zero and the team can operate and secure its own identity service.
3. Use **Auth0** if the priority is fastest SaaS setup and the user count remains small enough for the pricing to stay acceptable.
4. Use **Okta** for larger enterprise identity governance needs.
5. Use **Google Workspace identity** if the organisation is already Google-first and only needs straightforward workforce login.

Pragmatic recommendation for this project:

```text
Microsoft Entra ID if Microsoft 365 already exists.
Keycloak if there is no existing identity provider and license cost is the main constraint.
```

Why Entra ID is usually the best affordable production-ready choice:

- Many NGOs already pay for Microsoft 365, so identity may already be available.
- It supports OIDC/JWT, MFA, conditional access, groups, app registrations, and audit logs.
- It avoids running a self-hosted identity platform.
- It maps cleanly to API roles through group or app-role claims.

Why Keycloak is the best low-license-cost alternative:

- Open source.
- Supports OIDC/JWT, groups, roles, MFA, and federation.
- Good for demonstrations and controlled deployments.
- Main cost is operations: patching, hosting, backup, monitoring, TLS, and incident response.

## Production Target Flow

```text
User login
  -> OIDC provider
  -> access token with role/group claims
  -> dashboard sends Authorization: Bearer <jwt>
  -> API validates issuer, audience, signature, expiry, and claims
  -> API returns only permitted stakeholder read model
```

Minimum production checks:

- Validate JWT signature against provider JWKS.
- Validate issuer.
- Validate audience.
- Validate expiry.
- Map groups or app roles to HRT stakeholder roles.
- Reject wrong-role access server-side.
- Log auth failures and high-risk access attempts.
- Keep dashboard UI role controls as navigation only, not authorization.
