from flask import Flask, render_template, request, redirect, url_for, flash
import os, re, sqlite3
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.secret_key = "ai_resume_demo_secret"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn=db()
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        skills TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS resumes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        job_id INTEGER NOT NULL,
        score REAL NOT NULL,
        matched TEXT,
        missing TEXT,
        recommendation TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id))""")
    if conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO jobs(title,description,skills) VALUES(?,?,?)",
            [
                ("Python Developer","Develop web applications and data solutions.",
                 "python, flask, django, sql, git, html, css"),
                ("Data Analyst","Analyze business data and create reports.",
                 "python, pandas, numpy, sql, excel, statistics, machine learning"),
                ("Web Developer","Build modern websites and web applications.",
                 "html, css, javascript, react, node.js, sql, git")
            ])
    conn.commit()
    conn.close()

def extract_pdf(path):
    text=""
    reader=PdfReader(path)
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text

def clean(text):
    text=text.lower()
    text=re.sub(r"[^a-z0-9+#.\s-]"," ",text)
    return re.sub(r"\s+"," ",text).strip()

def get_skills(text, skill_text):
    resume=clean(text)
    skills=[clean(x) for x in skill_text.split(",") if clean(x)]
    matched=[]
    missing=[]
    for skill in skills:
        pattern=r"(?<!\w)"+re.escape(skill)+r"(?!\w)"
        if re.search(pattern,resume):
            matched.append(skill)
        else:
            missing.append(skill)
    return matched,missing

def ai_score(resume_text, job_description, required_skills):
    # TF-IDF converts text to numerical vectors.
    # Cosine similarity measures how similar the resume and job are.
    documents=[clean(resume_text), clean(job_description+" "+required_skills)]
    vectorizer=TfidfVectorizer(stop_words="english")
    matrix=vectorizer.fit_transform(documents)
    similarity=float(cosine_similarity(matrix[0:1],matrix[1:2])[0][0])
    matched,missing=get_skills(resume_text,required_skills)
    skill_score=len(matched)/max(1,len(matched)+len(missing))
    # Final score: 60% NLP similarity + 40% skill match.
    score=(similarity*60)+(skill_score*40)
    if score>=75: rec="Excellent Match"
    elif score>=55: rec="Good Match"
    elif score>=35: rec="Average Match"
    else: rec="Low Match"
    return round(score,2),matched,missing,rec

@app.route("/")
def index():
    conn=db()
    jobs=conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html",jobs=jobs)

@app.route("/screen",methods=["POST"])
def screen():
    job_id=request.form.get("job_id")
    file=request.files.get("resume")
    if not job_id or not file or file.filename=="":
        flash("Please select a job and upload a PDF resume.")
        return redirect(url_for("index"))
    if not file.filename.lower().endswith(".pdf"):
        flash("Only PDF resumes are supported.")
        return redirect(url_for("index"))

    conn=db()
    job=conn.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()
    conn.close()
    if not job:
        flash("Job not found.")
        return redirect(url_for("index"))

    filename=secure_filename(file.filename)
    path=os.path.join(UPLOAD_FOLDER,filename)
    file.save(path)

    try:
        text=extract_pdf(path)
        score,matched,missing,rec=ai_score(text,job["description"],job["skills"])
    except Exception as e:
        flash("Could not read this PDF: "+str(e))
        return redirect(url_for("index"))

    conn=db()
    conn.execute("""INSERT INTO resumes
        (filename,job_id,score,matched,missing,recommendation)
        VALUES(?,?,?,?,?,?)""",
        (filename,job["id"],score,", ".join(matched),", ".join(missing),rec))
    conn.commit()
    resume_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    return render_template("result.html",job=job,score=score,
                           matched=matched,missing=missing,
                           recommendation=rec,resume_id=resume_id)

@app.route("/admin",methods=["GET","POST"])
def admin():
    conn=db()
    if request.method=="POST":
        title=request.form.get("title","").strip()
        description=request.form.get("description","").strip()
        skills=request.form.get("skills","").strip()
        if title and description and skills:
            conn.execute("INSERT INTO jobs(title,description,skills) VALUES(?,?,?)",
                         (title,description,skills))
            conn.commit()
            flash("Job added successfully.")
    jobs=conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    results=conn.execute("""SELECT r.*,j.title FROM resumes r
                            JOIN jobs j ON r.job_id=j.id
                            ORDER BY r.score DESC""").fetchall()
    conn.close()
    return render_template("admin.html",jobs=jobs,results=results)

if __name__=="__main__":
    init_db()
    app.run(debug=True)
