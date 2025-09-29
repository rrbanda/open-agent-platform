# Sample Mortgage Documents

This folder contains realistic sample documents for demonstrating the mortgage document processing system.

## Documents Included

### Sarah Johnson's Financial Documents

**Employment Documentation:**
- `w2_2023_sarah_johnson.txt` - 2023 W-2 form showing $102,000 annual salary at TechCorp Austin
- `paystub_nov_2024_sarah_johnson.txt` - Recent paystub showing current earnings and deductions

**Financial Documentation:** 
- `bank_statement_nov_2024_sarah_johnson.txt` - Bank statement showing $74,755 balance and income deposits

## Document Details

### Sarah Johnson Profile
- **Name:** Sarah Johnson
- **SSN:** 123-45-6789  
- **Address:** 2100 Guadalupe St, Austin, TX 78705
- **Employment:** Senior Software Engineer at TechCorp Austin
- **Annual Salary:** $102,000
- **Monthly Gross:** $8,500 (matches demo profile)
- **Bank Balance:** $74,755
- **Down Payment Available:** $67,500 (15% of $450,000)

## Usage in Demo

These documents are used by the E2E demo script (`app/tests/run_e2e_auto.py`) to demonstrate:

1. **Document Upload Processing** - Files are read and processed by the document agent
2. **Content Extraction** - Key financial information is extracted automatically  
3. **Business Rule Validation** - Documents are validated against Neo4j mortgage rules
4. **Workflow Integration** - Processed documents feed into the mortgage workflow

## Technical Notes

- Documents contain realistic data that matches the demo customer profile
- All sensitive information uses placeholder values (SSN, account numbers)
- Content is formatted as extracted text (OCR simulation)
- Documents are designed to pass standard mortgage verification rules
