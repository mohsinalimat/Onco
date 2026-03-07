# Quick Start: Batch Numbers in Purchase Invoice

## TL;DR

Batch numbers are now visible and mandatory in Purchase Invoices. Just run the installation commands and you're good to go.

## Installation (3 Commands)

```bash
bench --site your-site-name migrate
bench --site your-site-name clear-cache
bench restart
```

## What You'll See

### Before:
- ❌ Batch number field hidden
- ❌ Can't enter batch numbers
- ❌ Data missing in shipments

### After:
- ✅ Batch number field visible in item table
- ✅ Mandatory for batch-tracked items
- ✅ Auto-validation prevents errors
- ✅ Flows to Shipments → Purchase Receipt

## How to Use

1. **Create Purchase Invoice** from Purchase Order
2. **Add items** - batch field appears automatically
3. **Enter batch number** for each item
4. **Save** - validation ensures no batch is missing
5. **Submit** - batch flows to next documents

## Enable Batch Tracking on Items

For items that need batches:
1. Open Item master
2. Check "Has Batch No"
3. Save

## Troubleshooting One-Liner

```bash
bench --site your-site-name clear-cache && bench restart
```

## Need More Info?

- **Full Documentation**: `BATCH_NUMBER_CONFIGURATION.md`
- **Installation Guide**: `INSTALL_BATCH_CONFIGURATION.md`
- **Technical Summary**: `BATCH_NUMBER_SUMMARY.md`

## Support Checklist

If batch field not showing:
- [ ] Ran `bench migrate`?
- [ ] Cleared cache?
- [ ] Restarted bench?
- [ ] Item has "Has Batch No" enabled?
- [ ] "Update Stock" checked in Purchase Invoice?

## That's It!

The system now handles batch numbers automatically. Just enter them when creating Purchase Invoices and they'll flow through your entire importation cycle.
