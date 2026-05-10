# Install Client Script via Customize Form

## Steps

1. Open any Landed Cost Voucher document

2. Click **Menu (⋮)** → **Customize**

3. Scroll down to **Client Script** section

4. Copy entire content from `landed_cost_client_script.js`

5. Paste into the Client Script field

6. Click **Update**

7. Reload any Landed Cost Voucher form

## Test

1. Create new Landed Cost Voucher

2. In "Vouchers" table, add Purchase Invoice: PHR-LOC-PINV-2026-00008

3. Shipment ID should auto-fill: SHIP-IMP-AWB-174

4. Check "Auto-fetch Vendor Invoices"

5. "Landed Cost" table should populate with 2 vendor invoices

## If It Doesn't Work

Check browser console (F12) for errors. The script runs client-side, errors will show there.
