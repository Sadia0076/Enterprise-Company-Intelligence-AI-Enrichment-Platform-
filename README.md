# 🚀 AI Product Enrichment & Validation Pipeline using LLM-as-a-Judge

> **Enterprise AI Pipeline for Automated Company Data Enrichment, Validation, and Confidence Scoring**

---

# 🏗️ System Architecture

<img width="1408" height="768" alt="Gemini_Generated_Image" src="https://github.com/user-attachments/assets/53fe5983-9fc9-4b28-a8f2-03bc5c93125d" />


---

# 📌 Business Problem

Many B2B companies maintain supplier or company information inside Excel files.

Unfortunately, these datasets are often incomplete.

Common missing information includes:

- Industry
- Products
- Services
- Company Description
- Target Customers
- Keywords
- Website Summary

Manually visiting every company website to verify and enrich this information is slow, repetitive, and error-prone.

This project automates the entire enrichment process using AI while ensuring that generated information is supported by the company's website.

---

# 💡 Solution

This project automatically:

✅ Reads company information from Excel

✅ Validates website URLs

✅ Validates email addresses

✅ Downloads company websites

✅ Extracts clean website content

✅ Uses an LLM (Groq Llama 3.3 70B) to enrich company data

✅ Compares AI output with existing Excel data

✅ Uses **LLM-as-a-Judge** to verify that AI-generated information is supported by website evidence

✅ Calculates an overall confidence score

✅ Generates a human-readable validation report

---

# ⚙️ Pipeline Overview

```
Excel File
      │
      ▼
Excel Reader
      │
      ▼
Website Validation
      │
      ▼
Email Validation
      │
      ▼
Website Scraper
      │
      ▼
HTML Parser
      │
      ▼
LLM Enrichment
      │
      ▼
Comparator
      │
      ▼
LLM-as-a-Judge
      │
      ▼
Confidence Scoring
      │
      ▼
Validation Report.xlsx
```

---

# 🧠 AI Workflow

## 1. Website Scraping

Downloads website HTML.

Extracts:

- Title
- Paragraphs
- Product Pages
- Clean Website Text

---

## 2. LLM Enrichment

The website content is sent to **Groq Llama 3.3 70B**.

The model generates structured company information.

Example:

- Company Name
- Industry
- Description
- Products
- Services
- Keywords
- Website Summary

---

## 3. Comparator

The comparator compares:

```
Excel Data

VS

LLM Output
```

It detects:

- Added Fields
- Modified Fields
- Missing Fields

---

## 4. LLM-as-a-Judge

Instead of blindly trusting AI-generated information, a second LLM evaluates whether every generated field is actually supported by the website.

Outputs include:

- Judge Score
- PASS / FAIL
- Supported Fields
- Unsupported Fields
- Missing Information
- Hallucination Detection

This significantly reduces the risk of hallucinated enrichment.

---

## 5. Confidence Scoring

The final confidence score combines multiple signals:

- Website Quality
- Email Validation
- Website Validation
- LLM Completeness
- Comparator Results
- LLM Judge Score

Result:

```
Confidence Score

0 → 100
```

---

# 📊 Example Output

The pipeline generates a validation report containing:

| Column | Description |
|---------|-------------|
| Company Name | Original company |
| Website | Website URL |
| Email | Company email |
| Website Valid | Validation status |
| Email Valid | Validation status |
| LLM Enrichment | AI-generated information |
| Comparator Result | Differences detected |
| Judge Score | AI verification score |
| Hallucination | Yes / No |
| Confidence Score | Overall reliability |
| Recommendation | Accept / Review / Reject |

---

# 🛠 Tech Stack

### Programming

- Python

### Data Processing

- Pandas
- OpenPyXL

### Web Scraping

- Requests
- BeautifulSoup

### AI

- Groq API
- Llama 3.3 70B
- OpenAI Compatible SDK

### Validation

- LLM-as-a-Judge

### Reporting

- Excel Validation Reports

---

# ▶️ How to Run

Clone the repository

```bash
git clone <repository-url>
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```text
GROQ_API_KEY=your_api_key
```

Run the project

```bash
python main.py
```

---

# 🎯 Key Features

- Modular Python architecture
- AI-powered company enrichment
- Website scraping and parsing
- LLM-as-a-Judge validation
- Confidence scoring engine
- Excel report generation
- Structured JSON outputs
- Production-style logging
- Error handling throughout the pipeline

---

# 🚀 Future Improvements

- Batch processing with parallel execution
- Async website scraping
- Redis caching for repeated websites
- Vector database integration for semantic search
- Multi-model support (OpenAI, Claude, Gemini, Mistral)
- Web dashboard for interactive validation
- Human review interface for low-confidence results

---

# 👩‍💻 Author

**Sadia Ali**

- GitHub: https://github.com/Sadia0076
- LinkedIn: https://www.linkedin.com/in/sadia-ali-ce/

---

# ⭐ If you found this project helpful, consider giving it a star!
