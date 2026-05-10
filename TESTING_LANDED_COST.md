# Testing Landed Cost Automation

## Prerequisites

1. Run migration to install custom fields:
```bash
bench --site [your-site] migrate
bench --site [your-site] clear-cache
```

2. Reload your browser

## Test Workflow

### Step 1: Create Foreign Supplier Purchase Invoice

1. Go to: **Buying → Purchase Invoice → New**

2. Fill in:
   - **Supplier**: Select your foreign supplier (e.g., "Foreign Pharma Co")
   - **Shipment ID**: Select an existing shipment (e.g., "SHIP-IMP-AWB-12345")
   - **Items**: Add imported pharma items
     - Item Code: [Your pharma item]
     - Qty: 100
     - Rate: 50.00
     - Amount: 5,000.00

3. **Save and Submit**

4. Note the invoice number (e.g., "PINV-2026-001")

---

### Step 2: Create Vendor Service Purchase Invoices

#### Vendor Invoice #1 - Customs Clearance

1. Go to: **Buying → Purchase Invoice → New**

2. Fill in:
   - **Supplier**: "Customs Broker Ltd"
   - **Shipment ID (Vendor Services)**: "SHIP-IMP-AWB-12345" ← **IMPORTANT!**
   - **Items/Expenses**:
     - Description: "Customs Clearance Fee"
     - Expense Account: "Customs Expenses - Onco" (or similar)
     - Qty: 1
     - Rate: 1,500.00

3. **Save and Submit**

#### Vendor Invoice #2 - Freight

1. Go to: **Buying → Purchase Invoice → New**

2. Fill in:
   - **Supplier**: "Freight Forwarder Co"
   - **Shipment ID (Vendor Services)**: "SHIP-IMP-AWB-12345" ← **IMPORTANT!**
   - **Items/Expenses**:
     - Description: "Air Freight Charges"
     - Expense Account: "Freight Expenses - Onco"
     - Qty: 1
     - Rate: 2,000.00

3. **Save and Submit**

#### Vendor Invoice #3 - Storage (Optional)

1. Go to: **Buying → Purchase Invoice → New**

2. Fill in:
   - **Supplier**: "Warehouse Storage Co"
   - **Shipment ID (Vendor Services)**: "SHIP-IMP-AWB-12345" ← **IMPORTANT!**
   - **Items/Expenses**:
     - Description: "Cold Storage Fee"
     - Expense Account: "Storage Expenses - Onco"
     - Qty: 1
     - Rate: 500.00

3. **Save and Submit**

---

### Step 3: Create Purchase Receipt

1. Go to the **Shipment** document: "SHIP-IMP-AWB-12345"

2. Click **Create → Purchase Receipt**

3. The Purchase Receipt will auto-populate with items from the foreign supplier invoice

4. **Save and Submit**

5. Note the Purchase Receipt number (e.g., "MAT-PRE-2026-001")

---

### Step 4: Create Landed Cost Voucher (AUTO-FETCH TEST)

1. Go to: **Stock → Landed Cost Voucher → New**

2. Fill in:
   - **Company**: Your company
   - **Posting Date**: Today

3. In **Purchase Receipts** table, click **Add Row**:
   - **Purchase Receipt**: "MAT-PRE-2026-001" (from Step 3)
   - Click anywhere outside the field

4. **Watch what happens**:
   - ✅ "Shipment ID" field should auto-populate: "SHIP-IMP-AWB-12345"

5. **Enable Auto-fetch**:
   - Check the box: **"Auto-fetch Vendor Invoices"**

6. **Watch the magic**:
   - The "Taxes and Charges" table should automatically populate with:
     ```
     Description                          | Expense Account           | Amount
     ─────────────────────────────────────────────────────────────────────────
     Customs Broker Ltd - PINV-2026-002   | Customs Expenses - Onco   | 1,500
     Freight Forwarder Co - PINV-2026-003 | Freight Expenses - Onco   | 2,000
     Warehouse Storage Co - PINV-2026-004 | Storage Expenses - Onco   |   500
     ─────────────────────────────────────────────────────────────────────────
     Total Taxes and Charges                                         | 4,000
     ```

7. The "Items" table should show:
   - Your pharma item with the landed cost distributed

8. **Save and Submit**

---

## Expected Results

### Before Landed Cost Voucher:
- Item valuation: **5,000.00** (base cost only)

### After Landed Cost Voucher:
- Item valuation: **9,000.00** (5,000 + 4,000 landed costs)
- Landed cost per unit: **90.00** (9,000 / 100 units)

### GL Entries Created:
```
Account                          | Debit  | Credit | Shipment ID
─────────────────────────────────────────────────────────────────
Stock In Hand                    | 4,000  |        | SHIP-IMP-AWB-12345
Customs Expenses - Onco          |        | 1,500  | SHIP-IMP-AWB-12345
Freight Expenses - Onco          |        | 2,000  | SHIP-IMP-AWB-12345
Storage Expenses - Onco          |        |   500  | SHIP-IMP-AWB-12345
```

---

## Troubleshooting

### ❌ "Shipment ID" field doesn't auto-populate

**Check**:
1. Does the Purchase Receipt have `custom_shipment_ref` or `shipment` field set?
2. Open Purchase Receipt → Check if Shipment link exists
3. If missing, the Purchase Receipt wasn't created from Shipment

**Fix**: Create Purchase Receipt from Shipment document using "Create" button

---

### ❌ "Auto-fetch" doesn't find vendor invoices

**Check**:
1. Open each vendor Purchase Invoice
2. Look for field: **"Shipment ID (Vendor Services)"**
3. Is it set to the correct Shipment ID?
4. Are the invoices **submitted** (docstatus = 1)?

**Fix**: 
- Edit vendor invoices (if draft)
- Set "Shipment ID (Vendor Services)" = "SHIP-IMP-AWB-12345"
- Submit them
- Return to Landed Cost Voucher and check "Auto-fetch" again

---

### ❌ Wrong expense account appears

**Reason**: Vendor invoice has multiple expense accounts, system picks the one with highest amount

**Fix**: Manually edit the expense account in Landed Cost Voucher before submitting

---

### ❌ "Auto-fetch Vendor Invoices" checkbox doesn't exist

**Check**:
```bash
bench --site [site] migrate
bench --site [site] clear-cache
```

Then reload browser (Ctrl+Shift+R)

---

## Manual Testing Alternative

If auto-fetch doesn't work, you can manually test:

1. In Landed Cost Voucher, after Shipment ID appears
2. Click button: **"Fetch Vendor Invoices"** (should appear in top-right)
3. This manually triggers the same auto-fetch logic

---

## Verification Queries

Run these in `bench console` to verify data:

```python
# Check if vendor invoices have Shipment ID dimension
frappe.db.sql("""
    SELECT name, supplier_name, grand_total, custom_shipment_id_dimension
    FROM `tabPurchase Invoice`
    WHERE custom_shipment_id_dimension = 'SHIP-IMP-AWB-12345'
    AND docstatus = 1
""", as_dict=1)

# Check Landed Cost Voucher
lcv = frappe.get_doc("Landed Cost Voucher", "LCV-2026-001")
print(f"Shipment ID: {lcv.custom_shipment_id}")
print(f"Total Charges: {lcv.total_taxes_and_charges}")
for tax in lcv.taxes:
    print(f"  {tax.description}: {tax.amount} ({tax.expense_account})")
```

---

## Success Criteria

✅ Shipment ID auto-detects from Purchase Receipt  
✅ Vendor invoices auto-populate in Taxes and Charges  
✅ Correct expense accounts are used  
✅ Item valuation increases by vendor costs  
✅ All costs traceable to Shipment ID  

---

**Test Date**: _____________  
**Tested By**: _____________  
**Result**: ☐ Pass  ☐ Fail  
**Notes**: _____________________________________________
