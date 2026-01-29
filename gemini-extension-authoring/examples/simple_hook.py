#!/usr/bin/env python3
import sys
import json
import os

def log(msg):
    """Log to stderr to avoid corrupting JSON stdout."""
    sys.stderr.write(f"[hook] {msg}\n")

def main():
    # 1. Configuration via Environment Variables (set by gemini-extension.json settings)
    api_key = os.environ.get("SERVICE_API_TOKEN")
    if not api_key:
        log("Warning: SERVICE_API_TOKEN is not set.")
    
    # 2. Read Event Data from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data:
            return
        data = json.loads(input_data)
    except Exception as e:
        log(f"Error parsing input: {e}")
        return

    event = data.get("hook_event_name")
    log(f"Received event: {event}")

    # 3. Process Event
    if event == "AfterAgent":
        response = data.get("prompt_response", "")
        log(f"Agent finished with response length: {len(response)}")
        
        # Example: Perform an action (e.g., call an API)
        # ... implementation ...

    # 4. Return Data (Optional) via stdout
    # print(json.dumps({"status": "success"}))

if __name__ == "__main__":
    main()

