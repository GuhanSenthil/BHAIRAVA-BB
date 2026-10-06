#!/usr/bin/env bash

set -uo pipefail

PASS=0
FAIL=0

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
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

pass() {
    echo "[PASS] $1"
    PASS=$((PASS + 1))
}

fail() {
    echo "[FAIL] $1"
    FAIL=$((FAIL + 1))
}

run_safe() {
    local name="$1"
    shift

    if "$@" >/tmp/bhairava-tool-test.out 2>&1; then
        pass "$name"
        return 0
    fi

    # Some tools return non-zero for help/version while still working.
    if grep -qiE 'usage|version|help|options|flags' /tmp/bhairava-tool-test.out; then
        pass "$name"
        return 0
    fi

    fail "$name"
    sed -n '1,20p' /tmp/bhairava-tool-test.out
    return 1
}

log "BHAIRAVA-BB SAFE TOOL TEST"

echo "[*] This test performs NO target scanning."
echo "[*] No domains or IP addresses are supplied."
echo "[*] Only local executable/version/help checks are performed."

log "1. BINARY EXISTENCE"

for tool in "${TOOLS[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        path="$(command -v "$tool")"

        if [[ -x "$path" ]]; then
            pass "$tool -> $path"
        else
            fail "$tool -> not executable"
        fi
    else
        fail "$tool -> command not found"
    fi
done

log "2. TOOL HELP / VERSION TESTS"

run_safe "subfinder help" subfinder -h
run_safe "amass help" amass -h
run_safe "assetfinder help" assetfinder -h
run_safe "httpx version" httpx -version
run_safe "gau help" gau -h
run_safe "waybackurls help" waybackurls -h
run_safe "ffuf version" ffuf -V
run_safe "linkfinder help" linkfinder -h
run_safe "nuclei version" nuclei -version
run_safe "dalfox version" dalfox version
run_safe "sqlmap version" sqlmap --version

log "3. BHAIRAVA TOOL REGISTRY"

if bhairava tools; then
    pass "bhairava tools"
else
    fail "bhairava tools"
fi

log "4. BHAIRAVA STATUS"

if bhairava status; then
    pass "bhairava status"
else
    fail "bhairava status"
fi

log "5. PYTHON QUALITY"

if ./.venv/bin/python -m ruff check .; then
    pass "ruff"
else
    fail "ruff"
fi

log "6. PYTHON TEST SUITE"

if ./.venv/bin/python -m pytest -q; then
    pass "pytest"
else
    fail "pytest"
fi

rm -f /tmp/bhairava-tool-test.out

log "FINAL RESULT"

echo "PASS: $PASS"
echo "FAIL: $FAIL"

if [[ "$FAIL" -eq 0 ]]; then
    echo
    echo "============================================================"
    echo "ALL BHAIRAVA-BB TESTS PASSED"
    echo "============================================================"
    exit 0
fi

echo
echo "============================================================"
echo "BHAIRAVA-BB TESTS FAILED"
echo "============================================================"

exit 1
