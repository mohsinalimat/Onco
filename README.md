# Onco - ERPNext Custom App for Pharmaceutical Importation

**Version**: 1.0  
**ERPNext Version**: 15.x  
**License**: MIT

## Overview

Onco is a custom ERPNext application designed specifically for pharmaceutical companies managing imported products. It provides a complete importation cycle workflow from regulatory approval through to sales, with comprehensive quality control and compliance features.

## Key Features

- ✅ Complete importation cycle management
- ✅ Regulatory approval tracking (EDA-IMAR)
- ✅ Shipment tracking with milestones
- ✅ Comprehensive incoming inspection
- ✅ Automatic stock movements based on inspection results
- ✅ Temperature control monitoring
- ✅ Batch tracking and expiry management
- ✅ Multi-warehouse support
- ✅ Compliance documentation
- ✅ Complete audit trail

## Documentation

📖 **[Complete Importation Cycle Documentation](IMPORTATION_CYCLE_COMPLETE_DOCUMENTATION.md)**

This comprehensive guide covers:
- Complete workflow overview
- All doctypes and their purpose
- Step-by-step user guide
- Field mappings
- Automatic processes
- Troubleshooting
- Deployment guide

## Quick Start

### Installation

```bash
cd ~/frappe-bench
bench get-app https://github.com/your-repo/onco.git
bench --site [your-site] install-app onco
bench --site [your-site] migrate
bench --site [your-site] clear-cache
bench restart
```

### First Steps

1. Set up required warehouses
2. Configure permissions
3. Create test data
4. Follow the workflow in the documentation

## Workflow Summary

```
Importation Approval → Purchase Order → Purchase Invoice → Shipments
  → Purchase Receipt → Stock Entry (to Inspection)
  → Incoming Check Report → Auto Stock Entries
  → Purchase Receipt Report → Printing Order
  → Authority Good Release → Auto Stock Entry (to Sales)
  → Sales
```

## Support

- 📧 Email: support@oncopharma.com
- 📚 Documentation: [IMPORTATION_CYCLE_COMPLETE_DOCUMENTATION.md](IMPORTATION_CYCLE_COMPLETE_DOCUMENTATION.md)
- 🌐 ERPNext Forum: https://discuss.erpnext.com

## License

MIT License - See LICENSE file for details

## Credits

Developed for Onco Pharma by the ERPNext development team.
