# COSC726 - Agentic Certificate Issuance System

Privacy-Preserving Local Agentic AI System for University Degree Certificate Generation - Al-Neelain University - COSC726

## Overview
This project implements an Agentic AI system using CrewAI with **5 autonomous agents and 7 sequential tasks** to automate certificate issuance locally.

Flow: Internet -> Email -> Gate 1 Digital -> Gate 2 Hash -> JSON -> Self-Correction -> Certificate in output

All reasoning is done locally with Ollama `qwen2.5:7b`. No student data is sent to external cloud APIs. Agents are forbidden from inventing any student names - all data comes only from tools reading the real PDF.

## Agents (5) and Tasks (7)

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
