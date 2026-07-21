#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/src"
OUTPUT_DIR="$SCRIPT_DIR/rendered"
MERMAID_VERSION="11.16.0"

mkdir -p "$OUTPUT_DIR"

if (( $# > 1 )); then
    echo "Usage: $0 [diagram-name]" >&2
    exit 2
fi

if (( $# == 1 )); then
    sources=("$SOURCE_DIR/$1.mmd")
    if [[ ! -f "${sources[0]}" ]]; then
        echo "Diagram source not found: ${sources[0]}" >&2
        exit 1
    fi
else
    sources=("$SOURCE_DIR"/*.mmd)
fi

for source in "${sources[@]}"; do
    name="$(basename "$source" .mmd)"

    npx -y "@mermaid-js/mermaid-cli@$MERMAID_VERSION" \
        -p "$SCRIPT_DIR/puppeteer-config.json" \
        -c "$SCRIPT_DIR/mermaid-config.json" \
        -i "$source" \
        -o "$OUTPUT_DIR/$name.svg" \
        -b white

    npx -y "@mermaid-js/mermaid-cli@$MERMAID_VERSION" \
        -p "$SCRIPT_DIR/puppeteer-config.json" \
        -c "$SCRIPT_DIR/mermaid-config.json" \
        -i "$source" \
        -o "$OUTPUT_DIR/$name.png" \
        -b white \
        -w 1600 \
        -H 900 \
        -s 1.5
done
