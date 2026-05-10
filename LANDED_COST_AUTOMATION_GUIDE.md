# Landed Cost Automation - User Guide

## Overview

This feature automates the distribution of landed costs (vendor service charges) to imported pharmaceutical items based on Shipment ID. It eliminates manual lookup and ensures accurate cost allocation.

## How It Works

### The Three-Step Process

#### Step 1: Foreign Supplier Purchase Invoice
- Create a Purchase Invoice for imported pharma items from the foreign supplier
- Link it to the **Shipment ID** using the "Shipment ID" field
- This invoice contains the base cost of the imported items

#### Step 2: Vendor Service Purchase Invoices
- Create separate Purchase Invoices for local service vendors (customs, freight, storage, etc.)
- Set the **Shipment ID (Vendor Services)** dimension on each invoice
- This tags the vendor costs to a specific shipment

#### Step 3: Landed Cost Voucher - Auto-fetch
- Create a new Landed Cost Voucher
- Select the Purchase Receipt (which is linked to the foreign supplier invoice)
- The system automatically:
  - Detects the Shipment ID
  - Finds all vendor invoices with the same Shipment ID
  - Populates the "Taxes and Charges" table
  - Uses the expense accounts from vendor invoices
  - Distributes costs to the imported items

## Field Guide

### Purchase Invoice Fields

| Field Name | Location | Purpose | Used For |
|------------|----------|---------|----------|
| **Shipment ID** | After Supplier Name | Link foreign supplier invoice to shipment | Foreign supplier invoices |
| **Shipment ID (Vendor Services)** | After Shipment ID | Tag vendor costs to shipment (accounting dimension) | Vendor service invoices |

### Landed Cost Voucher Fields

| Field Name | Location | Purpose |
|------------|----------|---------|
| **Shipment ID** | After Company | Auto-detected from Purchase Receipt (read-only) |
| **Auto-fetch Vendor Invoices** | After Shipment ID | Enable to automatically load vendor costs |

## Step-by-Step Workflow

### 1. Create Foreign Supplier Invoice

```
Purchase Invoice
├── Supplier: [Foreign Supplier Name]
├── Shipment ID: SHIP-IMP-AWB-12345
└── Items: [Imported pharma items]
```

**Submit the invoice**

### 2. Create Vendor Service Invoices

For each vendor (customs broker, freight forwarder, etc.):

```
Purchase Invoice
├── Supplier: [Vendor Name - e.g., Customs Broker]
├── Shipment ID (Vendor Services): SHIP-IMP-AWB-12345  ← Important!
├── Items/Expenses:
│   ├── Customs Clearance Fee
│   ├── Expense Account: Customs Expenses - Onco
│   └── Amount: 5,000
```

**Submit each vendor invoice**

### 3. Create Purchase Receipt

- Create Purchase Receipt from the Shipment
- The Purchase Receipt will automatically link to the Shipment ID
- Submit the Purchase Receipt

### 4. Create Landed Cost Voucher

1. Go to: **Stock → Landed Cost Voucher → New**

2. Select Company

3. In "Purchase Receipts" table, add the Purchase Receipt created in Step 3

4. The system will:
   - Auto-detect Shipment ID: `SHIP-IMP-AWB-12345`
   - Display it in the "Shipment ID" field

5. **Enable "Auto-fetch Vendor Invoices"** checkbox

6. The system automatically populates "Taxes and Charges" with:
   ```
   Description                    | Expense Account           | Amount
   ─────────────────────────────────────────────────────────────────
   Customs Broker - PINV-2026-001 | Customs Expenses - Onco   | 5,000
   Freight Co - PINV-2026-002     | Freight Expenses - Onco   | 3,000
   Storage Co - PINV-2026-003     | Storage Expenses - Onco   | 2,000
   ```

7. Review and adjust distribution if needed

8. **Submit** the Landed Cost Voucher

### 5. Result

- Item valuation increases by the total vendor costs (10,000 in example)
- Costs are distributed proportionally across imported items
- GL entries reflect the proper expense accounts
- All costs are traceable back to the Shipment ID

## Manual Override

If auto-fetch doesn't work or you need to manually add charges:

1. Uncheck "Auto-fetch Vendor Invoices"
2. Click **"Fetch Vendor Invoices"** button (appears when Shipment ID is set)
3. Or manually add rows in "Taxes and Charges" table

## Troubleshooting

### "No Vendor Invoices Found"

**Cause**: Vendor invoices don't have the Shipment ID dimension set

**Solution**:
1. Open each vendor Purchase Invoice
2. Find "Shipment ID (Vendor Services)" field
3. Set it to the correct Shipment ID
4. Save and re-submit if needed
5. Return to Landed Cost Voucher and retry auto-fetch

### "Shipment ID not detected"

**Cause**: Purchase Receipt is not linked to a Shipment

**Solution**:
1. Verify the Purchase Receipt has `custom_shipment_ref` or `shipment` field set
2. If missing, create Purchase Receipt from Shipment document
3. Or manually set the Shipment ID in Landed Cost Voucher

### "Wrong expense account"

**Cause**: Vendor invoice has multiple expense accounts

**Solution**:
- The system uses the expense account with the highest amount
- You can manually edit the expense account in Landed Cost Voucher before submitting

## Technical Notes

### Accounting Dimension

The "Shipment ID (Vendor Services)" field is configured as an **Accounting Dimension**, which means:
- It appears on GL Entry
- It can be used for financial reporting
- It enables tracking of costs by shipment across the entire accounting system

### Database Fields

| DocType | Field Name | Type | Purpose |
|---------|------------|------|---------|
| Purchase Invoice | `custom_shipments` | Link | Foreign supplier invoice → Shipment |
| Purchase Invoice | `custom_shipment_id_dimension` | Link (Dimension) | Vendor invoice → Shipment |
| Landed Cost Voucher | `custom_shipment_id` | Link | Auto-detected Shipment |
| Landed Cost Voucher | `custom_auto_fetch_vendor_invoices` | Check | Enable auto-fetch |

## Frappe v16 Compatibility

This implementation is fully compatible with Frappe v16 and uses:
- ✅ Modern Query Builder syntax
- ✅ Standard Accounting Dimensions API
- ✅ Client-side form events
- ✅ Server-side whitelisted methods
- ✅ Document hooks (validate, before_submit)

## Installation

Run the installation script after app installation:

```bash
bench --site [your-site-name] execute onco.onco.install_landed_cost_dimension.run_installation
```

This will:
1. Create the Shipment ID accounting dimension
2. Verify custom fields are installed
3. Display installation status

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the implementation plan: `LANDED_COST_AUTOMATION_PLAN.md`
3. Check Frappe logs: `bench --site [site] console` → `frappe.get_traceback()`

---

**Version**: 1.0  
**Last Updated**: May 10, 2026  
**Frappe Version**: v16+  
**ERPNext Version**: v16+
