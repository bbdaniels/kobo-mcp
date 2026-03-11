# Kobo MCP

[![PyPI version](https://badge.fury.io/py/kobo-mcp.svg)](https://pypi.org/project/kobo-mcp/)

An MCP server for KoboToolbox that enables Claude to deploy surveys and fetch submissions.

**[Documentation](https://bbdaniels.github.io/kobo-mcp/)**

**Requires Python 3.10+**

## Quick Start with Claude Code

Set your KoboToolbox API token, then register the server with a single command:

```bash
export KOBO_API_TOKEN="your-token-here"
claude mcp add kobotoolbox -- env KOBO_API_TOKEN=$KOBO_API_TOKEN uvx kobo-mcp
```

For the EU server, also pass the server URL:

```bash
export KOBO_API_TOKEN="your-token-here"
claude mcp add kobotoolbox -- env KOBO_API_TOKEN=$KOBO_API_TOKEN KOBO_SERVER=https://eu.kobotoolbox.org uvx kobo-mcp
```

That's it -- restart Claude Code and you can start managing KoboToolbox surveys directly from the CLI.

To get your API token, go to [KoboToolbox](https://kf.kobotoolbox.org) -> Account Settings -> Security -> API Key.

## Features

- **info** - Get help and discover workflows (translate, deploy, data export)
- **list_forms** - List all KoboToolbox surveys
- **get_form** - Get detailed form structure (JSON)
- **resolve_form** - Find the form UID for an Enketo submission URL
- **export_form** - Download an existing form as XLSForm (.xlsx)
- **get_submissions** - Fetch survey responses with optional filtering
- **deploy_form** - Upload and deploy new XLSForm files
- **replace_form** - Update existing forms preserving submissions
- **set_validation_status** - Approve, reject, or flag submissions
- **export_data** - Export data as CSV or Excel

## Installation

```bash
pip install kobo-mcp
```

Or run directly with uvx (no install needed):

```bash
uvx kobo-mcp
```

## Configuration

### Manual JSON configuration

If you prefer to configure Claude manually instead of using `claude mcp add`, add to `~/.claude.json`:

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

For the EU server, add `"KOBO_SERVER": "https://eu.kobotoolbox.org"` to the `env` block.

### Using with Claude Desktop

Add the same JSON block above to your Claude Desktop config file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## Development

```bash
git clone https://github.com/bbdaniels/kobo-mcp.git
cd kobo-mcp
pip install -e .
```

## Troubleshooting

### "KOBO_API_TOKEN not set"

The server requires a `KOBO_API_TOKEN` environment variable. Make sure it is passed in the `env` block of your MCP configuration, or exported in your shell before running `claude mcp add`.

To get your token: log in to [KoboToolbox](https://kf.kobotoolbox.org) -> Account Settings -> Security -> API Key.

### Server not appearing in Claude Code

After running `claude mcp add`, restart Claude Code for the change to take effect. You can verify the server is registered by running:

```bash
claude mcp list
```

### Connection errors or timeouts

- Check that your API token is valid and has not been revoked.
- If you are on the EU server (`eu.kobotoolbox.org`), make sure you set the `KOBO_SERVER` environment variable to `https://eu.kobotoolbox.org`.
- The default server is `https://kf.kobotoolbox.org`. If your organization uses a custom KoboToolbox instance, set `KOBO_SERVER` to its URL.

### "uvx: command not found"

Install `uv` first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or install with pip/pipx:

```bash
pip install uv
```

### Python version errors

Kobo MCP requires **Python 3.10 or later**. Check your version with:

```bash
python3 --version
```

## License

MIT
