# create_data.py - بيعمل ملفين: 10 طلاب و 50 طالب
import fitz, hashlib, os, random

os.makedirs("data", exist_ok=True)

#أسماء حقيقية 
names_10 = [
    "Ahmed Ali", "Sara Mohamed", "Omar Hassan", "Fatima Ahmed",
    "Ali Yousif", "Nada Khalid", "Mohamed Osman", "Huda Ibrahim",
    "Yasir Abdalla", "Reem Salah"
]

names_50 = [
    "Ahmed Ali", "Sara Mohamed", "Omar Hassan", "Fatima Ahmed",
    "Ali Yousif", "Nada Khalid", "Mohamed Osman", "Huda Ibrahim",
    "Yasir Abdalla", "Reem Salah", "Khalid Musa", "Aya Abbas",
    "Osman Idris", "Mona Saeed", "Tariq Nour", "Lina Kamal",
    "Abdelrahman Adam", "Salma Fathi", "Waleed Tayeb", "Dalia Omer",
    "Ibrahim Khalil", "Rania Mahmoud", "Samir Badawi", "Hiba Eltayeb",
    "Mustafa Hamid", "Zainab Ali", "Yousif Ahmed", "Marwa Hassan",
    "Anas Elamin", "Noor Elhadi", "Bashir Osman", "Safa Yousif",
    "Hassan Mohamed", "Iman Khalifa", "Faris Abdelaziz", "Alaa Eldin",
    "Maha Abdalla", "Karim Samir", "Lubna Ahmed", "Nadir Osman",
    "Sanaa Ibrahim", "Othman Khalid", "Rasha Mohamed", "Emad Yousif",
    "Wafa Salah", "Adil Hassan", "Hala Mahdi", "Bilal Ahmed",
    "Asma Khalid", "Mahmoud Ali"
]

def make_pdf(filename, names):
    doc = fitz.open()
    p = doc.new_page()
    y = 80
    p.insert_text((100, 40), "Results - COSC726", fontsize=16)
    for i, name in enumerate(names):
        sid = f"20210{i+1:03d}"  # مثلا 20210001
        # GPA متنوع عشان نختبر التصحيح الذاتي
        gpa = round(random.uniform(2.0, 4.0), 2)
        # لو GPA اقل من 1.5 او اكتر من 4.0 النظام حيرفضو - عشان كده خليهو بين 2 و 4
        line = f"{sid} {name} {gpa:.2f}"
        p.insert_text((100, y), line, fontsize=13)
        y += 30
        # لو الصفحة اتملت، اعمل صفحة جديدة
        if y > 800:
            p = doc.new_page()
            y = 80
    doc.save(filename)
    # احسب الهاش
    with open(filename, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    hash_file = filename.replace(".pdf", "_hash.txt")
    with open(hash_file, "w") as f:
        f.write(h)
    print(f"تم: {filename} - {len(names)} طالب - Hash: {h[:10]}...")
    return filename, h

# اعمل الملفين
make_pdf("data/test_10.pdf", names_10)
make_pdf("data/test_50.pdf", names_50)

print("\n✅ جاهز! عندك ملفين في data")
print("   - data/test_10.pdf")
print("   - data/test_50.pdf")