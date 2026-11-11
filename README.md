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

## 5. Run

One command only to start the system:


```bash
python main.py
```

**What you should see on success:**

```
What you will see on success:

=== 5 Agents شغالين ===
Crew: crew
├── Task: Network Checker - Used Check Internet
├── Task: Email Watcher - Used Fetch and Watch Email
├── Task: Gatekeeper Parser - Used Check Digital Gate 1
├── Task: Gatekeeper Parser - Used Check Hash Gate 2
├── Task: Verifier and Corrector - Used Parse Result Sheet to JSON
├── Task: Verifier and Corrector - Used Verify Self Correction
└── Task: Certificate Renderer - Used Render Certified Output

Then the Skip window appears to show the error report.
Then at the end you will see:
=== تم - وقف في output ===

```
**Important note:
If the hash of one file does not match, the system skips that file only and continues with the other files.
The system stops completely only if no file passes the gate.**


## 6. Test
One command to run the full test suite:

```bash
pytest test_system.py -v
```

**Expected result:**
```
================================================= test session starts =================================================

collected 9 items

test_system.py::test_T_E1_valid_5_from_test_04 PASSED                                                            [ 11%]
test_system.py::test_T_E2_scanned_pdf_blocked PASSED                                                             [ 22%]
test_system.py::test_T_E3_hash_mismatch_blocked PASSED                                                           [ 33%]
test_system.py::test_T_E4_missing_hash_blocked PASSED                                                            [ 44%]
test_system.py::test_T_E5_duplicate_run_blocked PASSED                                                           [ 55%]
test_system.py::test_T_E6_gate_correction_from_create_data PASSED                                                [ 66%]
test_system.py::test_T_E7_empty_pdf_blocked_no_hallucination PASSED                                              [ 77%]
test_system.py::test_T_E8_certificates_saved_to_output PASSED                                                    [ 88%]
test_system.py::test_gate_blocks_before_crew PASSED                                                              [100%]

================================================== 9 passed in 0.05s ==================================================
```

The tests do **NOT** require API keys and do **NOT** require internet. They run fully offline using the local Ollama model and local test files in `tests/fixtures/`.

## 7. A Worked Example

**Step 1 - Generate the inputs:**

```bash
python create_data.py
```

This creates 4 test files in `data/`:
1. `test_01_scanned.pdf` - Scanned / image-only file, with a correct hash
2. `test_02_no_hash.pdf` - Valid file, but with no hash file
3. `test_03_wrong_hash.pdf` - Valid file, but with an intentionally wrong hash
4. `test_04_duplicate_missing.pdf` - File with 10 students, including:
   - One duplicate ID: `2021004`, once as Ali Yousif and once as Mohamed Osman
   - Three students with missing values: `2021006` with no GPA, `2021007` with no name, and Huda Ibrahim with no student ID
   - Five valid students: `2021001`, `2021002`, `2021003`, `2021005`, and `2021008`

**Step 2 - Run the system:**

```bash
python main.py
```

**Expected Output - 5 files:**

1. `data/parsed.json` - Data extracted from the PDFs before correction
2. `data/verified.json` - Data after correcting the class from the GPA, for example:
```json
[
  {"id": "2021001", "name": "Ahmed Ali", "gpa": 3.72, "class": "First Class"}
]
```
3. `data/issued.json` - Record of certificates actually issued, 5 certificates only
4. `output/issues_report.pdf` - Report of rejected files, with 7 blocked cases
5. `output/certificates/` - 5 certificates only, for the valid students from `test_04`

**How to judge the run:**

| Result | Verdict |
| --- | --- |
| Accepted: 5 certificates, Blocked: 7 cases, and no certificate from `test_01`, `test_02`, or `test_03` | CORRECT run |
| Any certificate issued for a scanned, no-hash, or wrong-hash file, or any certificate issued for a duplicate / incomplete student | BROKEN run |


## 8. Reproduce the Evaluation
Run the evaluation suite:

```bash
python evaluation.py
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

## 10.Repository Map
 
- `main.py` -> Contains the 5 Agents and 7 Tasks, Tools and Functions (The Gates)
- `config.py` -> Contains ONLY the connection / linking to Ollama qwen2.5:7b (Local LLM setup)
- `create_data.py` -> Creates a sample PDF + hash file.
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
