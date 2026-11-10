# COSC726 - Agentic Certificate Issuance System

Privacy-Preserving Local Agentic AI System for University Degree Certificate Generation - Al-Neelain University - COSC726

## Overview

## 🎯 Project Idea
An intelligent system that uses 5 Agents to issue university certificates securely and without forgery.

The system works in order: **Internet Check -> [Yes: Try Email -> Download to data/ OR Email Failed -> Go to data/ | No: Go to data/ Directly] -> Gates -> Conversion -> Correction -> Rendering**

---
All reasoning is done locally with Ollama `qwen2.5:7b`. No student data is sent to external cloud APIs. Agents are forbidden from inventing any student names - all data comes only from tools reading the real PDF.


### 1. Network Agent - Task 1
**Role:** Checks internet connection only.
- **Task 1:** Check internet connection using `check_internet_tool` ONLY.
- If internet is OK, write exactly: `Internet OK - Watcher go check email`.
- If no internet, write exactly: `No Internet - Watcher continue locally from data/`.
- It does NOT stop the system if there is no internet, it sends the Watcher to local mode.

### 2. Watcher Agent - Task 2
**Role:** Tries email first, falls back to local `data/` folder if email fails.
- **Task 2:** Read message from Task 1 first.
- If it says `Internet OK`, use `fetch_and_watch_tool` to try to fetch from `results@university.edu`.
- If email fetch fails, or cannot reach email, or cannot open email, or any email error, do NOT stop, do NOT return error, immediately fallback and use same tool to work locally from `data/` folder.
- If it says `No Internet`, use same tool to work locally from `data/` folder directly.
- It does not accept email from any other sender.
- It does NOT invent emails. Always finishes with local data if email fails.

### 3. Parser Agent (Gatekeeper) - Task 3 + Task 4
**Role:** The security gatekeeper, works twice in a row.
- **Task 3 - Gate 1:** Checks if the PDF is a real digital PDF, or a scanned image. If it is an image, it rejects it.
- **Task 4 - Gate 2:** Checks the SHA-256 Hash **FIRST**. If the hash mismatches or no hash file exists, it STOPS everything and blocks issuance. **No JSON conversion happens before this step.**

### 4. Verifier Agent - Task 5 + Task 6
**Role:** Works only after the gate passes, works twice in a row.
- **Task 5:** **ONLY** if the hash matches, it converts the real PDF to `data/parsed.json`.
- **Task 6 - Self-Correction:** Fixes the Degree Classification from the GPA. For example, if GPA is 3.8 and the classification is wrong, it corrects it to First Class.

### 5. Render Agent - Task 7
**Role:** Final security layer and rendering.
- **Task 7:** Checks the hash again, blocks duplicate University IDs, blocks empty fields, then renders the certificate from `template.html` to `output/`.

---

## 🔒 Why This Order Matters

1. **Security First:** No JSON conversion before the hash matches.
2. **Each Agent With Its Tasks:** Parser does the Gates (3+4), and Verifier does the Processing (5+6). No going back.
3. **Anti-Forgery:** Any change in the PDF makes the hash fail, so no certificate is issued.
4. **No Hallucination:** Agents are forbidden from writing names from memory. They must use Tools only.
5. **Resilient Fallback:** If internet is OK but email cannot be reached, the system does NOT fail, it automatically continues offline from `data/` folder.

---

## 📁 Project Files
- `main.py` -> Contains the 5 Agents and 7 Tasks
- `config.py` -> Contains the Tools and Functions (The Gates)
- `create_data.py` -> Creates a sample PDF + hash file
- `template.html` -> Certificate template
- `data/` -> PDF and hash files are placed here
- `output/` -> Final certificates are generated here

## ▶️ How to Run
```bash
pip install -r requirements.txt
python create_data.py
python main.py
@@@@
This project implements an Agentic AI system using CrewAI with **5 autonomous agents and 7 sequential tasks** to automate certificate issuance locally.

Flow: Internet -> Email -> Gate 1 Digital -> Gate 2 Hash -> JSON -> Self-Correction -> Certificate in output

All reasoning is done locally with Ollama `qwen2.5:7b`. No student data is sent to external cloud APIs. Agents are forbidden from inventing any student names - all data comes only from tools reading the real PDF.

## Agents (5) and Tasks (7)
## Agents (5) and Tasks (7) - In Correct Order

1.  **Task 1 - Network Agent:** Checks internet connection only.
2.  **Task 2 - Watcher Agent:** Watches `data/` and fetches email only from `results@university.edu`.
3.  **Task 3 - Parser Agent (Gate 1):** Checks if PDF is digital (not scanned image).
4.  **Task 4 - Verifier Agent (Gate 2):** Checks SHA-256 Hash FIRST. If hash mismatches or no hash file, STOPS and blocks everything. No JSON conversion happens before this.
5.  **Task 5 - Parser Agent:** ONLY if Hash matches, converts the real PDF to `data/parsed.json`.
6.  **Task 6 - Verifier Agent:** Self-Correction - fixes degree classification from GPA.
7.  **Task 7 - Render Agent:** Final security layer - checks duplicates, empty fields, and Hash again. Renders certificates from `template.html` to `output/`.
//
1.  **Network Agent (Task 1):** Checks internet connection only via tool. Does not download any file by itself.
2.  **Watcher Agent (Task 2):** Watches `data/` folder and fetches email only from trusted sender `results@university.edu`. Downloads PDF + Hash to `data/`.
3.  **Parser Agent (Task 3 + Task 5):** Gate 1 - Checks if PDF is digital (not scanned image). Then parses the real PDF to `data/parsed.json`.
4.  **Verifier Agent (Task 4 + Task 6):** Gate 2 - Checks SHA-256 Hash. If no hash file or hash mismatches, STOPS and blocks issuance. Then does Self-Correction: fixes degree classification from GPA.
5.  **Render Agent (Task 7):** Final security layer - checks duplicate IDs, empty fields, Verified flag, and Hash again. Renders certificates from `template.html` to `output/` using WeasyPrint.

## Security Gates
- **Gate 1 - Digital Gate:** Rejects scanned image PDFs.
- **Gate 2 - Hash Gate:** SHA-256 must match `*_hash.txt`. No hash = No certificates.
- **Self-Correction:** GPA >= 3.5 = First Class, >= 3.0 = Second Upper, >= 2.5 = Second Lower, else Third Class.
- **Anti-Hallucination:** Agents must call tools only. No invented names.
- **Anti-Duplicate:** `issued_ids.json` prevents re-issuing same student_id.

## Project Structure
