---
layout: default
title: Kobo MCP
---

# Kobo MCP

An MCP (Model Context Protocol) server that enables Claude to interact with KoboToolbox -- deploy surveys, fetch submissions, and export data.

## Features

| Tool | Description |
|------|-------------|
| `list_forms` | List all KoboToolbox surveys with optional search filtering |
| `get_form` | Get detailed form information including question structure |
| `get_submissions` | Fetch survey responses with pagination and filtering |
| `deploy_form` | Upload and deploy new XLSForm surveys |
| `replace_form` | Update an existing form while preserving submissions |
| `export_data` | Export data as CSV or Excel with configurable options |

## Installation

```bash
pip install kobo-mcp
```

Or run directly with uvx (no install needed):

```bash
uvx kobo-mcp
```

## Configuration

### 1. Get your KoboToolbox API token

1. Log in to [KoboToolbox](https://kf.kobotoolbox.org)
2. Go to **Account Settings** → **Security**
3. Click **Display** next to your API token

### 2. Add to Claude configuration

Add the following to your `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "kobotoolbox": {
      "type": "stdio",
      "command": "kobo-mcp",
      "env": {
        "KOBO_API_TOKEN": "your-token-here",
        "KOBO_SERVER": "https://kf.kobotoolbox.org"
      }
    }
  }
}
```

For EU server users, set `KOBO_SERVER` to `https://eu.kobotoolbox.org`.

### 3. Restart Claude

The MCP server will be available after restarting Claude Code or Claude Desktop.

## Usage Examples

### List all forms

```
Claude, list my KoboToolbox forms
```

### Deploy a new survey

```
Claude, deploy the XLSForm at /path/to/survey.xlsx to KoboToolbox
```

### Fetch submissions

```
Claude, get all submissions for form abc123
```

### Update an existing form

```
Claude, replace form abc123 with the updated XLSForm at /path/to/survey_v2.xlsx
```

### Export data

```
Claude, export form abc123 data as CSV
```

## API Reference

### list_forms

```python
list_forms(search: str | None = None) -> str
```

Lists all deployed KoboToolbox surveys. Optionally filter by name using the `search` parameter.

**Returns**: JSON array of form objects with `uid`, `name`, `deployment_status`, `submission_count`, etc.

---

### get_form

```python
get_form(form_uid: str) -> str
```

Gets detailed information about a specific form, including the survey structure.

**Parameters**:
- `form_uid`: The unique identifier of the form

**Returns**: JSON object with form details and `content` containing the survey structure.

---

### get_submissions

```python
get_submissions(
    form_uid: str,
    limit: int = 100,
    start: int = 0,
    query: str | None = None
) -> str
```

Fetches survey responses with pagination support.

**Parameters**:
- `form_uid`: The unique identifier of the form
- `limit`: Maximum submissions to return (default 100)
- `start`: Offset for pagination (default 0)
- `query`: Optional JSON query string for filtering (e.g., `'{"field": "value"}'`)

**Returns**: JSON object with `count` and `results` array.

---

### deploy_form

```python
deploy_form(file_path: str, form_name: str | None = None) -> str
```

Uploads and deploys a new XLSForm survey.

**Parameters**:
- `file_path`: Path to the XLSForm (.xlsx) file
- `form_name`: Optional name for the form (defaults to filename)

**Returns**: JSON object with `uid`, `name`, `status`, and `url`.

---

### replace_form

```python
replace_form(form_uid: str, file_path: str) -> str
```

Replaces an existing form with a new XLSForm version. Preserves the form UID and all existing submissions.

**Parameters**:
- `form_uid`: The unique identifier of the form to replace
- `file_path`: Path to the new XLSForm (.xlsx) file

**Returns**: JSON object with `uid`, `name`, `status`, `submission_count`, and `url`.

---

### export_data

```python
export_data(
    form_uid: str,
    export_type: str = "csv",
    include_labels: bool = True
) -> str
```

Creates and retrieves a data export for a form.

**Parameters**:
- `form_uid`: The unique identifier of the form
- `export_type`: Export format -- `"csv"` or `"xls"` (default `"csv"`)
- `include_labels`: Include question labels in headers (default `True`)

**Returns**: JSON object with `status` and `download_url`.

## Development

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector kobo-mcp
```

### Running the server directly

```bash
# Set environment variables
export KOBO_API_TOKEN="your-token"
export KOBO_SERVER="https://kf.kobotoolbox.org"

# Run
kobo-mcp
```

Note: The server communicates via stdin/stdout (STDIO transport), so it won't produce visible output when run directly.

## Requirements

- Python 3.11+
- `mcp[cli]` -- MCP Python SDK
- `httpx` -- Async HTTP client

## Links

- [KoboToolbox](https://www.kobotoolbox.org/) -- Open source survey platform
- [KoboToolbox API Documentation](https://support.kobotoolbox.org/api.html)
- [MCP Protocol](https://modelcontextprotocol.io/) -- Model Context Protocol specification
- [Claude Code](https://claude.ai/code) -- Claude's CLI tool

## License

MIT
