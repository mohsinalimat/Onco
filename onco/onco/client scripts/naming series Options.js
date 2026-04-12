frappe.ui.form.on("Tenders", {
    onload(frm) {
        set_naming_series(frm);
    },

    tender_type(frm) {
        set_naming_series(frm);
    },

    category(frm) {
        set_naming_series(frm);
    },

    tender_number(frm) {
        set_naming_series(frm);
    }
});

function set_naming_series(frm) {
    let series = "";

    const tender_type = frm.doc.tender_type;
    const category = frm.doc.category;
    const is_accepted = frm.doc.is_accepted_tender;

    // Tenders for Market Data
    if (tender_type === "Tenders for market data") {
        series = "TNDR-FMD-.YYYY.-.####";
    }

    // Awarded Tenders
    else if (tender_type === "Awarded Tenders") {
        if (is_accepted) {
            // Accepted tender naming
            if (category === "UPA Tender") {
                series = "TNDR-ACP-UPA-.YYYY.-.{tender_number}.";
            }
            else if (category === "Private Tender") {
                series = "TNDR-ACP-PRV-.YYYY.-.{tender_number}.";
            }
        } else {
            // Awarded tender naming - removed tender_number requirement
            if (category === "UPA Tender") {
                series = "TNDR-AWR-UPA-.YYYY.-.{tender_number}.";
            }
            else if (category === "Private Tender") {
                series = "TNDR-AWR-PRV-.YYYY.-.{tender_number}.";
            }
        }
    }

    // Set only if changed and prevent FMD on Awarded Tenders
    if (series && frm.doc.naming_series !== series) {
        frm.set_value("naming_series", series);
    } else if (tender_type === "Awarded Tenders" && frm.doc.naming_series && frm.doc.naming_series.includes("FMD")) {
        // Force correction if FMD is set on Awarded Tender
        if (series) {
            frm.set_value("naming_series", series);
        }
    }
}
