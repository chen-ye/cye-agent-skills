# Procedure: Obtaining and Extracting Antigravity Binaries

This guide documents the canonical procedure for acquiring the official Google Antigravity Agent Client Protocol (ACP) package from public distribution channels and extracting the unstripped internal debug harness.

---

## 1. Package Discovery via ACP Agent Registry

The official Google package is cataloged in the open **Agent Client Protocol Registry**:

* **Registry Index URL**: `https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json`
* **Agent Identifier**: `antigravity-acp`

### Query Latest Release Asset URL
```bash
curl -sL https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json | \
  jq -r '.agents[] | select(.id=="antigravity-acp") | .distribution.binary["linux-x86_64"].archive'
```
*Direct Google CDN endpoint pattern:*
`https://dl.google.com/agy-extensions/releases/linux/agy-acp-server-agy_acp_server_<version>-linux-x86_64.zip`

---

## 2. Downloading and Unpacking the Release

1. **Download the archive**:
   ```bash
   mkdir -p /tmp/antigravity_dl
   curl -L -o /tmp/antigravity_dl/package.zip \
     https://dl.google.com/agy-extensions/releases/linux/agy-acp-server-agy_acp_server_1.1.1-linux-x86_64.zip
   ```

2. **Unpack distribution binaries**:
   ```bash
   unzip -q /tmp/antigravity_dl/package.zip -d /tmp/antigravity_dl/
   # Contents:
   #  - agy_acp_server.par (1.8 GB: Python/C++ server)
   #  - localharness_external (123 MB: Stripped Go execution harness)
   ```

3. **Install release binaries to PATH**:
   ```bash
   mkdir -p ~/.local/bin
   mv /tmp/antigravity_dl/agy_acp_server.par ~/.local/bin/
   mv /tmp/antigravity_dl/localharness_external ~/.local/bin/
   chmod +x ~/.local/bin/agy_acp_server.par ~/.local/bin/localharness_external
   ```

---

## 3. Extracting the Unstripped Debug Binary

Over half of `agy_acp_server.par` (~987 MB) consists of the unstripped development build of `localharness` bundled inside the PAR's internal ZIP archive.

To avoid decompressing or streaming from the 1.8 GB archive during investigation sessions, extract the unstripped binary directly to `~/.local/share/antigravity/`:

```bash
mkdir -p ~/.local/share/antigravity

python3 -c "
import zipfile, shutil, os

par_path = os.path.expanduser('~/.local/bin/agy_acp_server.par')
dest_path = os.path.expanduser('~/.local/share/antigravity/localharness.debug')

with zipfile.ZipFile(par_path) as z:
    with z.open('google3/third_party/jetski_prod/localharness/localharness') as src, open(dest_path, 'wb') as dst:
        shutil.copyfileobj(src, dst, length=16*1024*1024)

os.chmod(dest_path, 0o755)
print('Extracted unstripped localharness.debug (size:', os.path.getsize(dest_path), 'bytes)')
"
```

### Automated Extraction Utility
A helper script is bundled in this skill:
```bash
~/.gemini/skills/investigate-antigravity/scripts/extract_debug_binary.py
```
It automatically locates `agy_acp_server.par` from `~/.local/bin/`, extracts `localharness.debug`, and verifies ELF and `.symtab` integrity.
