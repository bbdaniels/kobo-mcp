# Kobo MCP

An MCP server for KoboToolbox that enables Claude to deploy surveys and fetch submissions.

## Features

- **list_forms** - List all KoboToolbox surveys
- **get_form** - Get detailed form information
- **get_submissions** - Fetch survey responses
- **deploy_form** - Upload and deploy XLSForm files
- **export_data** - Export data as CSV or Excel

## Installation

```bash
pip install -e .
```

## Configuration

Set your KoboToolbox API token:

```bash
export KOBO_API_TOKEN="your-token-here"
export KOBO_SERVER="https://kf.kobotoolbox.org"  # optional, this is the default
```

To get your API token:
1. Go to KoboToolbox → Account Settings → Security
2. Click "Display" next to API token

## Usage with Claude

Add to your Claude configuration (`~/.claude.json` or Claude Desktop config):

```json
{
  "mcpServers": {
    "kobotoolbox": {
      "command": "kobo-mcp",
      "env": {
        "KOBO_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Development

```bash
# Install in development mode
pip install -e .

# Test with MCP inspector
npx @modelcontextprotocol/inspector kobo-mcp
```
