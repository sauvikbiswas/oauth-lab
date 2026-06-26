"""RFC 8707 resource indicator URIs shared across auth server, resource server, and client.

Defaults derive from RESOURCE_SERVER_URL. Override with RESOURCE_A_INDICATOR /
RESOURCE_B_INDICATOR when hosts, ports, or path prefixes differ.
"""

import os


def resource_server_base() -> str:
    return os.environ.get("RESOURCE_SERVER_URL", "http://localhost:25002").rstrip("/")


def resource_a_indicator() -> str:
    return os.environ.get(
        "RESOURCE_A_INDICATOR",
        f"{resource_server_base()}/api/resource-a",
    ).rstrip("/")


def resource_b_indicator() -> str:
    return os.environ.get(
        "RESOURCE_B_INDICATOR",
        f"{resource_server_base()}/api/resource-b",
    ).rstrip("/")


def allowed_resources() -> set[str]:
    return {resource_a_indicator(), resource_b_indicator()}
