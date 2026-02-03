# Kobo MCP

[![PyPI version](https://badge.fury.io/py/kobo-mcp.svg)](https://pypi.org/project/kobo-mcp/)

An MCP server for KoboToolbox that enables Claude to deploy surveys and fetch submissions.

**[Documentation](https://bbdaniels.github.io/kobo-mcp/)**

## Features

- **list_forms** - List all KoboToolbox surveys
- **get_form** - Get detailed form information
- **get_submissions** - Fetch survey responses
- **deploy_form** - Upload and deploy XLSForm files
- **replace_form** - Update existing forms preserving submissions
- **export_data** - Export data as CSV or Excel

## Installation

```bash
pip install kobo-mcp
```

Or run directly with uvx (no install):

```bash
uvx kobo-mcp
```

## Configuration

### 1. Get your API token

Go to [KoboToolbox](https://kf.kobotoolbox.org) → Account Settings → Security → Display

### 2. Add to Claude

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "kobotoolbox": {
      "type": "stdio",
      "command": "kobo-mcp",
      "env": {
        "KOBO_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

Or with uvx:

```json
{
  "mcpServers": {
    "kobotoolbox": {
      "type": "stdio",
      "command": "uvx",
      "args": ["kobo-mcp"],
      "env": {
        "KOBO_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

For EU server, add `"KOBO_SERVER": "https://eu.kobotoolbox.org"` to env.

## Development

```bash
git clone https://github.com/bbdaniels/kobo-mcp.git
cd kobo-mcp
pip install -e .
```

## License

MIT
