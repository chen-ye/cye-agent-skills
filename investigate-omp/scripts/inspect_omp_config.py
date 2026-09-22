#!/usr/bin/env python3
"""
inspect_omp_config.py - Inspects and audits active OMP configuration, security policies, and model roles.

Reads resolved settings via 'omp config list --json' and parses ~/.omp/agent/config.yml / models.yml.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

def get_omp_bin() -> str:
    omp_bin = os.environ.get("OMP_BIN")
    if omp_bin and os.path.isfile(omp_bin) and os.access(omp_bin, os.X_OK):
        return omp_bin
    for candidate in ["/home/linuxbrew/.linuxbrew/bin/omp", "/usr/local/bin/omp", str(Path.home() / ".local/bin/omp")]:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return "omp"

def get_effective_config(omp_bin: str) -> dict:
    try:
        raw = subprocess.check_output([omp_bin, "config", "list", "--json"], stderr=subprocess.PIPE).decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to execute 'omp config list --json': {e}\n")
        return {}

def parse_simple_yaml_models(models_path: Path) -> dict:
    if not models_path.is_file():
        return {}
    content = models_path.read_text(encoding="utf-8", errors="ignore")
    providers = {}
    current_prov = None
    for line in content.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        # Provider heading under providers:
        prov_match = re.match(r"^  ([a-zA-Z0-9_\-]+):\s*$", line)
        if prov_match:
            current_prov = prov_match.group(1)
            providers[current_prov] = {}
            continue
        prop_match = re.match(r"^    ([a-zA-Z0-9_\-]+):\s*(.*)$", line)
        if prop_match and current_prov:
            k = prop_match.group(1)
            v = prop_match.group(2).strip().strip("\"'")
            if "key" in k.lower() or "token" in k.lower() or "secret" in k.lower():
                if len(v) > 8:
                    v = v[:4] + "..." + v[-4:]
            providers[current_prov][k] = v
    return providers

def format_overview(config: dict, agent_dir: Path, custom_providers: dict) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("OMP Configuration & Security Audit")
    lines.append("=" * 80)

    # 1. Model Roles
    roles = config.get("modelRoles", {}).get("value") or {}
    lines.append("\n[Model Roles]")
    if isinstance(roles, dict):
        for role, model in roles.items():
            lines.append(f"  {role:<12}: {model}")
    else:
        lines.append(f"  {roles}")

    # 2. Tool Approval & Security
    approval_mode = config.get("tools.approvalMode", {}).get("value", "write")
    per_tool = config.get("tools.approval", {}).get("value", {})
    interceptor = config.get("bashInterceptor.enabled", {}).get("value", False)

    lines.append("\n[Tool Approval & Sandboxing]")
    lines.append(f"  Default Approval Mode : {approval_mode}")
    lines.append(f"  Bash Interceptor      : {'enabled' if interceptor else 'disabled'}")
    lines.append("  Per-Tool Approvals    :")
    if isinstance(per_tool, dict):
        for t, policy in per_tool.items():
            lines.append(f"    - {t:<15}: {policy}")

    # 3. Bash Patterns Security Rules
    bash_patterns = config.get("bash.patterns", {}).get("value") or []
    allow_count = sum(1 for p in bash_patterns if p.get("approval") == "allow")
    deny_count = sum(1 for p in bash_patterns if p.get("approval") == "deny")
    prompt_count = sum(1 for p in bash_patterns if p.get("approval") == "prompt")

    lines.append("\n[Bash Security Patterns]")
    lines.append(f"  Total Rules : {len(bash_patterns)} (Allow: {allow_count}, Deny: {deny_count}, Prompt: {prompt_count})")
    lines.append("  Explicitly Denied Commands:")
    for p in bash_patterns:
        if p.get("approval") == "deny":
            lines.append(f"    [DENY] {p.get('match')}")

    # 4. Memory & Backend
    mem_backend = config.get("memory.backend", {}).get("value", "default")
    hs_url = config.get("hindsight.apiUrl", {}).get("value", "")
    lines.append("\n[Memory Subsystem]")
    lines.append(f"  Backend : {mem_backend}")
    if hs_url:
        lines.append(f"  Hindsight API: {hs_url}")

    # 5. Task & Agent Policy
    task_batch = config.get("task.batch", {}).get("value", True)
    concurrency = config.get("task.maxConcurrency", {}).get("value", 32)
    isolation = config.get("task.isolation.enabled", {}).get("value", False)
    lsp = config.get("task.enableLsp", {}).get("value", False)
    prewalk = config.get("task.prewalk", {}).get("value", False)

    lines.append("\n[Task & Subagent Orchestration]")
    lines.append(f"  Batch Spawning   : {'enabled' if task_batch else 'disabled'}")
    lines.append(f"  Max Concurrency  : {concurrency}")
    lines.append(f"  Task Isolation   : {'enabled' if isolation else 'disabled'}")
    lines.append(f"  Subagent LSP     : {'enabled' if lsp else 'disabled'}")
    lines.append(f"  Task Prewalk     : {'enabled' if prewalk else 'disabled'}")

    # 6. Custom Configured Providers
    if custom_providers:
        lines.append("\n[Configured Custom Providers (models.yml)]")
        for prov, details in custom_providers.items():
            base = details.get("baseUrl", "default")
            api = details.get("api", "default")
            lines.append(f"  {prov:<12}: api={api}, baseUrl={base}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Inspect and audit active OMP settings, model roles, and security policies.")
    parser.add_argument("--json", action="store_true", help="Output full effective configuration as JSON")
    parser.add_argument("--bash-rules", action="store_true", help="Print all bash pattern matching rules")
    parser.add_argument("--providers", action="store_true", help="Print detailed custom provider configurations")
    args = parser.parse_args()

    omp_bin = get_omp_bin()
    agent_dir = Path(os.environ.get("PI_CODING_AGENT_DIR", Path.home() / ".omp" / "agent"))
    models_path = agent_dir / "models.yml"

    effective_config = get_effective_config(omp_bin)
    custom_providers = parse_simple_yaml_models(models_path)

    if args.json:
        result = {
            "agentDir": str(agent_dir),
            "customProviders": custom_providers,
            "config": effective_config
        }
        print(json.dumps(result, indent=2))
        return

    if args.bash_rules:
        patterns = effective_config.get("bash.patterns", {}).get("value") or []
        print(f"Total Bash Pattern Rules: {len(patterns)}\n")
        print(f"{'Approval':<10} | Pattern")
        print("-" * 70)
        for p in patterns:
            appr = p.get("approval", "prompt").upper()
            match = p.get("match", "")
            print(f"{appr:<10} | {match}")
        return

    if args.providers:
        print("Configured Custom Providers in models.yml:\n")
        print(json.dumps(custom_providers, indent=2))
        return

    print(format_overview(effective_config, agent_dir, custom_providers))

if __name__ == "__main__":
    main()
