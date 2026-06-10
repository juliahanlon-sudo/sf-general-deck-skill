#!/usr/bin/env python3
"""
MCP Server for Google Slides creation.
Provides a slides_create tool that creates presentations from structured content.
"""

import json
import sys
import os
from typing import Any, Dict, List

# MCP Protocol implementation
def send_message(message: Dict[str, Any]):
    """Send a message following MCP protocol."""
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()

def read_message() -> Dict[str, Any]:
    """Read a message from stdin."""
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)

def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "google-slides-custom",
            "version": "1.0.0"
        }
    }

def handle_list_tools(params: Dict[str, Any]) -> Dict[str, Any]:
    """List available tools."""
    return {
        "tools": [
            {
                "name": "slides_create",
                "description": "Create a Google Slides presentation from structured content. Takes a title and list of slides with titles and bullet points.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Presentation title"
                        },
                        "slides": {
                            "type": "array",
                            "description": "Array of slide objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string",
                                        "description": "Slide title"
                                    },
                                    "bullets": {
                                        "type": "array",
                                        "description": "Bullet points for the slide",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["title"]
                            }
                        }
                    },
                    "required": ["title", "slides"]
                }
            }
        ]
    }

def create_slides_presentation(title: str, slides: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Create a Google Slides presentation.
    This uses the Google Slides API v1.
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        # Try to get credentials from AI Expert Suite's Google integration
        # The MCP server should inherit the same auth context
        creds = None

        # Check for existing token from AI Expert Suite
        token_path = os.path.expanduser("~/.aisuite/google_token.json")
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token_data = json.load(f)
                creds = Credentials.from_authorized_user_info(token_data)

        if not creds:
            return {
                "error": "Google authentication not found. Please ensure Google is connected in AI Expert Suite settings.",
                "presentation_url": ""
            }

        # Build the Slides API service
        service = build('slides', 'v1', credentials=creds)

        # Create a new presentation
        presentation = {
            'title': title
        }

        presentation_response = service.presentations().create(body=presentation).execute()
        presentation_id = presentation_response.get('presentationId')

        # Now add slides with content
        requests = []

        for idx, slide in enumerate(slides):
            # Create a new slide
            slide_id = f'slide_{idx}'
            requests.append({
                'createSlide': {
                    'objectId': slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY' if slide.get('bullets') else 'TITLE_ONLY'
                    }
                }
            })

        # Execute batch create
        if requests:
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()

        # Now add text to slides
        text_requests = []
        for idx, slide in enumerate(slides):
            slide_id = f'slide_{idx}'

            # Add title
            text_requests.append({
                'insertText': {
                    'objectId': slide_id,
                    'text': slide['title'],
                    'insertionIndex': 0
                }
            })

            # Add bullets if present
            if slide.get('bullets'):
                bullet_text = '\n'.join(f'• {bullet}' for bullet in slide['bullets'])
                text_requests.append({
                    'insertText': {
                        'objectId': slide_id,
                        'text': f'\n\n{bullet_text}',
                        'insertionIndex': len(slide['title'])
                    }
                })

        if text_requests:
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': text_requests}
            ).execute()

        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"

        return {
            "presentation_id": presentation_id,
            "presentation_url": presentation_url,
            "slides_created": len(slides)
        }

    except ImportError:
        return {
            "error": "Google API client library not installed. Run: pip install google-api-python-client google-auth",
            "presentation_url": ""
        }
    except HttpError as error:
        return {
            "error": f"Google API error: {error}",
            "presentation_url": ""
        }
    except Exception as e:
        return {
            "error": f"Error creating presentation: {str(e)}",
            "presentation_url": ""
        }

def handle_call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool call."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name == "slides_create":
        title = arguments.get("title")
        slides = arguments.get("slides", [])

        result = create_slides_presentation(title, slides)

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"error": f"Unknown tool: {tool_name}"})
            }
        ],
        "isError": True
    }

def main():
    """Main server loop."""
    # Send initial message indicating readiness
    send_message({"jsonrpc": "2.0", "method": "initialized", "params": {}})

    while True:
        try:
            message = read_message()
            if not message:
                break

            method = message.get("method")
            params = message.get("params", {})
            msg_id = message.get("id")

            if method == "initialize":
                result = handle_initialize(params)
            elif method == "tools/list":
                result = handle_list_tools(params)
            elif method == "tools/call":
                result = handle_call_tool(params)
            else:
                result = {"error": f"Unknown method: {method}"}

            # Send response
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
            send_message(response)

        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": message.get("id") if message else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            send_message(error_response)

if __name__ == "__main__":
    main()
