"""OpenAPI contract for the minimal HRT REST API."""

from __future__ import annotations

from typing import Any


def openapi_spec() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "HRT Evidence Operations API",
            "version": "0.1.0",
            "description": "REST-style JSON API wrapping the HRT dashboard reporting snapshot.",
        },
        "servers": [{"url": "http://127.0.0.1:8770", "description": "Local development API"}],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "Local demo HMAC token. Production should use OIDC/JWT.",
                }
            }
        },
        "paths": {
            "/": {
                "get": {
                    "summary": "API index",
                    "responses": {"200": {"description": "Available endpoints and valid roles"}},
                }
            },
            "/api": {
                "get": {
                    "summary": "API index",
                    "responses": {"200": {"description": "Available endpoints and valid roles"}},
                }
            },
            "/api/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {"200": {"description": "API and snapshot health"}},
                }
            },
            "/api/auth/demo-login": {
                "post": {
                    "summary": "Issue local demo role token",
                    "description": "Local-only proof of concept for backend role enforcement. Not production authentication.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["role", "password"],
                                    "properties": {
                                        "role": {"type": "string"},
                                        "password": {"type": "string"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Bearer token for requested demo role"},
                        "400": {"description": "Invalid role"},
                        "401": {"description": "Invalid demo password"},
                    },
                }
            },
            "/api/dashboard": {
                "get": {
                    "summary": "Full dashboard snapshot",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {"description": "Full generated dashboard read model"},
                        "401": {"description": "Missing or invalid token"},
                        "403": {"description": "Role is not allowed to access full snapshot"},
                    },
                }
            },
            "/api/dashboard/{role}": {
                "get": {
                    "summary": "Role-shaped dashboard response",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "role",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": [
                                    "ai",
                                    "data_protection",
                                    "investigations",
                                    "leadership",
                                    "legal",
                                    "media",
                                    "monitoring",
                                    "partners",
                                ],
                            },
                        }
                    ],
                    "responses": {
                        "200": {"description": "Dashboard data for the requested role"},
                        "400": {"description": "Invalid role"},
                        "401": {"description": "Missing or invalid token"},
                        "403": {"description": "Token role does not match requested role"},
                    },
                }
            },
            "/api/anomalies": {
                "get": {
                    "summary": "AI anomaly facts",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {"description": "Redacted anomaly facts"},
                        "401": {"description": "Missing or invalid token"},
                        "403": {"description": "Role is not allowed to access anomalies"},
                    },
                }
            },
            "/api/notifications": {
                "get": {
                    "summary": "Notification delivery status",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {"description": "Threshold notification events and delivery states"},
                        "401": {"description": "Missing or invalid token"},
                        "403": {"description": "Role is not allowed to access notifications"},
                    },
                }
            },
            "/api/openapi.json": {
                "get": {
                    "summary": "OpenAPI contract",
                    "responses": {"200": {"description": "OpenAPI 3.0 JSON contract"}},
                }
            },
            "/api/docs": {
                "get": {
                    "summary": "Human-readable API docs",
                    "responses": {"200": {"description": "Simple HTML API documentation page"}},
                }
            },
        },
    }
