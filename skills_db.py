"""Skill taxonomy used by the analyzer.

Each skill: canonical name -> (group, subcategory, [aliases]).
`group` is one of: technical, tools, soft  (used for the Skills Analysis tables).
`WHY` explains why a missing skill matters (shown to the user).
"""

SKILLS = {}

def _add(group, sub, items):
    for name, aliases in items.items():
        SKILLS[name] = (group, sub, aliases)

# ---------- Technical ----------
_add("technical", "language", {
    "Python": ["python", "python3"], "Java": ["java"], "JavaScript": ["javascript", "js", "ecmascript", "es6"],
    "TypeScript": ["typescript"], "C": ["c programming", "c language"], "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"], "Go": ["golang"], "Kotlin": ["kotlin"], "PHP": ["php"], "Ruby": ["ruby"],
    "Swift": ["swift"], "Rust": ["rust"], "R": ["r programming", "r language"], "Bash": ["bash", "shell scripting", "shell script"],
    "HTML": ["html", "html5"], "CSS": ["css", "css3"],
})
_add("technical", "frontend", {
    "React": ["react", "reactjs", "react.js"], "Angular": ["angular", "angularjs"], "Vue.js": ["vue", "vuejs", "vue.js"],
    "Bootstrap": ["bootstrap"], "Tailwind CSS": ["tailwind", "tailwindcss"], "Redux": ["redux"],
    "Responsive Design": ["responsive design", "responsive web design", "mobile-first"],
})
_add("technical", "backend", {
    "Node.js": ["node.js", "nodejs", "node js"], "Express.js": ["express.js", "expressjs"],
    "Flask": ["flask"], "Django": ["django"], "FastAPI": ["fastapi"], "Spring Boot": ["spring boot", "springboot"],
    ".NET": [".net", "dotnet", "asp.net"], "REST API": ["rest api", "rest apis", "restful", "restful api", "restful apis"],
    "GraphQL": ["graphql"], "Microservices": ["microservices", "microservice"],
})
_add("technical", "database", {
    "SQL": ["sql"], "MySQL": ["mysql"], "PostgreSQL": ["postgresql", "postgres"], "MongoDB": ["mongodb", "mongo"],
    "SQLite": ["sqlite"], "Oracle": ["oracle db", "oracle database", "pl/sql"], "Redis": ["redis"], "NoSQL": ["nosql"],
    "Firebase": ["firebase"],
})
_add("technical", "data", {
    "Machine Learning": ["machine learning"], "Deep Learning": ["deep learning"], "NLP": ["nlp", "natural language processing"],
    "Data Analysis": ["data analysis", "data analytics"], "Pandas": ["pandas"], "NumPy": ["numpy"],
    "Scikit-learn": ["scikit-learn", "sklearn", "scikit learn"], "TensorFlow": ["tensorflow"], "PyTorch": ["pytorch"],
    "Data Visualization": ["data visualization", "data visualisation"], "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"], "Statistics": ["statistics", "statistical analysis"], "Computer Vision": ["computer vision", "opencv"],
})
_add("technical", "concepts", {
    "Data Structures": ["data structures", "data structure", "dsa"], "Algorithms": ["algorithms", "algorithm"],
    "Object-Oriented Programming": ["oop", "oops", "object oriented", "object-oriented"],
    "Operating Systems": ["operating systems", "operating system"], "Computer Networks": ["computer networks", "networking"],
    "DBMS": ["dbms", "database management"], "System Design": ["system design"], "Design Patterns": ["design patterns"],
    "Software Testing": ["unit testing", "software testing", "test automation", "pytest", "junit", "selenium"],
    "Agile": ["agile", "scrum", "kanban"], "Cybersecurity": ["cybersecurity", "cyber security", "information security"],
    "Distributed Systems": ["distributed systems", "distributed computing"], "Android Development": ["android development", "android studio"],
})
# ---------- Tools & technologies ----------
_add("tools", "devops", {
    "Git": ["git"], "GitHub": ["github"], "GitLab": ["gitlab"], "Docker": ["docker", "containerization"],
    "Kubernetes": ["kubernetes", "k8s"], "CI/CD": ["ci/cd", "cicd", "continuous integration", "jenkins", "github actions"],
    "Linux": ["linux", "ubuntu", "unix"],
})
_add("tools", "cloud", {
    "AWS": ["aws", "amazon web services", "ec2", "s3"], "Azure": ["azure"], "Google Cloud": ["gcp", "google cloud"],
    "Cloud Computing": ["cloud computing"], "Heroku": ["heroku"],
})
_add("tools", "tooling", {
    "Jira": ["jira"], "Postman": ["postman"], "VS Code": ["vs code", "vscode", "visual studio code"],
    "Jupyter": ["jupyter"], "Figma": ["figma"], "MS Excel": ["excel", "ms excel", "microsoft excel"],
    "Hadoop": ["hadoop"], "Spark": ["apache spark", "pyspark"], "Kafka": ["kafka"], "Nginx": ["nginx"],
})
# ---------- Soft skills ----------
_add("soft", "soft", {
    "Communication": ["communication", "communicate", "presentation skills", "presenting"],
    "Teamwork": ["teamwork", "team player", "collaboration", "collaborate", "collaborative", "cross-functional"],
    "Leadership": ["leadership", "led a team", "team lead", "led"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical thinking", "analytical skills"],
    "Time Management": ["time management", "deadline", "deadlines", "prioritization"],
    "Adaptability": ["adaptability", "adaptable", "fast learner", "quick learner", "learning agility"],
    "Critical Thinking": ["critical thinking"], "Attention to Detail": ["attention to detail", "detail-oriented", "detail oriented"],
    "Creativity": ["creativity", "creative"], "Ownership": ["ownership", "self-motivated", "initiative", "proactive"],
})

WHY_SKILL = {
    "Python": "Python is listed in the job description; it is often used as a primary screening keyword for software, data and automation roles.",
    "SQL": "Database querying is a core requirement in many roles, and recruiters filter on it directly.",
    "REST API": "REST APIs are how front-end, mobile and back-end systems talk to each other; employers use it to check back-end readiness.",
    "AWS": "Cloud experience shows you can deploy and run software beyond your laptop; ATS filters often list a cloud platform.",
    "Docker": "Containers make deployments reproducible; teams expect at least a basic understanding.",
    "React": "React is a widely used front-end library; if the role is UI-focused, ATS filters often check for it by name.",
    "Git": "Version control is a baseline expectation for any team-based software work.",
    "Agile": "Most software teams work in sprints; familiarity shows you can fit into their workflow.",
    "Data Structures": "Data structures and algorithms are the most common basis of technical interviews and screening.",
    "Communication": "Employers look for evidence you can explain technical work to teammates and non-technical stakeholders.",
    "Teamwork": "Almost every role involves collaboration; hiring teams look for group-project or team evidence.",
    "Problem Solving": "A frequently listed trait; best shown through a concrete project example rather than as a bare keyword.",
}
WHY_SUB = {
    "language": "The job description names this language; ATS filters usually match programming languages exactly.",
    "frontend": "This front-end technology is part of the role's stack, so resumes without it may rank lower.",
    "backend": "This back-end technology is part of the role's stack and is checked for during screening.",
    "database": "Data storage knowledge is requested; mentioning the exact database helps keyword matching.",
    "data": "This data/ML skill is requested; ATS and recruiters look for the exact term.",
    "concepts": "This is a core computer-science concept the employer expects; coursework counts if it is real.",
    "devops": "This engineering tool is part of the team's workflow and is often a hard filter.",
    "cloud": "Cloud tooling is requested for this role; even coursework or a free-tier project is relevant if genuine.",
    "tooling": "This tool is used day-to-day by the team; naming it helps keyword matching.",
    "soft": "Employers want evidence of this trait; show it through a project or activity rather than just listing it.",
}
STOPWORDS = set("""a about above after again all also am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its just me more most my no nor not now of off on once only or other our out over own same she should so some such than that the their them then there these they this those through to too under until up us very was we were what when where which while who whom why will with would you your
ability able across including etc must may well work working experience years year strong good knowledge understanding looking join team role position candidate candidates responsibilities requirements required preferred plus job company will responsible duties skills skill using use new within build write develop maintain applications application clean fix help take part related field junior senior""".split())

DEGREE_LEVELS = [  # (level, regex)
    (3, r"\b(ph\.?d|doctorate)\b"),
    (2, r"\b(master'?s?|m\.?\s?tech|m\.?\s?e\b|m\.?\s?sc|mca|mba|m\.?\s?s\b)\b"),
    (1, r"\b(bachelor'?s?|b\.?\s?tech|b\.?\s?e\b|b\.?\s?sc|bca|b\.?\s?s\b|undergraduate|engineering degree|degree)\b"),
    (0, r"\b(diploma|associate)\b"),
]

JOB_TITLE_WORDS = ["developer", "engineer", "analyst", "intern", "scientist", "designer", "administrator", "architect", "consultant", "tester", "manager"]

# Ambiguous English words: only match when capitalised like a proper noun / acronym.
CASE_SENSITIVE = {"React", "Swift", "Rust", "Ruby", "R", "Oracle", "Spark"}
