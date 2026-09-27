#!/usr/bin/env bash
set -euo pipefail
BIN_LINK="/usr/local/bin/bhairava"
if [ -L "${BIN_LINK}" ]; then
  rm -f "${BIN_LINK}"
  echo "[+] removed ${BIN_LINK}"
fi
echo "[*] to remove the virtualenv and package, delete this folder."
