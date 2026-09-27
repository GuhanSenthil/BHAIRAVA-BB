#!/usr/bin/env bash
# BHAIRAVA-BB installer for Kali Linux / Debian-based systems.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_DIR}/.venv"
BIN_LINK="/usr/local/bin/bhairava"

echo "[*] BHAIRAVA-BB installer"
echo "[*] repo: ${REPO_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[-] python3 not found -- install it first" >&2
  exit 4
fi

if [ ! -d "${VENV_DIR}" ]; then
  echo "[*] creating virtualenv..."
  python3 -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[*] upgrading pip..."
python -m pip install --upgrade pip >/dev/null

echo "[*] installing bhairava-bb..."
pip install -e "${REPO_DIR}"

if [ -w "/usr/local/bin" ]; then
  ln -sf "${VENV_DIR}/bin/bhairava" "${BIN_LINK}"
  echo "[+] installed symlink: ${BIN_LINK}"
else
  echo "[!] cannot write /usr/local/bin without root."
  echo "    run: sudo ln -sf ${VENV_DIR}/bin/bhairava ${BIN_LINK}"
fi

echo "[*] verifying..."
bhairava --version

echo "[+] install complete."
