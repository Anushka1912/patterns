import re
import json
import sys
from pathlib import Path


def extract_invoice_data(text):
    """
    Extracts invoice data from text file into the required JSON structure.
    Uses pattern matching logic - no hardcoded values.
    Handles multiple invoice formats dynamically.
    """
    data = {
        "HeaderItem": {
            "GrnDate": "",
            "SupplierCIN": "",
            "TotalInvoiceAmount": "",
            "ShipToAddress": "",
            "ShipFromAddres": "",
            "IgstAmount": "",
            "CgstAmount": "",
            "TotalCess": "",
            "CustomerGstin": "",
            "EwayBillDate": "",
            "EwayBillNo": "",
            "SupplierPanNumber": "",
            "IrnDate": "",
            "ShipToGstin": "",
            "ShipFromGSTIN": "",
            "SupplierAddress": "",
            "TotalTax": "",
            "CustomerPanNumber": "",
            "InvoiceNumber": "",
            "InvoiceDate": "",
            "CustomerName": "",
            "IrnNo": "",
            "DocType": "",
            "PlaceOfSupply": "",
            "PoNumber": "",
            "ShipToName": "",
            "ShipFromName": "",
            "TotalAmount": "",
            "PoDate": "",
            "SupplierGstin": "",
            "RCMApplicable": "",
            "SupplierName": "",
            "GrnNo": "",
            "SgstAmount": "",
            "CustomerAddress": ""
        },
        "LineItems": []
    }

    # Helper function to find pattern in text
    def find_pattern(pattern, group_num=1, flags=re.IGNORECASE | re.DOTALL):
        match = re.search(pattern, text, flags)
        if not match:
            return ""
        # If group_num is 0 or pattern has no groups, return the whole match
        try:
            return match.group(group_num).strip()
        except IndexError:
            return match.group(0).strip() if group_num == 0 else ""
    
    def clean_value(value):
        """Clean extracted value by removing extra whitespace and newlines"""
        if not value:
            return ""
        return re.sub(r'\s+', ' ', value).strip()

    # ===== SUPPLIER INFORMATION =====
    
    # Extract Supplier Name - multiple patterns for different formats
    # Format 5: "## Company's Name" pattern
    supplier_name = find_pattern(r'^([A-Z\s&]+(?:ENTERPRISES|INDUSTRIES|SOLUTIONS|PRODUCTS|SERVICES|CORPORATION|COMPANY)[^\n]*?)(?:\n|$)', flags=re.MULTILINE | re.IGNORECASE)
    if not supplier_name:
        supplier_name = find_pattern(r'^([A-Z\s&]+(?:PVT|PRIVATE|LTD|LIMITED|INDUSTRIES|FOOTWEAR)[A-Z\s.]*?)\.?\s*\n', flags=re.MULTILINE | re.IGNORECASE)
    if not supplier_name:
        supplier_name = find_pattern(r'##\s*Company[\'"]?s?\s+Name\s*\n\s*([^\n]+)', flags=re.IGNORECASE | re.MULTILINE)
    if not supplier_name:
        supplier_name = find_pattern(r'^##\s*(.+?)(?:\n|$)', flags=re.MULTILINE)  # Format 2: ## heading
    if not supplier_name:
        supplier_name = find_pattern(r'^#\s*(.+?)(?:\n|$)', flags=re.MULTILINE)  # Format 1 & 3: # heading
    if not supplier_name:
        supplier_name = find_pattern(r'\|\s*BILL FROM\s*\|[^\n]*\n\|[^|]*\|\s*([^|]+?)\s*\|')
    if not supplier_name:
        # Format 9: "**Bill From**" at bottom
        supplier_name = find_pattern(r'\*\*Bill\s+From\*\*\s*\n([^\n]+)', flags=re.IGNORECASE)
    if not supplier_name:
    # Format 10: "## PROTECH APPLIANCES PRIVATE LIMITED" pattern
        supplier_name = find_pattern(r'##\s*([A-Z\s]+(?:PRIVATE|PVT)?\s+LIMITED)', flags=re.IGNORECASE | re.MULTILINE)
    data["HeaderItem"]["ShipFromName"] = clean_value(supplier_name)

    # Supplier Address - Format 5: line after Company's Name
    supplier_addr = find_pattern(r'^[A-Z\s&]+(?:ENTERPRISES|INDUSTRIES)[^\n]*\n(.+?)(?=Email|Phone|GSTN)', flags=re.DOTALL | re.IGNORECASE)
    if not supplier_addr:
        supplier_addr = find_pattern(r'^[A-Z\s&]+(?:PVT|PRIVATE|LTD|LIMITED)\.?\s*\n\s*(.+?)(?=\s+\d{3}\s+\d{8}|TAX\s+INVOICE)', flags=re.MULTILINE | re.IGNORECASE)
    if not supplier_addr:
        supplier_addr = find_pattern(r'##\s*Company[\'"]?s?\s+Name\s*\n\s*[^\n]+\n\s*([^\n]{5,200})', flags=re.IGNORECASE | re.MULTILINE)
    if not supplier_addr:
        # Format 3: FACTORY : address pattern
        supplier_addr = find_pattern(r'FACTORY\s*:\s*(.+?)(?=\n##|\nGST|\n\|)', flags=re.DOTALL | re.IGNORECASE)
    if not supplier_addr:
        supplier_addr = find_pattern(r'##\s*.+?\n(.+?)(?=Phone|GSTN|GST|PAN|CIN|\n\*\*|\n---)', flags=re.DOTALL)
    if not supplier_addr:
        supplier_addr = find_pattern(r'BILL FROM.*?Address\s*:\s*([^|]+?)(?:GST IN|PAN|$)', flags=re.DOTALL | re.IGNORECASE)
    if not supplier_addr:
        # Registered office fallback
        supplier_addr = find_pattern(r'Regd\.?\s*off?\.?\s*:\s*(.+?)(?:\n---|$)', flags=re.IGNORECASE)
    if not supplier_addr:
        # Format 9: "Address:-" after Bill From
        supplier_addr = find_pattern(r'\*\*Bill\s+From\*\*.*?Address\s*:-\s*(.+?)(?=Reg\.|CIN|$)', flags=re.DOTALL | re.IGNORECASE)
    if not supplier_addr:
    # Format 10: Address line after company name, before first table
        supplier_addr = find_pattern(r'##\s*[A-Z\s]+LIMITED\s*\n+(.+?)(?=\n\s*\|)', flags=re.DOTALL | re.IGNORECASE)
    data["HeaderItem"]["SupplierAddress"] = clean_value(supplier_addr)
    
    # Ship From Address - Format 5: "Ship From Address" section
    ship_from_addr = find_pattern(r'Ship\s+From\s+Address\s*\n([^\n]+)', flags=re.IGNORECASE)
    if not ship_from_addr:
        ship_from_addr = data["HeaderItem"]["SupplierAddress"]
    data["HeaderItem"]["ShipFromAddres"] = clean_value(ship_from_addr)

    # Supplier GSTIN - Format 5: "### GSTIN/UIN" pattern
    supplier_gstin = find_pattern(r'GSTN\s+No\.?\s*:\s*\n([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not supplier_gstin:
        supplier_gstin = find_pattern(r'1\.\s*GSTIN\s*\n([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not supplier_gstin:
        supplier_gstin = find_pattern(r'###\s*GSTIN\s*/\s*UIN\s*\n([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not supplier_gstin:
        supplier_gstin = find_pattern(r'##\s*GST\s*[-\s]+([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not supplier_gstin:
        supplier_gstin = find_pattern(r'GSTN?\s*:\s*([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not supplier_gstin:
        supplier_gstin = find_pattern(r'BILL FROM.*?GST\s*IN\s*:\s*([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not supplier_gstin:
        supplier_gstin = find_pattern(r'GST\s*IN\s*:\s*([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not supplier_gstin:
        # Format 9: "GST Number:" at bottom
        supplier_gstin = find_pattern(r'GST\s+Number\s*:\s*([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not supplier_gstin:
    # Format 10: "| GSTIN/UJN | : value |" in header table
        supplier_gstin = find_pattern(r'\|\s*GSTIN\s*/\s*UJN\s*\|\s*:\s*([0-9A-Z]{15})\s*\|', flags=re.IGNORECASE)
    data["HeaderItem"]["SupplierGstin"] = supplier_gstin
    

    # Supplier PAN - Format 5: "### PAN" pattern
    supplier_pan = find_pattern(r'###\s*PAN\s*\n([0-9A-Z]{10})', flags=re.IGNORECASE)
    if not supplier_pan:
        supplier_pan = find_pattern(r'PAN\s*No\.?\s*:\s*([0-9A-Z]{10})', flags=re.IGNORECASE)
    if not supplier_pan:
        supplier_pan = find_pattern(r'BILL FROM.*?PAN\s*No\.?\s*:\s*([0-9A-Z]{10})', flags=re.DOTALL | re.IGNORECASE)
    if not supplier_pan:
        # Format 9: "PAN No:" at bottom
        supplier_pan = find_pattern(r'PAN\s+No\s*:\s*([0-9A-Z]{10})', flags=re.IGNORECASE)
    data["HeaderItem"]["SupplierPanNumber"] = supplier_pan

    # Supplier CIN - Format 5: "### CIN" pattern
    supplier_cin = find_pattern(r'###\s*CIN\s*\n([A-Z0-9]{21})', flags=re.IGNORECASE)
    if not supplier_cin:
        supplier_cin = find_pattern(r'CIN[\s\-:]+([A-Z0-9]{21})', flags=re.IGNORECASE)
    if not supplier_cin:
        supplier_cin = find_pattern(r'CIN\s*NO\.?\s*[:\-]?\s*([A-Z0-9]+)', flags=re.IGNORECASE)
    if not supplier_cin:
        # Format 9: "CIN No -" pattern
        supplier_cin = find_pattern(r'CIN\s+No\s*-\s*([A-Z0-9]{21})', flags=re.IGNORECASE)
    if not supplier_cin:
    # Format 10: "| CINNo | : value |" in header table
        supplier_cin = find_pattern(r'\|\s*CIN\s*No\.?\s*\|\s*:\s*([A-Z0-9]{21})\s*\|', flags=re.IGNORECASE)
    data["HeaderItem"]["SupplierCIN"] = supplier_cin

    # ===== CUSTOMER INFORMATION =====
    
    # Customer Name - multiple patterns
    # Format 5: "### Bill To" section
    customer_name = find_pattern(r'Details\s+of\s+Receiver\s+\(Billed\s+to\)\s*\n([^\n]+)', flags=re.IGNORECASE)
    if not customer_name:
        customer_name = find_pattern(r'Details\s+of\s+Receiver\s+\(Billed\s+to\)\s*\n[^\n]*\n([^\n]+?)(?:\n|$)', flags=re.IGNORECASE)
    if not customer_name:
        customer_name = find_pattern(r'###\s*Bill\s+To\s*\n([^\n]+)', flags=re.IGNORECASE)
    if not customer_name:
        # Format 4: "Name and Address of Recipient:" followed by name on next line
        customer_name = find_pattern(r'Name\s+and\s+Address\s+of\s+Recipient\s*:?\s*\n([^\n(]+)', flags=re.IGNORECASE)
    if not customer_name:
        # Format 3: "Customer Name: value" pattern
        customer_name = find_pattern(r'Customer\s+Name\s*:\s*([^\n]+)', flags=re.IGNORECASE)
    if not customer_name:
        customer_name = find_pattern(r'Name\s+and\s+Address\s+of\s+Recipient\s*:?\s*\|?\s*[^\n]*\n\|?\s*([^|,]+?)(?:,|\|)', flags=re.IGNORECASE)
    if not customer_name:
        customer_name = find_pattern(r'\|\s*BILL TO\s*\|[^\n]*\n\|[^|]*\|\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    if not customer_name:
        customer_name = find_pattern(r'Bill\s+To\s*:?\s*([^\n,]+?)(?:,|\n)', flags=re.IGNORECASE)
    if not customer_name:
    # Format 8: "Name & Address of Receiver (Billed To) :" in table
        customer_name = find_pattern(r'Name\s+&\s+Address\s+of\s+Receiver\s+\(Billed\s+To\)\s*:?\s*\|[^\n]*\n\|[^\n]*\|\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    if not customer_name:
        # Format 9: "**Bill To :**" inline pattern
        customer_name = find_pattern(r'\*\*Bill\s+To\s*:\*\*\s*([^\n]+)', flags=re.IGNORECASE)
    if not customer_name:
    # Format 10: "| Name of Purchaser | : value |" pattern
        customer_name = find_pattern(r'\|\s*Name\s+of\s+Purchaser\s*\|\s*:\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    data["HeaderItem"]["CustomerName"] = clean_value(customer_name)

    # Customer Address - Format 5: "Address" line after Bill To
    customer_addr = find_pattern(r'Details\s+of\s+Receiver.*?\n[^\n]+\n(.+?)(?=State\s+Name\s+&\s+code|GSTIN)', flags=re.DOTALL | re.IGNORECASE)
    if not customer_addr:
        customer_addr = find_pattern(r'Details\s+of\s+Receiver.*?\n[^\n]+\n([^\n]+\n[^\n]+?)(?=\n\|\s*GSTIN)', flags=re.DOTALL | re.IGNORECASE)
    if not customer_addr:
        customer_addr = find_pattern(r'###\s*Bill\s+To.*?Address\s*\n(.+?)(?=State\s+Code|GSTIN|PAN|$)', flags=re.DOTALL | re.IGNORECASE)
    if not customer_addr:
        # Format 4: extract lines after customer name until Mob/PAN
        customer_addr = find_pattern(r'Name\s+and\s+Address\s+of\s+Recipient\s*:?\s*\n[^\n]+\n(.+?)(?=Mob\.|PAN\.|GST|$)', flags=re.DOTALL | re.IGNORECASE)
    if not customer_addr:
        # Format 3: extract lines after customer name until GST No
        customer_addr = find_pattern(r'Customer\s+Name\s*:.*?\n(.+?)(?=GST\s*No|State\s*Code|\n\|)', flags=re.DOTALL | re.IGNORECASE)
    if not customer_addr:
        customer_addr = find_pattern(r'Name\s+and\s+Address\s+of\s+Recipient\s*:?\s*\|?\s*[^\n]*\n\|?\s*[^,]+?,\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    if not customer_addr:
        customer_addr = find_pattern(r'BILL TO.*?Address\s*:\s*([^|]+?)(?:GST IN|PAN|$)', flags=re.DOTALL | re.IGNORECASE)
    if not customer_addr:
    # Format 8: Extract address from table row after customer name
        customer_addr = find_pattern(r'Name\s+&\s+Address\s+of\s+Receiver.*?\n\|[^\n]*\|[^\n]*\n\|[^\n]*\|\s*([^|]+?)\s*\|[^\n]*State\s*:', flags=re.DOTALL | re.IGNORECASE)
    if not customer_addr:
        # Format 9: "**Address :**" inline pattern
        customer_addr = find_pattern(r'\*\*Address\s*:\*\*\s*([^\n]+)', flags=re.IGNORECASE)
    if not customer_addr:
    # Format 10: "| Billing Address | : value |" pattern
        customer_addr = find_pattern(r'\|\s*Billing\s+Address\s*\|\s*:\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    data["HeaderItem"]["CustomerAddress"] = clean_value(customer_addr)

    # Customer GSTIN - multiple patterns
    # Format 5: "GSTIN / PAN" pattern under Bill To
    customer_gstin = find_pattern(r'\|\s*GSTIN\s*/\s*Unique\s+ID\s*:\s*\|\s*([0-9A-Z]{15})\s*\|', flags=re.IGNORECASE)
    if not customer_gstin:
        customer_gstin = find_pattern(r'###\s*Bill\s+To.*?GSTIN\s*/\s*PAN\s*\n([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not customer_gstin:
        # Format 4: "GSTIN NO:" after customer section
        customer_gstin = find_pattern(r'Name\s+and\s+Address\s+of\s+Recipient.*?GSTIN?\s*NO\.?\s*:\s*([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not customer_gstin:
        # Format 3: "GST No: value" pattern
        customer_gstin = find_pattern(r'Customer.*?GST\s*No\.?\s*:\s*([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not customer_gstin:
        customer_gstin = find_pattern(r'Name\s+and\s+Address\s+of\s+Recipient.*?GSTN?\s*NO\.?\s*:\s*([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not customer_gstin:
        customer_gstin = find_pattern(r'BILL TO.*?GST\s*IN\s*:\s*([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not customer_gstin:
    # Format 8: "## GSTIN :" after customer table
        customer_gstin = find_pattern(r'##\s*GSTIN\s*:\s*([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not customer_gstin:
        # Format 9: "**GSTIN/UIN of Customer :**" pattern
        customer_gstin = find_pattern(r'\*\*GSTIN/UIN\s+of\s+Customer\s*:\*\*\s*([0-9A-Z]{15})', flags=re.IGNORECASE)
    if not customer_gstin:
        # Format 10: Second "| GSTIN/UJN | : value |" in customer section
        gstin_matches = re.findall(r'\|\s*GSTIN\s*/\s*UJN\s*\|\s*:\s*([0-9A-Z]{15})\s*\|', text, re.IGNORECASE)
        if len(gstin_matches) >= 2:
            customer_gstin = gstin_matches[1]  # Second occurrence is customer
    data["HeaderItem"]["CustomerGstin"] = customer_gstin

    # Customer PAN - Format 5: extract from "GSTIN / PAN" line
    customer_pan = find_pattern(r'###\s*Bill\s+To.*?GSTIN\s*/\s*PAN\s*\n[0-9A-Z]{15}\s*/\s*([0-9A-Z]{10})', flags=re.DOTALL | re.IGNORECASE)
    if not customer_pan:
        # Format 4: "PAN. NO:" pattern
        customer_pan = find_pattern(r'Name\s+and\s+Address\s+of\s+Recipient.*?PAN\.?\s*NO\.?\s*:\s*([0-9A-Z]{10})', flags=re.DOTALL | re.IGNORECASE)
    if not customer_pan:
        customer_pan = find_pattern(r'BILL TO.*?PAN\s*No\.?\s*:\s*([0-9A-Z]{10})', flags=re.DOTALL | re.IGNORECASE)
    if not customer_pan:
    # Format 8: "PAIN No. :" pattern
        customer_pan = find_pattern(r'PAIN\s+No\.\s*:\s*([0-9A-Z]{10})', flags=re.IGNORECASE)
    #if not customer_pan:
        # Format 9: "**Customer PAN :**" pattern
        #customer_pan = find_pattern(r'\*\*Customer\s+PAN\s*:\*\*\s*([0-9A-Z]{10})', flags=re.IGNORECASE)
    data["HeaderItem"]["CustomerPanNumber"] = customer_pan

    # ===== SHIP TO INFORMATION =====
    
    # Ship To Name - Format 5: "### Ship To" section
    ship_to_name = find_pattern(r'Details\s+of\s+Consignee\s+\(Shipped\s+to\)\s*\n[^\n]*\n([^\n]+?)(?:\n|$)', flags=re.IGNORECASE)
    if not ship_to_name:
        ship_to_name = find_pattern(r'###\s*Ship\s+To\s*\n([^\n]+)', flags=re.IGNORECASE)
    if not ship_to_name:
        # Format 4: "Name and Address of Shipped to:" pattern
        ship_to_name = find_pattern(r'Name\s+and\s+Address\s+of\s+Shipped\s+to\s*:?\s*\n([^\n(]+)', flags=re.IGNORECASE)
    if not ship_to_name:
        ship_to_name = find_pattern(r'Name\s+and\s+Address\s+of\s+Shipped\s+to\s*:?\s*\|?\s*[^\n]*\n\|?\s*([^|,]+?)(?:,|\|)', flags=re.IGNORECASE)
    if not ship_to_name:
        ship_to_name = find_pattern(r'\|\s*SHIP TO\s*\|[^\n]*\n\|[^|]*\|\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    if not ship_to_name:
    # Format 8: "Name & Address of Consignee (Shipped To) :" in table
        ship_to_name = find_pattern(r'Name\s+&\s+Address\s+of\s+Consignee\s+\(Shipped\s+To\)\s*:?\s*\|[^\n]*\n\|[^\n]*\|\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    if not ship_to_name:
    # Format 10: "| Name of Recipient | : value |" pattern
        ship_to_name = find_pattern(r'\|\s*Name\s+of\s+Recipient\s*\|\s*:\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    data["HeaderItem"]["ShipToName"] = clean_value(ship_to_name)

    # Ship To Address - Format 5: "Address" line after Ship To
    ship_to_addr = find_pattern(r'Details\s+of\s+Consignee.*?\n[^\n]+\n([^\n]+\n[^\n]+?)(?=\n\|\s*GSTIN|$)', flags=re.DOTALL | re.IGNORECASE)
    if not ship_to_addr:
        ship_to_addr = find_pattern(r'###\s*Ship\s+To.*?Address\s*\n(.+?)(?=State\s+Code|GSTIN|PAN|$)', flags=re.DOTALL | re.IGNORECASE)
    if not ship_to_addr:
        # Format 4: extract lines after ship to name until Mob/PAN
        ship_to_addr = find_pattern(r'Name\s+and\s+Address\s+of\s+Shipped\s+to\s*:?\s*\n[^\n]+\n(.+?)(?=Mob\.|PAN\.|\n\|)', flags=re.DOTALL | re.IGNORECASE)
    if not ship_to_addr:
        ship_to_addr = find_pattern(r'Name\s+and\s+Address\s+of\s+Shipped\s+to\s*:?\s*\|?\s*[^\n]*\n\|?\s*[^,]+?,\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    if not ship_to_addr:
        ship_to_addr = find_pattern(r'SHIP TO.*?Address\s*:\s*([^|]+?)(?:GST IN|PAN|$)', flags=re.DOTALL | re.IGNORECASE)
    if not ship_to_addr:
    # Format 8: Extract address from consignee table row
        ship_to_addr = find_pattern(r'Name\s+&\s+Address\s+of\s+Consignee.*?\n\|[^\n]*\|[^\n]*\n\|[^\n]*\|\s*([^|]+?)\s*\|[^\n]*State\s*:', flags=re.DOTALL | re.IGNORECASE)
    if not ship_to_addr:
    # Format 10: "| Ship to Address | : value |" pattern
        ship_to_addr = find_pattern(r'\|\s*Ship\s+to\s+Address\s*\|\s*:\s*([^|]+?)\s*\|', flags=re.IGNORECASE)
    data["HeaderItem"]["ShipToAddress"] = clean_value(ship_to_addr)

    # Ship To GSTIN - Format 5: "GSTIN / PAN" pattern under Ship To
    ship_to_gstin = find_pattern(r'###\s*Ship\s+To.*?GSTIN\s*/\s*PAN\s*\n([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not ship_to_gstin:
        ship_to_gstin = find_pattern(r'Name\s+and\s+Address\s+of\s+Shipped\s+to.*?GSTN?\s*NO\.?\s*:\s*([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not ship_to_gstin:
        ship_to_gstin = find_pattern(r'SHIP TO.*?GST\s*IN\s*:\s*([0-9A-Z]{15})', flags=re.DOTALL | re.IGNORECASE)
    if not ship_to_gstin:
        # Format 10: Third "| GSTIN/UJN | : value |" in ship-to section
        gstin_matches = re.findall(r'\|\s*GSTIN\s*/\s*UJN\s*\|\s*:\s*([0-9A-Z]{15})\s*\|', text, re.IGNORECASE)
        if len(gstin_matches) >= 3:
            ship_to_gstin = gstin_matches[2]  # Third occurrence is ship-to
    data["HeaderItem"]["ShipToGstin"] = ship_to_gstin

    # ===== INVOICE DETAILS =====
    
    # Invoice Number - Format 5: "Invoice No." line after "Tax is Payable on Reverse Charges"
    invoice_no = find_pattern(r'\|\s*Invoice\s+No\.?\s*:\s*\|\s*([A-Z0-9]+)', flags=re.IGNORECASE)
    if not invoice_no:
        invoice_no = find_pattern(r'4\.\s*Serial\s+No\.?\s+of\s+invoice\s*\n([A-Z0-9/\-]+)', flags=re.IGNORECASE)
    if not invoice_no:
        invoice_no = find_pattern(r'Invoice\s+No\.?\s*\n([A-Z0-9]+)', flags=re.IGNORECASE)
    if not invoice_no:
        invoice_no = find_pattern(r'Invoice\s+No\s*:\s*Date\s*:\s*\|?\s*[^\n]*\n\|?\s*([A-Z0-9]+)', flags=re.IGNORECASE)
    if not invoice_no:
        invoice_no = find_pattern(r'Invoice\s+No\.?\s*:\s*([A-Z0-9/\-]+)', flags=re.IGNORECASE)
    if not invoice_no:
        invoice_no = find_pattern(r'Invoice\s+No\.?\s*:?\s*Date\s*:?\s*\|?\s*[^\n]*\n\|?\s*([A-Z0-9]+)\s+', flags=re.IGNORECASE)
    if not invoice_no:
        invoice_no = find_pattern(r'INVOICE\s*No\.?\s*\|?\s*([A-Z0-9/\-]+)', flags=re.IGNORECASE)
    if not invoice_no:
    # Format 8: "Our F.I. No. :" pattern
        invoice_no = find_pattern(r'Our\s+F\.I\.\s+No\.\s*:\s*([A-Z0-9/\-]+)', flags=re.IGNORECASE)
    if not customer_pan:
        # Format 9: "**Customer PAN :**" pattern
        customer_pan = find_pattern(r'\*\*Customer\s+PAN\s*:\*\*\s*([0-9A-Z]{10})', flags=re.IGNORECASE)
    if not invoice_no:
    # Format 10: "| Invoice No | : value |" in header table
        invoice_no = find_pattern(r'\|\s*Invoice\s+No\.?\s*\|\s*:\s*([A-Z0-9]+)\s*\|', flags=re.IGNORECASE)
    data["HeaderItem"]["InvoiceNumber"] = invoice_no

    # Invoice Date - Format 5: "### Invoice Date" pattern
    invoice_date = find_pattern(r'\|\s*Invoice\s+Date\s*:\s*\|\s*([\d\-A-Za-z]+)', flags=re.IGNORECASE)
    if not invoice_date:
        invoice_date = find_pattern(r'5\.\s*Date\s+of\s+invoice\s*\n([\d\-/.]+)', flags=re.IGNORECASE)
    if not invoice_date:
        invoice_date = find_pattern(r'F0\s+NO\s+&\s+DATE:.*?(\d{1,2}/\d{4})', flags=re.IGNORECASE)
    if not invoice_date:
        invoice_date = find_pattern(r'###\s*Invoice\s+Date\s*\n([\d\-/.]+)', flags=re.IGNORECASE)
    if not invoice_date:
        invoice_date = find_pattern(r'Invoice\s+No\s*:\s*Date\s*:\s*\|?\s*[^\n]*\n\|?\s*[A-Z0-9]+\s+([\d\-/.]+)', flags=re.IGNORECASE)
    if not invoice_date:
        invoice_date = find_pattern(r'Invoice\s+Date\s*:\s*([\d\-/.]+)', flags=re.IGNORECASE)
    if not invoice_date:
        invoice_date = find_pattern(r'Invoice\s+No\.?\s*:?\s*Date\s*:?\s*\|?\s*[^\n]*\n\|?\s*[A-Z0-9]+\s+([\d\-/]+)', flags=re.IGNORECASE)
    if not invoice_date:
        invoice_date = find_pattern(r'Invoice\s*Date\s*\|?\s*:?\s*([\d\-/]+)', flags=re.IGNORECASE)
    if not invoice_date:
        invoice_date = find_pattern(r'Date\s+Of\s+Issue\s*:?\s*\|?\s*[^\n]*\n\|?\s*([\d\-/]+)', flags=re.IGNORECASE)
    if not invoice_date:
    # Format 8: "Date of Preparation:" pattern
        invoice_date = find_pattern(r'Date\s+of\s+Preparation\s*:\s*([\d/]+)', flags=re.IGNORECASE)
    if not invoice_date:
        # Format 9: "**Invoice Date :**" inline pattern
        invoice_date = find_pattern(r'\*\*Invoice\s+Date\s*:\*\*\s*([\d\-A-Za-z\s]+)', flags=re.IGNORECASE)
    if not invoice_date:
    # Format 10: "| Date | : value |" in header table
        invoice_date = find_pattern(r'\|\s*Date\s*\|\s*:\s*([\d\-/]+)\s*\|', flags=re.IGNORECASE)
    data["HeaderItem"]["InvoiceDate"] = invoice_date

    # Document Type
    doc_type = find_pattern(r'\|\s*(Tax\s*Invoice)\s*\|', flags=re.IGNORECASE)
    if not doc_type:
        doc_type = find_pattern(r'^#\s*(TAX\s*INVOICE|INVOICE|CREDIT\s*NOTE|DEBIT\s*NOTE)', flags=re.MULTILINE | re.IGNORECASE)
    if not doc_type:
        doc_type = find_pattern(r'(TAX\s*INVOICE|INVOICE|CREDIT\s*NOTE|DEBIT\s*NOTE)', flags=re.IGNORECASE)
    data["HeaderItem"]["DocType"] = doc_type.upper() if doc_type else ""

    # IRN/INN Number - Format 5: "IRN NO:" at top
    irn_no = find_pattern(r'IRN\s+NO\s*:\s*([a-f0-9A-F]{64})', flags=re.IGNORECASE)
    if not irn_no:
        irn_no = find_pattern(r'INN\s*:?\s*([a-f0-9A-F]{64})', flags=re.IGNORECASE)
    if not irn_no:
        irn_no = find_pattern(r'IRN\s*:?\s*([a-f0-9]{64})', flags=re.IGNORECASE)
    if not irn_no:
        irn_no = find_pattern(r'IRN\s*No\.?\s*:?\s*([a-f0-9]{64})', flags=re.IGNORECASE)
    if not irn_no:
        # Format 9: "**IRN :**" inline pattern (shorter IRN)
        irn_no = find_pattern(r'\*\*IRN\s*:\*\*\s*([a-f0-9A-F]{58,64})', flags=re.IGNORECASE)
    if not irn_no:
    # Format 10: "**IRN No**" bold field followed by ": value" on next line
        irn_no = find_pattern(r'\*\*IRN\s+No\*\*\s*\n\s*:\s*([a-f0-9A-F]{64})', flags=re.IGNORECASE)
    data["HeaderItem"]["IrnNo"] = irn_no

    # IRN/INN Date
    irn_date = find_pattern(r'INN\s*DT\.?\s*([\d\-/]+)', flags=re.IGNORECASE)
    if not irn_date:
        irn_date = find_pattern(r'IRN\s*DT\.?\s*([\d\-/]+)', flags=re.IGNORECASE)
    if not irn_date:
        irn_date = find_pattern(r'IRN.*?Date\s*:?\s*([\d\-/]+)', flags=re.IGNORECASE)
    data["HeaderItem"]["IrnDate"] = irn_date

    # E-way Bill Number
    eway_no = find_pattern(r'E-?WAY\s+BILL\s+NO\.?\s*:?\s*([A-Z0-9\-]+)', flags=re.IGNORECASE)
    if not eway_no:
        eway_no = find_pattern(r'E-?WAY\s+BILL\s+NO\.?\s*:?\s*\|?\s*[^\n]*\n\|?\s*([A-Z0-9\-]+)', flags=re.IGNORECASE)
    if not eway_no:
        eway_no = find_pattern(r'E-?way\s*Bill\s*No\.?\s*\|?\s*:?\s*(\d+)', flags=re.IGNORECASE)
    data["HeaderItem"]["EwayBillNo"] = eway_no

    # E-way Bill Date
    eway_date = find_pattern(r'E-?WAY\s+BILL\s+DATE\s*:?\s*([^\n]+?)(?:\n|$)', flags=re.IGNORECASE)
    if not eway_date:
        eway_date = find_pattern(r'E-?WAY\s+BILL\s+DATE\s*:?\s*\|?\s*[^\n]*\n\|?\s*([\d\-/\s:]+?)(?:\n|$)', flags=re.IGNORECASE)
    if not eway_date:
        eway_date = find_pattern(r'E-?way\s*Bill\s*Date\s*\|?\s*:?\s*([\d\-/\s:]+)', flags=re.IGNORECASE)
    data["HeaderItem"]["EwayBillDate"] = clean_value(eway_date)

    # PO Number - Format 5: "Client PO No & Date" pattern
    po_no = find_pattern(r'\|\s*P\.?O\.?\s*No\.?\s*\|\s*([A-Z0-9]+)', flags=re.IGNORECASE)
    if not po_no:
        po_no = find_pattern(r'Client\s+PO\s+No\s+&\s+Date\s*\n([A-Z0-9]+)', flags=re.IGNORECASE)
    if not po_no:
        po_no = find_pattern(r'Customer\s+Reference\s*:?\s*\|?\s*[^\n]*\n\|?\s*([A-Z0-9]+)', flags=re.IGNORECASE)
    if not po_no:
        po_no = find_pattern(r'P\.?O\.?\s*No\.?\s*[:|]?\s*([A-Z0-9/\-]+)', flags=re.IGNORECASE)
    if not po_no:
    # Format 8: "Your P.O. No. & Date:" pattern
        po_no = find_pattern(r'Your\s+P\.O\.\s+No\.\s+&\s+Date\s*:\s*([A-Z0-9]+)', flags=re.IGNORECASE)
    data["HeaderItem"]["PoNumber"] = po_no

    # PO Date - Format 5: part of "Client PO No & Date" line
    po_date = find_pattern(r'\|\s*P\.?O\.?\s*Date\s*\|\s*([\d\-/]+)', flags=re.IGNORECASE)
    if not po_date:
        po_date = find_pattern(r'Client\s+PO\s+No\s+&\s+Date\s*\n[A-Z0-9]+\s*-\s*([\d\-/.]+)', flags=re.IGNORECASE)
    if not po_date:
        po_date = find_pattern(r'Our\s+Reference\s+No.*?DATE\s*:?\s*\|?\s*[^\n]*\n\|?\s*([\d\-/]+)', flags=re.DOTALL | re.IGNORECASE)
    if not po_date:
        po_date = find_pattern(r'P\.?O\.?\s*Date\s*[:|]?\s*([\d\-/]+)', flags=re.IGNORECASE)
    if not po_date:
    # Format 8: Extract date from "Your P.O. No. & Date: 4100020925-2708/2022"
        po_date = find_pattern(r'Your\s+P\.O\.\s+No\.\s+&\s+Date\s*:.*?(\d{2,4}/\d{4})', flags=re.IGNORECASE)
    data["HeaderItem"]["PoDate"] = po_date

    # GRN details
    data["HeaderItem"]["GrnNo"] = find_pattern(r'GRN\s*No\.?\s*[:|]?\s*([A-Z0-9/\-]+)', flags=re.IGNORECASE)
    data["HeaderItem"]["GrnDate"] = find_pattern(r'GRN\s*Date\s*[:|]?\s*([\d\-/]+)', flags=re.IGNORECASE)

    # Place of Supply - Format 5: "Place of Supply" line
    
    place_of_supply = find_pattern(r'Place\s+of\s+Supply\s*\n([^\n]+)', flags=re.IGNORECASE)
    if not place_of_supply:
        # Format 9: "**Place Of Supply :**" inline pattern
        place_of_supply = find_pattern(r'\*\*Place\s+Of\s+Supply\s*:\*\*\s*([^\n]+)', flags=re.IGNORECASE)
    if place_of_supply:
        data["HeaderItem"]["PlaceOfSupply"] = clean_value(place_of_supply)
    elif data["HeaderItem"]["CustomerGstin"] and len(data["HeaderItem"]["CustomerGstin"]) >= 2:
        data["HeaderItem"]["PlaceOfSupply"] = data["HeaderItem"]["CustomerGstin"][:2]
    elif data["HeaderItem"]["ShipToGstin"] and len(data["HeaderItem"]["ShipToGstin"]) >= 2:
        data["HeaderItem"]["PlaceOfSupply"] = data["HeaderItem"]["ShipToGstin"][:2]

    # RCM Applicable - Format 5: "Tax is Payable on Reverse Charges"
    # Check if pattern exists (no capture group)
    rcm_match = re.search(r'Tax\s+is\s+Payable\s+on\s+Reverse\s+Charges', text, re.IGNORECASE)
    if rcm_match:
        data["HeaderItem"]["RCMApplicable"] = "YES"
    else:
        rcm = find_pattern(r'(?:Whether\s+tax\s+has\s+to\s+be\s+paid\s+under\s+)?re[vw]e[rs]se\s+Charges?\s+Basis\??\s*(Yes|No|Y|N)', flags=re.IGNORECASE)
        if not rcm:
            rcm = find_pattern(r'RCM\s*Applicable\s*[:|]?\s*(Yes|No|Y|N)', flags=re.IGNORECASE)
        data["HeaderItem"]["RCMApplicable"] = rcm.upper() if rcm else ""

        # ===== LINE ITEMS EXTRACTION =====

        # Format 9: Complex table with merged cells - Item description spans columns
    # Pattern: | S.No | Item (multi-column) | ... | Amount |
    format9_table = re.search(
        r'\*\*S\.No\.\s+Item\*\*.*?\*\*Amount\(INR\)\*\*\s*\n(.*?)(?=\n\s*\*\*Amount\s+in\s+words|---)',
        text, re.DOTALL | re.IGNORECASE
    )
    
    if format9_table:
        table_body = format9_table.group(1)
        # Extract data rows: | number | description with dates | qty | pax | rate | amount |
        format9_rows = re.finditer(
            r'\|\s*(\d+)\s*\|\s*(.+?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*\|\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|',
            table_body, re.IGNORECASE
        )
        
        for row in format9_rows:
            sr_no = row.group(1).strip()
            description = clean_value(row.group(2))
            start_date = row.group(3).strip()
            end_date = row.group(4).strip()
            qty = row.group(5).strip()
            pax = row.group(6).strip()
            unit_price = row.group(7).strip()
            amount = row.group(8).strip()
            
            # Combine description with period
            full_description = f"{description} (Period: {start_date} to {end_date})"
            
            line_item = {
                "IgstRate": "",
                "Description": full_description,
                "UnitOfMeasurement": "NOS",
                "IgstAmount": "",
                "CgstAmount": "",
                "TaxableValue": amount,
                "Quantity": qty,
                "TotalItemAmount": "",
                "CessAmount": "",
                "UnitPrice": unit_price,
                "CgstRate": "",
                "HsnCode": "",
                "SgstAmount": "",
                "CessRate": "",
                "SgstRate": ""
            }
            
            data["LineItems"].append(line_item)

    if not data["LineItems"]:

            # Format 8: Non-table format - numbered list with values on separate lines
        # Pattern: "1. Description\n HSN\n Qty\n Rate\n ..."
        format8_pattern = re.search(
            r'###\s*Sr\.\s*No\..*?\n(.*?)(?=###\s*Total|$)',
            text, re.DOTALL | re.IGNORECASE
        )
        
        if format8_pattern:
            items_section = format8_pattern.group(1)
            # Match numbered items: "1. DESCRIPTION\n HSN\n numbers..."
            format8_items = re.finditer(
                r'(\d+)\.\s+([^\n]+?)\s*\n\s*(\d{8})\s*\n\s*(\d+)\s*\n\s*([\d.]+)\s*\n\s*([\d,.]+)\s*\n\s*([\d.]+)\s*\n\s*([\d,.]+)',
                items_section, re.IGNORECASE
            )
            
            for item in format8_items:
                sr_no = item.group(1).strip()
                description = clean_value(item.group(2))
                hsn_code = item.group(3).strip()
                no_of_pkgs = item.group(4).strip()
                contents_per_pack = item.group(5).strip()
                quantity = item.group(6).strip()
                unit_price = item.group(7).strip()
                amount = item.group(8).strip().replace('.', '').replace(',', '.')
                
                line_item = {"IgstRate": "", "Description": description, "UnitOfMeasurement": "NOS", "IgstAmount": "", "CgstAmount": "", "TaxableValue": amount, "Quantity": quantity, "TotalItemAmount": "", "CessAmount": "", "UnitPrice": unit_price, "CgstRate": "", "HsnCode": hsn_code, "SgstAmount": "", "CessRate": "", "SgstRate": ""}
                
                data["LineItems"].append(line_item)

    if not data["LineItems"]:
        # Format 10: Table with | S.No. | Description | HSN/SAC | Qty (Nos) | Rate | Value | Disc. | Handling Charge | Taxable Value | IGST % | CGST % | SGST % | GST Amount |
        format10_table = re.search(
            r'\|\s*S\.No\.\s*\|\s*Description\s*\|\s*HSN/SAC.*?\|\s*GST\s+Amount\s*\|[^\n]*\n(.*?)(?=\n\s*Invoice\s+Amount\s+in\s+words|$)',
            text, re.DOTALL | re.IGNORECASE
        )
        
        if format10_table:
            table_body = format10_table.group(1)
            # Extract data rows: | num | desc | hsn | qty | rate | value | disc | handling | taxable | igst% | cgst% | sgst% | gst_amt |
            format10_rows = re.finditer(
                r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([\d,.]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d.]+)%\s*\|\s*([\d.]+)%\s*\|\s*([\d.]+)%\s*\|\s*([\d,.]+)\s*\|',
                table_body, re.IGNORECASE
            )
            
            for row in format10_rows:
                desc = clean_value(row.group(2))
                hsn = row.group(3).strip()
                qty = row.group(4).replace(',', '')
                rate = row.group(5).replace(',', '')
                value = row.group(6).replace(',', '')
                discount = row.group(7).replace(',', '')
                handling = row.group(8).replace(',', '')
                taxable = row.group(9).replace(',', '')
                igst_pct = row.group(10).strip()
                cgst_pct = row.group(11).strip()
                sgst_pct = row.group(12).strip()
                gst_amt = row.group(13).replace(',', '')
                
                # Calculate individual tax amounts
                igst_amt = ""
                cgst_amt = ""
                sgst_amt = ""
                
                try:
                    if float(igst_pct) > 0:
                        igst_amt = str(round(float(taxable) * float(igst_pct) / 100, 2))
                    if float(cgst_pct) > 0:
                        cgst_amt = str(round(float(taxable) * float(cgst_pct) / 100, 2))
                    if float(sgst_pct) > 0:
                        sgst_amt = str(round(float(taxable) * float(sgst_pct) / 100, 2))
                except (ValueError, ZeroDivisionError):
                    pass
                
                data["LineItems"].append({
                    "ItemDescription": desc,
                    "HsnCode": hsn,
                    "Quantity": qty,
                    "Unit": "Nos",
                    "Rate": rate,
                    "ItemAmount": value,
                    "DiscountAmount": discount,
                    "TaxableAmount": taxable,
                    "IgstRate": igst_pct,
                    "CgstRate": cgst_pct,
                    "SgstRate": sgst_pct,
                    "IgstAmount": igst_amt,
                    "CgstAmount": cgst_amt,
                    "SgstAmount": sgst_amt,
                    "TotalAmount": str(float(taxable) + float(gst_amt))
                })

    if not data["LineItems"]:

        # Format 7: Table with | number | Description | HSN | Units | Quantity | Rate | Total |
        format7_table = re.search(
            r'\|\s*Description\s+of\s+Goods\s*\|\s*HSN\s+Code\s*\|\s*Units\s*\|\s*Quantity\s*\|\s*Rate\s*\|\s*Total\s*\|[^\n]*\n(.*?)(?=\n\s*\|\s*TOTAL|\n\s*Certified|$)',
            text, re.DOTALL | re.IGNORECASE
        )

        if format7_table:
            table_body = format7_table.group(1)
            # Extract data rows: | number | description | hsn | units | qty | rate | total |
            format7_rows = re.finditer(
                r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d{6})?\s*\|\s*([A-Za-z]+)\s*\|\s*([\d.-]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|',
                table_body, re.IGNORECASE
            )
            
            for row in format7_rows:
                line_no = row.group(1).strip()
                description = clean_value(row.group(2))
                hsn_code = row.group(3).strip() if row.group(3) else ""
                uom = row.group(4).strip().upper()
                quantity = row.group(5).strip()
                unit_price = row.group(6).strip()
                total = row.group(7).strip()
                
                line_item = {"IgstRate": "", "Description": description, "UnitOfMeasurement": uom, "IgstAmount": "", "CgstAmount": "", "TaxableValue": total, "Quantity": quantity, "TotalItemAmount": "", "CessAmount": "", "UnitPrice": unit_price, "CgstRate": "", "HsnCode": hsn_code, "SgstAmount": "", "CessRate": "", "SgstRate": ""}
                
                data["LineItems"].append(line_item)

    if not data["LineItems"]:

        # Format 6: Table with Sr. No. | Description | HSN | COL | SIZE | Qty | Rate | Total (Taxable) | CGST | SGST | IGST
        # Note: This format has misaligned columns where data spans multiple pipe separators
        format6_table = re.search(
            r'\|\s*Sr\.\s*No\.\s*\|\s*Description.*?Goods\s*\|.*?HSN.*?\|.*?(?:COL|COLOR).*?\|.*?SIZE.*?\|.*?Qty.*?\|.*?Rate.*?\|.*?Total.*?\(Taxable\).*?\|.*?CGST.*?\|.*?SGST.*?\|.*?IGST.*?\|[^\n]*\n(.*?)(?=\n\s*freight\s+insurance|\n\s*Total\s+Invoice|$)',
            text, re.DOTALL | re.IGNORECASE
        )

        if format6_table:
            table_body = format6_table.group(1)
            # Extract data rows - flexible pattern to handle misaligned columns
            # Pattern: | number | text | 8-digit-HSN | ... numbers scattered across pipes
            format6_rows = re.finditer(
                r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d{8})\s*\|.*?\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d.]+)%\s*\|\s*([\d,.]+)\s*\|\s*([\d.]+)%\s*\|\s*([\d,.]+)',
                table_body, re.IGNORECASE
            )
            
            for row in format6_rows:
                sr_no = row.group(1).strip()
                description = clean_value(row.group(2))
                hsn_code = row.group(3).strip()
                quantity = row.group(4).strip()
                unit_price = row.group(5).strip()
                taxable_value = row.group(6).strip().replace(',', '')
                cgst_rate = row.group(7).strip()
                cgst_amount = row.group(8).strip().replace(',', '')
                sgst_rate = row.group(9).strip()
                sgst_amount = row.group(10).strip().replace(',', '')
                
                line_item = {"IgstRate": "", "Description": description, "UnitOfMeasurement": "NOS", "IgstAmount": "", "CgstAmount": cgst_amount, "TaxableValue": taxable_value, "Quantity": quantity, "TotalItemAmount": "", "CessAmount": "", "UnitPrice": unit_price, "CgstRate": cgst_rate, "HsnCode": hsn_code, "SgstAmount": sgst_amount, "CessRate": "", "SgstRate": sgst_rate}
                
                data["LineItems"].append(line_item)
    
    # Format 5: Complex table with Site | Description | HSNBAC CODE | Batch No | Qty | UOM | Rate | Total | Discount | Taxable Value | CGST | SGST | IGST
    if not data["LineItems"]:
        format5_table = re.search(
            r'\|\s*Site\s*\|\s*Description\s*\|.*?HSN.*?CODE.*?\|.*?(?:Batch|City).*?\|.*?(?:City|LOM).*?\|.*?LOM.*?\|.*?Rate.*?\|.*?Total.*?\|.*?Discount.*?\|.*?Taxable\s+Value.*?\|.*?CGST.*?\|.*?SGST.*?\|.*?IGST.*?\|[^\n]*\n(.*?)(?=\n\s*Remark|$)',
            text, re.DOTALL | re.IGNORECASE
        )
        
        if format5_table:
            table_body = format5_table.group(1)
            # Extract data rows - look for numeric site/line numbers
            format5_rows = re.finditer(
                r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d{4,8})\s*\|\s*([^|]*?)\s*\|\s*([\d.]+)\s*\|\s*([A-Z]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d,.]+)\s*\|',
                table_body, re.IGNORECASE
            )
            
            for row in format5_rows:
                site = row.group(1).strip()
                description = clean_value(row.group(2))
                hsn_code = row.group(3).strip()
                batch_no = clean_value(row.group(4))
                quantity = row.group(5).strip()
                uom = row.group(6).strip().upper()
                unit_price = row.group(7).strip().replace(',', '')
                total = row.group(8).strip().replace(',', '')
                discount = row.group(9).strip()
                taxable_value = row.group(10).strip().replace(',', '')
                
                # Skip rows with "Total:" or summary text
                if any(keyword in description.lower() for keyword in ['total', 'grand total', 'details of tax']):
                    continue
                
                line_item = {
                    "IgstRate": "",
                    "Description": description,
                    "UnitOfMeasurement": uom,
                    "IgstAmount": "",
                    "CgstAmount": "",
                    "TaxableValue": taxable_value,
                    "Quantity": quantity,
                    "TotalItemAmount": total,
                    "CessAmount": "",
                    "UnitPrice": unit_price,
                    "CgstRate": "",
                    "HsnCode": hsn_code,
                    "SgstAmount": "",
                    "CessRate": "",
                    "SgstRate": ""
                }
                
                data["LineItems"].append(line_item)
    
    # Try Format 1: Complex table with multiple columns (S.No | Description | HSN | ... | IGST | CGST | SGST | Total)
    if not data["LineItems"]:
        table_match = re.search(
            r'\|\s*S\.?No\.?.*?(?:HSN|SAC).*?(?:Quantity|Qty).*?(?:Price|Rate).*?(?:Total|Amount).*?\|.*?\n(.*?)(?=\n\s*---|\n\s*###|\n\s*\*\*|SubTotal|Total Amount|Narration|$)',
            text, re.DOTALL | re.IGNORECASE
        )
        
        if table_match:
            table_body = table_match.group(1)
            # Format 1: Full table with tax columns
            row_pattern = r'\|\s*(\d+)\s*\|([^|]+)\|([^|]+)\|([^|]*)\|([^|]*)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]*)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|'
            rows = re.finditer(row_pattern, table_body, re.MULTILINE)
            
            for row in rows:
                groups = row.groups()
                if len(groups) >= 10:
                    line_item = {
                        "IgstRate": "",
                        "Description": clean_value(groups[1]),
                        "UnitOfMeasurement": "",
                        "IgstAmount": "",
                        "CgstAmount": "",
                        "TaxableValue": "",
                        "Quantity": "",
                        "TotalItemAmount": "",
                        "CessAmount": "",
                        "UnitPrice": "",
                        "CgstRate": "",
                        "HsnCode": "",
                        "SgstAmount": "",
                        "CessRate": "",
                        "SgstRate": ""
                    }
                    
                    # Extract HSN
                    hsn_match = re.search(r'\d{4,8}', groups[2] if len(groups) > 2 else "")
                    if hsn_match:
                        line_item["HsnCode"] = hsn_match.group(0)
                    
                    # Extract quantity and UOM
                    if len(groups) > 5:
                        qty_text = groups[5].strip()
                        qty_match = re.search(r'([\d.]+)\s*([A-Z]+)', qty_text, re.IGNORECASE)
                        if qty_match:
                            line_item["Quantity"] = qty_match.group(1)
                            line_item["UnitOfMeasurement"] = qty_match.group(2).upper()
                        else:
                            line_item["Quantity"] = re.sub(r'[^0-9.]', '', qty_text)
                    
                    # Extract prices and amounts
                    if len(groups) > 6:
                        line_item["UnitPrice"] = re.sub(r'[^0-9.]', '', groups[6])
                    if len(groups) > 9:
                        line_item["TaxableValue"] = re.sub(r'[^0-9.]', '', groups[9])
                    if len(groups) > 10:
                        line_item["IgstAmount"] = re.sub(r'[^0-9.]', '', groups[10])
                    if len(groups) > 11:
                        line_item["CgstAmount"] = re.sub(r'[^0-9.]', '', groups[11])
                    if len(groups) > 12:
                        line_item["SgstAmount"] = re.sub(r'[^0-9.]', '', groups[12])
                    if len(groups) > 13:
                        line_item["TotalItemAmount"] = re.sub(r'[^0-9.]', '', groups[13])
                    
                    # Calculate tax rates
                    try:
                        if line_item["TaxableValue"] and float(line_item["TaxableValue"]) > 0:
                            taxable = float(line_item["TaxableValue"])
                            if line_item["IgstAmount"] and float(line_item["IgstAmount"]) > 0:
                                line_item["IgstRate"] = str(round((float(line_item["IgstAmount"]) / taxable) * 100, 2))
                            if line_item["CgstAmount"] and float(line_item["CgstAmount"]) > 0:
                                line_item["CgstRate"] = str(round((float(line_item["CgstAmount"]) / taxable) * 100, 2))
                            if line_item["SgstAmount"] and float(line_item["SgstAmount"]) > 0:
                                line_item["SgstRate"] = str(round((float(line_item["SgstAmount"]) / taxable) * 100, 2))
                    except (ValueError, ZeroDivisionError):
                        pass
                    
                    data["LineItems"].append(line_item)
    
    # Try Format 2 & 4: Table without "No. Of Packages" column (Description | UOM | Quantity | Rate | Amount)
    if not data["LineItems"]:
        # Format 4 specific: table starts with "Description of Goods"
        simple_table = re.search(
            r'\|\s*Description\s+of\s+Goods\s*\|.*?UOM.*?\|.*?Quantity.*?\|.*?Rate.*?\|.*?Amount.*?\|[^\n]*\n(.*?)(?=\n\s*\*\*|\n\s*Narration|$)',
            text, re.DOTALL | re.IGNORECASE
        )
        
        if not simple_table:
            simple_table = re.search(
                r'\|\s*No\.?\s*Of\s*Packages\s*\|.*?Description.*?\|.*?UOM.*?\|.*?Quantity.*?\|.*?Rate.*?\|.*?Amount.*?\|[^\n]*\n(.*?)(?=\n\s*---|\n\s*###|Narration|$)',
                text, re.DOTALL | re.IGNORECASE
            )
        
        if simple_table:
            table_body = simple_table.group(1)
            
            # Format 4 special handling: Description might span multiple rows, quantity/rate/amount on separate row
            # Look for rows with numeric data at the end
            data_rows = re.finditer(
                r'\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|',
                table_body, re.IGNORECASE
            )
            
            current_description = None
            current_uom = None
            
            for row in data_rows:
                col1 = clean_value(row.group(1))
                col2 = clean_value(row.group(2))
                quantity = row.group(3).strip()
                unit_price = row.group(4).strip()
                amount = row.group(5).strip()
                
                # Check if this is a description row (has text in first column)
                if col1 and not quantity:
                    current_description = col1
                    current_uom = col2 if col2 else None
                    continue
                
                # If we have quantity/rate/amount, create line item
                if quantity and unit_price and amount:
                    description = current_description if current_description else col1
                    uom = current_uom if current_uom else col2
                    
                    line_item = {
                        "IgstRate": "",
                        "Description": description,
                        "UnitOfMeasurement": uom.upper() if uom else "",
                        "IgstAmount": "",
                        "CgstAmount": "",
                        "TaxableValue": amount,
                        "Quantity": quantity,
                        "TotalItemAmount": "",
                        "CessAmount": "",
                        "UnitPrice": unit_price,
                        "CgstRate": "",
                        "HsnCode": "",
                        "SgstAmount": "",
                        "CessRate": "",
                        "SgstRate": ""
                    }
                    
                    data["LineItems"].append(line_item)
                    current_description = None
                    current_uom = None
    
    # Try Format 3: Simplified table (S.No | Description of Work | SAC | Amount)
    if not data["LineItems"]:
        format3_table = re.search(
            r'\|\s*S\.?No\.?\s*\|\s*Description\s+of\s+Work\s*\|\s*(?:SAC|HSN)\s*\|\s*Amount\s*\|[^\n]*\n(.*?)(?=\n\s*Sub\s*Total|\n\s*Amount\s+Chargeable|$)',
            text, re.DOTALL | re.IGNORECASE
        )
        
        if format3_table:
            table_body = format3_table.group(1)
            # Extract rows - can be with or without S.No column
            format3_rows = re.finditer(
                r'\|\s*(?:\d+\s*\|)?\s*([^|]+?)\s*\|\s*(?:\d*)\s*\|\s*(\d{4,8})\s*\|\s*([\d.]+)\s*\|',
                table_body, re.IGNORECASE
            )
            
            for row in format3_rows:
                description = clean_value(row.group(1))
                hsn_sac = row.group(2).strip()
                amount = row.group(3).strip()
                
                # Skip summary rows
                if any(keyword in description.lower() for keyword in ['cgst', 'sgst', 'igst', 'total', 'sub total', 'charges @']):
                    continue
                
                line_item = {
                    "IgstRate": "",
                    "Description": description,
                    "UnitOfMeasurement": "",
                    "IgstAmount": "",
                    "CgstAmount": "",
                    "TaxableValue": amount,
                    "Quantity": "",
                    "TotalItemAmount": "",
                    "CessAmount": "",
                    "UnitPrice": "",
                    "CgstRate": "",
                    "HsnCode": hsn_sac,
                    "SgstAmount": "",
                    "CessRate": "",
                    "SgstRate": ""
                }
                
                data["LineItems"].append(line_item)
    
    # Extract HSN Code from separate section if not in line items
    if data["LineItems"] and not data["LineItems"][0]["HsnCode"]:
        hsn_code = find_pattern(r'HSN\s+Code\s*:?\s*\|?\s*[^\n]*\n\|?\s*(\d{4,8})', flags=re.IGNORECASE)
        if not hsn_code:
            # Format 3: HSN in tax table
            hsn_code = find_pattern(r'\|\s*HSN\s*\|.*?\n\|[^\n]*\n\|\s*(\d+)', flags=re.IGNORECASE)
        if hsn_code:
            for item in data["LineItems"]:
                if not item["HsnCode"]:
                    item["HsnCode"] = hsn_code

    # Format 9: "SAC Code:" at bottom
    if data["LineItems"] and not data["LineItems"][0]["HsnCode"]:
        sac_code = find_pattern(r'SAC\s+Code\s*:\s*(\d{6})', flags=re.IGNORECASE)
        if sac_code:
            for item in data["LineItems"]:
                if not item["HsnCode"]:
                    item["HsnCode"] = sac_code

    # ===== TAX TOTALS EXTRACTION =====
    
    # Extract tax amounts from text patterns
    # Format 4: "Amount of GST RS ... in words" pattern for GST amount
    gst_amount_text = find_pattern(r'Amount\s+of\s+GST\s+RS\s+(.+?)\s+in\s+words', flags=re.IGNORECASE)
    
    # Extract tax amounts from tax summary section
    # Format 3: "CGST @ 9 %" format
    cgst_amount = find_pattern(r'CGST\s*@\s*[\d.]+\s*%\s*\|?\s*[^\n]*\n?[^\d]*\|?\s*([\d,.]+)', flags=re.IGNORECASE)
    if not cgst_amount:
        cgst_amount = find_pattern(r'CGST\s*\|\s*[\d.]+%\s*\|\s*([\d.]+)', flags=re.IGNORECASE)
    if not cgst_amount:
        cgst_amount = find_pattern(r'CGST.*?[\d.]+%.*?([\d,]+\.?\d*)', flags=re.IGNORECASE)
    if not cgst_amount:
    # Format 8: "COST Payable in words Rs. ..." pattern
        cgst_text = find_pattern(r'COST\s+Payable\s+in\s+words\s+Rs\.\s+(.+?)\s+only', flags=re.IGNORECASE)
        if cgst_text:
            # Try to extract numeric value from text
            cgst_numeric = re.search(r'([\d,]+\.?\d*)', cgst_text)
            if cgst_numeric:
                cgst_amount = cgst_numeric.group(1)
    if not cgst_amount:
        # Format 9: Extract from "**Taxable Value**" summary row
        # Pattern: | **Taxable Value** | taxable | cgst | sgst | total_tax | grand_total |
        format9_tax = re.search(r'\|\s*\*\*Taxable\s+Value\*\*\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|', text, re.IGNORECASE)
        if format9_tax:
            cgst_amount = format9_tax.group(2).strip()
            sgst_amount = format9_tax.group(3).strip()
    
    sgst_amount = find_pattern(r'SGST\s*@\s*[\d.]+\s*%\s*\|?\s*[^\n]*\n?[^\d]*\|?\s*([\d,.]+)', flags=re.IGNORECASE)
    if not sgst_amount:
        sgst_amount = find_pattern(r'SGST\s*\|\s*[\d.]+%\s*\|\s*([\d.]+)', flags=re.IGNORECASE)
    if not sgst_amount:
        sgst_amount = find_pattern(r'SGST.*?[\d.]+%.*?([\d,]+\.?\d*)', flags=re.IGNORECASE)
    if not sgst_amount:
    # Format 8: "SOST Payable in words Rs. ..." pattern (SOST = SGST typo)
        sgst_text = find_pattern(r'(?:SOST|SGST)\s+Payable\s+in\s+words\s+Rs\.\s+(.+?)\s+only', flags=re.IGNORECASE)
        if sgst_text:
            # Try to extract numeric value from text
            sgst_numeric = re.search(r'([\d,]+\.?\d*)', sgst_text)
            if sgst_numeric:
                sgst_amount = sgst_numeric.group(1)
    if not sgst_amount:
    # Format 10: "Total SGST" followed by value on next line
        sgst_amount = find_pattern(r'Total\s+SGST\s*\n\s*([\d,.]+)', flags=re.IGNORECASE)
    
    igst_amount = find_pattern(r'IGST\s*@\s*[\d.]+\s*%\s*\|?\s*[^\n]*\n?[^\d]*\|?\s*([\d,.]+)', flags=re.IGNORECASE)
    if not igst_amount:
        igst_amount = find_pattern(r'IGST\s*\|\s*[\d.]+%\s*\|\s*([\d.]+)', flags=re.IGNORECASE)
    if not igst_amount:
        igst_amount = find_pattern(r'IGST.*?[\d.]+%.*?([\d,]+\.?\d*)', flags=re.IGNORECASE)
    if not igst_amount:
    # Format 10: "Total IGST" followed by value on next line
        igst_amount = find_pattern(r'Total\s+IGST\s*\n\s*([\d,.]+)', flags=re.IGNORECASE)

    # Format 7: "GST 18% | 103507.82" pattern - split into CGST and SGST
    if not cgst_amount:
    # Format 10: "Total CGST" followed by value on next line
        cgst_amount = find_pattern(r'Total\s+CGST\s*\n\s*([\d,.]+)', flags=re.IGNORECASE)
    if not cgst_amount and not sgst_amount and not igst_amount:
        gst_match = re.search(r'\|\s*GST\s+([\d.]+)%\s*\|\s*([\d,.]+)', text, re.IGNORECASE)
        if gst_match:
            gst_rate = gst_match.group(1)
            tax_amount = gst_match.group(2).replace(',', '')
            try:
                half_tax = float(tax_amount) / 2
                cgst_amount = str(half_tax)
                sgst_amount = str(half_tax)
                cgst_rate = str(float(gst_rate) / 2)
                sgst_rate = str(float(gst_rate) / 2)
            except ValueError:
                pass
    
    # Extract tax rates
    cgst_rate = find_pattern(r'CGST\s*@\s*([\d.]+)\s*%', flags=re.IGNORECASE)
    if not cgst_rate:
        cgst_rate = find_pattern(r'CGST\s*\|\s*([\d.]+)%', flags=re.IGNORECASE)
    
    sgst_rate = find_pattern(r'SGST\s*@\s*([\d.]+)\s*%', flags=re.IGNORECASE)
    if not sgst_rate:
        sgst_rate = find_pattern(r'SGST\s*\|\s*([\d.]+)%', flags=re.IGNORECASE)
    
    igst_rate = find_pattern(r'IGST\s*@\s*([\d.]+)\s*%', flags=re.IGNORECASE)
    if not igst_rate:
        igst_rate = find_pattern(r'IGST\s*\|\s*([\d.]+)%', flags=re.IGNORECASE)
    
    # Extract Sub Total (Taxable Value)
    sub_total = find_pattern(r'Sub\s+Total\s*\|?\s*[^\d]*\|?\s*[^\d]*\|?\s*([\d,.]+)', flags=re.IGNORECASE)
    if not sub_total:
        sub_total = find_pattern(r'\|\s*\*?\*?Total\*?\*?\s*\|\s*\*?\*?([\d,.]+)\*?\*?\s*\|', flags=re.IGNORECASE)
    
    # Apply tax amounts and rates to line items if extracted from summary
    if data["LineItems"]:
        # For Format 3, distribute taxable value if we have sub total
        if sub_total and not data["LineItems"][0]["TaxableValue"]:
            sub_total_val = sub_total.replace(',', '')
            # If single line item, assign full taxable value
            if len(data["LineItems"]) == 1:
                data["LineItems"][0]["TaxableValue"] = sub_total_val
        
        if igst_amount and igst_amount != "0.00" and igst_amount != "0":
            data["LineItems"][0]["IgstAmount"] = igst_amount.replace(',', '')
            if igst_rate:
                data["LineItems"][0]["IgstRate"] = igst_rate
        
        if cgst_amount and cgst_amount != "0.00" and cgst_amount != "0":
            data["LineItems"][0]["CgstAmount"] = cgst_amount.replace(',', '')
            if cgst_rate:
                data["LineItems"][0]["CgstRate"] = cgst_rate
        
        if sgst_amount and sgst_amount != "0.00" and sgst_amount != "0":
            data["LineItems"][0]["SgstAmount"] = sgst_amount.replace(',', '')
            if sgst_rate:
                data["LineItems"][0]["SgstRate"] = sgst_rate

    # Extract Taxable Value and Total Value
    taxable_value = find_pattern(r'Taxable\s+Value\s*\|?\s*([\d,.]+)', flags=re.IGNORECASE)
    if not taxable_value and sub_total:
        taxable_value = sub_total
    
    # Format 5: "Grand Total value (in figures)" or word format
    total_value = find_pattern(r'\|\s*GRAND\s+TOTAL\s*\|\s*([\d,.]+)', flags=re.IGNORECASE)
    if not total_value:
        total_value = find_pattern(r'Total\s+Invoice\s+Value\s*:\s*\n[^\n]+\n([\d,.]+)', flags=re.IGNORECASE)
    if not total_value:
        total_value = find_pattern(r'Grand\s+Total\s+[Vv]alue.*?([\d,]+\.?\d*)', flags=re.IGNORECASE)
    if not total_value:
        # Format 4: "Total Value RS ... in Words:" pattern
        total_value = find_pattern(r'Total\s+Value\s+RS\s+(.+?)\s+in\s+Words', flags=re.IGNORECASE)
    if not total_value:
        # Format 3: "Total Value Including GST"
        total_value = find_pattern(r'Total\s+Value\s+Including\s+GST\s*\|?\s*[^\d]*\|?\s*[^\d]*\|?\s*([\d,.]+)', flags=re.IGNORECASE)
    if not total_value:
        total_value = find_pattern(r'Total\s+Value\s*\|\s*([\d,.]+)', flags=re.IGNORECASE)
    # Parse total value from words if needed
    if total_value and not re.match(r'^\d', total_value):
        # Extract numeric value if available in text
        total_numeric = find_pattern(r'Total\s+Value.*?([\d,]+\.?\d*)', flags=re.IGNORECASE)
        if total_numeric:
            total_value = total_numeric
    if not total_value:
    # Format 8: "Total Invoice Value in words Rs. ..." pattern
        total_text = find_pattern(r'Total\s+Invoice\s+Value\s+in\s+words\s+Rs\.\s+(.+?)\s+only', flags=re.IGNORECASE)
        if total_text:
            # Extract numeric value from text
            total_numeric = re.search(r'([\d,]+\.?\d*)', total_text)
            if total_numeric:
                total_value = total_numeric.group(1)
    if not total_value:
        # Format 9: Extract from "**Taxable Value**" summary row (last column)
        format9_total = re.search(r'\|\s*\*\*Taxable\s+Value\*\*\s*\|.*?\|\s*([\d.]+)\s*\|[^\|]*$', text, re.IGNORECASE | re.MULTILINE)
        if format9_total:
            total_value = format9_total.group(1).strip()
    if not total_value:
    # Format 10: "**Total Invoice Value**" followed by value on next line
        total_value = find_pattern(r'\*\*Total\s+Invoice\s+Value\*\*\s*\n\s*([\d,.]+)', flags=re.IGNORECASE)
    
    if taxable_value:
        taxable_value = taxable_value.replace(',', '')
        if data["LineItems"] and not data["LineItems"][0]["TaxableValue"]:
            data["LineItems"][0]["TaxableValue"] = taxable_value
    
    if total_value and data["LineItems"]:
        # Handle both field naming conventions
        if "TotalItemAmount" in data["LineItems"][0] and not data["LineItems"][0]["TotalItemAmount"]:
            data["LineItems"][0]["TotalItemAmount"] = total_value
        elif "TotalAmount" in data["LineItems"][0] and not data["LineItems"][0]["TotalAmount"]:
            data["LineItems"][0]["TotalAmount"] = total_value

    # ===== CALCULATE HEADER TOTALS =====
    
    
    if data["LineItems"]:
        # Handle both field naming conventions (TaxableValue vs TaxableAmount, etc.)
        total_taxable = sum(float(item.get("TaxableValue") or item.get("TaxableAmount") or 0) for item in data["LineItems"])
        total_igst = sum(float(item.get("IgstAmount", 0) or 0) for item in data["LineItems"])
        total_cgst = sum(float(item.get("CgstAmount", 0) or 0) for item in data["LineItems"])
        total_sgst = sum(float(item.get("SgstAmount", 0) or 0) for item in data["LineItems"])
        total_cess = sum(float(item.get("CessAmount", 0) or 0) for item in data["LineItems"])
        total_tax = total_igst + total_cgst + total_sgst + total_cess
        total_amount = total_taxable + total_tax
        
        data["HeaderItem"]["IgstAmount"] = str(total_igst) if total_igst > 0 else ""
        data["HeaderItem"]["CgstAmount"] = str(total_cgst) if total_cgst > 0 else ""
        data["HeaderItem"]["SgstAmount"] = str(total_sgst) if total_sgst > 0 else ""
        data["HeaderItem"]["TotalCess"] = str(total_cess) if total_cess > 0 else ""
        data["HeaderItem"]["TotalTax"] = str(total_tax) if total_tax > 0 else ""
        data["HeaderItem"]["TotalAmount"] = str(total_amount) if total_amount > 0 else ""
        data["HeaderItem"]["TotalInvoiceAmount"] = str(total_amount) if total_amount > 0 else ""


    # Fallback: Extract totals from text if not calculated
    if not data["HeaderItem"]["TotalAmount"] or data["HeaderItem"]["TotalAmount"] == "0":
        total_match = find_pattern(r'Grand\s+Total.*?([\d,]+\.?\d*)', flags=re.IGNORECASE)
        if not total_match:
            total_match = find_pattern(r'Total\s+Value\s+RS.*?([\d,]+\.?\d*)', flags=re.IGNORECASE)
        if not total_match:
            total_match = find_pattern(r'Total\s+Value\s+Including\s+GST\s*\|?\s*[^\d]*\|?\s*[^\d]*\|?\s*([\d,.]+)', flags=re.IGNORECASE)
        if not total_match:
            total_match = find_pattern(r'Total\s+Value\s*\|?\s*([\d,]+\.?\d*)', flags=re.IGNORECASE)
        if total_match:
            data["HeaderItem"]["TotalAmount"] = total_match.replace(',', '')
            data["HeaderItem"]["TotalInvoiceAmount"] = total_match.replace(',', '')
    
    if not data["HeaderItem"]["IgstAmount"]:
        data["HeaderItem"]["IgstAmount"] = igst_amount.replace(',', '') if igst_amount and igst_amount not in ["0.00", "0"] else ""
    if not data["HeaderItem"]["CgstAmount"]:
        data["HeaderItem"]["CgstAmount"] = cgst_amount.replace(',', '') if cgst_amount and cgst_amount not in ["0.00", "0"] else ""
    if not data["HeaderItem"]["SgstAmount"]:
        data["HeaderItem"]["SgstAmount"] = sgst_amount.replace(',', '') if sgst_amount and sgst_amount not in ["0.00", "0"] else ""
    
    # Extract total tax amount separately if present
    if not data["HeaderItem"]["TotalTax"]:
        tax_amount = find_pattern(r'Tax\s+Amount\s*:\s*([\d,.]+)', flags=re.IGNORECASE)
        if not tax_amount:
            # Format 4: extract from "Amount of GST RS ... in words"
            tax_amount = find_pattern(r'Amount\s+of\s+GST\s+RS.*?([\d,]+\.?\d*)', flags=re.IGNORECASE)
        if tax_amount:
            data["HeaderItem"]["TotalTax"] = tax_amount.replace(',', '')

    return data


def main():
    """Main function to handle file input and output"""
    if len(sys.argv) < 2:
        print("Usage: python c.py <input_txt_file> [output_json_file]")
        print("Example: python c.py txt_files/5108975.txt output.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    
    # Read the text file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Extract data
    extracted_data = extract_invoice_data(text_content)
    
    # Output JSON
    json_output = json.dumps(extracted_data, indent=2, ensure_ascii=False)
    
    if output_file:
        # Save to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"Data extracted and saved to '{output_file}'")
        except Exception as e:
            print(f"Error writing file: {e}")
            sys.exit(1)
    else:
        # Print to console
        print(json_output)


if __name__ == "__main__":
    main()