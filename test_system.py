# test_system.py - ملف الاختبارات
# التشغيل بالترتيب:
#   python create_data.py
#   python main.py
#   pytest test_system.py -v
import json
import os
import glob
import pytest

# ---------- تحميل الملفات الحقيقية ----------

@pytest.fixture
def issues():
    # قائمة الملفات المحظورة
    path = "data/issues.json"
    assert os.path.exists(path), "ملف data/issues.json غير موجود - شغل python create_data.py ثم python main.py أولا"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            return data.get("issues", data.get("blocked", []))
        return data

@pytest.fixture
def verified():
    # قائمة الطلاب المقبولين بعد التصحيح
    path = "data/verified.json"
    assert os.path.exists(path), "ملف data/verified.json غير موجود - شغل python main.py أولا"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            return data.get("students", data.get("verified", []))
        return data

@pytest.fixture
def certs():
    # الشهادات محفوظة في مجلد output
    return glob.glob("output/*_certificate.pdf") + glob.glob("output/*_certificate.html")

# ---------- الاختبار الأول: الطلاب المقبولون ----------

def test_T_E1_valid_5_from_test_04(verified, certs):
    # الملف test_04 فيه 10 طلاب، المقبول منهم 5 فقط
    assert len(verified) == 5, f"المتوقع 5 طلاب، الموجود {len(verified)}"
    assert len(certs) == 5, f"المتوقع 5 شهادات، الموجود {len(certs)}"
    expected_ids = {"2021001", "2021002", "2021003", "2021005", "2021008"}
    actual_ids = {str(s.get("student_id")) for s in verified}
    assert actual_ids == expected_ids, f"الطلاب المقبولون يجب أن يكونوا {expected_ids}، الموجود {actual_ids}"

# ---------- الاختبار الثاني: الملف المصور محظور ----------

def test_T_E2_scanned_pdf_blocked(issues):
    assert any(i["type"] == "SCANNED PDF" for i in issues), "الملف المصور test_01 لم يحظر"
    assert any("test_01" in str(i.get("file", "")) for i in issues if i["type"] == "SCANNED PDF"), "الحظر من نوع SCANNED PDF يجب أن يكون من test_01"

# ---------- الاختبار الثالث: الهاش غير المتطابق محظور ----------

def test_T_E3_hash_mismatch_blocked(issues):
    assert any(i["type"] == "HASH MISMATCH" for i in issues), "لم يسجل HASH MISMATCH"
    assert any("test_03" in str(i.get("file", "")) for i in issues if i["type"] == "HASH MISMATCH"), "الحظر من نوع HASH MISMATCH يجب أن يكون من test_03"

# ---------- الاختبار الرابع: غياب الهاش محظور ----------

def test_T_E4_missing_hash_blocked(issues):
    assert any(i["type"] == "MISSING HASH" for i in issues), "لم يسجل MISSING HASH"
    assert any("test_02" in str(i.get("file", "")) for i in issues if i["type"] == "MISSING HASH"), "الحظر من نوع MISSING HASH يجب أن يكون من test_02"

# ---------- الاختبار الخامس: الرقم المكرر محظور ----------

def test_T_E5_duplicate_run_blocked(issues, verified, certs):
    assert any(i["type"] == "DUPLICATE ID" for i in issues), "لم يسجل DUPLICATE ID"
    ids = [str(s.get("student_id")) for s in verified]
    assert len(ids) == len(set(ids)), f"يوجد رقم مكرر في verified: {ids}"
    assert "2021004" not in ids, "الرقم المكرر 2021004 دخل verified - يجب أن يحظر كله"
    names = [s.get("student_name") or "" for s in verified]
    assert not ("Ali Yousif" in names and "Mohamed Osman" in names), "نسختا الرقم المكرر 2021004 دخلتا verified معا"
    assert not any("Huda" in (s.get("student_name") or "") for s in verified), "الطالبة Huda بدون رقم دخلت verified"
    assert not any("2021004" in c for c in certs), "الرقم المكرر 2021004 صدرت له شهادة"
    assert not any("2021006" in c for c in certs), "الطالب 2021006 بدون معدل صدرت له شهادة"
    assert not any("2021007" in c for c in certs), "الطالب 2021007 بدون اسم صدرت له شهادة"

# ---------- الاختبار السادس: تصحيح التقدير من المعدل ----------

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
            f"معدل {s.get('student_name')} يجب أن يكون برقمين عشريين مثل 3.10 لا {gpa_str}"

# ---------- الاختبار السابع: عدم اختراع أسماء ----------

def test_T_E7_empty_pdf_blocked_no_hallucination(verified, issues):
    all_text = json.dumps(verified, ensure_ascii=False) + json.dumps(issues, ensure_ascii=False)
    assert "John Doe" not in all_text, "اسم مخترع: John Doe"
    assert "Jane Smith" not in all_text, "اسم مخترع: Jane Smith"
    assert len(verified) <= 5, "يوجد طلاب زائدون مخترعون"
    assert len(verified) == 5, "المقبول يجب أن يكون 5 فقط من test_04"

# ---------- الاختبار الثامن: حفظ الشهادات ----------

def test_T_E8_certificates_saved_to_output(certs):
    # الشهادات الخمس محفوظة في مجلد output
    assert len(certs) == 5, f"لم تولد كل الشهادات، الموجود {len(certs)}"
    assert os.path.exists("output"), "مجلد output غير موجود"
    for c in certs:
        assert os.path.exists(c), f"الشهادة غير محفوظة في output: {c}"

# ---------- الاختبار التاسع: العدد الكلي للمحظور ----------

def test_gate_blocks_before_crew(issues):
    # العدد الكلي: 7 محظور = 1 مصور + 1 بدون هاش + 1 هاش غير متطابق + 1 مكرر + 3 ناقص
    assert len(issues) == 7, f"المتوقع 7 حالات محظورة، الموجود {len(issues)}"
    types = [i["type"] for i in issues]
    assert types.count("SCANNED PDF") == 1, "SCANNED PDF يجب أن تكون 1"
    assert types.count("MISSING HASH") == 1, "MISSING HASH يجب أن تكون 1"
    assert types.count("HASH MISMATCH") == 1, "HASH MISMATCH يجب أن تكون 1"
    assert types.count("DUPLICATE ID") == 1, "DUPLICATE ID يجب أن تكون 1"
    assert types.count("MISSING FIELD") == 3, "MISSING FIELD يجب أن تكون 3"
