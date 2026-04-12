import json
import os

def fix_labels(file_path):
    print(f"Fixing {file_path}")
    with open(file_path, 'r') as f:
        data = json.load(f)
    for field in data.get('fields', []):
        if field['fieldname'] == 'quantity':
            field['label'] = 'Tender Quantity'
        elif field['fieldname'] == 'price':
            field['label'] = 'Tender Price'
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=1)

base_dir = "f:/Workfiles/oncopharma project/Onco/onco/onco/doctype"
fix_labels(os.path.join(base_dir, "onco_price_offer", "onco_price_offer.json"))
fix_labels(os.path.join(base_dir, "distributors_price_offer", "distributors_price_offer.json"))
print("Done")
