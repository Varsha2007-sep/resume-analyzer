# AI Resume Analyzer

Upload a resume (PDF/DOCX), paste a job description, and get an explainable ATS match score, matched/missing keywords,
skills tables, strengths/weaknesses, an ATS checklist, honest Before → After rewrites, history and a downloadable report.

## 1. Folder structure
```
resume-analyzer/
├── app.py                 Flask routes, SQLite history, report download
├── analyzer.py            NLP engine: skills, keywords, TF-IDF similarity, scoring, suggestions
├── skills_db.py           Skill taxonomy (aliases, categories, "why it matters" text), stopwords
├── extractor.py           PDF (pypdf) and DOCX (python-docx) text extraction + validation
├── requirements.txt
├── templates/             base, index, analyze, results, history, about, report, 404, _icons
├── static/css/style.css   Design system (blue + teal), responsive
├── static/js/main.js      Upload/drag-drop, validation, fetch, animations, copy, delete
├── sample/                sample_resume.pdf / .docx, sample_job_description.txt
└── tests/test_app.py      Unit + integration tests
```

## 2. Installation (Windows / macOS / Linux)
```bash
cd resume-analyzer
python -m venv venv
venv\Scripts\activate          # Windows      (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
Required packages: **Flask**, **pypdf**, **python-docx** (SQLite is built into Python).

## 3. Run
```bash
python app.py
```
Open http://127.0.0.1:5000

## 4. Testing
Automated: `python -m unittest discover -s tests -v` (8 tests: skill boundaries, determinism, matched/missing,
better-resume-scores-higher, no fabricated numbers, page loads, validation, full upload→results→report→delete flow).

Manual demo:
1. Open **Analyzer**. Drag in `sample/sample_resume.pdf` (or .docx).
2. Click **Use sample job description** (or paste `sample/sample_job_description.txt`).
3. Click **Analyze Resume**. Expected for the sample: score about **51/100**, matched Python/SQL/Java/Git/JavaScript,
   missing React/REST API/Docker/AWS/Agile.
4. Check **Score calculation**, copy a rewrite, **Download Analysis Report**, then open **History**.
5. Validation checks: analyze with no file or empty JD (button disabled), upload a `.txt` (error), a file over 5 MB (error).
6. Improve the resume honestly (add skills you truly have) and re-run: the score must rise.

## 5. How the score works (all deterministic, no random numbers)
| Component | Weight | How it is computed |
|---|---|---|
| Keyword Match | 40% | Weighted share of job keywords found in the resume: taxonomy skills (required = 2, preferred = 1, +0.5 per extra mention, max +1) plus up to 12 frequent job-specific terms (weight 1) |
| Skills Relevance | 25% | Weighted share of required skills found; soft skills count half; a skill only in the Skills list gets 0.8 credit, one shown in projects/experience gets 1.0 |
| Job Description Relevance | 20% | TF-IDF cosine similarity of resume vs job description (unigrams + bigrams), scaled so 0.50 similarity = 100% |
| Education/Experience | 10% | 40% education (present, degree level ≥ required) + 60% experience/projects (or years vs "N+ years" requirement) |
| Resume Structure | 5% | Contact (20), education (20), skills (20), projects/experience (20), sensible length (10), clean bullets (10) |

`ATS score = Σ (component % × weight)`

## 6. Major components
- **extractor.py**: validates type/size, reads PDF pages or DOCX paragraphs and tables, rejects scanned/empty/encrypted files.
- **skills_db.py**: ~100 skills with aliases, so "ReactJS", "react.js" and "React" are one skill; each has a "why it matters" text.
- **analyzer.py**: (1) split resume into sections, (2) detect skills with word-boundary regex (SQL ≠ MySQL, Java ≠ JavaScript),
  (3) read the JD and mark each skill required/preferred from headings such as "Nice to have", (4) extra keywords by n-gram frequency,
  (5) TF-IDF cosine similarity, (6) score, (7) rule-based strengths, weaknesses, checklist, (8) rewrites.
- **Rewrites** only reword existing lines (e.g. "Worked on" → "Developed") and use `[brackets]` for facts the user must supply.
  The engine never adds numbers, tools or achievements. Missing keywords always carry the "add only if you genuinely have it" warning.
- **app.py**: routes `/`, `/analyze`, `/results/<id>`, `/history`, `/report/<id>`, `/about`, `POST /api/analyze`, `DELETE /api/history/<id>`.
  SQLite stores resume file name, job title, score, date, JD and results JSON. Resume text is never stored.
- **Frontend**: Jinja templates, one CSS file with design tokens, vanilla JS (no build step), SVG icons, responsive nav.

## 7. Faculty presentation (3-4 minutes)
1. **Problem**: ATS software rejects weak or mismatched resumes; students do not know why.
2. **Existing solution**: manual comparison of resume and job description; slow and subjective. Many online tools give opaque scores.
3. **Proposed solution**: automatic, explainable comparison with honest suggestions.
4. **Workflow**: upload → extract text → analyse JD → extract skills/keywords → compare → score → missing keywords → strengths → suggestions → dashboard.
5. **NLP used**: text extraction, tokenisation/stop-words/stemming, n-grams, skill taxonomy matching, TF-IDF cosine similarity, rule-based generation.
6. **Demo**: run the sample, show the formula table, then improve the resume and show the score rise.
7. **Ethics**: never recommends faking skills; stores no resume text.
8. **Limitations / future work**: rule-based (no deep model); text PDFs only (no OCR); ~100-skill taxonomy; could add spaCy/BERT embeddings, OCR, more roles.

## 8. Possible viva questions
1. **What is ATS?** Software employers use to parse, store and rank resumes, usually by keywords and structure.
2. **Why not use a large AI model?** A transparent algorithm gives repeatable, explainable scores, runs offline, and is easy to justify.
3. **What is TF-IDF?** Term frequency × inverse document frequency; it weights words that are distinctive for a document.
4. **What is cosine similarity?** Cosine of the angle between two vectors; 1 = same direction (very similar), 0 = unrelated.
5. **Why scale similarity by 0.50?** Resume and JD are different genres; strong matches score about 0.3-0.5, so raw cosine would look unfairly low.
6. **How do you stop SQL matching MySQL?** Regex look-around boundaries: the match cannot touch letters, digits, `+` or `#`.
7. **How are required vs preferred skills decided?** By JD headings and phrases like "nice to have"/"preferred".
8. **Is the score random?** No. Same inputs always give the same score (covered by a test).
9. **How do you extract text from PDF/DOCX?** pypdf for PDF pages; python-docx for paragraphs and tables.
10. **What about scanned PDFs?** No text layer, so extraction fails with a clear message; OCR (Tesseract) is future work.
11. **How do you avoid encouraging lying?** Missing-keyword cards carry an honesty warning; rewrites use placeholders, never invented facts.
12. **Why SQLite?** Zero-config, file-based, ideal for a single-user demo; replaceable by PostgreSQL with the same SQL.
13. **How is privacy handled?** Resume text is processed in memory and discarded; only results and the JD are stored.
14. **Limitations?** Fixed taxonomy, English only, no layout analysis, heuristic section detection.
15. **How would you improve it?** spaCy NER, sentence embeddings (SBERT), OCR, role-specific taxonomies, user accounts.
16. **Keyword match vs skills relevance?** Keyword covers all job terms; skills relevance covers only skills, weighted by priority and evidence in projects.
