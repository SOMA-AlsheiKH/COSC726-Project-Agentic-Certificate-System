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
# 1. EMAIL
# ============================================================
EMAIL_USER = "project_email@gmail.com"
EMAIL_PASS = "app_password"
TRUSTED_SENDER = "results@university.edu"

PARSED_FILE = "data/parsed.json"
VERIFIED_FILE = "data/verified.json"
ISSUED_FILE = "issued_ids.json"

# ============================================================
# تعديل البوابة فقط - بداية
# قائمة الأخطاء للبوابة فقط، عشان نافذة التخطي تعرضها
# ============================================================
ISSUES = []
ISSUES_FILE = "data/issues.json"
REPORT_PDF = "output/issues_report.pdf"

def add_issue(type_, file_, field, desc):
    for x in ISSUES:
        if x["type"] == type_ and x["file"] == file_ and x["desc"] == desc:
            return
    ISSUES.append({"type": type_, "file": file_, "field": field, "desc": desc})

def save_issues():
    os.makedirs("data", exist_ok=True)
    with open(ISSUES_FILE, "w", encoding="utf-8") as f:
        json.dump(ISSUES, f, ensure_ascii=False, indent=2)
# ============================================================
# تعديل البوابة فقط - نهاية
# ============================================================

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

def find_all_pdfs():
    return sorted(glob.glob("data/*.pdf"))

def get_hash_status():
    pdf, hash_file = find_pdf_and_hash()
    if not pdf or not hash_file or not os.path.exists(hash_file):
        return False
    with open(pdf, "rb") as f:
        real = hashlib.sha256(f.read()).hexdigest()
    with open(hash_file, "r") as f:
        expected = f.read().strip().lower()
    return real == expected

def is_gate_passed(pdf):
    # فحص البوابة لملف واحد: رقمي + هاش - بترجع True لو عدى، False لو اتجاهل
    p = Path(pdf)
    doc = fitz.open(pdf)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    if len(text.strip()) < 50:
        return False
    hash_file = str(p.with_name(p.stem + "_hash.txt"))
    if not os.path.exists(hash_file):
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
    """يراقب الشبكة فقط، لا يقوم بتنزل أي ملف."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "يوجد شبكة انترنت"
    except Exception:
        return "لا يوجد شبكة انترنت - قم بالعمل محليا من ملف البيانات"

@tool("Fetch and Watch Email")
def fetch_and_watch_tool():
    """بيفتح الايميل من ادارة النتائج فقط، وينزل الملف في data."""
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
        return "يوجد جديد في data"
    return "لا يوجد ملف جديد"

@tool("Check Digital Gate 1")
def check_digital_tool():
    """البوابة 1: الملف رقمي ولا صورة؟ - يتم فحص كل الملفات، يتم تخطي المصور يسجل كخطأ في التقرير، وتكمل الباقي"""
    pdfs = find_all_pdfs()
    if not pdfs:
        return "لا يوجد ملف"
    results = []
    for pdf in pdfs:
        doc = fitz.open(pdf)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        if len(text.strip()) < 50:
            add_issue("SCANNED PDF", os.path.basename(pdf), "الملف", f"الملف {os.path.basename(pdf)} مصور - تم تخطيه")
            save_issues()
            results.append(f"SKIPPED - {os.path.basename(pdf)} مصور - يتم تخطيه  يسجل كخطأ في التقرير ")
        else:
            results.append(f"Digital OK - {os.path.basename(pdf)}")
    return "\n".join(results)

@tool("Parse Result Sheet to JSON")
def parse_to_json_tool():
    """بعد البوابتين: حول كل الكشوفات التي إجتازت البوابة لـ JSON - الخطأ يتم تخطيه  ويكمل الباقي"""
    pdfs = find_all_pdfs()
    if not pdfs:
        return "لا يوجد ملف"
    students = []
    seen_ids = {}
    duplicate_ids = set()
    for pdf in pdfs:
        # في حال الملف لم يجتاز البوابة، قم بتخطيه فورا - البوابة تقوم بتسجيله في التقرير 
        if not is_gate_passed(pdf):
            continue
        doc = fitz.open(pdf)
        for page in doc:
            words = page.get_text("words")
            rows = {}
            for w in words:
                y = round(w[1] / 5) * 5
                rows.setdefault(y, []).append(w)
            for y in sorted(rows):
                line = " ".join([w[4] for w in sorted(rows[y], key=lambda x: x[0])]).strip()
                if not line or "Result" in line or "Student" in line:
                    continue
                if line.lower() in ["name", "gpa", "id", "الاسم", "الرقم", "الجامعي", "المعدل", "النتيجة"]:
                    continue
                m = re.search(r"(\d{7,8})", line)
                if not m:
                    arabic_tmp = re.findall(r"[\u0600-\u06FF]+", line)
                    arabic_tmp = [w for w in arabic_tmp if w not in ["الاسم", "الرقم", "الجامعي", "المعدل", "النتيجة"]]
                    english_tmp = re.findall(r"[A-Za-z]{3,}", line)
                    english_tmp = [w for w in english_tmp if w.lower() not in ["name", "student", "gpa", "result", "class"]]
                    tmp_name = " ".join(arabic_tmp) if arabic_tmp else " ".join(english_tmp[:2])
                    if len(tmp_name.split()) >= 2:
                        add_issue("MISSING FIELD", os.path.basename(pdf), "الرقم الجامعي", f"الطالب {tmp_name} بدون رقم جامعي في الملف {os.path.basename(pdf)}")
                        save_issues()
                    continue
                sid = m.group(1)
                arabic = re.findall(r"[\u0600-\u06FF]+", line)
                arabic = [w for w in arabic if w not in ["الاسم", "الرقم", "الجامعي", "المعدل", "النتيجة"]]
                english = re.findall(r"[A-Za-z]{3,}", line)
                english = [w for w in english if w.lower() not in ["name", "student", "gpa", "result", "class"]]
                name = " ".join(arabic) if arabic else " ".join(english[:2])
                if len(name.split()) < 2:
                    add_issue("MISSING FIELD", os.path.basename(pdf), "الاسم", f"الطالب برقم {sid} بدون اسم في الملف {os.path.basename(pdf)} - تم تخطيه")
                    save_issues()
                    continue
                if sid in duplicate_ids:
                    continue
                if sid in seen_ids:
                    add_issue("DUPLICATE ID", os.path.basename(pdf), "الرقم الجامعي", f"الرقم {sid} مكرر داخل الملف - {seen_ids[sid]} و {name} - الاتنين ما حيطلع ليهم شهادة")
                    save_issues()
                    students = [s for s in students if s["student_id"] != sid]
                    del seen_ids[sid]
                    duplicate_ids.add(sid)
                    continue
                gpa_m = re.search(r"([0-4])\.(\d{1,2})", line)
                if not gpa_m:
                    if "ABC" in line:
                        add_issue("BAD GPA", os.path.basename(pdf), "المعدل", f"الطالب {name} معدله ABC وليس رقما")
                    else:
                        add_issue("MISSING FIELD", os.path.basename(pdf), "المعدل", f"الطالب {name} ({sid}) بدون معدل")
                    save_issues()
                    continue
                gpa = float(f"{gpa_m.group(1)}.{gpa_m.group(2)}")
                gpa_str = f"{gpa:.2f}"
                if gpa < 1.0 or gpa > 4.0:
                    add_issue("BAD GPA", os.path.basename(pdf), "المعدل", f"الطالب {name} معدله {gpa_str} أكبر من 4.0")
                    save_issues()
                    continue
                seen_ids[sid] = name
                if any(s["student_id"] == sid for s in students):
                    continue
                students.append({
                    "student_name": name,
                    "student_id": sid,
                    "gpa": gpa,
                    "gpa_str": gpa_str,
                    "raw_class": ""
                })
    os.makedirs("data", exist_ok=True)
    with open(PARSED_FILE, "w", encoding="utf-8") as f:
        json.dump(students, f, ensure_ascii=False, indent=2)
    if len(students) == 0:
        add_issue("NO STUDENTS", "all files", "الملف", "لم يوجد أي طالب سليم في الملفات التي تجاوزت البوابة")
        save_issues()
    return f"تم تحويل {len(students)} طالب لـ JSON"

@tool("Check Hash Gate 2")
def check_hash_tool():
    """البوابة 2: الهاش مطابق ام لا؟ - بتفحص كل الملفات، تتجاهل الخطأ وتقوم بتسجليه في التقرير، وتكمل الباقي"""
    pdfs = find_all_pdfs()
    if not pdfs:
        return "لا يوجد ملف"
    results = []
    for pdf in pdfs:
        fname = os.path.basename(pdf)
        p = Path(pdf)
        hash_file = str(p.with_name(p.stem + "_hash.txt"))
        if not os.path.exists(hash_file):
            add_issue("MISSING HASH", fname, "الهاش", f"الملف {fname} بدون هاش - تم تخطيه")
            save_issues()
            results.append(f"SKIPPED - {fname} بدون هاش - يتم تخطيه  يسجل كخطأ في التقرير ")
            continue
        with open(pdf, "rb") as f:
            real = hashlib.sha256(f.read()).hexdigest()
        with open(hash_file, "r") as f:
            expected = f.read().strip().lower()
        if real != expected:
            add_issue("HASH MISMATCH", fname, "الهاش", f"الملف {fname} هاشه غير مطابق - تم تخطيه")
            save_issues()
            results.append(f"SKIPPED - {fname}  هاش خطأ - يتم تخطيه  يسجل كخطأ في التقرير")
            continue
        results.append(f"Hash MATCHED - {fname}")
    return "\n".join(results)

@tool("Verify Self Correction")
def verify_self_correct_tool():
    """التصحيح الذاتي: GPA vs التقدير."""
    with open(PARSED_FILE, "r", encoding="utf-8") as f:
        students = json.load(f)
    corrected = []
    for s in students:
        gpa = float(s["gpa"])
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
    """طبقة الأمان الأخيرة: رقم مكرر + حقل فارغ + بوابة Verified. قالب شهاده من template.html - تكمل العمل في حال ملف واحد على الأقل تجاوز البوابة"""
    pdfs = find_all_pdfs()
    passed = [p for p in pdfs if is_gate_passed(p)]
    if not passed:
        return "BLOCKED: لا يوجد ملف تجاوز البوابة - ممنوع إصدار شهادات"

    if not os.path.exists(VERIFIED_FILE):
        if not os.path.exists(PARSED_FILE):
            return "BLOCKED: لا يوجد verified.json ولا parsed.json - الـ Verifier لم يعمل"
        with open(PARSED_FILE, "r", encoding="utf-8") as f:
            students = json.load(f)
        for s in students:
            gpa = float(s["gpa"])
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
        gpa = s.get("gpa_str") or s.get("gpa") or ""
        try:
            gpa = f"{float(gpa):.2f}"
        except Exception:
            pass
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
    return f"تم تجهيز {count} شهادة في output من template.html -تم توقف"

# ============================================================
# 1. AGENTS (5) - Each agent has ONLY its own tools, it cannot see the other tools
# ============================================================

agent1_network = Agent(
    role="Network Checker",
    goal="Check internet connection only",
    backstory="You only check internet, you never touch student data.",
    tools=[check_internet_tool],
    allow_delegation=False,
    llm=local_llm,
    verbose=True
)

agent2_watcher = Agent(
    role="Email Watcher",
    goal="Watch data/ folder and fetch email only from results@university.edu",
    backstory="You only fetch from the official university email.",
    tools=[fetch_and_watch_tool],
    allow_delegation=False,
    llm=local_llm,
    verbose=True
)

agent3_parser = Agent(
    role="Gatekeeper Parser",
    goal="Check if PDF is digital AND check SHA-256 Hash for all PDFs. Skip bad file only, log it, continue with others.",
    backstory="You are the security gate. You check digital first, then hash, for every file. If a file fails, you skip that file only, log it, and continue.",
    tools=[check_digital_tool, check_hash_tool],
    allow_delegation=False,
    llm=local_llm,
    verbose=True
)

agent4_verifier = Agent(
    role="Verifier and Corrector",
    goal="Convert PDF to JSON ONLY if hash matched, then do self-correction from GPA.",
    backstory="You only work after the gate passed. You convert to JSON and fix degree classification.",
    tools=[parse_to_json_tool, verify_self_correct_tool],
    allow_delegation=False,
     llm=local_llm,
    verbose=True
)

agent5_render = Agent(
    role="Certificate Renderer",
    goal="Render final certificates safely, check duplicates and empty fields",
    backstory="You are the final layer. You never invent names.",
    tools=[render_cert_tool],
    allow_delegation=False,
    llm=local_llm,
    verbose=True
)

# ============================================================
# 4. TASKS (7)
# ============================================================

task1 = Task(
    description="Use check_internet_tool ONLY. If internet is OK, write exactly: 'Internet OK - Watcher go check email'. If no internet, write exactly: 'No Internet - Watcher continue locally from data/'",
    expected_output="One clear message for Watcher: Internet OK OR No Internet",
    agent=agent1_network
)

task2 = Task(
    description="Read message from Task 1 first. If it says Internet OK, use fetch_and_watch_tool to try to fetch from results@university.edu. If email fetch fails, or cannot reach email, or cannot open email, or any email error, do NOT stop, do NOT return error, immediately fallback and use same tool to work locally from data/ folder. If it says No Internet, use same tool to work locally from data/ folder directly. Always finish with local data if email fails. Return tool output only. Do NOT invent emails.",
    expected_output="Tool output only: list of PDFs found and their source (email if success, local data/ if email failed or no internet), plus message: 'Watcher done - Gatekeeper check digital now'",
    agent=agent2_watcher,
    context=[task1]
)

task3 = Task(
    description="Read Task 2 output first. Use check_digital_tool ONLY. It checks ALL PDFs in data/. If a PDF is scanned/image, write: 'SKIPPED - Scanned PDF - Skip this file only, continue to next file'. If digital, write: 'Digital OK'. Do NOT stop the whole crew. Do NOT call any other tool.",
    expected_output="For each PDF: Digital OK OR SKIPPED - Scanned. Plus message: 'Digital done - Parser check hash now'",
    agent=agent3_parser,
    context=[task2]
)

task4 = Task(
    description="Read Task 3 output first. Use check_hash_tool ONLY. It checks ALL PDFs in data/. If hash matches, write: 'Hash MATCHED - Verifier parse now'. If not matches or no hash file, write: 'SKIPPED - Hash Mismatch - Skip this file only, continue to next file'. Do NOT stop the whole crew. Do NOT call digital tool again.",
    expected_output="For each PDF: Hash MATCHED OR SKIPPED - Hash Mismatch. Plus message: 'Hash done - Verifier parse now'",
    agent=agent3_parser,
    context=[task3]
)

task5 = Task(
    description="Read Task 4 output first. ONLY for PDFs with Hash MATCHED, use parse_to_json_tool ONLY. Convert PDF to JSON. Do NOT call hash or digital tools. If a PDF was SKIPPED, skip that PDF only and continue with the others. Do NOT stop.",
    expected_output="JSON data for matched PDFs only. Plus message: 'Parse done - Verifier self-correct now'",
    agent=agent4_verifier,
    context=[task4]
)

task6 = Task(
    description="Read Task 5 output first. Use verify_self_correct_tool ONLY. Recalculate degree classification from GPA in JSON. If classification is wrong, fix it. If GPA missing, write: 'BLOCKED - GPA Missing'. Do NOT call parse tool again.",
    expected_output="Corrected JSON with correct degree classification. Plus message: 'Verify done - Renderer render now'",
    agent=agent4_verifier,
    context=[task5]
)

task7 = Task(
    description="Read Task 6 output first. Use render_cert_tool ONLY. Return the tool output EXACTLY as it is. Do NOT write any HTML yourself. Do NOT invent John Doe, Jane Smith, or any names. Do NOT add example certificates. If tool says BLOCKED, return BLOCKED only.",
    expected_output="Tool output only, exactly as returned by render_cert_tool. No HTML, no invented names.",
    agent=agent5_render,
    context=[task6]
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

def make_report_pdf(issues):
    os.makedirs("output", exist_ok=True)
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 60
    page.insert_text((50, y), "Issues Report - COSC726", fontsize=20)
    y += 30
    from datetime import datetime as dt
    page.insert_text((50, y), f"Date: {dt.now().strftime('%Y-%m-%d %H:%M')}", fontsize=12)
    y += 25
    page.insert_text((50, y), f"Total Issues: {len(issues)}", fontsize=14)
    y += 30
    for i, iss in enumerate(issues, 1):
        if y > 730:
            page = doc.new_page(width=595, height=842)
            y = 60
        page.insert_text((50, y), f"{i}. {iss['type']} - {iss['file']}", fontsize=12)
        y += 18
        page.insert_text((70, y), f"Field: {iss['field']}", fontsize=11)
        y += 18
        page.insert_text((70, y), iss['desc'][:110], fontsize=11)
        y += 28
    doc.save(REPORT_PDF)
    doc.close()
    print(f"  تم تنزيل ورقة التقرير: {REPORT_PDF}")
    try:
        os.startfile(REPORT_PDF)
    except Exception:
        pass

def show_skip_window():
    issues = ISSUES
    if not issues and os.path.exists(ISSUES_FILE):
        with open(ISSUES_FILE, "r", encoding="utf-8") as f:
            issues = json.load(f)
    print(f"\n[البوابة البشرية ] الكود اكتشف {len(issues)} خطأ...")
    for i, iss in enumerate(issues, 1):
        print(f"  {i}. {iss['type']} | {iss['file']} | {iss['desc']}")
    try:
        import tkinter as tk
    except Exception:
        make_report_pdf(issues)
        return
    root = tk.Tk()
    root.title("تقرير الأخطاء - اضغط تخطي")
    root.geometry("620x520")
    root.attributes("-topmost", True)
    tk.Label(root, text=f"تم اكتشاف {len(issues)} أخطاء", font=("Segoe UI", 16, "bold")).pack(pady=12)
    tk.Label(root, text="اضغط تخطي لتنزيل ورقة التقرير PDF", font=("Segoe UI", 11), fg="gray").pack()
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, padx=16, pady=12)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    listbox = tk.Listbox(frame, font=("Segoe UI", 10), yscrollcommand=scrollbar.set, height=14)
    for i, iss in enumerate(issues, 1):
        listbox.insert("end", f"{i}. {iss['type']} - {iss['file']}")
        listbox.insert("end", f"   {iss['desc']}")
        listbox.insert("end", "")
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)
    def on_skip():
        make_report_pdf(issues)
        root.destroy()
    tk.Button(root, text="تخطي - تنزيل ورقة التقرير PDF", font=("Segoe UI", 14, "bold"), bg="#ff9800", fg="white", padx=20, pady=14, command=on_skip).pack(pady=12, padx=16, fill="x")
    root.mainloop()

if __name__ == "__main__":
    print("=== 5 Agents شغالين ===")
    print(crew.kickoff())
    save_issues()
    show_skip_window()
    print("=== تم - وقف في output ===")
