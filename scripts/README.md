# Package Contract: `scripts`

## 1. Overview & System Scope

The `scripts` directory contains operational automation scripts for installing MiniKick from the official GitHub release channel. It is not part of the Python application runtime — it runs outside the application process as a user-invoked PowerShell script.

---

## 2. Files

| File | Type | Purpose |
| :--- | :--- | :--- |
| [`install.ps1`](./install.ps1) | PowerShell 5.1+ | Downloads the latest MiniKick release from GitHub, verifies its SHA-256 digest, and launches the Inno Setup installer. |

---

## 3. Interface

### `install.ps1`

**Parameters:**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `-Silent` | `[switch]` | Optional. Runs the Inno Setup installer in fully silent mode (`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-`). |

**Execution contract:**

1. Queries `https://api.github.com/repos/Andro2k/MiniKick/releases/latest` to resolve the latest version tag.
2. Locates the asset named exactly `MiniKick_Installer_v{version}.exe`.
3. Validates that the download URL originates from `github.com/Andro2k/MiniKick/releases/download/`.
4. Requires GitHub to supply a `sha256:` digest on the asset; aborts without downloading if absent.
5. Downloads the installer to a randomised `%TEMP%\MiniKick-Install-{guid}\` directory.
6. Verifies the SHA-256 hash of the downloaded file against the GitHub-provided digest before execution.
7. Launches the installer and waits for completion; throws if exit code is non-zero.
8. Removes the temporary directory unconditionally in the `finally` block.

---

## 4. Invariants

1. **Supply-Chain Validation**: The installer binary is never executed unless both the download URL domain and the SHA-256 digest pass the guard checks.
2. **Temporary File Cleanup**: `Remove-Item -Recurse -Force` on the temp directory runs in a `finally` block, guaranteeing cleanup even after errors.
3. **Version Tag Format Enforcement**: Rejects any release whose tag does not match `^\d+\.\d+\.\d+(?:\.\d+)?$`.

---

## 5. Side Effects

| Category | Target | Description |
| :--- | :--- | :--- |
| **Network** | `api.github.com`, `objects.githubusercontent.com` | Fetches release metadata and downloads the installer binary. |
| **Filesystem** | `%TEMP%\MiniKick-Install-{guid}\` | Creates and removes a temporary directory containing the downloaded installer. |
| **Process** | `MiniKick_Installer_v{version}.exe` | Launches the Inno Setup installer process and blocks until it exits. |

---

## 6. Usage

```powershell
# Interactive installation
irm https://raw.githubusercontent.com/Andro2k/MiniKick/main/scripts/install.ps1 | iex

# Silent installation (no UI prompts)
& .\scripts\install.ps1 -Silent
```
