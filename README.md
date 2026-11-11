# Privacy-Preserving Local Agentic AI System for University Degree Certificate Generation

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
```

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
Total Tests: 8
Passed: 8
Failed: 0
Clean PDF: PASS
Scanned PDF Blocked: PASS
Hash Mismatch Blocked: PASS
Missing Hash Blocked: PASS
Duplicate Blocked: PASS
Wrong Classification Corrected: PASS
Empty PDF Blocked: PASS
Email Failure Fallback: PASS
Latency for 10 students: 60-120 seconds
Total Cost: $0.00

```

If any line shows `FAIL`, your environment is not matching the report.

## 9. The Approval Gate
**Location of the consequential action:** In `main.py`, function `run_pipeline()` after Verifier and before Renderer. The Renderer **cannot** run without approval.

**How to activate it:**
The gate is ON by default. You do not need to enable it.

**What the human reviewer sees:**
1. The terminal pauses and prints: `>>> WAITING FOR HUMAN APPROVAL`
2. Open `data/verified.json` in any text editor. You will see the full list of students, GPAs, and corrected classifications.
3. If correct, type `yes` in the terminal and press Enter. Certificates will be generated.
4. If wrong, type `no`. The system stops and generates NOTHING. No certificate is issued.

No certificate can be generated without typing `yes`.

## 10. Repository Map
- `main.py` - Main entry point, runs the 5 agents in order and contains the approval gate.
- `config.py` - Loads `.env`, selects LLM provider, and defines paths.
- `agents/` - Definitions of the 5 CrewAI agents and their tools.
- `data/input/` - Place input `results.pdf` + `.sha256` file here.
- `data/verified.json` - Human-reviewed intermediate output before rendering.
- `output/certificates/` - Final generated PDF certificates go here.
- `templates/template.html` - Jinja2 HTML template for the certificate design.
- `tests/` - Pytest suite with 8 tests and fixtures.
- `evaluate.py` - Runs the evaluation suite and prints the numbers in Section 8.
- `.env.example` - Template for configuration, copy to `.env`.
- `requirements.txt` - Python dependencies.

## 11. Limitations
- **No OCR:** Scanned / image-only PDFs are blocked by Gate 1 and cannot be processed.
- **Single layout:** Parser expects `ID, Name, GPA` in one line. Different Results Office formats will fail.
- **Arabic names:** Arabic names with extra spaces may be split incorrectly. English names work best.
- **No digital signature:** Certificates are PDFs without cryptographic signature.
- **Local model only:** Qwen 2.5 7B is slower and less accurate than large cloud models. Out-of-memory will occur on machines with less than 8 GB RAM.
- **Email dependency:** If IMAP is blocked and no file is in `data/input/`, the system stops with no output.
