# """Temporary entry point — read Excel and print row count."""

# from pathlib import Path

# from data.excel_reader import read_excel

# EXCEL_FILE = Path(__file__).parent / "data" / "companies.xlsx"

# df = read_excel(EXCEL_FILE)
# print(f"Rows Loaded: {len(df)}")

##########################################################
# This is the tesrt code for validator.py for checking website url
# from pathlib import Path

# from data.excel_reader import read_excel
# from validation.validator import is_valid_url

# # Path to Excel file
# EXCEL_FILE = Path(__file__).parent / "data" / "companies.xlsx"

# # Read Excel
# df = read_excel(EXCEL_FILE)

# print("=" * 60)
# print("Excel Loaded Successfully")
# print("=" * 60)

# # Print all column names
# print("\nColumns in Excel:")
# print(df.columns.tolist())

# print("\nChecking Website URLs...\n")

# # Change this column name if necessary
# WEBSITE_COLUMN = "website"

# if WEBSITE_COLUMN not in df.columns:
#     print(f"Column '{WEBSITE_COLUMN}' not found!")
#     print("Available columns are:")
#     print(df.columns.tolist())
# else:
#     for index, row in df.iterrows():
#         website = str(row[WEBSITE_COLUMN])

#         print(f"Row {index+1}")
#         print(f"Website : {website}")
#         print(f"Valid   : {is_valid_url(website)}")
#         print("-" * 40)
##########################################################
# This is the tesrt code for email_validator.py for checking email
# from pathlib import Path

# from data.excel_reader import read_excel
# from validation.email_validator import is_valid_email

# EXCEL_FILE = Path(__file__).parent / "data" / "companies.xlsx"

# df = read_excel(EXCEL_FILE)

# print("=" * 60)
# print("Checking Email Addresses")
# print("=" * 60)

# EMAIL_COLUMN = "e-mail"

# for index, row in df.iterrows():
#     email = str(row[EMAIL_COLUMN])

#     print(f"Row {index+1}")
#     print(f"Email : {email}")
#     print(f"Valid : {is_valid_email(email)}")
#     print("-" * 40)
##########################################################
#testing for scrapping
# from pathlib import Path

# from data.excel_reader import read_excel
# from scraper.scraper import fetch_html

# EXCEL_FILE = Path(__file__).parent / "data" / "companies.xlsx"

# df = read_excel(EXCEL_FILE)

# website = df.loc[0, "website"]

# print("Company:", df.loc[0, "full_name"])
# print("Website:", website)

# html = fetch_html(website)

# print("\nWebsite Scraped Successfully")
# print("HTML Length:", len(html))
# print("\nFirst 500 Characters:\n")
# print(html[:500])


#### test for parsing
# from pathlib import Path

# from data.excel_reader import read_excel
# from scraper.scraper import fetch_html
# from scraper.parser import parse_html

# # Read Excel
# EXCEL_FILE = Path(__file__).parent / "data" / "companies.xlsx"
# df = read_excel(EXCEL_FILE)

# # Get first company's website
# website = df.loc[0, "website"]
# company = df.loc[0, "full_name"]

# print("=" * 60)
# print("Company:", company)
# print("Website:", website)
# print("=" * 60)

# # Step 1: Scrape website
# html = fetch_html(website)

# print("\n✅ Website Scraped Successfully")
# print("HTML Length:", len(html))

# # Step 2: Parse HTML
# page = parse_html(html, base_url=website)

# print("\n" + "=" * 60)
# print("PARSER RESULTS")
# print("=" * 60)

# print("\nTITLE")
# print(page.title)

# print("\nPARAGRAPHS FOUND")
# print(len(page.paragraphs))

# print("\nFIRST 3 PARAGRAPHS")

# for paragraph in page.paragraphs[:3]:
#     print("-")
#     print(paragraph)

# print("\nPRODUCT LINKS FOUND")

# for link in page.product_page_urls:
#     print(link)

# print("\nCLEAN TEXT LENGTH")
# print(len(page.clean_text))

############### test pipeline 
# from pathlib import Path
# import sys
# from pprint import pprint

# from data.excel_reader import read_excel
# from validation.email_validator import is_valid_email
# from validation.validator import is_valid_url

# from scraper.scraper import fetch_html
# from scraper.parser import parse_html

# from enrichment.llm_client import analyze_company
# from enrichment.comparator import compare_excel_vs_llm
# from enrichment.llm_judge import judge_enrichment
# from enrichment.scoring import calculate_confidence_score

# from reports.report_generator import generate_validation_report


# EXCEL_FILE = Path(__file__).parent / "data" / "companies.xlsx"


# def process_company(company, index, total):
#     """
#     Process a single company and return the record.
#     """
    
#     company_name = str(company.get("full_name", "")).strip()
#     website = str(company.get("website", "")).strip()
#     email = str(company.get("e-mail", "")).strip()
    
#     print(f"\n[{index + 1}/{total}] Processing: {company_name}")
#     print("-" * 40)
    
#     # STEP 2 - Website Validation
#     website_valid = is_valid_url(website)
#     print(f"  Website Valid: {website_valid}")
    
#     # STEP 3 - Email Validation
#     email_valid = is_valid_email(email)
#     print(f"  Email Valid: {email_valid}")
    
#     # STEP 4 - Scrape Website
#     html = fetch_html(website)
#     print(f"  Downloaded HTML: {len(html)} chars")
    
#     # STEP 5 - Parse HTML
#     page = parse_html(html, base_url=website)
#     print(f"  Title: {page.title[:50] if page.title else 'N/A'}")
#     print(f"  Clean Text: {len(page.clean_text)} chars")
    
#     # STEP 6 - LLM Enrichment
#     llm_output = analyze_company(
#         company_name=company_name,
#         website=website,
#         website_text=page.clean_text,
#     )
#     print("  LLM Enrichment: Completed")
    
#     # STEP 7 - Comparator
#     comparison = compare_excel_vs_llm(
#         excel_row=company,
#         llm_output=llm_output,
#     )
#     print("  Comparator: Completed")
    
#     # STEP 8 - LLM Judge
#     judge = judge_enrichment(
#         website_text=page.clean_text,
#         llm_output=llm_output,
#         excel_data=company.to_dict(),
#     )
#     print("  LLM Judge: Completed")
    
#     # STEP 9 - Confidence Score
#     confidence = calculate_confidence_score(
#         comparison=comparison,
#         llm_output=llm_output,
#         judge_result=judge,
#         website_valid=website_valid,
#         email_valid=email_valid,
#         clean_text_length=len(page.clean_text),
#     )
#     print("  Confidence Score: Completed")
    
#     # Create record for this company
#     record = {
#         # Original Excel Row
#         "excel_data": company.to_dict(),
        
#         # Basic Info
#         "company_name": company_name,
#         "website": website,
#         "email": email,
        
#         # Validation
#         "status": "success" if website_valid else "failed",
#         "error_message": "",
#         "website_valid": website_valid,
#         "email_valid": email_valid,
#         "clean_text_length": len(page.clean_text),
        
#         # AI Outputs
#         "llm_output": llm_output,
#         "comparison": comparison,
#         "judge": judge,
#         "confidence": confidence,
#     }
    
#     return record


# def main():
    
#     print("=" * 70)
#     print("MUNAFAH AI PRODUCT ENRICHMENT PIPELINE")
#     print("=" * 70)
    
#     # ==========================================================
#     # STEP 1 - READ EXCEL
#     # ==========================================================
    
#     print("\nSTEP 1 - Reading Excel")
    
#     df = read_excel(EXCEL_FILE)
    
#     if df.empty:
#         print("Excel file is empty.")
#         sys.exit(1)
    
#     total_companies = len(df)
#     print(f"Loaded {total_companies} companies")
#     print(f"Processing ALL {total_companies} companies...")
#     print("=" * 70)
    
#     # ==========================================================
#     # PROCESS ALL COMPANIES
#     # ==========================================================
    
#     all_records = []
#     failed_companies = []
    
#     for index, company in df.iterrows():
#         try:
#             record = process_company(company, index, total_companies)
#             all_records.append(record)
            
#         except Exception as e:
#             print(f"\n❌ ERROR processing company {index + 1}: {str(e)}")
#             failed_companies.append({
#                 "index": index,
#                 "company": company.get("full_name", "Unknown"),
#                 "error": str(e)
#             })
#             continue
    
#     # ==========================================================
#     # STEP 10 - REPORT GENERATOR
#     # ==========================================================
    
#     print("\n" + "=" * 70)
#     print(f"STEP 10 - Report Generator")
#     print(f"Successfully processed: {len(all_records)}/{total_companies} companies")
    
#     if failed_companies:
#         print(f"Failed: {len(failed_companies)} companies")
#         for fail in failed_companies:
#             print(f"  - {fail['company']}: {fail['error']}")
    
#     if all_records:
#         report_path = generate_validation_report(
#             records=all_records
#         )
        
#         print("\n✅ Validation Report Generated")
#         print(f"📁 Report Path: {report_path}")
#     else:
#         print("\n❌ No records to generate report")
#         sys.exit(1)
    
#     print("\n" + "=" * 70)
#     print("PIPELINE COMPLETED SUCCESSFULLY")
#     print("=" * 70)


# if __name__ == "__main__":
#     main()



"""
Application entry point.

Starts the complete AI Product Enrichment Pipeline.
"""

from pathlib import Path
import sys

from pipeline.pipeline import run_pipeline


EXCEL_FILE = Path(__file__).parent / "data" / "companies.xlsx"


def main() -> None:
    print("=" * 70)
    print("MUNAFAH AI PRODUCT ENRICHMENT PIPELINE")
    print("=" * 70)

    try:
        result = run_pipeline(
            excel_file=EXCEL_FILE,
        )

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print(f"Total Companies : {result.total_companies}")
        print(f"Successful      : {result.successful}")
        print(f"Failed          : {result.failed}")
        print(f"Report          : {result.report_path}")

    except Exception as exc:
        print("\nPipeline Failed")
        print(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()