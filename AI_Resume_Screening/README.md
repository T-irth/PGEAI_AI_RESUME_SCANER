# AI Resume Screening & Job Matching System

Easy semester-level AI project.

## Technologies
- Python
- Flask
- SQLite
- HTML/CSS/JavaScript
- Scikit-learn
- TF-IDF
- Cosine Similarity
- PDF text extraction

## Features
1. Upload PDF resume
2. Select job
3. Extract resume text
4. Detect required skills
5. Calculate AI match score
6. Show matched/missing skills
7. Give recommendation
8. Admin page
9. Add jobs
10. Rank screened resumes

## Installation

### Windows
Open Command Prompt inside the project folder:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open:
http://127.0.0.1:5000

Admin:
http://127.0.0.1:5000/admin

## AI method

TF-IDF:
Converts resume and job text into numerical vectors based on word importance.

Cosine Similarity:
Measures the similarity between the two vectors.

Final score:
60% text similarity + 40% required skill match.

## Important
Use text-based PDF resumes. Scanned image-only PDFs may not contain extractable text.
