# Quick Reference - Oncopharma Fixes

## 🔴 MOST CRITICAL FIX

### Issue #20: Net Released Qty Calculation

**Problem**: Negative values (-100 instead of 200)

**Fix**: Changed formula in `calculate_net_quantities()` method

**Before**: `net_released = released - shortage` ❌
**After**: `net_released = released` ✓

**Example**:
- Requested: 500
- Released: 200
- Shortage Control: 300
- Net Released: 200 ✓ (was -100 ❌)

---

## All Fixes at a Glance

| Issue | What Was Fixed | File |
|-------|---------------|------|
| #19 | Added shipments validation | `shipments.py` |
| #20 | Fixed net released qty formula | `authority_good_release.py` |
| #21 | Fixed release type update error | `authority_good_release.py` |
| #22 | Verified (no changes) | - |
| #23 | Added registration number field | `item_price_registration.json` |
| #24 | Hidden update_stock field | `purchase_invoice.json` |
| #25 | Not implemented (feature request) | - |
| #26 | Fixed serial/batch bundle error | `authority_good_release.py` |

---

## Deployment Commands

```bash
# 1. Backup
bench --site your-site-name backup

# 2. Pull changes
cd ~/frappe-bench/apps/onco
git pull origin main

# 3. Migrate
bench --site your-site-name migrate

# 4. Clear cache
bench --site your-site-name clear-cache

# 5. Restart
bench restart
```

---

## Quick Test

### Test Net Released Qty (Issue #20)
1. Create Authority Good Release
2. Select: Lot Release Batch → With Shortage Control
3. Item: Requested=500, Released=200, Shortage=300
4. **Verify**: Net Released = 200 (NOT -100)

### Test Stock Entry (Issue #26)
1. Submit Authority Good Release
2. Click "Create Stock Entries"
3. **Verify**: No "already used" error

### Test Shipments (Issue #19)
1. Create Shipment
2. Try to submit without filling fields
3. **Verify**: Error messages appear

### Test Update Stock Hidden (Issue #24)
1. Open Purchase Invoice
2. **Verify**: "Update Stock" field is NOT visible

---

## Formula Reference

### Shortage Control Logic

```
Requested Qty = Released Qty + Shortage Control Qty

Example:
500 = 200 + 300

Where:
- Requested Qty: 500 (total available)
- Released Qty: 200 (going to warehouse)
- Shortage Control Qty: 300 (staying in source)
- Net Released Qty: 200 (same as Released)
```

---

## Rollback (If Needed)

```bash
# Restore database
bench --site your-site-name restore /path/to/backup.sql.gz

# Revert code
cd ~/frappe-bench/apps/onco
git revert HEAD

# Restart
bench restart
```

---

## Documentation Files

- `FINAL_SUMMARY.md` - Complete overview
- `IMPLEMENTATION_GUIDE.md` - Detailed deployment steps
- `CRITICAL_FIX_NET_RELEASED_QTY.md` - Issue #20 deep dive
- `FIXES_COMPLETED.md` - Executive summary
- `QUICK_REFERENCE.md` - This file

---

## Support

**Error Logs**: `bench --site your-site-name logs`

**Common Issues**:
- Field not found → Run `bench migrate` again
- Validation not working → Clear cache
- Stock entry fails → Check batch tracking enabled

---

**Status**: ✅ Ready for Deployment
**Priority**: 🔴 Deploy ASAP (critical bugs fixed)

