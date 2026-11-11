# test_system.py - الاختبارات النهائية
# تعمل دون API Key ودون إنترنت ودون Ollama ودون تشغيل main.py داخل الاختبار
# التشغيل:
#   python create_data.py
#   python main.py
#   pytest test_system.py -v
import json
import os
import glob
import pytest

# ---------- ملفات حقيقية ----------

@pytest.fixture
def issues():
    path = "data/issues.json"
    assert os.path.exists(path), "لا يوجد data/issues.json - شغّل python create_data.py ثم python main.py أولاً"
    with open(path, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def verified():
    path = "data/verified.json"
    assert os.path.exists(path), "لا يوجد data/verified.json - شغّل python main.py أولاً"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            return data.get("students", data.get("verified", []))
        return data

@pytest.fixture
def certs():
    return glob.glob("output/*_certificate.pdf") + glob.glob("output/*_certificate.html")

# ---------- T_E1 الملف السليم - 5 طلاب ----------

def test_T_E1_clean_pdf_10_from_create_data(verified, certs):
    assert len(verified) == 5, f"المتوقع 5 طلاب، الظاهر {len(verified)}"
    assert len(certs) == 5, f"المتوقع 5 شهادات، الظاهر {len(certs)}"

# ---------- T_E2 الملف المصوّر محظور ----------

def test_T_E2_scanned_pdf_blocked(issues):
    assert any(i["type"] == "SCANNED PDF" for i in issues), "الملف المصوّر لم يُحظر"

# ---------- T_E3 عدم تطابق الهاش محظور ----------

def test_T_E3_hash_mismatch_blocked(issues):
    assert any(i["type"] == "HASH MISMATCH" for i in issues), "لم يُسجَّل HASH MISMATCH"

# ---------- T_E4 غياب الهاش محظور ----------

def test_T_E4_missing_hash_blocked(issues):
    assert any(i["type"] == "MISSING HASH" for i in issues), "لم يُسجَّل MISSING HASH"

# ---------- T_E5 الرقم المكرر محظور ----------

def test_T_E5_duplicate_run_blocked(issues, verified, certs):
    assert any(i["type"] == "DUPLICATE ID" for i in issues), "لم يُسجَّل DUPLICATE ID"
    ids = [s.get("student_id") for s in verified]
    assert len(ids) == len(set(ids)), f"رقم مكرر في verified: {ids}"
    assert not any("Huda" in (s.get("student_name") or "") for s in verified), "Huda بدون رقم دخلت verified"
    assert not any("2021009" in c for c in certs), "المكرر 2021009 صدرت له شهادة"

# ---------- T_E6 تصحيح البوابة ----------

def test_T_E6_gate_correction_from_create_data(verified):
    for s in verified:
        gpa = float(s["gpa"])
        if gpa >= 3.5:
            exp = "First Class"
        elif gpa >= 3.0:
            exp = "Second Upper"
        elif gpa >= 2.5:
            exp = "Second Lower"
        else:
            exp = "Third Class"
        assert s.get("degree_classification") == exp, \
            f"{s.get('student_name')} معدله {gpa} وتقديره يجب أن يكون {exp} لا {s.get('degree_classification')}"
        gpa_str = s.get("gpa_str") or str(s.get("gpa"))
        assert "." in gpa_str and len(gpa_str.split(".")[1]) == 2, \
            f"معدل {s.get('student_name')} يجب أن يكون 3.10 لا {gpa_str}"

# ---------- T_E7 ملف فارغ محظور ودون هلوسة ----------

def test_T_E7_empty_pdf_blocked_no_hallucination(verified, issues):
    all_text = json.dumps(verified, ensure_ascii=False) + json.dumps(issues, ensure_ascii=False)
    assert "John Doe" not in all_text, "اسم مخترع: John Doe"
    assert "Jane Smith" not in all_text, "اسم مخترع: Jane Smith"
    assert len(verified) <= 5, "طلاب زائدون مخترعون"

# ---------- T_E8 توليد الشهادة وحفظها في output ----------

def test_T_E8_certificates_saved_to_output(certs):
    # 5 شهادات محفوظة في output 
    assert len(certs) == 5, f"لم تُولَّد كل الشهادات، الظاهر {len(certs)}"
    assert os.path.exists("output"), "مجلد output غير موجود"
    for c in certs:
        assert os.path.exists(c), f"الشهادة غير محفوظة في output: {c}"

# ---------- البوابة ----------

def test_gate_blocks_before_crew(issues):
    assert len(issues) > 0, "البوابة لم تحظر أي ملف"