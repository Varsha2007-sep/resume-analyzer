"""NLP engine: skill/keyword extraction, similarity, ATS scoring and suggestions.

Pure Python (no external ML models) so every number can be explained in a viva.
"""
import math
import re
from collections import Counter

from skills_db import (CASE_SENSITIVE, DEGREE_LEVELS, JOB_TITLE_WORDS, SKILLS, STOPWORDS,
                       WHY_SKILL, WHY_SUB)

WEIGHTS = {"keyword": 40, "skills": 25, "relevance": 20, "education": 10, "structure": 5}

# ---------------------------------------------------------------- skill matching
def _build_patterns():
    pats = {}
    for name, (_g, _s, aliases) in SKILLS.items():
        variants = set(a for a in aliases)
        if len(name) > 2:
            variants.add(name.lower())
        flags = 0 if name in CASE_SENSITIVE else re.I
        if name in CASE_SENSITIVE:
            variants = {v2 for v in variants for v2 in (v, v.capitalize(), v.upper())} | {name}
        body = "|".join(re.escape(v) for v in sorted(variants, key=len, reverse=True))
        pats[name] = re.compile(r"(?<![A-Za-z0-9+#])(?:%s)(?![A-Za-z0-9+#])" % body, flags)
    return pats

PATTERNS = _build_patterns()


def find_skills(text):
    """Return {skill: {'count': n, 'matched': 'text as written'}}."""
    found = {}
    for name, pat in PATTERNS.items():
        hits = pat.findall(text)
        if hits:
            found[name] = {"count": len(hits), "matched": hits[0]}
    return found


# ---------------------------------------------------------------- text helpers
def _stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def _words(text):
    return [w.rstrip(".-") for w in re.findall(r"[a-z][a-z0-9+#.\-]*", text.lower())]


def _content_tokens(text):
    return [_stem(w) for w in _words(text) if len(w) > 2 and w not in STOPWORDS]


def _ngrams(tokens):
    return tokens + [a + " " + b for a, b in zip(tokens, tokens[1:])]


def cosine_tfidf(a, b):
    """TF-IDF cosine similarity between two documents (unigrams + bigrams)."""
    da, db = Counter(_ngrams(_content_tokens(a))), Counter(_ngrams(_content_tokens(b)))
    vocab = set(da) | set(db)
    if not vocab:
        return 0.0
    idf = {t: math.log((1 + 2) / (1 + (t in da) + (t in db))) + 1 for t in vocab}
    va = {t: (1 + math.log(c)) * idf[t] for t, c in da.items()}
    vb = {t: (1 + math.log(c)) * idf[t] for t, c in db.items()}
    dot = sum(va[t] * vb[t] for t in va if t in vb)
    na, nb = math.sqrt(sum(v * v for v in va.values())), math.sqrt(sum(v * v for v in vb.values()))
    return dot / (na * nb) if na and nb else 0.0


# ---------------------------------------------------------------- resume parsing
SECTION_PATTERNS = {
    "education": r"education|academic background|academic qualifications?|qualifications?",
    "skills": r"(technical |key |core )?skills|core competencies|technologies|tools( (&|and) technologies)?|skills (&|and) tools|technical proficiency",
    "projects": r"(academic |personal |key |major |mini )?projects?",
    "experience": r"(work |professional |relevant )?experience|internships?|employment( history)?|work history",
    "summary": r"(professional |career )?summary|(career )?objective|profile|about me",
    "certifications": r"certifications?|licen[sc]es( (&|and) certifications?)?|courses|training",
    "achievements": r"achievements|awards|honou?rs|accomplishments|extracurricular activities|activities",
}
_SEC_RE = {k: re.compile(r"^(?:%s)$" % v, re.I) for k, v in SECTION_PATTERNS.items()}


def split_sections(text):
    sections, current, buf = {}, "header", []
    for line in text.split("\n"):
        stripped = re.sub(r"[:\-–—_|•*#]+", " ", line).strip()
        key = None
        if 2 < len(stripped) <= 40:
            for k, rx in _SEC_RE.items():
                if rx.match(stripped):
                    key = k
                    break
        if key:
            sections[current] = sections.get(current, "") + "\n".join(buf) + "\n"
            current, buf = key, []
        else:
            buf.append(line)
    sections[current] = sections.get(current, "") + "\n".join(buf)
    return {k: v.strip() for k, v in sections.items() if v.strip()}


BULLET = re.compile(r"^\s*[•●▪◦‣\-*–·]\s*")
WEAK = [  # (regex, replacement verb)
    (r"worked on", "Developed"), (r"responsible for", "Performed"), (r"helped (?:with|in|to)", "Contributed to"),
    (r"involved in", "Contributed to"), (r"participated in", "Contributed to"), (r"assisted (?:in|with)", "Supported"),
    (r"handled", "Managed"), (r"made", "Built"), (r"did", "Completed"),
]
WEAK_RE = [(re.compile(r"^(?:%s)\b\s*(.*)$" % rx, re.I), verb) for rx, verb in WEAK]
ACTION_VERBS = set("""developed built designed implemented created led managed analyzed analysed automated optimized optimised
deployed engineered integrated improved reduced increased launched tested architected configured researched trained
collaborated delivered organized organised presented migrated maintained debugged coordinated established
contributed supported completed produced wrote constructed""".split())


def _bullets(text):
    out = []
    for line in text.split("\n"):
        s = BULLET.sub("", line).strip()
        if len(s) >= 20:
            out.append(s)
    return out


def detect_contact(text):
    return {
        "email": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)),
        "phone": bool(re.search(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{4,5}", text[:600])),
        "linkedin": "linkedin.com" in text.lower(),
        "github": "github.com" in text.lower(),
    }


def degree_level(text, case_text=None):
    best = -1
    for level, rx in DEGREE_LEVELS:
        if re.search(rx.replace(r"\bm\.?\s?e\b", r"\bm\.e\b"), text.lower()):
            best = max(best, level)
    if case_text and re.search(r"\bB\.?E\.?(?=\s*(?:in\b|\(|-|,|Computer|CSE|ECE|EEE|IT\b|Mech|Civil|\.))", case_text):
        best = max(best, 1)
    return best


# ---------------------------------------------------------------- JD analysis
PREF_RE = re.compile(r"preferred|nice to have|good to have|bonus|a plus|desirable|optional|added advantage", re.I)
REQ_HEAD = re.compile(r"requirements?|qualifications?|responsibilit|must have|what you.?ll (need|do)|skills|you have", re.I)


def analyze_jd(jd):
    skill_ctx = {}
    state = "required"
    for line in jd.split("\n"):
        s = line.strip()
        if not s:
            continue
        if len(s) < 60 and (s.endswith(":") or s.isupper() or len(s.split()) <= 4):
            if PREF_RE.search(s):
                state = "preferred"
            elif REQ_HEAD.search(s):
                state = "required"
        line_state = "preferred" if PREF_RE.search(s) else state
        for name, info in find_skills(s).items():
            d = skill_ctx.setdefault(name, {"count": 0, "required": 0, "matched": info["matched"]})
            d["count"] += info["count"]
            if line_state == "required":
                d["required"] += info["count"]
    skills = {}
    for name, d in skill_ctx.items():
        importance = "required" if d["required"] else "preferred"
        weight = (2 if importance == "required" else 1) + min(d["count"] - 1, 2) * 0.5
        skills[name] = {"count": d["count"], "importance": importance, "weight": weight}

    # additional job-specific keywords (non-taxonomy) by frequency
    skill_words = set()
    for name in skills:
        for a in SKILLS[name][2] + [name.lower()]:
            skill_words.update(_words(a))
    toks = [t for t in _content_tokens(jd) if t not in skill_words and not t.isdigit()]
    uni = Counter(toks)
    bi = Counter(a + " " + b for a, b in zip(toks, toks[1:]))
    extras = [(k, c) for k, c in bi.most_common(20) if c >= 2][:5]
    used = {w for k, _ in extras for w in k.split()}
    extras += [(k, c) for k, c in uni.most_common(30) if c >= 2 and k not in used and len(k) > 4][:10]
    extras = extras[:12]

    min_years = None
    m = re.findall(r"(\d+)\s*\+?\s*(?:-\s*\d+\s*)?(?:years|yrs)", jd, re.I)
    if m:
        min_years = min(int(x) for x in m)
    return {"skills": skills, "extras": extras, "req_degree": degree_level(jd), "min_years": min_years}


def guess_title(jd, given=""):
    if given.strip():
        return given.strip()[:80]
    m = re.search(r"(?:job title|position|role|title)\s*[:\-–]\s*(.+)", jd, re.I)
    if m:
        return m.group(1).strip().split("\n")[0][:80]
    for line in jd.split("\n")[:5]:
        s = line.strip(" -•*#:")
        if 3 < len(s) <= 70 and any(w in s.lower() for w in JOB_TITLE_WORDS):
            return s
    m = re.search(r"((?:[A-Z][\w+#.]*\s){0,3}(?:%s))\b" % "|".join(w.capitalize() for w in JOB_TITLE_WORDS), jd)
    return m.group(1).strip() if m else "Untitled Role"


# ---------------------------------------------------------------- main entry
def analyze(resume_text, jd_text, resume_name="resume", job_title=""):
    sections = split_sections(resume_text)
    resume_skills = find_skills(resume_text)
    evidence_text = "\n".join(v for k, v in sections.items() if k not in ("skills", "header"))
    evidence_skills = find_skills(evidence_text) if evidence_text else {}
    jd = analyze_jd(jd_text)
    contact = detect_contact(resume_text)
    r_tokens = _content_tokens(resume_text)
    r_set = set(_ngrams(r_tokens))

    # ---- skills table + skills relevance
    tables = {"technical": [], "tools": [], "soft": []}
    s_total = s_got = 0.0
    matched_names, missing = [], []
    for name, info in sorted(jd["skills"].items(), key=lambda kv: -kv[1]["weight"]):
        group, sub, _ = SKILLS[name]
        present = name in resume_skills
        w = info["weight"] * (0.5 if group == "soft" else 1)
        s_total += w
        credit = 0.0
        if present:
            credit = 1.0 if (name in evidence_skills or not evidence_text) else 0.8
        s_got += w * credit
        tables[group].append({"skill": name, "resume": resume_skills[name]["matched"] if present else "—",
                              "status": "Matched" if present else "Missing", "importance": info["importance"],
                              "demonstrated": present and name in evidence_skills})
        if present:
            matched_names.append({"name": name, "kind": "skill"})
        else:
            missing.append({"name": name, "kind": "skill", "importance": info["importance"],
                            "why": WHY_SKILL.get(name) or WHY_SUB.get(sub, "")})
    skills_pct = round(100 * s_got / s_total) if s_total else None

    # ---- keyword match (skills + extra job keywords)
    k_total = sum(i["weight"] for i in jd["skills"].values())
    k_got = sum(jd["skills"][m["name"]]["weight"] for m in matched_names)
    for kw, c in jd["extras"]:
        k_total += 1
        parts = kw.split()
        if kw in r_set:
            k_got += 1
            matched_names.append({"name": kw, "kind": "term"})
        else:
            missing.append({"name": kw, "kind": "term", "importance": "required" if c >= 3 else "preferred",
                            "why": f"This term appears {c} times in the job description, so the employer treats it as important. "
                                   "Use it only where it truthfully describes your work."})
    keyword_pct = round(100 * k_got / k_total) if k_total else 0
    if skills_pct is None:  # JD with no recognised skills: fall back to keyword coverage
        skills_pct = keyword_pct

    # ---- relevance
    cos = cosine_tfidf(resume_text, jd_text)
    relevance_pct = round(100 * min(1.0, cos / 0.5))

    # ---- education / experience
    r_level = degree_level(resume_text, resume_text)
    has_edu = "education" in sections or r_level >= 0
    exp_text = sections.get("experience", "")
    has_exp = bool(exp_text) or bool(re.search(r"\bintern", resume_text, re.I))
    has_proj = "projects" in sections
    edu_pts = 0.3
    if has_edu:
        edu_pts = 1.0 if (jd["req_degree"] < 0 or r_level >= jd["req_degree"]) else 0.5
    years = [int(x) for x in re.findall(r"(\d+)\+?\s*years?", resume_text, re.I)]
    est = max(years) if years else 0
    if jd["min_years"] and jd["min_years"] >= 2:
        exp_pts = min(1.0, est / jd["min_years"]) if est else (0.4 if (has_exp or has_proj) else 0.1)
    else:
        exp_pts = 1.0 if (has_exp or has_proj) else 0.3
    education_pct = round(100 * (0.4 * edu_pts + 0.6 * exp_pts))

    # ---- structure
    wc = len(resume_text.split())
    bullets = _bullets(resume_text)
    nonascii = sum(1 for ch in resume_text if ord(ch) > 0x2FFF) / max(1, len(resume_text))
    struct = {
        "contact": 20 if (contact["email"] and contact["phone"]) else 10 if (contact["email"] or contact["phone"]) else 0,
        "education": 20 if has_edu else 0, "skills": 20 if "skills" in sections or len(resume_skills) >= 3 else 0,
        "projects": 20 if (has_proj or has_exp) else 0,
        "length": 10 if 200 <= wc <= 1000 else 5 if 120 <= wc < 200 or 1000 < wc <= 1400 else 0,
        "bullets": 10 if len(bullets) >= 4 and nonascii < 0.03 else 4 if bullets else 0,
    }
    structure_pct = sum(struct.values())

    pcts = {"keyword": keyword_pct, "skills": skills_pct, "relevance": relevance_pct,
            "education": education_pct, "structure": structure_pct}
    overall = round(sum(pcts[k] * WEIGHTS[k] / 100 for k in WEIGHTS))
    breakdown = {k: {"pct": pcts[k], "weight": WEIGHTS[k], "points": round(pcts[k] * WEIGHTS[k] / 100, 1)} for k in WEIGHTS}

    # ---- strengths / weaknesses / checklist
    num_bullets = [b for b in bullets if re.search(r"\d", b)]
    weak_lines = []
    for b in bullets:
        for rx, verb in WEAK_RE:
            m = rx.match(b)
            if m:
                weak_lines.append((b, verb, m.group(1).strip()))
                break
    verb_bullets = [b for b in bullets if b.split()[0].lower().rstrip(",") in ACTION_VERBS]
    proj_bullets = _bullets(sections.get("projects", ""))
    n_match = sum(1 for m in matched_names if m["kind"] == "skill")
    n_jd = len(jd["skills"])

    strengths, weaknesses = [], []
    if n_jd and skills_pct >= 50:
        strengths.append(("Relevant technical skills", f"Your resume covers {n_match} of the {n_jd} skills found in the job description."))
    if has_edu:
        strengths.append(("Clear education section", "An education section/degree was detected, which ATS parsers look for first."))
    if has_proj and len(proj_bullets) >= 2:
        strengths.append(("Good project experience", f"{len(proj_bullets)} project lines detected, which shows applied skills."))
    elif has_exp:
        strengths.append(("Experience / internship listed", "Work or internship experience section detected."))
    if contact["email"] and contact["phone"]:
        strengths.append(("Contact information detected", "Email and phone number were found."))
    if contact["github"] or contact["linkedin"]:
        strengths.append(("Professional profile links", "LinkedIn/GitHub link found, which lets recruiters verify your work."))
    if len(num_bullets) >= 2:
        strengths.append(("Measurable details present", f"{len(num_bullets)} lines contain numbers, which helps show impact."))
    if len(verb_bullets) >= 3:
        strengths.append(("Strong action verbs", "Several bullet points start with action verbs."))
    if "certifications" in sections:
        strengths.append(("Certifications listed", "A certifications/courses section was detected."))
    if not strengths:
        strengths.append(("Resume text readable", "Your file was parsed successfully by the extractor."))

    if keyword_pct < 50:
        weaknesses.append(("Few job-specific keywords", f"Only {keyword_pct}% of the job's key terms appear in your resume."))
    if any(m["importance"] == "required" and m["kind"] == "skill" for m in missing):
        names = ", ".join(m["name"] for m in missing if m["importance"] == "required" and m["kind"] == "skill")[:120]
        weaknesses.append(("Required skills not found", f"Not detected: {names}. Add only what you genuinely know."))
    if weak_lines or (bullets and len(verb_bullets) < max(2, len(bullets) // 4)):
        weaknesses.append(("Weak project descriptions", "Some lines use passive wording (e.g. 'worked on') instead of action verbs and outcomes."))
    if len(num_bullets) < 2:
        weaknesses.append(("Missing measurable achievements", "Few lines include numbers (users, size, accuracy, time saved). Add only figures that are true."))
    if "skills" not in sections:
        weaknesses.append(("No dedicated Skills section", "A labelled Skills section helps ATS parsers pick up your keywords."))
    undemonstrated = [m["name"] for m in matched_names if m["kind"] == "skill" and m["name"] not in evidence_skills and SKILLS[m["name"]][0] != "soft"]
    if evidence_text and undemonstrated:
        weaknesses.append(("Skills listed but not demonstrated", f"{', '.join(undemonstrated[:4])} appear only in the skills list; mention them in a project or experience bullet if true."))
    if not (contact["github"] or contact["linkedin"]):
        weaknesses.append(("No LinkedIn/GitHub link", "Adding profile links gives recruiters evidence to verify your skills."))
    if wc < 200 or wc > 1000:
        weaknesses.append(("Resume length", f"About {wc} words; aim for roughly 300-700 words (one page for students)."))

    checklist = [
        ("Contact information", contact["email"] and contact["phone"], "Email and phone detected" if contact["email"] and contact["phone"] else "Add a professional email and phone number"),
        ("Education section", has_edu, "Found" if has_edu else "Add a clear Education section"),
        ("Skills section", "skills" in sections, "Found" if "skills" in sections else "Add a section titled 'Skills'"),
        ("Projects / experience section", has_proj or has_exp, "Found" if has_proj or has_exp else "Add Projects or Internship experience"),
        ("Relevant keywords", keyword_pct >= 60, f"{keyword_pct}% of job keywords matched"),
        ("Simple formatting", struct["bullets"] >= 10 and nonascii < 0.03, "Plain text parsed cleanly" if struct["bullets"] >= 10 else "Use simple bullet points; avoid tables, images and text boxes"),
    ]
    warnings = []
    if keyword_pct < 50:
        warnings.append("Few job-specific keywords")
    if weak_lines or len(proj_bullets) < 2:
        warnings.append("Weak project descriptions")
    if len(num_bullets) < 2:
        warnings.append("Missing measurable achievements")
    if "summary" not in sections:
        warnings.append("No professional summary / objective")

    # ---- suggestions (never invent facts)
    rewrites = []
    for before, verb, rest in weak_lines[:4]:
        techs = [n for n in find_skills(before)]
        rest = re.sub(r"^(?:on\s+)?", "", rest).rstrip(".")
        after = f"{verb} {rest}"
        needs_input = False
        if techs and " using " not in after.lower():
            after += " using " + (", ".join(techs[:-1]) + " and " + techs[-1] if len(techs) > 1 else techs[0])
        elif not techs and re.search(r"project|app|system|website|module|application|tool|dashboard|bot|model|api|game|portal", after, re.I) and not re.search(r"\busing\b", after):
            after += " using [technologies you actually used]"
            needs_input = True
        if not re.search(r"\d", after):
            after += " to [purpose or result you can verify]"
            needs_input = True
        rewrites.append({"before": before, "after": after + ".", "needs_input": needs_input})
    if not rewrites:
        top = [m["name"] for m in matched_names if m["kind"] == "skill" and SKILLS[m["name"]][0] != "soft"][:3]
        if top:
            tech = ", ".join(top[:-1]) + " and " + top[-1] if len(top) > 1 else top[0]
            rewrites.append({"before": "Worked on a project.", "after": f"Built [project name] using {tech} to [what it does / result you can verify].",
                             "needs_input": True, "template": True})
    keyword_tips = []
    for m in [x for x in missing if x["kind"] == "skill"][:4]:
        keyword_tips.append({"skill": m["name"], "example": f"Implemented [feature or task] using {m['name']} in [project / coursework / internship]."})

    general = []
    if keyword_pct < 70:
        general.append("Mirror the job description's wording where it truthfully describes your experience (e.g. use 'REST API' if that is the term used).")
    if undemonstrated:
        general.append("Show your listed skills in action: mention them inside project or experience bullets, not only in the Skills list.")
    if len(num_bullets) < 2:
        general.append("Quantify real results where possible (dataset size, number of users, response time, test coverage). Skip numbers you cannot back up.")
    if "summary" not in sections:
        general.append("Add a 2-line summary that names the target role and your strongest relevant skills.")
    if not (contact["github"] or contact["linkedin"]):
        general.append("Add your GitHub and LinkedIn URLs so recruiters can verify your projects.")
    if any(m["kind"] == "skill" for m in missing):
        general.append("For missing skills: add them only if you genuinely have experience, coursework, a certification or knowledge. Otherwise, treat them as a learning plan.")

    return {
        "resume_name": resume_name, "job_title": guess_title(jd_text, job_title), "overall": overall,
        "scores": breakdown,
        "dashboard": {"skills": skills_pct, "keyword": keyword_pct, "relevance": relevance_pct, "structure": structure_pct},
        "keywords": {"matched": matched_names, "missing": sorted(missing, key=lambda m: m["importance"] != "required")},
        "skills_table": tables,
        "additional_skills": [n for n in resume_skills if n not in jd["skills"] and SKILLS[n][0] != "soft"][:15],
        "strengths": [{"title": t, "detail": d} for t, d in strengths],
        "weaknesses": [{"title": t, "detail": d} for t, d in weaknesses],
        "checklist": [{"label": l, "ok": bool(ok), "detail": d} for l, ok, d in checklist],
        "warnings": warnings,
        "suggestions": {"rewrites": rewrites, "keyword_tips": keyword_tips, "general": general},
        "meta": {"words": wc, "sections": sorted(k for k in sections if k != "header"), "cosine": round(cos, 3),
                 "jd_skills": n_jd, "structure_parts": struct},
    }
