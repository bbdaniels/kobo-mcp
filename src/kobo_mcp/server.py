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


WORKFLOWS = {
    "overview": """KoboToolbox MCP Server — Tool & Workflow Reference

TOOLS:
  info          — Show this help. Use topic="translate", "deploy", or "data" for details.
  list_forms    — List all forms/surveys. Returns uid, name, status, submission count.
  get_form      — Get a form's JSON structure (questions, choices, settings).
  export_form   — Download a form as an XLSForm (.xlsx) file for editing.
  deploy_form   — Upload and deploy a new XLSForm (.xlsx).
  replace_form  — Replace an existing form's definition (preserves uid & submissions).
  get_submissions — Fetch submission data with pagination and filtering.
  export_data   — Export submission data as CSV or XLS.

WORKFLOWS (use info with topic for step-by-step):
  translate — Add translations to an existing form
  deploy    — Create and deploy a new form from an XLSForm
  data      — Retrieve and export submission data""",
    "translate": """Workflow: Translate an Existing Form

STEP 1 — Find the form:
  list_forms(search="My Survey")
  → Note the form uid from the results

STEP 2 — Download the XLSForm:
  export_form(form_uid="aBC123xYz", output_path="/path/to/form.xlsx")
  → Saves the .xlsx file locally

STEP 3 — Edit the XLSForm to add translations:
  In both the "survey" and "choices" sheets, add columns for each language:
    label::English (en)    | label::French (fr)     | hint::English (en)  | hint::French (fr)
    What is your name?     | Quel est votre nom?    | Full name           | Nom complet
    How old are you?       | Quel âge avez-vous?    |                     |

  Important:
  - The format is: column_type::Language Name (code)
  - Both survey and choices sheets need translation columns
  - The "settings" sheet can set default_language
  - Keep the original "name" column unchanged (it's the internal field ID)

STEP 4 — Redeploy:
  replace_form(form_uid="aBC123xYz", file_path="/path/to/form_translated.xlsx")
  → Updates the live form while preserving all existing submissions

TIPS:
  - Common language codes: en, fr, es, pt, ar, sw, hi, zh, am
  - You can add multiple languages at once
  - Use get_form() to inspect the current JSON structure if needed
  - The form uid and all submission data are preserved through replace_form""",
    "deploy": """Workflow: Deploy a New Form

STEP 1 — Prepare an XLSForm (.xlsx) with these sheets:
  "survey" sheet columns:  type, name, label (+ label::Language columns for translations)
  "choices" sheet columns: list_name, name, label (+ label::Language columns)
  "settings" sheet:        form_title, form_id, default_language (optional)

STEP 2 — Deploy:
  deploy_form(file_path="/path/to/survey.xlsx", form_name="My Survey")
  → Returns uid, enketo_url (web form link), and management_url

STEP 3 — Verify:
  get_form(form_uid="<uid>")
  → Check the form structure is correct

TIPS:
  - form_name is optional; defaults to the filename without extension
  - The enketo_url is the shareable web form link for data collection
  - To update later, use replace_form() (not deploy_form) to keep the same uid""",
    "data": """Workflow: Retrieve and Export Data

OPTION A — Fetch submissions directly (good for small datasets or filtering):
  get_submissions(form_uid="aBC123xYz", limit=100, start=0)
  → Returns JSON with submission data
  → Use query parameter for filtering: query='{"district": "Kampala"}'

OPTION B — Export as CSV/XLS (good for large datasets or analysis):
  export_data(form_uid="aBC123xYz", export_type="csv")
  → Returns a download URL for the export file

TIPS:
  - get_submissions supports pagination via limit/start
  - export_data supports "csv" or "xls" format
  - Set include_labels=True (default) for human-readable column headers
  - For large forms, export_data is more efficient than paginating through get_submissions""",
}


@mcp.tool()
async def info(topic: str | None = None) -> str:
    """Get help and discover KoboToolbox MCP capabilities and workflows.

    Call this tool to learn what tools are available and how to use them
    together for common tasks like translating forms, deploying surveys,
    or exporting data.

    Args:
        topic: Optional topic for detailed guidance. One of:
               "overview" (default) — list all tools and workflows
               "translate" — step-by-step guide to adding form translations
               "deploy" — how to deploy a new XLSForm
               "data" — how to fetch and export submission data

    Returns:
        Workflow documentation as text.
    """
    key = (topic or "overview").lower().strip()
    if key not in WORKFLOWS:
        return f"Unknown topic: {topic}. Available topics: {', '.join(WORKFLOWS.keys())}"
    return WORKFLOWS[key]


@mcp.tool()
async def list_forms(search: str | None = None) -> str:
    """List all KoboToolbox forms/surveys.

    Use this as a starting point to find form UIDs for other tools.
    Call info(topic="translate") or info(topic="data") for workflow guidance.

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
    """Get a form's JSON structure including questions, choices, and settings.

    Returns the internal JSON representation — useful for inspecting form
    structure. To get the editable XLSForm (.xlsx), use export_form() instead.

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
        "deployment_links": data.get("deployment__links", {}),
        "submission_count": data.get("deployment__submission_count", 0),
        "date_created": data.get("date_created"),
        "date_modified": data.get("date_modified"),
        "owner": data.get("owner__username"),
        "content": data.get("content"),  # Contains survey structure
    }
    return json.dumps(result, indent=2)


@mcp.tool()
async def resolve_form(enketo_url: str) -> str:
    """Find the form UID that corresponds to an Enketo submission URL.

    Given an Enketo URL (e.g. https://ee.kobotoolbox.org/single/6F7QA1uJ),
    searches all deployed forms to find the one whose deployment links match.
    Returns the form UID, name, and all deployment links.

    Args:
        enketo_url: The Enketo submission URL to look up.

    Returns:
        JSON object with uid, name, and deployment_links, or an error if not found.
    """
    # Normalize: strip trailing slashes
    target = enketo_url.strip().rstrip("/")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/",
            headers=get_headers(),
            params={"asset_type": "survey"},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    for asset in data.get("results", []):
        links = asset.get("deployment__links", {}) or {}
        for _key, url in links.items():
            if isinstance(url, str) and url.rstrip("/") == target:
                return json.dumps(
                    {
                        "uid": asset.get("uid"),
                        "name": asset.get("name"),
                        "deployment_links": links,
                    },
                    indent=2,
                )

    return json.dumps({"error": f"No form found matching Enketo URL: {enketo_url}"})


@mcp.tool()
async def export_form(form_uid: str, output_path: str) -> str:
    """Download an existing form as an XLSForm (.xlsx) file.

    This is essential for modifying existing forms — for example, adding
    translations. The typical workflow is:
      1. export_form() to get the .xlsx
      2. Edit the .xlsx (e.g., add label::Language columns for translations)
      3. replace_form() to redeploy with changes

    Note: get_form() returns the JSON representation, not the XLSForm.
    Use this tool when you need the actual .xlsx to edit and re-upload.

    Args:
        form_uid: The unique identifier (uid) of the form.
        output_path: Local file path where the .xlsx will be saved.

    Returns:
        JSON object with form_uid, output_path, and form name.
    """
    import os.path

    # Create parent directories if needed
    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    async with httpx.AsyncClient() as client:
        # Get form metadata first (for the name in the response)
        meta_response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}/",
            headers=get_headers(),
            timeout=30.0,
        )
        meta_response.raise_for_status()
        meta = meta_response.json()

        # Download the XLSForm binary
        response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}.xls",
            headers=get_headers(),
            timeout=60.0,
        )
        response.raise_for_status()

        # Write binary content to file
        with open(output_path, "wb") as f:
            f.write(response.content)

    return json.dumps(
        {
            "form_uid": form_uid,
            "name": meta.get("name"),
            "output_path": output_path,
            "status": "downloaded",
        },
        indent=2,
    )


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
    """Upload and deploy a NEW XLSForm to KoboToolbox.

    Creates a new form and makes it live. The XLSForm can include
    multiple languages via label::Language (code) columns.

    To update an EXISTING form, use replace_form() instead — it preserves
    the form UID and all existing submissions.

    Args:
        file_path: Path to the XLSForm (.xlsx) file.
        form_name: Optional name for the form (defaults to filename).

    Returns:
        JSON object with uid, enketo_url (web form link), and management_url.
    """
    import os.path

    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    name = form_name or os.path.splitext(os.path.basename(file_path))[0]

    async with httpx.AsyncClient() as client:
        # Step 1: Upload the XLSForm to create an asset
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"name": name, "asset_type": "survey"}
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

        # Step 3: Get asset info including enketo URL
        asset_response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/{uid}/",
            headers=get_headers(),
            timeout=30.0,
        )
        asset_response.raise_for_status()
        asset_data = asset_response.json()

    # Extract enketo submission URL from deployment links
    deployment_links = asset_data.get("deployment__links", {})
    enketo_url = deployment_links.get("url") or deployment_links.get("offline_url")

    return json.dumps(
        {
            "uid": uid,
            "name": name,
            "status": "deployed",
            "enketo_url": enketo_url,
            "management_url": f"{KOBO_SERVER}/#/forms/{uid}",
        },
        indent=2,
    )


@mcp.tool()
async def replace_form(form_uid: str, file_path: str) -> str:
    """Replace an existing form with a new XLSForm version.

    Updates the form definition while preserving the form UID and all existing
    submissions. Use this for adding translations, modifying questions, or any
    update to a live form.

    Typical translation workflow:
      1. export_form() → download the .xlsx
      2. Add label::Language (code) columns to survey and choices sheets
      3. replace_form() → redeploy with translations

    Call info(topic="translate") for detailed guidance.

    Args:
        form_uid: The unique identifier (uid) of the form to replace.
        file_path: Path to the new XLSForm (.xlsx) file.

    Returns:
        JSON object with uid, enketo_url, and management_url.
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
        # PATCH with version_id triggers actual redeployment of new content
        # First get the current asset version
        version_response = await client.get(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}/",
            headers=get_headers(),
            timeout=30.0,
        )
        version_response.raise_for_status()
        version_data = version_response.json()
        version_id = version_data.get("version_id")

        deploy_response = await client.patch(
            f"{KOBO_SERVER}/api/v2/assets/{form_uid}/deployment/",
            headers=get_headers(),
            json={"active": True, "version_id": version_id},
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

    # Extract enketo submission URL from deployment links
    deployment_links = asset.get("deployment__links", {})
    enketo_url = deployment_links.get("url") or deployment_links.get("offline_url")

    return json.dumps(
        {
            "uid": form_uid,
            "name": asset.get("name"),
            "status": "redeployed",
            "submission_count": asset.get("deployment__submission_count", 0),
            "enketo_url": enketo_url,
            "management_url": f"{KOBO_SERVER}/#/forms/{form_uid}",
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
