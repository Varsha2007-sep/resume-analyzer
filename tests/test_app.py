"""Run:  python -m unittest discover -s tests -v"""
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["RESUME_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from analyzer import analyze, find_skills  # noqa: E402
from app import app  # noqa: E402

JD = open(os.path.join(ROOT, "sample", "sample_job_description.txt"), encoding="utf-8").read()
RESUME_TXT = ("Asha K\nasha@example.com +91 90000 00000\nEDUCATION\nB.E. Computer Science\nSKILLS\nPython, SQL, Git\n"
              "PROJECTS\n- Built a Flask app using Python and SQL with 2 user roles\n- Worked on a web project\n" * 2)


class EngineTests(unittest.TestCase):
    def test_skill_detection_boundaries(self):
        found = find_skills("Experienced in Java and JavaScript, MySQL, C++ and Node.js")
        self.assertIn("Java", found); self.assertIn("JavaScript", found)
        self.assertIn("MySQL", found); self.assertNotIn("SQL", found)   # 'SQL' must not match inside 'MySQL'
        self.assertIn("C++", found); self.assertIn("Node.js", found)

    def test_score_is_deterministic_and_bounded(self):
        a = analyze(RESUME_TXT, JD); b = analyze(RESUME_TXT, JD)
        self.assertEqual(a["overall"], b["overall"])
        self.assertTrue(0 <= a["overall"] <= 100)

    def test_matched_and_missing(self):
        r = analyze(RESUME_TXT, JD)
        matched = {k["name"] for k in r["keywords"]["matched"]}
        missing = {k["name"] for k in r["keywords"]["missing"]}
        self.assertIn("Python", matched); self.assertIn("Docker", missing); self.assertIn("React", missing)

    def test_better_resume_scores_higher(self):
        better = RESUME_TXT + "\nSKILLS\nReact, Docker, AWS, REST API, Agile, Algorithms, Communication"
        self.assertGreater(analyze(better, JD)["overall"], analyze(RESUME_TXT, JD)["overall"])

    def test_no_invented_facts_in_rewrites(self):
        for w in analyze(RESUME_TXT, JD)["suggestions"]["rewrites"]:
            self.assertNotRegex(w["after"], r"\d+%")          # never fabricates percentages


class WebTests(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def test_pages_load(self):
        for url in ("/", "/analyze", "/about", "/history"):
            self.assertEqual(self.c.get(url).status_code, 200, url)

    def test_validation(self):
        r = self.c.post("/api/analyze", data={"job_description": JD})
        self.assertEqual(r.status_code, 400)
        r = self.c.post("/api/analyze", data={"job_description": "short", "resume": (io.BytesIO(b"x"), "a.pdf")})
        self.assertEqual(r.status_code, 400)
        r = self.c.post("/api/analyze", data={"job_description": JD, "resume": (io.BytesIO(b"hello"), "a.txt")})
        self.assertEqual(r.status_code, 400)

    def test_full_flow(self):
        path = os.path.join(ROOT, "sample", "sample_resume.pdf")
        with open(path, "rb") as f:
            r = self.c.post("/api/analyze", data={"job_description": JD, "resume": (f, "sample_resume.pdf")},
                            content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200, r.data)
        url = r.get_json()["url"]
        page = self.c.get(url)
        self.assertEqual(page.status_code, 200); self.assertIn(b"ATS MATCH SCORE", page.data)
        self.assertIn(b"genuinely have experience", page.data)
        self.assertIn(b"sample_resume.pdf", self.c.get("/history").data)
        rep = self.c.get(url.replace("results", "report"))
        self.assertEqual(rep.status_code, 200); self.assertIn("attachment", rep.headers["Content-Disposition"])
        aid = r.get_json()["id"]
        self.assertEqual(self.c.delete(f"/api/history/{aid}").status_code, 200)
        self.assertEqual(self.c.get(url).status_code, 404)


if __name__ == "__main__":
    unittest.main()
