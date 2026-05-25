"""
Management command: seed_data
Creates a full set of realistic dummy data for An-Nadaa Diagnostic Centre.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear   (wipes existing non-admin data first)
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User, UserProfile
from apps.invoices.models import Invoice, InvoiceItem, Payment, Referral
from apps.reports.models import Report, ReportParameter
from apps.services.models import Service, ServiceCategory


# ── Seed data pools ────────────────────────────────────────────────────────────

SURNAMES = [
    "Mohammed", "Ibrahim", "Abdullahi", "Musa", "Suleiman", "Abubakar",
    "Bello", "Usman", "Ahmad", "Garba", "Adeyemi", "Okonkwo", "Chukwu",
    "Okafor", "Nwosu", "Eze", "Obi", "Afolabi", "Akintola", "Adeleke",
    "Lawal", "Haruna", "Yakubu", "Danladi", "Saidu", "Idris", "Aliyu",
    "Tijjani", "Bashir", "Isah", "Nnaji", "Onwudiwe", "Ekwueme", "Agbo",
]

FIRST_NAMES = [
    "Amina", "Fatima", "Aisha", "Hauwa", "Maryam", "Ramatu", "Zainab",
    "Khadija", "Sadiya", "Halima", "Ibrahim", "Emeka", "Chidi", "Tunde",
    "Seun", "Biodun", "Kayode", "Funmi", "Ngozi", "Chiamaka", "Chioma",
    "Ahmed", "Aliyu", "Mustapha", "Uche", "Ifeanyi", "Nkechi", "Adaeze",
    "Yakubu", "Dauda", "Sani", "Laila", "Sulaiman", "Rabiu", "Zubairu",
]

OTHER_NAMES = [
    "Abdullahi", "Mohammed", "Ibrahim", "Bello", "Ahmad", "Usman",
    "Chukwuemeka", "Oluwaseun", "Olabisi", "Nnamdi", "Ifechukwu", "",
    "Garba", "Haruna", "Ismail", "Danladi", "Sunday", "Monday", "Grace", "",
]

PHONE_PREFIXES = ["0801", "0802", "0803", "0805", "0806", "0807", "0808",
                  "0809", "0810", "0811", "0812", "0813", "0814", "0815",
                  "0816", "0817", "0818", "0819", "0901", "0902", "0903"]


def rnd_phone():
    return random.choice(PHONE_PREFIXES) + "".join(str(random.randint(0, 9)) for _ in range(7))


def rnd_name():
    surname = random.choice(SURNAMES)
    first   = random.choice(FIRST_NAMES)
    other   = random.choice(OTHER_NAMES)
    return surname, first, other


def rnd_age():
    n = random.randint(1, 85)
    if n < 2:
        return f"{random.randint(1, 11)}m"  # months
    return str(n)


# ── Service catalogue ──────────────────────────────────────────────────────────

CATALOGUE = {
    "Laboratory": [
        ("Full Blood Count (FBC)",              3500,  True),
        ("Malaria Parasite (MP)",               2000,  True),
        ("Urinalysis",                          2000,  True),
        ("Blood Group & Genotype",              3000,  False),
        ("Widal Test (Typhoid)",                2500,  False),
        ("HIV Screening",                       2500,  False),
        ("Hepatitis B Surface Antigen (HBsAg)", 3000,  False),
        ("Fasting Blood Sugar (FBS)",           2000,  False),
        ("Random Blood Sugar (RBS)",            1500,  False),
        ("Liver Function Test (LFT)",           8000,  True),
        ("Kidney Function Test (KFT)",          7000,  True),
        ("Lipid Profile",                       8000,  True),
        ("Thyroid Function Test (TFT)",        12000,  True),
        ("Electrolytes & Urea",                 6000,  True),
        ("Urine MCS",                           5000,  True),
        ("Stool Analysis",                      2500,  True),
        ("Semen Analysis",                      5000,  True),
        ("Serum Creatinine",                    3000,  False),
        ("ESR (Erythrocyte Sedimentation Rate)",2500,  False),
        ("Rheumatoid Factor",                   4000,  False),
        ("VDRL / Syphilis",                     2500,  False),
        ("Pregnancy Test (Urine)",              1500,  False),
        ("Troponin I (Cardiac)",               10000,  True),
        ("Prothrombin Time (PT)",               4500,  True),
        ("HbA1c (Glycated Haemoglobin)",        7000,  True),
        ("Serum Albumin",                       3500,  False),
        ("Uric Acid",                           3000,  False),
        ("PSA (Prostate Specific Antigen)",     8000,  True),
        ("CA-125 (Ovarian Marker)",             9000,  True),
        ("D-Dimer",                             8000,  True),
    ],
    "Radiology / Scan": [
        ("Ultrasound — Abdominal",             12000,  True),
        ("Ultrasound — Pelvic",                12000,  True),
        ("Ultrasound — Obstetric",             15000,  True),
        ("Ultrasound — Prostate",              13000,  True),
        ("Ultrasound — Thyroid",               12000,  True),
        ("Ultrasound — Breast",                12000,  True),
        ("Chest X-Ray (PA)",                    8000,  True),
        ("Abdominal X-Ray",                     8000,  True),
        ("Lumbosacral X-Ray",                   9000,  True),
        ("Pelvis X-Ray",                        9000,  True),
        ("Knee X-Ray",                          8000,  True),
        ("Skull X-Ray",                         9000,  True),
        ("CT Scan — Head / Brain",             45000,  True),
        ("CT Scan — Chest",                    50000,  True),
        ("CT Scan — Abdomen & Pelvis",         55000,  True),
        ("CT Scan — Spine",                    50000,  True),
        ("MRI — Brain",                        80000,  True),
        ("MRI — Spine",                        85000,  True),
    ],
    "Cardiology": [
        ("ECG (Electrocardiogram)",             5000,  True),
        ("Echocardiogram",                     25000,  True),
        ("24-hr Holter Monitoring",            35000,  True),
        ("Stress Test (TMT)",                  30000,  True),
    ],
    "Ophthalmology": [
        ("Visual Acuity Test",                  3000,  True),
        ("Intraocular Pressure (IOP)",          3500,  True),
        ("Fundoscopy",                          5000,  True),
        ("Refraction Test",                     4000,  True),
    ],
    "Physiology / Other": [
        ("Spirometry (Lung Function)",          6000,  True),
        ("Audiometry (Hearing Test)",           5000,  True),
        ("BMI & Body Composition",              2000,  False),
        ("Medical Certificate / Fitness",       5000,  False),
        ("Pre-employment Screening Package",   25000,  False),
    ],
}

# ReportParameter templates for key services
PARAMETER_TEMPLATES = {
    "Full Blood Count (FBC)": [
        ("Haemoglobin (Hb)",    "number", "g/dL",      "11.5–16.5",  [], True,  0),
        ("WBC",                 "number", "×10³/µL",   "4.0–11.0",   [], True,  1),
        ("RBC",                 "number", "×10⁶/µL",   "4.0–5.5",    [], True,  2),
        ("Platelets",           "number", "×10³/µL",   "150–400",    [], True,  3),
        ("PCV / Haematocrit",   "number", "%",          "35–50",      [], True,  4),
        ("MCV",                 "number", "fL",         "80–100",     [], False, 5),
        ("MCH",                 "number", "pg",         "27–32",      [], False, 6),
        ("MCHC",                "number", "g/dL",       "32–36",      [], False, 7),
        ("Neutrophils",         "number", "%",          "40–75",      [], False, 8),
        ("Lymphocytes",         "number", "%",          "20–45",      [], False, 9),
        ("Monocytes",           "number", "%",          "2–10",       [], False, 10),
        ("Eosinophils",         "number", "%",          "1–6",        [], False, 11),
        ("Comment",             "textarea","",          "",           [], False, 12),
    ],
    "Malaria Parasite (MP)": [
        ("Malaria Parasite", "select", "", "", ["Positive", "Negative"], True, 0),
        ("Species",          "select", "", "",
         ["P. falciparum", "P. vivax", "P. ovale", "P. malariae", "Not Applicable"], False, 1),
        ("Parasite Density", "select", "", "", ["+", "++", "+++", "++++", "N/A"], False, 2),
        ("Comment",          "textarea","","",                         [], False, 3),
    ],
    "Urinalysis": [
        ("Colour",        "select",  "", "", ["Pale Yellow","Yellow","Dark Yellow","Amber","Brown","Colourless"], True, 0),
        ("Appearance",    "select",  "", "", ["Clear","Slightly Cloudy","Cloudy","Turbid"], True, 1),
        ("pH",            "number",  "", "4.5–8.0",  [], True,  2),
        ("Specific Gravity","number","", "1.005–1.030",[], True, 3),
        ("Protein",       "select",  "", "Negative", ["Negative","Trace","+","++","+++"], True, 4),
        ("Glucose",       "select",  "", "Negative", ["Negative","Trace","+","++","+++"], True, 5),
        ("Ketones",       "select",  "", "Negative", ["Negative","Trace","+","++","+++"], False, 6),
        ("Blood",         "select",  "", "Negative", ["Negative","Trace","+","++","+++"], False, 7),
        ("Leucocytes",    "select",  "", "Negative", ["Negative","+","++","+++"],         False, 8),
        ("Nitrites",      "select",  "", "Negative", ["Negative","Positive"],             False, 9),
        ("Bilirubin",     "select",  "", "Negative", ["Negative","Positive"],             False, 10),
        ("Urobilinogen",  "select",  "", "Normal",   ["Normal","Reduced","Elevated"],     False, 11),
        ("Microscopy — WBC/hpf", "text","","0–5",    [], False, 12),
        ("Microscopy — RBC/hpf", "text","","0–2",    [], False, 13),
        ("Microscopy — Casts",   "text","","None",    [], False, 14),
        ("Microscopy — Organisms","text","","None",   [], False, 15),
        ("Comment", "textarea","","",                 [], False, 16),
    ],
    "Liver Function Test (LFT)": [
        ("Total Bilirubin",  "number","µmol/L","2–17",   [], True, 0),
        ("Direct Bilirubin", "number","µmol/L","0–5",    [], True, 1),
        ("AST (SGOT)",       "number","U/L",   "5–40",   [], True, 2),
        ("ALT (SGPT)",       "number","U/L",   "5–35",   [], True, 3),
        ("ALP",              "number","U/L",   "40–130", [], True, 4),
        ("GGT",              "number","U/L",   "5–55",   [], False,5),
        ("Total Protein",    "number","g/L",   "60–80",  [], True, 6),
        ("Albumin",          "number","g/L",   "35–50",  [], True, 7),
        ("Globulin",         "number","g/L",   "25–35",  [], False,8),
        ("Comment",          "textarea","","",           [], False,9),
    ],
    "Kidney Function Test (KFT)": [
        ("Urea",           "number","mmol/L","2.5–7.5",    [], True, 0),
        ("Creatinine",     "number","µmol/L","60–120",     [], True, 1),
        ("eGFR",           "number","mL/min/1.73m²",">60", [], True, 2),
        ("Uric Acid",      "number","µmol/L","200–430",    [], False,3),
        ("Sodium",         "number","mmol/L","135–145",    [], True, 4),
        ("Potassium",      "number","mmol/L","3.5–5.0",    [], True, 5),
        ("Chloride",       "number","mmol/L","95–110",     [], False,6),
        ("Bicarbonate",    "number","mmol/L","22–29",      [], False,7),
        ("Comment",        "textarea","","",               [], False,8),
    ],
    "Chest X-Ray (PA)": [
        ("Lung Fields",      "textarea","","", [], True, 0),
        ("Heart Shadow",     "textarea","","", [], True, 1),
        ("Bony Thorax",      "textarea","","", [], False,2),
        ("Diaphragm",        "textarea","","", [], False,3),
        ("Impression",       "textarea","","", [], True, 4),
        ("Recommendation",   "textarea","","", [], False,5),
    ],
    "Ultrasound — Abdominal": [
        ("Liver",       "textarea","","", [], True, 0),
        ("Gall Bladder","textarea","","", [], False,1),
        ("Spleen",      "textarea","","", [], False,2),
        ("Pancreas",    "textarea","","", [], False,3),
        ("Kidneys",     "textarea","","", [], True, 4),
        ("Aorta",       "textarea","","", [], False,5),
        ("Impression",  "textarea","","", [], True, 6),
    ],
    "Ultrasound — Obstetric": [
        ("Gestational Age (by LMP)",   "text","weeks","", [], True, 0),
        ("Gestational Age (by USS)",   "text","weeks","", [], True, 1),
        ("Foetal Presentation",        "select","","",["Cephalic","Breech","Transverse","Oblique"], True, 2),
        ("Foetal Heart Rate",          "number","bpm","120–160", [], True, 3),
        ("Estimated Foetal Weight",    "text","kg","",  [], False,4),
        ("Amniotic Fluid Index (AFI)", "number","cm","5–25",     [], False,5),
        ("Placenta Location",          "select","","",["Anterior","Posterior","Fundal","Lateral","Low-lying","Praevia"], False, 6),
        ("Foetal Movement",            "select","","",["Active","Reduced","Absent"], False, 7),
        ("Number of Foetuses",         "select","","",["Singleton","Twins","Triplets"], True, 8),
        ("Impression / Conclusion",    "textarea","","", [], True, 9),
    ],
    "ECG (Electrocardiogram)": [
        ("Rate",          "number","bpm","60–100",  [], True, 0),
        ("Rhythm",        "select","","",["Regular","Irregular","Regular Irregular"], True, 1),
        ("Axis",          "select","","",["Normal","Left Axis Deviation","Right Axis Deviation"], False,2),
        ("P Wave",        "text","","Normal",       [], False,3),
        ("PR Interval",   "text","ms","120–200 ms", [], False,4),
        ("QRS Duration",  "text","ms","<120 ms",    [], False,5),
        ("QT Interval",   "text","ms","",           [], False,6),
        ("ST Segment",    "text","","",             [], False,7),
        ("Impression",    "textarea","","",         [], True, 8),
    ],
    "Stool Analysis": [
        ("Colour",          "text",    "", "",         [], False, 0),
        ("Consistency",     "select",  "", "",         ["Formed","Semi-formed","Soft","Liquid","Watery"], True,  1),
        ("Mucus",           "select",  "", "",         ["Absent","Present"],    False, 2),
        ("Blood",           "select",  "", "",         ["Absent","Present"],    False, 3),
        ("Ova / Parasites", "select",  "", "",         ["None seen","Present"], True,  4),
        ("Organisms",       "text",    "", "None seen",[], False, 5),
        ("Comment",         "textarea","", "",         [], False, 6),
    ],
}

# Referral sources
REFERRALS = [
    # (name, category)
    ("General Hospital Abuja",              "HOSPITAL"),
    ("National Hospital Abuja",             "HOSPITAL"),
    ("Garki District Hospital",             "HOSPITAL"),
    ("Maitama District Hospital",           "HOSPITAL"),
    ("Gwagwalada Specialist Hospital",      "HOSPITAL"),
    ("University of Abuja Teaching Hospital","HOSPITAL"),
    ("Medicare Specialist Clinic",          "CLINIC"),
    ("Lifecare Medical Centre",             "CLINIC"),
    ("Prime Health Clinic Wuse",            "CLINIC"),
    ("Excel Medical Centre",                "CLINIC"),
    ("Nisa Premier Hospital",               "CLINIC"),
    ("Cedarcrest Hospitals",                "CLINIC"),
    ("Dr. Musa Abdullahi",                  "DOCTOR"),
    ("Dr. Amina Ibrahim",                   "DOCTOR"),
    ("Dr. Chukwuemeka Obi",                 "DOCTOR"),
    ("Dr. Fatima Mohammed",                 "DOCTOR"),
    ("Dr. Suleiman Garba",                  "DOCTOR"),
    ("Dr. Ngozi Adeyemi",                   "DOCTOR"),
    ("NNPC Medical Centre",                 "ORGANIZATION"),
    ("Federal Civil Service Commission",    "ORGANIZATION"),
    ("Nigerian Army Medical Corps",         "ORGANIZATION"),
    ("MTN Nigeria Health Scheme",           "ORGANIZATION"),
    ("NHIS / NHIA",                         "ORGANIZATION"),
    ("National Population Commission",      "ORGANIZATION"),
]

# Staff users
STAFF = [
    # (username, first, last, role, password)
    ("cashier1",  "Aisha",      "Bello",     "CASHIER",   "Staff@1234"),
    ("cashier2",  "Emeka",      "Johnson",   "CASHIER",   "Staff@1234"),
    ("cashier3",  "Fatima",     "Usman",     "CASHIER",   "Staff@1234"),
    ("doctor1",   "Sule",       "Garba",     "DOCTOR",    "Staff@1234"),
    ("doctor2",   "Ngozi",      "Okonkwo",   "DOCTOR",    "Staff@1234"),
    ("labtech1",  "Ibrahim",    "Yusuf",     "LAB_TECH",  "Staff@1234"),
    ("labtech2",  "Grace",      "Adeyemi",   "LAB_TECH",  "Staff@1234"),
]


class Command(BaseCommand):
    help = "Seed the database with realistic dummy data for An-Nadaa Diagnostic Centre"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all non-superuser data before seeding",
        )
        parser.add_argument(
            "--invoices",
            type=int,
            default=60,
            help="Number of invoices to generate (default: 60)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        self.stdout.write("\n[*] Seeding An-Nadaa Diagnostic Centre...\n")

        categories  = self._seed_categories()
        services    = self._seed_services(categories)
        self._seed_report_parameters(services)
        referrals   = self._seed_referrals()
        staff       = self._seed_staff()
        self._seed_invoices(services, referrals, staff, n=options["invoices"])

        self.stdout.write(self.style.SUCCESS(
            "\n[OK] Seed complete! Login at http://127.0.0.1:8000\n"
            "   admin    / Admin@1234\n"
            "   cashier1 / Staff@1234\n"
            "   doctor1  / Staff@1234\n"
            "   labtech1 / Staff@1234\n"
        ))

    # ── Clear ──────────────────────────────────────────────────────────────────

    def _clear(self):
        self.stdout.write("  Clearing existing data...")
        Report.objects.all().delete()
        Payment.objects.all().delete()
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()
        Referral.objects.all().delete()
        ReportParameter.objects.all().delete()
        Service.objects.all().delete()
        ServiceCategory.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write("  Cleared.\n")

    # ── Service categories ─────────────────────────────────────────────────────

    def _seed_categories(self):
        cats = {}
        for name in CATALOGUE:
            cat, created = ServiceCategory.objects.get_or_create(name=name)
            cats[name] = cat
            if created:
                self.stdout.write(f"  Category: {name}")
        return cats

    # ── Services ───────────────────────────────────────────────────────────────

    def _seed_services(self, categories):
        services = {}
        for cat_name, items in CATALOGUE.items():
            for (svc_name, price, needs_report) in items:
                svc, created = Service.objects.get_or_create(
                    name=svc_name,
                    defaults={
                        "category": categories[cat_name],
                        "price": Decimal(str(price)),
                        "is_active": True,
                        "requires_report": needs_report,
                    },
                )
                services[svc_name] = svc
        self.stdout.write(f"  [OK] {Service.objects.count()} services created")
        return services

    # ── Report parameters ──────────────────────────────────────────────────────

    def _seed_report_parameters(self, services):
        count = 0
        for svc_name, params in PARAMETER_TEMPLATES.items():
            svc = services.get(svc_name)
            if not svc:
                continue
            ReportParameter.objects.filter(service=svc).delete()
            for row in params:
                if len(row) != 7:
                    continue
                name, ptype, unit, normal_range, options, required, order = row
                ReportParameter.objects.create(
                    service=svc,
                    name=name,
                    parameter_type=ptype,
                    unit=unit or None,
                    normal_range=normal_range or None,
                    options=options,
                    required=required,
                    order=order,
                )
                count += 1
        self.stdout.write(f"  [OK] {count} report parameters created")

    # ── Referrals ──────────────────────────────────────────────────────────────

    def _seed_referrals(self):
        refs = []
        for name, cat in REFERRALS:
            ref, _ = Referral.objects.get_or_create(name=name, defaults={"category": cat})
            refs.append(ref)
        self.stdout.write(f"  [OK] {len(refs)} referrals created")
        return refs

    # ── Staff ──────────────────────────────────────────────────────────────────

    def _seed_staff(self):
        staff = {}
        for (username, first, last, role, pwd) in STAFF:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "role": role,
                    "email": f"{username}@annadaa.com",
                    "password": make_password(pwd),
                    "is_active": True,
                },
            )
            if created:
                UserProfile.objects.get_or_create(user=user)
            staff[role] = staff.get(role, [])
            staff[role].append(user)
        self.stdout.write(f"  [OK] {len(STAFF)} staff users created")
        return staff

    # ── Invoices ───────────────────────────────────────────────────────────────

    def _seed_invoices(self, services, referrals, staff, n=60):
        cashiers = staff.get("CASHIER", [])
        doctors  = staff.get("DOCTOR", [])
        lab_techs= staff.get("LAB_TECH", [])

        # Admin also acts as cashier for some invoices
        admin = User.objects.filter(is_superuser=True).first()
        if admin:
            cashiers.append(admin)

        all_services = list(services.values())
        report_services = [s for s in all_services if s.requires_report]

        created_invoices = 0
        created_reports  = 0

        now = timezone.now()

        # Build a time-slot schedule:
        #   - First 20 invoices  → TODAY   (hours 7am–5pm)
        #   - Next  20 invoices  → last 7 days (realistic recent history)
        #   - Final 20 invoices  → last 8–45 days (older history)
        #
        # This ensures the dashboard always has meaningful "today" data.

        def make_inv_time(i, total):
            if i < total // 3:
                # Today — spread through a working day (07:00–17:00)
                work_minute = int((i / (total // 3)) * 600)   # 600 mins = 10 hrs
                return now.replace(hour=7, minute=0, second=0, microsecond=0) \
                       + timedelta(minutes=work_minute + random.randint(0, 8))
            elif i < 2 * total // 3:
                # 1–7 days ago
                d = random.randint(1, 7)
                return now - timedelta(days=d, hours=random.randint(7, 17),
                                       minutes=random.randint(0, 59))
            else:
                # 8–45 days ago
                d = random.randint(8, 45)
                return now - timedelta(days=d, hours=random.randint(7, 17),
                                       minutes=random.randint(0, 59))

        for i in range(n):
            inv_time = make_inv_time(i, n)

            surname, first_name, other_names = rnd_name()
            sex = random.choice(["M", "F"])
            cashier = random.choice(cashiers)

            # 70% of invoices have a referral
            referral = random.choice(referrals) if random.random() < 0.70 else None

            # Pick 1–4 services
            n_services = random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5])[0]
            chosen = random.sample(all_services, min(n_services, len(all_services)))

            # Payment method distribution: 60% cash, 25% transfer, 15% card
            method = random.choices(
                ["CASH", "TRANSFER", "CARD"], weights=[60, 25, 15]
            )[0]
            ref_no = ""
            if method in ("TRANSFER", "CARD"):
                ref_no = f"TXN{random.randint(100000000, 999999999)}"

            # Discount on ~15% of invoices
            discount = Decimal("0.00")
            if random.random() < 0.15:
                discount = Decimal(str(random.choice([500, 1000, 1500, 2000, 2500, 5000])))

            # Create invoice
            invoice = Invoice(
                surname=surname,
                first_name=first_name,
                other_names=other_names,
                age=rnd_age(),
                sex=sex,
                phone_number=rnd_phone(),
                referral=referral,
                discount=discount,
                payment_method=method,
                reference_number=ref_no or None,
                status="PAID",
                created_by=cashier,
                notes="" if random.random() > 0.1 else "Urgent — patient requested fast result.",
            )
            # Bypass auto_now_add by using update after save
            invoice.save()

            # Back-date the invoice
            Invoice.objects.filter(pk=invoice.pk).update(
                created_at=inv_time, updated_at=inv_time
            )
            invoice.refresh_from_db()

            # Items
            subtotal = Decimal("0.00")
            has_report_service = False
            for svc in chosen:
                qty = random.choices([1, 2], weights=[90, 10])[0]
                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    service=svc,
                    quantity=qty,
                    unit_price=svc.price,
                )
                subtotal += item.total_price
                if svc.requires_report:
                    has_report_service = True

            total = max(subtotal - discount, Decimal("0.00"))
            Invoice.objects.filter(pk=invoice.pk).update(
                total_amount=total, amount_paid=total
            )
            invoice.refresh_from_db()

            # Payment record
            payment = Payment.objects.create(
                invoice=invoice,
                amount=total,
                payment_method=method,
                reference_number=ref_no or None,
                received_by=cashier,
            )
            Payment.objects.filter(pk=payment.pk).update(payment_date=inv_time)

            created_invoices += 1

            # ── Create reports for services that require them ──────────────────
            if has_report_service and lab_techs and doctors:
                for item in invoice.items.filter(service__requires_report=True):
                    svc      = item.service
                    lab_tech = random.choice(lab_techs)
                    doctor   = random.choice(doctors)

                    # Pick a realistic signatory (one of the seeded doctors)
                    signatory = f"Dr. {doctor.get_full_name() or doctor.username}, MBBS"

                    report = Report(
                        invoice     = invoice,
                        invoice_item= item,
                        service     = svc,
                        created_by  = lab_tech,
                        signatory   = signatory,
                    )
                    report.save()
                    Report.objects.filter(pk=report.pk).update(
                        created_at=inv_time + timedelta(minutes=random.randint(10, 60)),
                        updated_at=inv_time + timedelta(minutes=random.randint(10, 90)),
                    )
                    report.refresh_from_db()

                    # Populate parameter values
                    params = ReportParameter.objects.filter(service=svc)
                    values = {}
                    for p in params:
                        values[str(p.id)] = self._fake_param_value(p)
                    Report.objects.filter(pk=report.pk).update(parameters=values)

                    created_reports += 1

        self.stdout.write(
            f"  [OK] {created_invoices} invoices + {created_reports} reports created"
        )

    # ── Fake parameter value generator ────────────────────────────────────────

    def _fake_param_value(self, param):
        if param.parameter_type == "select" and param.options:
            return random.choice(param.options)
        if param.parameter_type == "checkbox":
            return random.choice(["Yes", ""])
        if param.parameter_type == "number":
            # Parse normal range and return a value near it
            nr = param.normal_range or ""
            try:
                parts = nr.replace("–", "-").replace(">", "").replace("<", "").split("-")
                lo = float(parts[0].strip())
                hi = float(parts[-1].strip()) if len(parts) > 1 else lo * 1.5
                # 80% in range, 20% slightly out of range
                if random.random() < 0.80:
                    val = round(random.uniform(lo, hi), 2)
                else:
                    spread = (hi - lo) * 0.3
                    val = round(random.uniform(lo - spread, hi + spread), 2)
                    val = max(0, val)
                return str(val)
            except Exception:
                return str(round(random.uniform(1, 100), 2))
        if param.parameter_type == "textarea":
            return random.choice([
                "Normal appearance. No significant abnormality detected.",
                "Mild changes noted. Clinical correlation advised.",
                "Findings within normal limits.",
                "Borderline result. Repeat test recommended.",
                "",
            ])
        # text / date / other
        return random.choice([
            "Normal", "Negative", "Not detected", "Within range", "See comment"
        ])
