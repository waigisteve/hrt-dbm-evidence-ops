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
            "/api/dashboard": {
                "get": {
                    "summary": "Full dashboard snapshot",
                    "responses": {"200": {"description": "Full generated dashboard read model"}},
                }
            },
            "/api/dashboard/{role}": {
                "get": {
                    "summary": "Role-shaped dashboard response",
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
                    },
                }
            },
            "/api/anomalies": {
                "get": {
                    "summary": "AI anomaly facts",
                    "responses": {"200": {"description": "Redacted anomaly facts"}},
                }
            },
            "/api/notifications": {
                "get": {
                    "summary": "Notification delivery status",
                    "responses": {"200": {"description": "Threshold notification events and delivery states"}},
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
