#!/bin/bash
# ==============================================================================
# Switch to Production Database
# สลับไปใช้ฐานข้อมูล Production
# ==============================================================================

echo "=========================================================================="
echo "  Switching to PRODUCTION Database"
echo "  CeremonyBadge_Production"
echo "=========================================================================="
echo ""

# ตรวจสอบว่ามีไฟล์ .env.production หรือไม่
if [ ! -f ".env.production" ]; then
    echo "❌ Error: .env.production not found!"
    echo "   Please create .env.production first"
    exit 1
fi

# Backup .env ปัจจุบัน
if [ -f ".env" ]; then
    echo "📋 Backing up current .env to .env.development..."
    cp .env .env.development
    echo "   ✅ Backup complete"
fi

# Copy .env.production เป็น .env
echo "🔄 Switching to production environment..."
cp .env.production .env
echo "   ✅ Now using Production database"

echo ""
echo "=========================================================================="
echo "✅ Successfully switched to PRODUCTION"
echo ""
echo "📊 Current database: CeremonyBadge_Production"
echo "⚠️  DEBUG mode: False (Production)"
echo ""
echo "🔄 To switch back to development, run: ./use_development.sh"
echo "=========================================================================="
