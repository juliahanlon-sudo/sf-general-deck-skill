# SF General Deck Skill

A Claude Code plugin for creating Salesforce-branded Google Slides presentations.

## Overview

This plugin provides both a skill definition and MCP server implementation for generating presentation slides with Salesforce branding, data integration, and automated formatting.

## Features

- **General Deck Builder**: Create Salesforce-branded presentations using the Corporate Template 2026
- **Content Research**: Automatically research and populate slide content from web sources
- **Author Detection**: Auto-detect author name from git config or Google account
- **Google Slides API Integration**: Direct manipulation of slides via Google Slides API
- **Automated Formatting**: Salesforce color scheme, fonts, and layout standards

## Structure

```
.
├── .claude-plugin/     # Plugin metadata
│   └── plugin.json
├── server/             # MCP server implementation
│   └── slides_server.py
├── skills/             # Claude Code skills
│   └── sf-general-deck/
│       └── skill.md
└── .mcp.json          # MCP server configuration
```

## Installation

This plugin is designed to work within the Claude Code ecosystem. Place it in your `~/.claude/plugins/` directory structure.

## Usage

Invoke via Claude Code skills:
- `/sf-general-deck` - Build a general-purpose Salesforce-branded presentation

The skill will:
1. Ask for presentation title, sections, content, and any links/photos
2. Research any sections where content wasn't provided
3. Generate a deck plan for your review
4. Build the deck using the Salesforce Corporate Template 2026
5. Open the finished presentation in your browser

## Requirements

- Claude Code
- Google Workspace access
- Authentication via MCP adaptor (run `/salesforce-trust-foundations:mcp-auth`)

## Workflow

1. **Intake**: Provide title, sections, and content
2. **Research**: Automatically research blank sections from the web
3. **Plan**: Review the deck structure before building
4. **Build**: Generate slides from the Salesforce template
5. **Verify**: Auto-open and check for any issues

## Author

Julia Hanlon

## Version

1.2.0
