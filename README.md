# BHAIRAVA-BB

Authorized Bug Bounty Security Research Framework.

Use only against targets you have explicit written authorization to test.

## Install (Kali / Debian)

    git clone https://github.com/GuhanSenthil/BHAIRAVA-BB
    cd BHAIRAVA-BB
    chmod +x install.sh
    sudo ./install.sh
    bhairava --version

## Usage

    bhairava --help
    bhairava scope validate <target>
    bhairava scope show
    bhairava tools
    bhairava status
    bhairava pipeline --dry-run

## Scope

Every active operation passes through the Scope Guard. Out-of-scope
targets are blocked before any network testing begins.

## Exit codes

    0  success
    1  general error
    2  invalid configuration
    3  scope violation
    4  missing dependency
    5  validation failure

## License

MIT. See LICENSE.
