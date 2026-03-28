from typing import Dict, Any, List

TASKS: Dict[str, Dict[str, Any]] = {

    # ─────────────────────────────────────────────
    # TASK 1 — EASY: Syntax & Basic Error Detection
    # ─────────────────────────────────────────────
    "task_1_syntax_errors": {
        "task_id": "task_1_syntax_errors",
        "task_name": "Syntax & Basic Error Detection",
        "task_description": (
            "Review the Python code snippet below and identify ALL syntax errors, "
            "undefined variables, and obvious runtime errors. "
            "For each issue, report: type (syntax_error | undefined_variable | type_error | logic_error), "
            "line number, and a brief description."
        ),
        "difficulty": "easy",
        "language": "python",
        "max_steps": 3,
        "code_snippet": '''\
def calculate_average(numbers):
    total = 0
    for num in numbers
        total += num
    average = total / count          # count is undefined
    return averege                   # typo: averege instead of average

result = calculate_average([10, 20, 30])
print("Average is: " + result)      # TypeError: can't concat str + float
''',
        "ground_truth_issues": [
            {
                "type": "syntax_error",
                "line": 3,
                "keywords": ["for", "colon", "missing colon", "syntax"]
            },
            {
                "type": "undefined_variable",
                "line": 5,
                "keywords": ["count", "undefined", "not defined", "nameError"]
            },
            {
                "type": "undefined_variable",
                "line": 6,
                "keywords": ["averege", "typo", "undefined", "not defined"]
            },
            {
                "type": "type_error",
                "line": 9,
                "keywords": ["concatenat", "str", "float", "int", "type", "+"]
            }
        ],
        "approved_expected": False,
    },

    # ──────────────────────────────────────────────
    # TASK 2 — MEDIUM: Code Smell & Quality Review
    # ──────────────────────────────────────────────
    "task_2_code_smells": {
        "task_id": "task_2_code_smells",
        "task_name": "Code Smell & Quality Review",
        "task_description": (
            "Review the Python code below for code quality issues and smells. "
            "Identify: magic numbers, missing error handling, poor variable names, "
            "functions doing too much (SRP violation), missing docstrings, and "
            "hardcoded configuration. For each issue report: type, line, description."
        ),
        "difficulty": "medium",
        "language": "python",
        "max_steps": 4,
        "code_snippet": '''\
import requests
import json

def f(u, d):
    r = requests.post(u, data=json.dumps(d))
    if r.status_code == 200:
        x = json.loads(r.text)
        if x["status"] == "ok":
            with open("C:/Users/admin/output.txt", "w") as file:
                file.write(str(x["data"]))
            print("done")
            return x["data"]
    return None

def process(items):
    result = []
    for i in range(len(items)):
        if items[i] > 42:
            result.append(items[i] * 1.15)
        elif items[i] > 10:
            result.append(items[i] * 1.08)
        else:
            result.append(items[i] * 1.02)
    return result
''',
        "ground_truth_issues": [
            {
                "type": "poor_naming",
                "line": 4,
                "keywords": ["f", "u", "d", "r", "x", "naming", "name", "descriptive", "unclear"]
            },
            {
                "type": "missing_error_handling",
                "line": 5,
                "keywords": ["exception", "error", "try", "except", "handle", "network", "timeout", "request"]
            },
            {
                "type": "hardcoded_path",
                "line": 9,
                "keywords": ["hardcoded", "path", "C:/", "absolute", "config", "windows"]
            },
            {
                "type": "magic_number",
                "line": 18,
                "keywords": ["42", "10", "1.15", "1.08", "1.02", "magic", "constant", "named"]
            },
            {
                "type": "missing_docstring",
                "line": 4,
                "keywords": ["docstring", "documentation", "comment", "doc"]
            },
            {
                "type": "srp_violation",
                "line": 4,
                "keywords": ["single responsibility", "too much", "multiple", "SRP", "separate", "function"]
            }
        ],
        "approved_expected": False,
    },

    # ────────────────────────────────────────────────────
    # TASK 3 — HARD: Security Vulnerability Detection
    # ────────────────────────────────────────────────────
    "task_3_security": {
        "task_id": "task_3_security",
        "task_name": "Security Vulnerability Detection",
        "task_description": (
            "Perform a security review of the Python web application code below. "
            "Identify ALL security vulnerabilities including: SQL injection, "
            "hardcoded credentials, insecure randomness, path traversal, "
            "missing input validation, and sensitive data exposure. "
            "For each vulnerability report: type, line, severity (critical|high|medium|low), description."
        ),
        "difficulty": "hard",
        "language": "python",
        "max_steps": 5,
        "code_snippet": '''\
import sqlite3
import random
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = "supersecret123"          # hardcoded secret
DB_PASSWORD = "admin@1234"            # hardcoded credential
UPLOAD_DIR = "/var/www/uploads"

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username=\'{username}\' AND password=\'{password}\'"
    cursor.execute(query)             # SQL injection vulnerability
    user = cursor.fetchone()
    if user:
        token = str(random.randint(100000, 999999))  # insecure random token
        return jsonify({"token": token, "user": str(user)})  # exposes full user row
    return jsonify({"error": "invalid credentials"})

@app.route("/file", methods=["GET"])
def get_file():
    filename = request.args.get("name")
    filepath = os.path.join(UPLOAD_DIR, filename)  # path traversal
    with open(filepath, "r") as f:                 # no validation
        return f.read()

@app.route("/debug", methods=["GET"])
def debug():
    return jsonify({                               # exposes sensitive config
        "secret": SECRET_KEY,
        "db_password": DB_PASSWORD,
        "env": dict(os.environ)
    })
''',
        "ground_truth_issues": [
            {
                "type": "hardcoded_credentials",
                "line": 7,
                "keywords": ["hardcoded", "secret", "credential", "key", "password", "plaintext"]
            },
            {
                "type": "sql_injection",
                "line": 16,
                "keywords": ["sql injection", "sql", "injection", "f-string", "format", "parameterized", "query"]
            },
            {
                "type": "insecure_randomness",
                "line": 20,
                "keywords": ["random", "insecure", "predictable", "secrets", "token", "randint"]
            },
            {
                "type": "sensitive_data_exposure",
                "line": 21,
                "keywords": ["expose", "user row", "sensitive", "data", "leak", "full row"]
            },
            {
                "type": "path_traversal",
                "line": 27,
                "keywords": ["path traversal", "traversal", "directory", "../", "validation", "sanitize", "path"]
            },
            {
                "type": "sensitive_data_exposure",
                "line": 32,
                "keywords": ["debug", "expose", "secret", "environment", "config", "sensitive", "endpoint"]
            }
        ],
        "approved_expected": False,
    }
}


def get_task_list() -> List[Dict[str, Any]]:
    return [
        {
            "task_id": t["task_id"],
            "task_name": t["task_name"],
            "difficulty": t["difficulty"],
            "description": t["task_description"],
            "action_schema": {
                "issues": "List of {type: str, line: int, description: str, severity: str}",
                "summary": "str — overall review summary",
                "approved": "bool — whether code passes review"
            }
        }
        for t in TASKS.values()
    ]
