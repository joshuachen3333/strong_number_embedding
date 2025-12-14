#!/bin/bash
# Pre-commit hook: Ensure CLAUDE.md is updated when source files change
#
# CUSTOMIZATION:
#   1. Set SOURCE_DIR to your source code directory
#   2. Set SOURCE_EXT to your file extension (js, py, ts, etc.)
#   3. Set CLAUDE_MD to the path of your CLAUDE.md file
#
# Installation:
#   1. Copy this file to your project's hooks/ directory
#   2. Customize the variables below
#   3. Run: ln -sf /path/to/hooks/pre-commit .git/hooks/pre-commit
#   4. Run: chmod +x .git/hooks/pre-commit
#
# To bypass (emergency only):
#   git commit --no-verify

# ============================================================
# CUSTOMIZE THESE VARIABLES FOR YOUR PROJECT
# ============================================================

SOURCE_DIR="viewer_v2/js"           # Directory containing source files
SOURCE_EXT="js"                      # File extension to watch (js, py, ts, etc.)
CLAUDE_MD="viewer_v2/CLAUDE.md"      # Path to CLAUDE.md file

# ============================================================
# DO NOT MODIFY BELOW THIS LINE
# ============================================================

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Get staged files
STAGED_SOURCE=$(git diff --cached --name-only --diff-filter=ACMR | grep "^${SOURCE_DIR}/.*\.${SOURCE_EXT}$" || true)
STAGED_CLAUDE=$(git diff --cached --name-only --diff-filter=ACMR | grep "^${CLAUDE_MD}$" || true)

# If no source files staged, allow commit
if [ -z "$STAGED_SOURCE" ]; then
    exit 0
fi

# Source files are staged - check if CLAUDE.md is also staged
if [ -z "$STAGED_CLAUDE" ]; then
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  COMMIT BLOCKED: CLAUDE.md not updated                        ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}You modified these source files:${NC}"
    echo "$STAGED_SOURCE" | sed 's/^/  - /'
    echo ""
    echo -e "${YELLOW}But ${CLAUDE_MD} is not staged.${NC}"
    echo ""
    echo "Before committing, please verify:"
    echo "  1. Did you add new functions? → Add to Component Index"
    echo "  2. Did you remove functions? → Remove from Component Index"
    echo "  3. Did you change function behavior? → Update description"
    echo "  4. Did you discover new patterns/anti-patterns? → Update Patterns section"
    echo ""
    echo "If CLAUDE.md genuinely doesn't need updates, stage it anyway:"
    echo -e "  ${GREEN}git add ${CLAUDE_MD}${NC}"
    echo ""
    echo "To bypass this check (emergency only):"
    echo -e "  ${RED}git commit --no-verify${NC}"
    echo ""
    exit 1
fi

# Both source and CLAUDE.md are staged - show reminder
echo ""
echo -e "${GREEN}✓ CLAUDE.md is staged along with source changes${NC}"
echo ""
echo -e "${YELLOW}Quick verification checklist:${NC}"
echo "  □ Component Index reflects new/changed functions"
echo "  □ Design Patterns updated if new pattern discovered"
echo "  □ Anti-Patterns updated if new pitfall discovered"
echo ""

exit 0
