## Privacy-Preserving Local Agentic AI System for University Degree Certificate Generation

## 1. What it does
The manual process of issuing official university degree certificates is labor-intensive, time-consuming, and susceptible to human error. Furthermore, processing sensitive student records via external cloud-based AI models presents data privacy and sovereignty concerns.

This project proposes a fully local, privacy-preserving agentic system designed to automate the academic degree generation workflow. Built upon the CrewAI multi-agent orchestration framework and powered locally by Qwen 2.5 via Ollama, the system functions as a virtual administrative agent. It autonomously ingests result PDFs, dynamically parses and validates student academic records, renders standardized high-resolution PDF certificates, and logs output data locally without external API dependencies.


## 2. Prerequisites
- **Python:** 3.10 or higher (tested on 3.10, 3.11, 3.12)
- **OS:** Windows 10/11, macOS, or Linux
- **Model Runtime:** Ollama locally. No cloud API key is required for the default mode.
- **Model:** `qwen2.5:7b` - download size ~4.7 GB, download time 5-15 minutes depending on internet speed. Disk space required: 6 GB free.
- **Git:** installed

## 3. Install
Copy and paste these commands in order in a new clean folder:

```bash
git clone https://github.com/YOUR-USERNAME/degree-generation-agent.git
cd degree-generation-agent
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:7b
ollama serve
```

Keep `ollama serve` running in a separate terminal.

## 4. Configure
Copy the example env file:

```bash
cp .env.example .env
# Windows PowerShell:
# Copy-Item .env.example .env
```

Open `.env` and check these two variables. They are the ONLY two variables that switch the model provider:

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
OPENAI_API_KEY = "ollama"
# A dummy key is set because the `CrewAI` framework requires the `OPENAI_API_KEY` environment variable to initialize, even when using a fully local model.
```
**A dummy key is set because the `CrewAI` framework requires the `OPENAI_API_KEY` environment variable to initialize, even when using a fully local model.**

Other variables in `.env`:
```env
TRUSTED_SENDER=results@university.edu
IMAP_SERVER=imap.gmail.com
EMAIL_USER=project_email@gmail.com
EMAIL_PASS=your_app_password

```

If you leave `LLM_PROVIDER=ollama`, no API key is needed.

## 5. Run
One command only to start the system:

```bash
python main.py
```

**What you should see on success:**
```
[1/5] Network Checker: Internet OK
[2/5] Email Watcher: Found results.pdf in data/input/
[3/5] Gatekeeper: PDF is text-based, SHA-256 MATCHED
[4/5] Verifier: students parsed, classifications corrected
[5/5] Renderer:  certificates generated in output/certificates/
DONE - Cost: $0.00
```
If you see `SHA-256 MISMATCH - STOPPED`, the system correctly blocked issuance. Do not continue.

## 6. Test
One command to run the full test suite:

```bash
python -m pytest tests/ -v
```

**Expected result:**
```
8 passed in 60-120s
```

The tests do **NOT** require API keys and do **NOT** require internet. They run fully offline using the local Ollama model and local test files in `tests/fixtures/`.

## 7. A Worked Example
**Input - Put these 2 files in `data/input/`:**
1. `results.pdf` - Text-based PDF with this exact content:
```
ID: 2021001, Name: Ahmed Ali, GPA: 3.72
ID: 2021002, Name: Sara Mohamed, GPA: 2.85
```
2. `results.pdf.sha256` - Text file containing the SHA-256 hash of `results.pdf`

**Run:**
```bash
python main.py
```

**Expected Output:**
- `data/verified.json`:
```json
[
  {"id": "2021001", "name": "Ahmed Ali", "gpa": 3.72, "class": "First Class"},
  {"id": "2021002", "name": "Sara Mohamed", "gpa": 2.85, "class": "Second Lower"}
]
```
- `output/certificates/2021001_Ahmed_Ali.pdf` - Certificate says: First Class
- `output/certificates/2021002_Sara_Mohamed.pdf` - Certificate says: Second Lower

If you get `First Class` for 3.72 and `Second Lower` for 2.85, the run is CORRECT. If you get any other class, the run is BROKEN.

## 8. Reproduce the Evaluation
Run the evaluation suite:

```bash
python evaluate.py
```

**Numbers that must print on screen and must match the report:**
```
=============================================
EVALUATION RESULTS
=============================================
Correctly Accepted (TP): 5
Correctly Blocked (TN): 7
False Accepted (FP): 0
False Rejected (FN): 0
Certificates: 5
---------------------------------------------
Blocked by Type:
  SCANNED PDF: 1
  MISSING HASH: 1
  HASH MISMATCH: 1
  DUPLICATE ID: 1
  MISSING FIELD: 3
---------------------------------------------
Blocked by File:
  test_01_scanned.pdf: 1 errors
  test_02_no_hash.pdf: 1 errors
  test_03_wrong_hash.pdf: 1 errors
  test_04_duplicate_missing.pdf: 4 errors
---------------------------------------------
Total: 12 (5 accepted + 7 blocked)
Accuracy: 100%
Precision: 100%
Recall: 100%
Hallucination: 0%
=============================================

```

If any line shows `FAIL`, your environment is not matching the report.

## 9. The Approval Gate
**The Security Gate with Human Gate**

**Location:** In `main.py`, inside `run_pipeline()`, after reading the files and before certificate generation. The Renderer **cannot** run without passing both the Security Gate and the Human Gate.

The system uses two gates:

### 1. Security Gate - Automatic Check

The system automatically checks every file:

**Gate 1 - File Type Check:**
If the file is a scanned PDF, it is blocked.

**Gate 2 - Hash Check:**
The `SHA-256` hash is calculated and compared with the provided hash.
- If the hash is missing, the file is blocked.
- If the hash does not match, the file is blocked.

### 2. Human Gate - Staff Review

The Security Gate does not delete rejected files. It converts them into a review task for staff.

All rejected files are collected in `issues_report.pdf` with:
- File name
- Error type
- Required action

**What the human reviewer does:**
1. Opens `issues_report.pdf`.
2. Reviews each rejected file and its reason.
3. Decides the action: fix and resubmit, or confirm rejection.
4. Approves the valid files to proceed to certificate generation.

No certificate is generated for a rejected file unless staff fixes it and resubmits it through the gate again.

**In short:** The machine detects the error, the human makes the decision.

## 10. Repository Map

- `main.py` - Main entry point, runs the 5 agents and 7 tasks, contains the security gate and certificate generation.
- `config.py` - Configures the local model `qwen2.5:7b` via `Ollama`.
- `create_data.py` - Creates test data, 12 cases.
- `test_system.py` - Automated test suite with 9 tests.
- `evaluation.py` - Calculates `Accuracy, Precision, Recall, Hallucination` metrics.
- `data/` - Input folder for result sheet `PDF` files.
- `output/` - Final certificates and `issues_report.pdf` are saved here.
- `template.html` - Certificate template.
- `requirements.txt` - Python dependencies.

## 11. Limitations

- **No OCR:** Scanned PDFs are blocked by Gate 1 and cannot be processed.
- **Single layout:** Parser expects `ID, Name, GPA` in one line.
- **Classification correction:** Degree classification is corrected from GPA only, not from any other source.
- **No digital signature:** Certificates are PDFs without cryptographic signature.
- **Local model only:** `Qwen 2.5 7B` is slower and less accurate than large cloud models. It requires at least 8 GB of RAM.
- **Local storage only:** The system generates certificates and saves them in the `output/` folder only. It does not send them by email.
