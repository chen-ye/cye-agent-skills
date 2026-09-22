import json
import os
import subprocess
import sys
import time
from pathlib import Path


def test_servers():
    settings_path = Path.home() / ".gemini" / "settings.json"
    if not settings_path.exists():
        print(f"Error: settings.json not found at {settings_path}")
        sys.exit(1)

    with open(settings_path) as f:
        data = json.load(f)

    servers = data.get("mcpServers", {})
    excluded = data.get("mcp", {}).get("excluded", [])

    results = []
    print("Testing enabled MCP servers...\n")

    for name, config in servers.items():
        if name in excluded:
            continue
            
        start = time.time()
        cmd = ["mcp", "tools"]
        env = os.environ.copy()
        
        if "command" in config:
            cmd.append(config["command"])
            cmd.extend(config.get("args", []))
        elif "url" in config or "httpUrl" in config:
            url = config.get("url") or config.get("httpUrl")
            cmd.append(url)
        else:
            results.append(f"⚠️  {name}: Skipped (No command or URL configured)")
            continue
            
        if "env" in config:
            for k, v in config["env"].items():
                env[k] = str(v)
                
        try:
            # Give it up to 15 seconds to respond
            res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
            elapsed = time.time() - start
            
            if res.returncode == 0:
                if elapsed > 3.0:
                    results.append(f"✅ {name}: Working, but slow ({elapsed:.2f}s)")
                else:
                    results.append(f"✅ {name}: Working ({elapsed:.2f}s)")
            else:
                err = (res.stderr.strip() or res.stdout.strip() or "Unknown error").split('\n')[-1]
                if "unexpected status code" in err or "Method Not Allowed" in err:
                    results.append(f"❓ {name}: Responded with HTTP error ({elapsed:.2f}s) - Endpoint is reachable but might require specific headers/SSE client. Error: {err[:100]}")
                else:
                    results.append(f"❌ {name}: Failed ({elapsed:.2f}s) - {err[:100]}")
                
        except subprocess.TimeoutExpired:
            results.append(f"⏳ {name}: Timeout (>15s)")
        except Exception as e:
            results.append(f"❌ {name}: Failed - {str(e)[:100]}")

    print("\n".join(results))

if __name__ == "__main__":
    test_servers()
