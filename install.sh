#!/usr/bin/env bash
# BHAIRAVA-BB installer for Kali Linux / Debian-based systems.
#
# Installs:
#   BHAIRAVA-BB
#   subfinder
#   amass
#   assetfinder
#   httpx (ProjectDiscovery)
#   gau
#   waybackurls
#   ffuf
#   linkfinder
#   nuclei
#   dalfox
#   sqlmap
#
# This installer configures software only. It does NOT run scans.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_DIR}/.venv"
BIN_DIR="/usr/local/bin"
LINKFINDER_DIR="/opt/bhairava-linkfinder"
LINKFINDER_VENV="${LINKFINDER_DIR}/.venv"
BHAIRAVA_LINK="${BIN_DIR}/bhairava"

TOOLS=(
    subfinder
    amass
    assetfinder
    httpx
    gau
    waybackurls
    ffuf
    linkfinder
    nuclei
    dalfox
    sqlmap
)

log() {
    echo
    echo "[*] $*"
}

ok() {
    echo "[+] $*"
}

warn() {
    echo "[!] $*" >&2
}

die() {
    echo "[-] $*" >&2
    exit 1
}

if [[ "${EUID}" -ne 0 ]]; then
    die "Run this installer with sudo: sudo ./install.sh"
fi

if [[ ! -f "${REPO_DIR}/pyproject.toml" ]]; then
    die "pyproject.toml not found. Run this from the BHAIRAVA-BB repository."
fi

export DEBIAN_FRONTEND=noninteractive

log "BHAIRAVA-BB installer"
echo "[*] Repository: ${REPO_DIR}"
echo "[*] User: ${SUDO_USER:-root}"
echo "[*] Architecture: $(uname -m)"

log "Installing system dependencies"

apt-get update

apt-get install -y \
    ca-certificates \
    curl \
    git \
    golang-go \
    python3 \
    python3-venv \
    python3-pip \
    build-essential \
    sqlmap

ok "System dependencies installed."

log "Checking Go"

command -v go >/dev/null 2>&1 || die "Go installation failed."

GO_VERSION="$(go version)"
echo "[*] ${GO_VERSION}"

# Modern Go supports automatic toolchain selection. This lets current
# ProjectDiscovery tools obtain a compatible Go toolchain when necessary.
export GOTOOLCHAIN=auto

mkdir -p "${BIN_DIR}"
chmod 755 "${BIN_DIR}"

log "Installing Go-based security tools"

install_go_tool() {
    local name="$1"
    local module="$2"

    echo
    echo "[*] Installing ${name}..."

    if GOBIN="${BIN_DIR}" go install "${module}"; then
        ok "${name} installed."
    else
        die "${name} installation failed."
    fi

    [[ -x "${BIN_DIR}/${name}" ]] || die "${name} binary was not created."
}

install_go_tool "subfinder" \
    "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"

install_go_tool "amass" \
    "github.com/owasp-amass/amass/v4/...@master"

install_go_tool "assetfinder" \
    "github.com/tomnomnom/assetfinder@latest"

#
# IMPORTANT:
# ProjectDiscovery httpx is different from Python's httpx CLI.
# If a Python httpx executable exists in /usr/local/bin, preserve it
# under a different name before installing ProjectDiscovery httpx.
#
if [[ -x "${BIN_DIR}/httpx" ]]; then
    if "${BIN_DIR}/httpx" --help 2>&1 | grep -qE "Usage: httpx \[OPTIONS\] URL"; then
        if [[ ! -e "${BIN_DIR}/httpx-python" ]]; then
            mv "${BIN_DIR}/httpx" "${BIN_DIR}/httpx-python"
            warn "Existing Python httpx CLI moved to ${BIN_DIR}/httpx-python."
        else
            rm -f "${BIN_DIR}/httpx"
        fi
    fi
fi

install_go_tool "httpx" \
    "github.com/projectdiscovery/httpx/cmd/httpx@latest"

install_go_tool "gau" \
    "github.com/lc/gau/v2/cmd/gau@latest"

install_go_tool "waybackurls" \
    "github.com/tomnomnom/waybackurls@latest"

install_go_tool "ffuf" \
    "github.com/ffuf/ffuf/v2@latest"

install_go_tool "nuclei" \
    "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"

install_go_tool "dalfox" \
    "github.com/hahwul/dalfox/v2@latest"

log "Installing LinkFinder"

if [[ ! -d "${LINKFINDER_DIR}/.git" ]]; then
    rm -rf "${LINKFINDER_DIR}"
    git clone --depth 1 \
        https://github.com/GerbenJavado/LinkFinder.git \
        "${LINKFINDER_DIR}"
else
    git -C "${LINKFINDER_DIR}" pull --ff-only
fi

python3 -m venv "${LINKFINDER_VENV}"

"${LINKFINDER_VENV}/bin/python" -m pip install --upgrade pip
"${LINKFINDER_VENV}/bin/python" -m pip install -r \
    "${LINKFINDER_DIR}/requirements.txt"

cat > "${BIN_DIR}/linkfinder" <<EOF
#!/usr/bin/env bash
exec "${LINKFINDER_VENV}/bin/python" \
    "${LINKFINDER_DIR}/linkfinder.py" "\$@"
EOF

chmod 755 "${BIN_DIR}/linkfinder"

ok "LinkFinder installed."

log "Verifying SQLMap"

command -v sqlmap >/dev/null 2>&1 || die "sqlmap installation failed."

ok "SQLMap installed."

log "Verifying all 11 core tools"

check_tool() {
    local name="$1"

    if command -v "${name}" >/dev/null 2>&1; then
        local path
        path="$(command -v "${name}")"
        echo "[+] ${name}: ${path}"
        return 0
    fi

    echo "[-] ${name}: NOT FOUND"
    return 1
}

missing=0

for tool in "${TOOLS[@]}"; do
    if ! check_tool "${tool}"; then
        missing=$((missing + 1))
    fi
done

echo
echo "============================================================"
echo "BHAIRAVA-BB CORE TOOL VERIFICATION"
echo "============================================================"
echo "Required: 11"
echo "Missing:  ${missing}"
echo "============================================================"

if [[ "${missing}" -ne 0 ]]; then
    die "Core tool installation incomplete: ${missing}/11 missing."
fi

ok "ALL 11 CORE TOOLS ARE INSTALLED."

log "Creating BHAIRAVA virtual environment"

if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip

log "Installing BHAIRAVA-BB"

python -m pip install -e "${REPO_DIR}"

ln -sf "${VENV_DIR}/bin/bhairava" "${BHAIRAVA_LINK}"
chmod 755 "${BHAIRAVA_LINK}"

ok "BHAIRAVA command installed: ${BHAIRAVA_LINK}"

log "Verifying BHAIRAVA"

"${BHAIRAVA_LINK}" --version
"${BHAIRAVA_LINK}" status

log "Verifying BHAIRAVA tool registry"

"${BHAIRAVA_LINK}" tools

log "Running first-run setup"

cd "${REPO_DIR}"

python - <<'PY'
from pathlib import Path

from bhairava.setup import run_first_setup
from bhairava.utils.tools import installed_tools

scope = Path("config/scope.yaml")
config = Path("config/config.yaml")

available = [tool.name for tool in installed_tools()]

print()
print("============================================================")
print("BHAIRAVA-BB FIRST-RUN")
print("============================================================")
print(f"Detected tools: {len(available)}/11")

if len(available) != 11:
    raise SystemExit(
        f"First-run setup requires all 11 core tools; detected {len(available)}/11."
    )

run_first_setup(
    scope_path=str(scope),
    config_path=str(config),
    available_tools=available,
)
PY

log "Final verification"

"${BHAIRAVA_LINK}" tools

echo
echo "============================================================"
echo "BHAIRAVA-BB INSTALLATION COMPLETE"
echo "============================================================"
echo
echo "BHAIRAVA version:"
"${BHAIRAVA_LINK}" --version

echo
echo "Core tools:"
"${BHAIRAVA_LINK}" tools

echo
echo "Scope configuration:"
if [[ -f "${REPO_DIR}/config/scope.yaml" ]]; then
    echo "[+] ${REPO_DIR}/config/scope.yaml"
else
    warn "No scope.yaml was created."
fi

echo
echo "[+] Installation finished."
echo "[+] No security scan was executed."
echo "[+] Only explicitly authorized targets should be tested."
echo "============================================================"
