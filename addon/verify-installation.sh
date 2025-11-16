#!/bin/bash
# Wine Fermentation Monitor - Installation Verification Script

set -e

ADDON_DIR="/home/user/tipsyhomelab/addon"

echo "======================================================================"
echo "Wine Fermentation Monitor - Installation Verification"
echo "======================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (MISSING)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (MISSING)"
        return 1
    fi
}

errors=0

echo "Checking core add-on structure..."
check_file "$ADDON_DIR/config.yaml" || ((errors++))
check_file "$ADDON_DIR/Dockerfile" || ((errors++))
check_file "$ADDON_DIR/build.yaml" || ((errors++))
check_file "$ADDON_DIR/requirements.txt" || ((errors++))
check_file "$ADDON_DIR/run.sh" || ((errors++))
echo ""

echo "Checking documentation..."
check_file "$ADDON_DIR/README.md" || ((errors++))
check_file "$ADDON_DIR/DOCS.md" || ((errors++))
check_file "$ADDON_DIR/CHANGELOG.md" || ((errors++))
check_file "$ADDON_DIR/LICENSE" || ((errors++))
echo ""

echo "Checking application files..."
check_dir "$ADDON_DIR/rootfs/app" || ((errors++))
check_file "$ADDON_DIR/rootfs/app/__init__.py" || ((errors++))
check_file "$ADDON_DIR/rootfs/app/main.py" || ((errors++))
check_file "$ADDON_DIR/rootfs/app/config.py" || ((errors++))
echo ""

echo "Checking translations..."
check_dir "$ADDON_DIR/translations" || ((errors++))
check_file "$ADDON_DIR/translations/en.yaml" || ((errors++))
echo ""

echo "Checking configuration files..."
check_file "$ADDON_DIR/.dockerignore" || ((errors++))
check_file "$ADDON_DIR/.gitignore" || ((errors++))
check_file "$ADDON_DIR/test-config.json" || ((errors++))
echo ""

# Validate YAML syntax
echo "Validating YAML syntax..."
if command -v python3 &> /dev/null; then
    python3 -c "import yaml; yaml.safe_load(open('$ADDON_DIR/config.yaml'))" 2>/dev/null && \
        echo -e "${GREEN}✓${NC} config.yaml syntax valid" || \
        echo -e "${RED}✗${NC} config.yaml syntax invalid" && ((errors++))
else
    echo -e "${YELLOW}⚠${NC} Python3 not available, skipping YAML validation"
fi
echo ""

# Check file permissions
echo "Checking file permissions..."
if [ -x "$ADDON_DIR/run.sh" ]; then
    echo -e "${GREEN}✓${NC} run.sh is executable"
else
    echo -e "${RED}✗${NC} run.sh is not executable"
    ((errors++))
fi
echo ""

# Check Python syntax
echo "Checking Python syntax..."
if command -v python3 &> /dev/null; then
    python3 -m py_compile "$ADDON_DIR/rootfs/app/main.py" 2>/dev/null && \
        echo -e "${GREEN}✓${NC} main.py syntax valid" || \
        echo -e "${RED}✗${NC} main.py syntax invalid" && ((errors++))

    python3 -m py_compile "$ADDON_DIR/rootfs/app/config.py" 2>/dev/null && \
        echo -e "${GREEN}✓${NC} config.py syntax valid" || \
        echo -e "${RED}✗${NC} config.py syntax invalid" && ((errors++))
else
    echo -e "${YELLOW}⚠${NC} Python3 not available, skipping Python validation"
fi
echo ""

# Summary
echo "======================================================================"
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Add-on structure is complete.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Copy addon/ directory to your Home Assistant addons folder"
    echo "  2. Refresh the Add-on Store"
    echo "  3. Install 'Wine Fermentation Monitor'"
    echo "  4. Configure MQTT and sensors"
    echo "  5. Start the add-on"
else
    echo -e "${RED}✗ $errors error(s) found. Please fix them before installation.${NC}"
    exit 1
fi
echo "======================================================================"
