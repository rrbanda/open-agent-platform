"""Extract Document Data Tool - Neo4j Powered"""

import json
import re
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection


class DocumentExtractionRequest(BaseModel):
    """Schema for document extraction requests"""
    document_content: str = Field(description="Text content of the document")
    document_type: str = Field(description="Type: paystub, w2, bank_statement, employment_verification")
    borrower_name: Optional[str] = Field(description="Expected borrower name", default=None)


@tool
def extract_document_data(document_info: str) -> str:
    """Extract structured data from mortgage documents using Neo4j business rules.
    
    Args:
        document_info: Document details like "Type: paystub, Content: John Smith, TechCorp, Pay Period: 01/01-01/15, Gross: 4500, Net: 3200, YTD Gross: 18000"
    """
    
    try:
        # Parse document info string
        import re
        info = document_info.lower()
        
        # Extract document type
        type_match = re.search(r'type:\s*([a-z_]+)', info)
        document_type = type_match.group(1) if type_match else "paystub"
        
        # Extract borrower name
        name_match = re.search(r'(?:content:|borrower:)\s*([a-z]+\s+[a-z]+)', info)
        borrower_name = name_match.group(1).title() if name_match else "John Smith"
        
        # Extract document content (simplified)
        content_match = re.search(r'content:\s*(.+)', info)
        document_content = content_match.group(1) if content_match else info
        
        # Get rules from Neo4j
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            query = """
            MATCH (dvr:DocumentVerificationRule)
            WHERE toLower(dvr.document_type) CONTAINS toLower($doc_type)
            RETURN dvr.required_fields as required_fields, dvr.red_flags as red_flags
            LIMIT 5
            """
            result = session.run(query, doc_type=document_type)
            rules = [dict(record) for record in result]
        
        # Extract data based on document type
        if document_type.lower() == "paystub":
            fields = _extract_paystub(document_content)
        elif document_type.lower() == "w2":
            fields = _extract_w2(document_content)
        elif document_type.lower() == "bank_statement":
            fields = _extract_bank_statement(document_content)
        else:
            fields = {"document_type": document_type}
        
        # Validate
        issues = []
        if not fields.get("full_name"):
            issues.append("No name found in document")
        
        if borrower_name and fields.get("full_name"):
            name_match = _name_similarity(fields["full_name"], borrower_name)
            if name_match < 0.7:
                issues.append(f"Name mismatch: expected {borrower_name}")
        
        result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "fields": fields,
            "document_info": {
                "type": document_type,
                "timestamp": datetime.now().isoformat(),
                "rules_checked": len(rules)
            },
            "success": True
        }
        
        return json.dumps(result, ensure_ascii=False, default=str)
        
    except Exception as e:
        return json.dumps({
            "valid": False,
            "issues": [f"Extraction failed: {str(e)}"],
            "fields": {},
            "document_info": {"type": document_type, "error": str(e)},
            "success": False
        })


def _extract_paystub(content: str) -> Dict:
    """Extract comprehensive paystub data including UNC format"""
    fields = {"document_type": "paystub"}
    
    try:
        # Employee Information
        # Employee Name - multiple patterns
        name_patterns = [
            r"Employee Name\s+([A-Za-z\s,]+)",
            r"(?:Employee|Name):\s*([A-Za-z\s,]+)",
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, content, re.IGNORECASE)
            if name_match:
                fields["full_name"] = name_match.group(1).strip()
                fields["employee_name"] = fields["full_name"]
                break
        
        # Employee ID
        id_match = re.search(r"Employee ID:\s*(\d+)", content, re.IGNORECASE)
        if id_match:
            fields["employee_id"] = id_match.group(1)
        
        # Employee Address
        address_patterns = [
            r"(\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane))",
            r"([A-Z\s]+,\s*[A-Z]{2}\s+\d{5})"  # City, State ZIP
        ]
        for pattern in address_patterns:
            addr_match = re.search(pattern, content, re.IGNORECASE)
            if addr_match:
                if "employee_address" not in fields:
                    fields["employee_address"] = addr_match.group(1).strip()
                else:
                    fields["employee_address"] += ", " + addr_match.group(1).strip()
        
        # Job Title - improved pattern to exclude "Pay Rate"
        title_match = re.search(r"Job Title\s+([A-Za-z\s&.,]+?)(?:\s+Pay Rate|$)", content, re.IGNORECASE)
        if title_match:
            fields["job_title"] = title_match.group(1).strip()
        
        # Employer Information - University patterns
        if 'University of North Carolina at Chapel Hill' in content:
            fields["employer_name"] = 'The University of North Carolina at Chapel Hill'
        elif 'University of' in content:
            employer_match = re.search(r"(University of [A-Za-z\s]+)", content, re.IGNORECASE)
            if employer_match:
                fields["employer_name"] = employer_match.group(1).strip()
        
        # Department - improved pattern to exclude extra text
        dept_match = re.search(r"Department\s+([A-Z0-9\-\s]+?)(?:\s+Allowances|$)", content, re.IGNORECASE)
        if dept_match:
            fields["department"] = dept_match.group(1).strip()
        
        # Pay Rate - Annual Salary
        rate_patterns = [
            r"Pay Rate:\s*\$([0-9,]+\.?[0-9]*)\s*Annual",
            r"\$([0-9,]+\.00)\s*Annual"
        ]
        
        for pattern in rate_patterns:
            rate_match = re.search(pattern, content, re.IGNORECASE)
            if rate_match:
                try:
                    salary_str = rate_match.group(1).replace(',', '')
                    fields["annual_salary"] = float(salary_str)
                except ValueError:
                    fields["annual_salary"] = rate_match.group(1)
                break
        
        # Pay Period dates
        begin_match = re.search(r"Pay Begin Date:\s*(\d{2}/\d{2}/\d{4})", content)
        if begin_match:
            fields["pay_begin_date"] = begin_match.group(1)
            
        end_match = re.search(r"Pay End Date\s*(\d{2}/\d{2}/\d{4})", content)
        if end_match:
            fields["pay_end_date"] = end_match.group(1)
        
        # Current Period Earnings from TOTAL line
        total_match = re.search(r"TOTAL:\s*([0-9.]+)\s*([0-9,]+\.[0-9]+)", content)
        if total_match:
            fields["current_hours"] = float(total_match.group(1))
            try:
                fields["current_gross_pay"] = float(total_match.group(2).replace(',', ''))
            except ValueError:
                fields["current_gross_pay"] = total_match.group(2)
        
        # Year-to-Date Earnings - look for the pattern before Federal taxes
        ytd_match = re.search(r"([0-9]+\.00)\s+([0-9,]+\.[0-9]+)\s*\|\s*Fed Withholdng", content)
        if ytd_match:
            fields["ytd_hours"] = float(ytd_match.group(1))
            try:
                fields["ytd_gross_pay"] = float(ytd_match.group(2).replace(',', ''))
            except ValueError:
                fields["ytd_gross_pay"] = ytd_match.group(2)
        
        # Tax Withholdings - comprehensive patterns
        tax_patterns = {
            "federal_withholding_current": r"Fed Withholdng\s+([0-9.]+)",
            "federal_withholding_ytd": r"Fed Withholdng\s+[0-9.]+\s+([0-9,]+\.[0-9]+)",
            "fica_medicare_current": r"Fed MED/EE\s+([0-9.]+)",
            "fica_medicare_ytd": r"Fed MED/EE\s+[0-9.]+\s+([0-9,]+\.[0-9]+)",
            "fica_oasdi_current": r"Fed OASDUEE\s+([0-9.]+)",
            "fica_oasdi_ytd": r"Fed OASDUEE\s+[0-9.]+\s+([0-9,]+\.[0-9]+)",
            "state_withholding_current": r"NC Withholdng\s+([0-9.]+)",
            "state_withholding_ytd": r"NC Withholdng\s+[0-9.]+\s+([0-9,]+\.[0-9]+)"
        }
        
        for field_name, pattern in tax_patterns.items():
            tax_match = re.search(pattern, content)
            if tax_match:
                try:
                    fields[field_name] = float(tax_match.group(1).replace(',', ''))
                except ValueError:
                    fields[field_name] = tax_match.group(1)
        
        # Retirement Contributions
        retirement_patterns = {
            "retirement_current": r"TSERS - Retirement\s+([0-9.]+)",
            "retirement_ytd": r"TSERS - Retirement\s+[0-9.]+\s+([0-9,]+\.[0-9]+)"
        }
        
        for field_name, pattern in retirement_patterns.items():
            ret_match = re.search(pattern, content)
            if ret_match:
                try:
                    fields[field_name] = float(ret_match.group(1).replace(',', ''))
                except ValueError:
                    fields[field_name] = ret_match.group(1)
        
        # Health Insurance
        health_patterns = {
            "health_insurance_current": r"State Health Plan.*?([0-9.]+)",
            "health_insurance_ytd": r"State Health Plan.*?[0-9.]+\s+([0-9,]+\.[0-9]+)"
        }
        
        for field_name, pattern in health_patterns.items():
            health_match = re.search(pattern, content)
            if health_match:
                try:
                    fields[field_name] = float(health_match.group(1).replace(',', ''))
                except ValueError:
                    fields[field_name] = health_match.group(1)
        
        # Net Pay (if available)
        net_patterns = [
            r"Net Pay.*?\$?([0-9,]+\.?[0-9]*)",
            r"Take Home.*?\$?([0-9,]+\.?[0-9]*)"
        ]
        
        for pattern in net_patterns:
            net_match = re.search(pattern, content, re.IGNORECASE)
            if net_match:
                try:
                    fields["net_pay"] = float(net_match.group(1).replace(',', '').replace('$', ''))
                except ValueError:
                    fields["net_pay"] = net_match.group(1)
                break
        
        return fields
        
    except Exception as e:
        # Fallback to basic extraction if enhanced parsing fails
        fields = {"document_type": "paystub", "extraction_error": str(e)}
        
        # Basic name extraction
        name_match = re.search(r"(?:Employee|Name):\s*([A-Za-z\s,]+)", content, re.IGNORECASE)
        if name_match:
            fields["full_name"] = name_match.group(1).strip()
        
        # Basic gross pay extraction
        gross_match = re.search(r"(?:Gross Pay|Gross):\s*\$?([0-9,]+\.?[0-9]*)", content, re.IGNORECASE)
        if gross_match:
            try:
                fields["gross_pay"] = float(gross_match.group(1).replace(',', '').replace('$', ''))
            except ValueError:
                fields["gross_pay"] = gross_match.group(1)
        
        return fields


def _extract_w2(content: str) -> Dict:
    """Extract W2 data"""
    fields = {"document_type": "w2"}
    
    name_match = re.search(r"(?:Employee|Name):\s*([A-Za-z\s,]+)", content, re.IGNORECASE)
    if name_match:
        fields["full_name"] = name_match.group(1).strip()
    
    wages_match = re.search(r"(?:Wages|Box 1):\s*\$?([0-9,]+\.?[0-9]*)", content, re.IGNORECASE)
    if wages_match:
        try:
            fields["wages"] = float(wages_match.group(1).replace(',', '').replace('$', ''))
        except ValueError:
            fields["wages"] = wages_match.group(1)
    
    return fields


def _extract_bank_statement(content: str) -> Dict:
    """Extract bank statement data"""
    fields = {"document_type": "bank_statement"}
    
    holder_match = re.search(r"(?:Account Holder|Name):\s*([A-Za-z\s,&]+)", content, re.IGNORECASE)
    if holder_match:
        fields["full_name"] = holder_match.group(1).strip()
        fields["account_holder"] = fields["full_name"]
    
    balance_match = re.search(r"(?:Ending Balance|Balance):\s*\$?([0-9,]+\.?[0-9]*)", content, re.IGNORECASE)
    if balance_match:
        try:
            fields["ending_balance"] = float(balance_match.group(1).replace(',', '').replace('$', ''))
        except ValueError:
            fields["ending_balance"] = balance_match.group(1)
    
    return fields


def _name_similarity(name1: str, name2: str) -> float:
    """Calculate name similarity"""
    if not name1 or not name2:
        return 0.0
    
    words1 = set(name1.lower().split())
    words2 = set(name2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0