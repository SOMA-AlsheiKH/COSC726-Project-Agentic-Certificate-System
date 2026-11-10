# ============================================================
# main.py
# Certificate Generation System - 5 Agents - CrewAI
# Flow: Internet -> Email -> Gate1 Digital -> Gate2 Hash
#       -> JSON -> Self-Correction -> Certificate in output
# ============================================================

import os
import re
import json
import hashlib
import socket
import imaplib
import email
import glob
from pathlib import Path
from crewai.tools import tool
import fitz  # PyMuPDF
from config import local_llm
from crewai import Agent, Task, Crew

# ============================================================
# 1. CONFIG
# ============================================================
EMAIL_USER = "your_project_email@gmail.com"
EMAIL_PASS = "your_app_password"
TRUSTED_SENDER = "results@university.edu"

PARSED_FILE = "data/parsed.json"
VERIFIED_FILE = "data/verified.json"
ISSUED_FILE = "issued_ids.json"

# ============================================================
# Helper: لقى أي PDF بأي اسم + الهاش بنفس الاسم + _hash
# مثال: data/test_10.pdf -> data/test_10_hash.txt
# ============================================================
def find_pdf_and_hash():
    pdfs = glob.glob("data/*.pdf") + glob.glob("*.pdf")
    if not pdfs:
        return None, None
    pdf = sorted(pdfs)[-1]
    p = Path(pdf)
    hash_file = str(p.with_name(p.stem + "_hash.txt"))
    if not os.path.exists(hash_file) and os.path.exists(p.stem + "_hash.txt"):
        hash_file = p.stem + "_hash.txt"
    return pdf, hash_file

def get_hash_status():
    pdf, hash_file = find_pdf_and_hash()
    if not pdf or not hash_file or not os.path.exists(hash_file):
        return False
    with open(pdf, "rb") as f:
        real = hashlib.sha256(f.read()).hexdigest()
    with open(hash_file, "r") as f:
        expected = f.read().strip().lower()
    return real == expected

# ============================================================
# 2. TOOLS
# ============================================================

@tool("Check Internet")
def check_internet_tool():
    """بيراقب النت بس، ما بينزل أي ملف."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "في نت"
    except Exception:
        return "ما في نت - نوم 5 دقائق"

@tool("Fetch and Watch Email")
def fetch_and_watch_tool():
    """بيفتح الايميل من ادارة النتائج بس، وينزل الملف في data."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        _, data = mail.search(None, f'FROM "{TRUSTED_SENDER}"')
        if data[0]:
            latest = data[0].split()[-1]
            _, msg_data = mail.fetch(latest, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            body = ""
            pdf_data = None
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
                if part.get_content_type() == "application/pdf":
                    pdf_data = part.get_payload(decode=True)
            m = re.search(r"Hash:\s*([a-f0-9]{64})", body, re.IGNORECASE)
            if pdf_data and m:
                os.makedirs("data", exist_ok=True)
                pdf_path = "data/downloaded.pdf"
                hash_path = "data/downloaded_hash.txt"
                with open(pdf_path, "wb") as f:
                    f.write(pdf_data)
                with open(hash_path, "w") as f:
                    f.write(m.group(1).lower())
                return "ملف جديد نزل في data من الايميل"
    except Exception:
        pass
    pdf, _ = find_pdf_and_hash()
    if pdf:
        return "في ملف جديد في data"
    return "ما في ملف جديد"

@tool("Check Digital Gate 1")
def check_digital_tool():
    """البوابة 1: الملف رقمي ولا صورة؟"""
    pdf, _ = find_pdf_and_hash()
    if not pdf:
        return "لا يوجد ملف"
    doc = fitz.open(pdf)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    if len(text.strip()) < 50:
        return "مرفوض: ملف مصور - قيف طوالي"
    return "ملف رقمي - امشي للبوابة التانية الهاش"

@tool("Parse Result Sheet to JSON")
def parse_to_json_tool():
    """بعد البوابتين: حول الكشف لـ JSON."""
    pdf, _ = find_pdf_and_hash()
    if not pdf:
        return "لا يوجد ملف"
    doc = fitz.open(pdf)
    students = []
    for page in doc:
        words = page.get_text("words")
        rows = {}
        for w in words:
            y = round(w[1] / 5) * 5
            rows.setdefault(y, []).append(w)
        for y in sorted(rows):
            line = " ".join([w[4] for w in sorted(rows[y], key=lambda x: x[0])])
            m = re.search(r"(\d{8})", line)
            if not m:
                continue
            sid = m.group(1)
            arabic = re.findall(r"[\u0600-\u06FF]+", line)
            arabic = [w for w in arabic if w not in ["الاسم", "الرقم", "الجامعي", "المعدل", "النتيجة"]]
            english = re.findall(r"[A-Za-z]{3,}", line)
            english = [w for w in english if w.lower() not in ["name", "student", "gpa", "result", "class"]]
            name = " ".join(arabic) if arabic else " ".join(english[:2])
            if len(name.split()) < 2:
                continue
            gpa_m = re.search(r"([0-4])\.(\d{1,2})", line)
            if not gpa_m:
                continue
            gpa = float(f"{gpa_m.group(1)}.{gpa_m.group(2)}")
            if gpa < 1.0 or gpa > 4.0:
                continue
            if any(s["student_id"] == sid for s in students):
                continue
            students.append({
                "student_name": name,
                "student_id": sid,
                "gpa": gpa,
                "raw_class": ""
            })
    os.makedirs("data", exist_ok=True)
    with open(PARSED_FILE, "w", encoding="utf-8") as f:
        json.dump(students, f, ensure_ascii=False, indent=2)
    return f"تم تحويل {len(students)} طالب لـ JSON"

@tool("Check Hash Gate 2")
def check_hash_tool():
    """البوابة 2: الهاش مطابق ولا لا؟ لو مافي هاش، قيف - ممنوع إصدار شهادات"""
    pdf, hash_file = find_pdf_and_hash()
    if not pdf:
        return "لا يوجد ملف - قيف طوالي"
    if not hash_file or not os.path.exists(hash_file):
        return "مرفوض: لا يوجد ملف هاش - قيف طوالي - ممنوع إصدار شهادات"
    with open(pdf, "rb") as f:
        real = hashlib.sha256(f.read()).hexdigest()
    with open(hash_file, "r") as f:
        expected = f.read().strip().lower()
    if real != expected:
        return "الهاش مختلف - قيف طوالي - ممنوع إصدار شهادات"
    return "الهاش مطابق - امشي حول لـ JSON"

@tool("Verify Self Correction")
def verify_self_correct_tool():
    """التصحيح الذاتي: GPA vs التقدير."""
    with open(PARSED_FILE, "r", encoding="utf-8") as f:
        students = json.load(f)
    corrected = []
    for s in students:
        gpa = s["gpa"]
        if gpa >= 3.5:
            correct_class = "First Class"
        elif gpa >= 3.0:
            correct_class = "Second Upper"
        elif gpa >= 2.5:
            correct_class = "Second Lower"
        else:
            correct_class = "Third Class"
        if s.get("raw_class") and s["raw_class"] != correct_class:
            print(f"Self-Correction: {s['student_name']} -> {correct_class}")
        s["degree_classification"] = correct_class
        corrected.append(s)
    with open(VERIFIED_FILE, "w", encoding="utf-8") as f:
        json.dump(corrected, f, ensure_ascii=False, indent=2)
    return f"تم التصحيح الذاتي لـ {len(corrected)} طالب"

@tool("Render Certified Output")
def render_cert_tool():
    """طبقة الأمان الأخيرة: رقم مكرر + حقل فارغ + بوابة Verified + بوابة الهاش. التيمبلت من template.html"""
    pdf, hash_file = find_pdf_and_hash()
    if not hash_file or not os.path.exists(hash_file):
        return "BLOCKED: لا يوجد ملف هاش - ممنوع إصدار شهادات"
    with open(pdf, "rb") as f:
        real = hashlib.sha256(f.read()).hexdigest()
    with open(hash_file, "r") as f:
        expected = f.read().strip().lower()
    if real != expected:
        return "BLOCKED: الهاش مختلف - ممنوع إصدار شهادات"

    # لو verified.json ما اتعمل لأن الـ Verifier اتلخبط، ابنبهو من parsed.json هنا جوه نفس الأداة
    if not os.path.exists(VERIFIED_FILE):
        if not os.path.exists(PARSED_FILE):
            return "BLOCKED: لا يوجد verified.json ولا parsed.json - الـ Verifier ما اشتغل"
        with open(PARSED_FILE, "r", encoding="utf-8") as f:
            students = json.load(f)
        for s in students:
            gpa = s["gpa"]
            if gpa >= 3.5: s["degree_classification"] = "First Class"
            elif gpa >= 3.0: s["degree_classification"] = "Second Upper"
            elif gpa >= 2.5: s["degree_classification"] = "Second Lower"
            else: s["degree_classification"] = "Third Class"
        with open(VERIFIED_FILE, "w", encoding="utf-8") as f:
            json.dump(students, f, ensure_ascii=False, indent=2)

    with open(VERIFIED_FILE, "r", encoding="utf-8") as f:
        students = json.load(f)
    if isinstance(students, dict):
        students = students.get("students", []) or students.get("verified", [])
    issued = []
    if os.path.exists(ISSUED_FILE):
        with open(ISSUED_FILE, "r", encoding="utf-8") as f:
            issued = json.load(f)
    try:
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        return "ERROR: template.html not found next to main.py"
    os.makedirs("output", exist_ok=True)
    count = 0
    for s in students:
        name = s.get("student_name") or s.get("name") or ""
        sid = s.get("student_id") or s.get("id") or ""
        gpa = s.get("gpa") or ""
        cls = s.get("degree_classification") or s.get("classification") or ""
        if sid in issued:
            print(f"SKIPPED: {name} - رقم مكرر")
            continue
        if not name or not sid or not gpa or not cls:
            print(f"مرفوض: حقل فارغ - {s}")
            continue
        verified = s.get("verified", True)
        if isinstance(verified, str):
            verified = verified.lower() == "true"
        if not verified:
            print(f"BLOCKED: {name} - Verified=False - NOT issued")
            continue
        html = template
        html = re.sub(r"\{\{\s*student_name\s*\}\}", str(name), html)
        html = re.sub(r"\{\{\s*name\s*\}\}", str(name), html)
        html = re.sub(r"\{\{\s*student_id\s*\}\}", str(sid), html)
        html = re.sub(r"\{\{\s*id\s*\}\}", str(sid), html)
        html = re.sub(r"\{\{\s*gpa\s*\}\}", str(gpa), html)
        html = re.sub(r"\{\{\s*degree_classification\s*\}\}", str(cls), html)
        html = re.sub(r"\{\{\s*classification\s*\}\}", str(cls), html)
        try:
            from weasyprint import HTML
            out_path = f"output/{sid}_certificate.pdf"
            HTML(string=html).write_pdf(out_path)
        except Exception as e:
            out_path = f"output/{sid}_certificate.html"
            with open(out_path, "w", encoding="utf-8") as out:
                out.write(html)
            print(f"NOTE: saved as HTML: {out_path}")
        issued.append(sid)
        count += 1
    with open(ISSUED_FILE, "w", encoding="utf-8") as f:
        json.dump(issued, f, ensure_ascii=False, indent=2)
    return f"تم تجهيز {count} شهادة في output من template.html - وقف هنا"

# ============================================================
# 3. AGENTS
# ============================================================

agent1_network = Agent(
    role="Network Agent",
    goal="التأكد من النت فقط باستخدام الأداة، ممنوع تأليف أي بيانات",
    backstory="انت روبوت دقيق. ممنوع تكتب أي اسم طالب أو رقم من راسك. شغلك الوحيد هو تنادي الأداة وترجع نتيجتها كما هي. لو ما في نت، قول ما في نت.",
    tools=[check_internet_tool, fetch_and_watch_tool],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

agent2_watcher = Agent(
    role="Watcher Agent",
    goal="مراقبة مجلد data باستخدام الأداة فقط",
    backstory="ممنوع تأليف أي ملف أو طالب. نادي الأداة ورجع نتيجتها فقط.",
    tools=[fetch_and_watch_tool],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

agent3_parser = Agent(
    role="Parser Agent",
    goal="تحويل PDF الحقيقي لـ JSON باستخدام الأداة فقط",
    backstory="ممنوع تكتب أي اسم من راسك. ممنوع تخترع أسماء صينية أو عربية أو انجليزية. شغلك تنادي parse_to_json_tool فقط وتقرأ من data/*.pdf الحقيقي.",
    tools=[check_digital_tool, parse_to_json_tool],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

agent4_verifier = Agent(
    role="Verifier Agent",
    goal="التحقق من الهاش والتصحيح باستخدام الأداة فقط",
    backstory="ممنوع تأليف. نادي الأداة ورجع نتيجتها. لو الهاش غلط أو مافي هاش، قيف.",
    tools=[check_hash_tool, verify_self_correct_tool],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

agent5_render = Agent(
    role="Render Agent",
    goal="طباعة الشهادات من template.html باستخدام الأداة فقط",
    backstory="ممنوع تكتب شهادة من راسك. ممنوع تكتب أي اسم طالب في الرد. شغلك الوحيد: نادي render_cert_tool ورجع الرقم البتقولو الأداة فقط. ممنوع تطبع Verified جوه الشهادة.",
    tools=[render_cert_tool],
    llm=local_llm,
    allow_delegation=False,
    verbose=True
)

# ============================================================
# 4. TASKS 
# ============================================================

task1 = Task(
    description="You MUST call check_internet_tool. Do NOT write any student data. Return only tool output.",
    expected_output="في نت OR ما في نت - من الأداة فقط",
    agent=agent1_network
)
task2 = Task(
    description="You MUST call fetch_and_watch_tool. Do NOT invent files. Return only tool output.",
    expected_output="نتيجة الأداة فقط",
    agent=agent2_watcher
)
task3 = Task(
    description="You MUST call check_digital_tool. Do NOT invent any names. Return only tool output.",
    expected_output="نتيجة الأداة فقط",
    agent=agent3_parser
)
task4 = Task(
    description="You MUST call check_hash_tool. Do NOT invent hash. If no hash file exists, you MUST stop and return BLOCKED. Return only tool output. This MUST run BEFORE parsing.",
    expected_output="الهاش مطابق - من الأداة فقط، أو BLOCKED لو مافي هاش",
    agent=agent4_verifier
)
task5 = Task(
    description="You MUST call parse_to_json_tool. This tool reads data/*.pdf. Do NOT write any student names yourself. Do NOT use Chinese names. Return only tool output: تم تحويل X طالب.",
    expected_output="تم تحويل X طالب لـ JSON - من الأداة فقط",
    agent=agent3_parser
)
task6 = Task(
    description="You MUST call ONLY verify_self_correct_tool. DO NOT call check_hash_tool again, hash already checked. Do NOT write student names. Return only tool output.",
    expected_output="تم التصحيح الذاتي لـ X طالب - من الأداة فقط",
    agent=agent4_verifier
)
task7 = Task(
    description="You MUST call render_cert_tool. DO NOT write any certificate content yourself. DO NOT list student names. DO NOT invent names like Zhang Wei. Just call the tool and return its count: تم تجهيز X شهادة.",
    expected_output="تم تجهيز X شهادة في output - من الأداة فقط، بدون أسماء",
    agent=agent5_render
)

# ============================================================
# 5. CREW + RUN
# ============================================================
from crewai import Process
crew = Crew(
    agents=[agent1_network, agent2_watcher, agent3_parser, agent4_verifier, agent5_render],
    tasks=[task1, task2, task3, task4, task5, task6, task7],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    print("=== 5 Agents شغالين ===")
    print(crew.kickoff())
    print("=== تم - وقف في output ===")