# create_data.py - بيعمل 4 ملفات للاختبار
# 1: سكان / 2: بدون هاش / 3: هاش غلط / 4: مكرر + مفقود
import fitz, hashlib, os, random

os.makedirs("data", exist_ok=True)

names_10 = [
    "Ahmed Ali", "Sara Mohamed", "Omar Hassan", "Fatima Ahmed",
    "Ali Yousif", "Nada Khalid", "Mohamed Osman", "Huda Ibrahim",
    "Yasir Abdalla", "Reem Salah"
]

def write_hash(pdf_path, correct=True):
    with open(pdf_path, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    if not correct:
        h = "0" * 64  # هاش غلط متعمد
    hash_file = pdf_path.replace(".pdf", "_hash.txt")
    with open(hash_file, "w") as f:
        f.write(h)
    print(f"Hash: {pdf_path} -> {h[:10]}... {'صح' if correct else 'غلط متعمد'}")

def make_normal_pdf(filename, names):
    doc = fitz.open()
    p = doc.new_page()
    y = 80
    p.insert_text((100, 40), "Results - COSC726", fontsize=16)
    for i, name in enumerate(names):
        sid = f"20210{i+1:03d}"
        gpa = round(random.uniform(2.0, 4.0), 2)
        line = f"{sid} {name} {gpa:.2f}"
        p.insert_text((100, y), line, fontsize=13)
        y += 30
        if y > 800:
            p = doc.new_page()
            y = 80
    doc.save(filename)
    doc.close()
    return filename

# ============================================================
# 1. ملف مصور / سكان - ما فيهو نص رقمي
# ============================================================
def make_scanned():
    filename = "data/test_01_scanned.pdf"
    tmp = "data/_tmp.pdf"
    make_normal_pdf(tmp, names_10)
    doc = fitz.open(tmp)
    out = fitz.open()
    for page in doc:
        pix = page.get_pixmap(dpi=100)
        p = out.new_page(width=pix.width, height=pix.height)
        # التعديل هنا: p.rect بدل p.get_rect()
        p.insert_image(p.rect, pixmap=pix)
    out.save(filename)
    out.close()
    doc.close()
    if os.path.exists(tmp):
        os.remove(tmp)
    write_hash(filename, correct=True)
    print(f"تم: {filename} - ملف مصور / سكان")

# ============================================================
# 2. ملف بدون هاش خالص
# ============================================================
def make_no_hash():
    filename = "data/test_02_no_hash.pdf"
    make_normal_pdf(filename, names_10)
    print(f"تم: {filename} - بدون هاش")

# ============================================================
# 3. ملف الهاش بتاعو غلط
# ============================================================
def make_wrong_hash():
    filename = "data/test_03_wrong_hash.pdf"
    make_normal_pdf(filename, names_10)
    write_hash(filename, correct=False)
    print(f"تم: {filename} - هاش غلط")

# ============================================================
# 4. ملف فيه طالبين بنفس الرقم + 3 طلاب قيمهم مفقودة
# ============================================================
def make_duplicate_missing():
    filename = "data/test_04_duplicate_missing.pdf"
    doc = fitz.open()
    p = doc.new_page()
    y = 80
    p.insert_text((100, 40), "Results - COSC726 - Duplicate + Missing", fontsize=16)

    lines = []
    lines.append(("2021001", "Ahmed Ali", 3.72))
    lines.append(("2021002", "Sara Mohamed", 3.10))
    lines.append(("2021003", "Omar Hassan", 2.80))
    # --- طالبين بنفس الرقم الجامعي - المكرر ---
    lines.append(("2021004", "Ali Yousif", 3.50))
    lines.append(("2021004", "Mohamed Osman", 2.90))
    lines.append(("2021005", "Fatima Ahmed", 3.90))
    # --- 3 طلاب بقيم مفقودة مختلفة ---
    lines.append(("2021006", "Nada Khalid", None))  # مفقود GPA
    lines.append(("2021007", "", 3.20))  # مفقود الاسم
    lines.append(("", "Huda Ibrahim", 2.60))  # مفقود الرقم الجامعي
    lines.append(("2021008", "Yasir Abdalla", 3.00))

    for sid, name, gpa in lines:
        if gpa is None:
            line = f"{sid} {name}"
        elif sid == "":
            line = f"{name} {gpa:.2f}"
        elif name == "":
            line = f"{sid} {gpa:.2f}"
        else:
            line = f"{sid} {name} {gpa:.2f}"
        p.insert_text((100, y), line, fontsize=13)
        y += 30
        if y > 800:
            p = doc.new_page()
            y = 80
    doc.save(filename)
    doc.close()
    write_hash(filename, correct=True)
    print(f"تم: {filename} - مكرر + 3 مفقودين")

# شغل الأربعة
make_scanned()
make_no_hash()
make_wrong_hash()
make_duplicate_missing()

print("\n✅ جاهز! عندك 4 ملفات في data:")
print("   1. data/test_01_scanned.pdf - مصور")
print("   2. data/test_02_no_hash.pdf - بدون هاش")
print("   3. data/test_03_wrong_hash.pdf - هاش غلط")
print("   4. data/test_04_duplicate_missing.pdf - مكرر + 3 مفقودين")
print("      - المكرر: 2021004 - Ali Yousif و Mohamed Osman")
print("      - المفقود 1: 2021006 Nada Khalid - بدون GPA")
print("      - المفقود 2: 2021007 - بدون اسم")
print("      - المفقود 3: Huda Ibrahim - بدون رقم جامعي")
