"""KoboToolbox MCP Server - Deploy surveys and fetch submissions."""

import json
import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Server instance
mcp = FastMCP("kobotoolbox")

# Configuration from environment
KOBO_API_TOKEN = os.environ.get("KOBO_API_TOKEN", "")
KOBO_SERVER = os.environ.get("KOBO_SERVER", "https://kf.kobotoolbox.org")


def get_headers() -> dict[str, str]:
    """Get authorization headers for API requests."""
    if not KOBO_API_TOKEN:
        raise ValueError("KOBO_API_TOKEN environment variable is not set")
    return {"Authorization": f"Token {KOBO_API_TOKEN}"}


def format_asset(asset: dict[str, Any]) -> dict[str, Any]:
    """Format an asset object for display."""
    return {
        "uid": asset.get("uid"),
        "name": asset.get("name"),
        "asset_type": asset.get("asset_type"),
        "deployment_status": asset.get("deployment_status"),
        "submission_count": asset.get("deployment__submission_count", 0),
        "date_created": asset.get("date_created"),
        "date_modified": asset.get("date_modified"),
        "owner": asset.get("owner__username"),
    }


@mcp.tool()
async def list_forms(search: str | None = None) -> str:
    """List all KoboToolbox forms/surveys.

    Args:
        search: Optional search term to filter forms by name.

    Returns:
        JSON list of forms with uid, name, status, and submission count.
    """
    params: dict[str, Any] = {"asset_type": "survey"}
    if search:
        params["q"] = search

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/",
            headers=get_headers(),
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])
    forms = [format_asset(asset) for asset in results]
    return json.dumps(forms, indent=2)


@mcp.tool()
async def get_form(form_uid: str) -> str:
    """Get detailed information about a specific form.

    Args:
        form_uid: The unique identifier (uid) of the form.

    Returns:
        JSON object with form details including questions/fields.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}/",
            headers=get_headers(),
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    # Extract key information
    result = {
        "uid": data.get("uid"),
        "name": data.get("name"),
        "deployment_status": data.get("deployment_status"),
        "submission_count": data.get("deployment__submission_count", 0),
        "date_created": data.get("date_created"),
        "date_modified": data.get("date_modified"),
        "owner": data.get("owner__username"),
        "content": data.get("content"),  # Contains survey structure
    }
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_submissions(
    form_uid: str,
    limit: int = 100,
    start: int = 0,
    query: str | None = None,
) -> str:
    """Get submissions (responses) for a form.

    Args:
        form_uid: The unique identifier (uid) of the form.
        limit: Maximum number of submissions to return (default 100).
        start: Offset for pagination (default 0).
        query: Optional JSON query string to filter submissions (e.g., '{"field": "value"}').

    Returns:
        JSON object with count and list of submissions.
    """
    params: dict[str, Any] = {"limit": limit, "start": start}
    if query:
        params["query"] = query

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}/data/",
            headers=get_headers(),
            params=params,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

    return json.dumps(
        {"count": data.get("count", 0), "results": data.get("results", [])},
        indent=2,
    )


@mcp.tool()
async def deploy_form(file_path: str, form_name: str | None = None) -> str:
    """Upload and deploy an XLSForm to KoboToolbox.

    Args:
        file_path: Path to the XLSForm (.xlsx) file.
        form_name: Optional name for the form (defaults to filename).

    Returns:
        JSON object with the created form's uid and deployment status.
    """
    import os.path

    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    name = form_name or os.path.splitext(os.path.basename(file_path))[0]

    async with httpx.AsyncClient() as client:
        # Step 1: Upload the XLSForm to create an asset
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"name": name}
            response = await client.post(
                f"{KOBO_SERVER}/api/v2/assets/",
                headers=get_headers(),
                files=files,
                data=data,
                timeout=60.0,
            )
            response.raise_for_status()
            asset = response.json()

        uid = asset.get("uid")

        # Step 2: Deploy the form
        deploy_response = await client.post(
            f"{KOBO_SERVER}/api/v2/assets/{uid}/deployment/",
            headers=get_headers(),
            json={"active": True},
            timeout=30.0,
        )
        deploy_response.raise_for_status()

    return json.dumps(
        {
            "uid": uid,
            "name": name,
            "status": "deployed",
            "url": f"{KOBO_SERVER}/#/forms/{uid}",
        },
        indent=2,
    )


@mcp.tool()
async def replace_form(form_uid: str, file_path: str) -> str:
    """Replace an existing form with a new XLSForm version.

    This updates the form definition while preserving the form UID and existing submissions.

    Args:
        form_uid: The unique identifier (uid) of the form to replace.
        file_path: Path to the new XLSForm (.xlsx) file.

    Returns:
        JSON object with the updated form's uid and deployment status.
    """
    import asyncio
    import os.path

    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    async with httpx.AsyncClient() as client:
        # Step 1: Create an import task targeting the existing asset
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"destination": f"{KOBO_SERVER}/api/v2/assets/{form_uid}/"}
            response = await client.post(
                f"{KOBO_SERVER}/api/v2/imports/",
                headers=get_headers(),
                files=files,
                data=data,
                timeout=60.0,
            )
            response.raise_for_status()
            import_task = response.json()

        import_uid = import_task.get("uid")

        # Step 2: Poll for import completion (max 60 seconds)
        for _ in range(60):
            status_response = await client.get(
                f"{KOBO_SERVER}/api/v2/imports/{import_uid}/",
                headers=get_headers(),
                timeout=30.0,
            )
            status_response.raise_for_status()
            status_data = status_response.json()

            if status_data.get("status") == "complete":
                break
            elif status_data.get("status") == "error":
                return json.dumps(
                    {"status": "error", "message": status_data.get("messages", {})},
                    indent=2,
                )

            await asyncio.sleep(1)
        else:
            return json.dumps(
                {"status": "timeout", "message": "Import is still processing."},
                indent=2,
            )

        # Step 3: Redeploy the form to make changes live
        deploy_response = await client.patch(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}/deployment/",
            headers=get_headers(),
            json={"active": True},
            timeout=30.0,
        )
        deploy_response.raise_for_status()

        # Step 4: Get updated asset info
        asset_response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}/",
            headers=get_headers(),
            timeout=30.0,
        )
        asset_response.raise_for_status()
        asset = asset_response.json()

    return json.dumps(
        {
            "uid": form_uid,
            "name": asset.get("name"),
            "status": "redeployed",
            "submission_count": asset.get("deployment__submission_count", 0),
            "url": f"{KOBO_SERVER}/#/forms/{form_uid}",
        },
        indent=2,
    )


@mcp.tool()
async def export_data(
    form_uid: str,
    export_type: str = "csv",
    include_labels: bool = True,
) -> str:
    """Create and download a data export for a form.

    Args:
        form_uid: The unique identifier (uid) of the form.
        export_type: Export format - 'csv' or 'xls' (default 'csv').
        include_labels: Include question labels in headers (default True).

    Returns:
        JSON object with export download URL or the data itself for small exports.
    """
    export_settings = {
        "fields_from_all_versions": True,
        "group_sep": "/",
        "hierarchy_in_labels": include_labels,
        "multiple_select": "both",
        "type": export_type,
    }

    async with httpx.AsyncClient() as client:
        # Create export
        response = await client.post(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}/exports/",
            headers=get_headers(),
            json=export_settings,
            timeout=30.0,
        )
        response.raise_for_status()
        export_data = response.json()

        export_uid = export_data.get("uid")

        # Poll for completion (max 30 seconds)
        import asyncio

        for _ in range(30):
            status_response = await client.get(
                f"{KOBO_SERVER}/api/v2/assets/{form_uid}/exports/{export_uid}/",
                headers=get_headers(),
                timeout=30.0,
            )
            status_response.raise_for_status()
            status_data = status_response.json()

            if status_data.get("status") == "complete":
                return json.dumps(
                    {
                        "status": "complete",
                        "download_url": status_data.get("result"),
                        "type": export_type,
                    },
                    indent=2,
                )
            elif status_data.get("status") == "error":
                return json.dumps(
                    {"status": "error", "message": status_data.get("messages", {})},
                    indent=2,
                )

            await asyncio.sleep(1)

    return json.dumps(
        {"status": "pending", "message": "Export is still processing. Try again later."},
        indent=2,
    )


def main():
    """Run the MCP server."""
    # Log to stderr (stdout is reserved for MCP protocol)
    print("Starting KoboToolbox MCP server...", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
