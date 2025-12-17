#!/bin/bash
# ==============================================================================
# Switch to Development Database
# สลับกลับไปใช้ฐานข้อมูล Development
# ==============================================================================

echo "=========================================================================="
echo "  Switching to DEVELOPMENT Database"
echo "  CeremonyBadge (Development)"
echo "=========================================================================="
echo ""

# ตรวจสอบว่ามีไฟล์ .env.development หรือไม่
if [ ! -f ".env.development" ]; then
    echo "⚠️  Warning: .env.development not found!"
    echo "   Creating from current .env..."

    if [ -f ".env" ]; then
        cp .env .env.development
    else
        echo "❌ Error: No .env file found!"
        exit 1
    fi
fi

# Copy .env.development เป็น .env
echo "🔄 Switching to development environment..."
cp .env.development .env
echo "   ✅ Now using Development database"

echo ""
echo "=========================================================================="
echo "✅ Successfully switched to DEVELOPMENT"
echo ""
echo "📊 Current database: CeremonyBadge"
echo "🐛 DEBUG mode: True (Development)"
echo ""
echo "🔄 To switch to production, run: ./use_production.sh"
echo "=========================================================================="
