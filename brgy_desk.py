# ===== PROBLEMA =====
# Mano-mano pa ang pagtala ng mga residente, certificate requests, at blotter
# sa barangay. Nawawala ang record ng bayad, hindi alam kung ilan ang pending
# na certificate, at walang malinaw na status ng bawat blotter case.
#
# ===== SOLUSYON =====
# Barangay Certificate & Blotter System: resident CRUD, certificate request
# at release, blotter records, at reports ng pending at nakolektang bayad.

import re
from datetime import datetime

import mysql.connector

import brgy_db
from brgy_db import BrgyError


CIVIL_STATUS = ["Single", "Married", "Widowed", "Separated"]

CERT_TYPES = {
    "Barangay Clearance": 50.00,
    "Certificate of Residency": 30.00,
    "Certificate of Indigency": 0.00,
    "Certificate of Good Moral": 30.00,
    "Business Permit Clearance": 100.00,
    "First Time Job Seeker": 0.00,
    "Others": 0.00,
}

BLOTTER_TYPES = [
    "Away/Argument",
    "Pananakit",
    "Pagtatalo sa Lupa",
    "Ingay/Public Disturbance",
    "Pagnanakaw",
    "Iba pa",
]

BLOTTER_STATUS = [
    "Bagong Reklamo",
    "Mediation",
    "Naayos na",
    "Isinangguni sa Pulis",
]


def prompt_value(msg):
    while True:
        v = input(msg).strip()
        if v == "":
            print("  * Hindi puwede blangko.")
            continue
        return v


def prompt_optional(msg, current):
    v = input(msg).strip()
    return current if v == "" else v


def prompt_money(msg):
    while True:
        v = input(msg).strip().replace(",", "")
        try:
            num = float(v)
        except ValueError:
            print("  * Halaga sa numero ang kailangan (hal. 50.00).")
            continue
        if num < 0:
            print("  * Hindi puwedeng negative ang halaga.")
            continue
        return round(num, 2)


def ask_date(msg):
    while True:
        v = input(msg).strip()
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            print("  * Mali ang petsa. Halimbawa: 2026-10-30")


def ask_date_optional(msg):
    while True:
        v = input(msg).strip()
        if v == "":
            return None
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            print("  * Mali ang petsa. Halimbawa: 1990-05-15")


def ask_time(msg):
    while True:
        v = input(msg).strip()
        if re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            return v
        print("  * Mali ang oras. Halimbawa: 14:30")


def choose_from(options, prompt_text, current=None):
    for i, name in enumerate(options, start=1):
        mark = "  <-- kasalukuyan" if name == current else ""
        print(f"    [{i}] {name}{mark}")
    while True:
        c = input(prompt_text).strip()
        if c == "" and current:
            return current
        if c.isdigit() and 1 <= int(c) <= len(options):
            return options[int(c) - 1]
        print(f"  * Pumili ng 1 hanggang {len(options)}.")


def choose_cert_type():
    names = list(CERT_TYPES.keys())
    for i, name in enumerate(names, start=1):
        print(f"    [{i}] {name:<32} P {CERT_TYPES[name]:,.2f}")
    while True:
        c = input(f"    Pumili (1-{len(names)}): ").strip()
        if c.isdigit() and 1 <= int(c) <= len(names):
            return names[int(c) - 1]
        print(f"  * Pumili ng 1 hanggang {len(names)}.")


def short(text, width):
    text = str(text)
    if len(text) <= width:
        return text.ljust(width)
    return text[: width - 3] + "..."


def render_resident_card(r, links=None):
    print("\n" + "-" * 58)
    print(f"  RESIDENT CODE : {r['resident_code']}")
    print("-" * 58)
    print(f"  Pangalan      : {r['full_name']}")
    print(f"  Purok         : {r['purok']}")
    print(f"  Contact       : {r['contact_no'] or '---'}")
    birthdate = r["birthdate"].strftime("%Y-%m-%d") if r["birthdate"] else "---"
    print(f"  Kaarawan      : {birthdate}")
    print(f"  Civil Status  : {r['civil_status']}")
    print(f"  Rehistrado    : {r['date_registered'].strftime('%Y-%m-%d')}")
    if links is not None:
        print(f"  Certificates  : {links['requests']}")
        print(f"  Blotter (name): {links['blotters']}")
    print("-" * 58)


def render_request_card(c):
    print("\n" + "-" * 58)
    print(f"  REQUEST #    : {c['request_no']}")
    print("-" * 58)
    print(f"  Residente    : {c['full_name']} ({c['resident_code']})")
    print(f"  Purok        : {c['purok']}")
    print(f"  Certificate  : {c['cert_type']}")
    print(f"  Layunin      : {c['purpose']}")
    print(f"  Bayad        : P {float(c['fee']):,.2f}")
    print(f"  Kalagayan    : {c['status']}")
    print(f"  Hiniling     : {c['requested_at'].strftime('%Y-%m-%d %H:%M')}")
    released = c["released_at"].strftime("%Y-%m-%d %H:%M") if c["released_at"] else "---"
    print(f"  Na-release   : {released}")
    print(f"  Nag-issue    : {c['issued_by'] or '---'}")
    print(f"  Remarks      : {c['remarks'] or '---'}")
    print("-" * 58)


def render_blotter_card(b):
    print("\n" + "-" * 58)
    print(f"  BLOTTER #    : {b['blotter_no']}")
    print("-" * 58)
    print(f"  Nagrereklamo : {b['complainant']}")
    print(f"  Inirereklamo : {b['respondent']}")
    print(f"  Petsa/Oras   : {b['incident_date']} {b['incident_time']}")
    print(f"  Uri          : {b['incident_type']}")
    print(f"  Lugar        : {b['location']}")
    print("\n  SALAYSAY:")
    print(f"  {b['narrative']}")
    print("\n  AKSYON NA GINAWA:")
    print(f"  {b['action_taken'] or '--- WALA PA ---'}")
    print(f"  Kalagayan    : {b['status']}")
    print(f"  Nagtala      : {b['recorded_by']}")
    print(f"  Petsa ng tala: {b['recorded_at'].strftime('%Y-%m-%d %H:%M')}")
    print("-" * 58)


# Menu 1
def register_resident():
    print("\n--- MAG-REGISTER NG RESIDENTE (CREATE) ---")
    code = brgy_db.next_resident_code()
    print(f"  Resident Code (awtomatiko): {code}")
    name = prompt_value("  Buong Pangalan: ")
    purok = prompt_value("  Purok / Address: ")
    contact = input("  Contact No. (puwedeng blangko): ").strip()
    birthdate = ask_date_optional("  Kaarawan YYYY-MM-DD (blangko = laktawan): ")
    print("  Civil Status:")
    civil = choose_from(CIVIL_STATUS, "    Pumili: ")
    try:
        brgy_db.add_resident(
            code, name, purok, contact or None, birthdate, civil
        )
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    print(f"\n  [TAPOS NA] Nairehistro si {name} ({code}).")


# Menu 2
def show_residents():
    search = input("  Hanapin (pangalan o purok, blangko = lahat): ").strip()
    try:
        rows = brgy_db.list_residents(search or None)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not rows:
        print("\n  Walang residenteng nahanap.")
        return
    print("\n--- LISTAHAN NG RESIDENTE ---")
    print(f"  {'CODE':<10} {'PANGALAN':<28} {'PUROK':<18} {'CONTACT':<14} CERT")
    print("  " + "-" * 78)
    for r in rows:
        print(
            f"  {r['resident_code']:<10} {short(r['full_name'], 28)} "
            f"{short(r['purok'], 18)} {short(r['contact_no'] or '---', 14)} "
            f"{r['request_count']:>4}"
        )
    print("  " + "-" * 78)
    print(f"  Kabuuang residente: {len(rows)}")


# Menu 3
def show_resident_profile():
    code = prompt_value("  Resident Code: ").upper()
    try:
        r = brgy_db.find_resident(code)
        if not r:
            print("  [WALA] Hindi matagpuan ang residente.")
            return
        links = brgy_db.resident_links(r)
        requests = brgy_db.list_requests(resident_code=code)
        blotters = brgy_db.list_blotters(name=r["full_name"])
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    render_resident_card(r, links)
    if requests:
        print("\n  MGA CERTIFICATE REQUEST:")
        print(f"  {'REQUEST #':<18} {'CERTIFICATE':<30} {'BAYAD':>8} STATUS")
        print("  " + "-" * 72)
        for c in requests:
            print(
                f"  {c['request_no']:<18} {short(c['cert_type'], 30)} "
                f"P{float(c['fee']):>7,.2f} {c['status']}"
            )
    else:
        print("\n  Wala pang certificate request.")
    if blotters:
        print("\n  MGA BLOTTER NA SANGKOT ANG PANGALAN:")
        for b in blotters:
            print(f"  [{b['blotter_no']}] {b['incident_date']} | {b['status']}")
    else:
        print("\n  Wala pang blotter record sa pangalan niya.")


# Menu 4
def request_certificate():
    print("\n--- CERTIFICATE REQUEST (CREATE) ---")
    code = prompt_value("  Resident Code: ").upper()
    try:
        r = brgy_db.find_resident(code)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not r:
        print("  [WALA] Hindi matagumpay. I-register muna ang residente sa [1].")
        return
    render_resident_card(r)
    print("  Uri ng Certificate:")
    cert_type = choose_cert_type()
    default_fee = CERT_TYPES[cert_type]
    purpose = prompt_value("  Layunin (hal. Scholarship, Employment): ")
    fee_input = input(f"  Bayad [P {default_fee:,.2f}] (blangko = default): ").strip()
    if fee_input == "":
        fee = default_fee
    else:
        try:
            fee = round(float(fee_input.replace(",", "")), 2)
        except ValueError:
            print("  * Mali ang bayad. Default na lang ang gagamitin.")
            fee = default_fee
        if fee < 0:
            fee = default_fee
    remarks = input("  Remarks (blangko = wala): ").strip()
    try:
        request_no = brgy_db.next_request_no()
        brgy_db.add_request(
            request_no, code, cert_type, purpose, fee, remarks or None
        )
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    print(f"\n  [TAPOS NA] Request #: {request_no}")
    print(f"  Kalagayan: PENDING - pumunta sa [5] kapag i-release na.")
    print(f"  Bayad na kailangan: P {fee:,.2f}")


# Menu 5
def release_certificate():
    print("\n--- RELEASE NG CERTIFICATE (UPDATE) ---")
    request_no = prompt_value("  Request #: ").upper()
    try:
        c = brgy_db.find_request(request_no)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not c:
        print("  [WALA] Hindi matagpuan ang request.")
        return
    render_request_card(c)
    if c["status"] != "Pending":
        print(f"  [PAALALA] Ang status ay {c['status']}, hindi na ito ma-release.")
        return
    issued_by = prompt_value("  Sino ang nag-issue (Pangalan): ")
    konf = input("  I-release na ba ang certificate? (oo/hindi): ").strip().lower()
    if konf not in ("oo", "o", "yes", "y"):
        print("  Kinansela.")
        return
    try:
        brgy_db.release_request(request_no, issued_by)
        print(f"\n  [NA-RELEASE] handa na ang {c['cert_type']} para kay {c['full_name']}.")
    except BrgyError as e:
        print(f"  [MALI] {e}")
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")


# Menu 6
def cancel_certificate():
    print("\n--- KANSELAHIN ANG CERTIFICATE REQUEST (UPDATE) ---")
    request_no = prompt_value("  Request #: ").upper()
    try:
        c = brgy_db.find_request(request_no)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not c:
        print("  [WALA] Hindi matagpuan ang request.")
        return
    render_request_card(c)
    if c["status"] != "Pending":
        print(f"  [PAALALA] Ang status ay {c['status']}, hindi na makansela.")
        return
    reason = prompt_value("  Dahilan ng pagkansela: ")
    konf = input("  Kanselahin ang request? (oo/hindi): ").strip().lower()
    if konf not in ("oo", "o", "yes", "y"):
        print("  Kinansela.")
        return
    try:
        brgy_db.cancel_request(request_no, reason)
        print(f"\n  [NAKANSELA] Nakansela ang request {request_no}.")
    except BrgyError as e:
        print(f"  [MALI] {e}")
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")


# Menu 7
def show_requests():
    print("\n  Filter: [A] Lahat  [P] Pending  [R] Released  [C] Cancelled")
    f = input("  Pumili: ").strip().upper()
    status = {"P": "Pending", "R": "Released", "C": "Cancelled"}.get(f)
    try:
        rows = brgy_db.list_requests(status=status)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not rows:
        print("\n  Walang certificate request na nahanap.")
        return
    print("\n--- LISTAHAN NG CERTIFICATE REQUESTS ---")
    print(f"  {'REQUEST #':<18} {'RESIDENTE':<24} {'CERTIFICATE':<28} {'BAYAD':>8} STATUS")
    print("  " + "-" * 90)
    for c in rows:
        print(
            f"  {c['request_no']:<18} {short(c['full_name'], 24)} "
            f"{short(c['cert_type'], 28)} P{float(c['fee']):>7,.2f} {c['status']}"
        )
    print("  " + "-" * 90)
    print(f"  Kabuuan: {len(rows)}")


# Menu 8
def certificate_report():
    try:
        s = brgy_db.certificate_summary()
        by_type = brgy_db.certificate_by_type()
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    print("\n--- CERTIFICATE REPORT ---")
    print(f"  Kabuuang residente    : {s['total_residents']}")
    print(f"  Kabuuang requests     : {s['total_requests'] or 0}")
    print(f"    Pending             : {s['pending'] or 0}")
    print(f"    Released            : {s['released'] or 0}")
    print(f"    Cancelled           : {s['cancelled'] or 0}")
    print(f"  Bayad na nakolekta    : P {float(s['fees_collected']):,.2f}")
    print(f"  Bayad pa sa pending   : P {float(s['fees_pending']):,.2f}")
    if not by_type:
        print("\n  Wala pang certificate request.")
        return
    print("\n  PER URI NG CERTIFICATE:")
    print(
        f"  {'CERTIFICATE':<34} {'REQUESTS':>9} {'RELEASED':>9} "
        f"{'PENDING':>8} {'KOLEKTA':>12}"
    )
    print("  " + "-" * 76)
    for t in by_type:
        print(
            f"  {short(t['cert_type'], 34)} {t['request_count']:>9} "
            f"{t['released'] or 0:>9} {t['pending'] or 0:>8} "
            f"P{float(t['fees_collected']):>11,.2f}"
        )


# Menu 9
def file_blotter():
    print("\n--- FILE NG BLOTTER RECORD (CREATE) ---")
    blotter_no = brgy_db.next_blotter_no()
    print(f"  Blotter #: {blotter_no}")
    complainant = prompt_value("  Pangalan ng Nagrereklamo: ")
    respondent = prompt_value("  Pangalan ng Inirereklamo: ")
    incident_date = ask_date("  Petsa ng pangyayari (YYYY-MM-DD): ")
    incident_time = ask_time("  Oras ng pangyayari (HH:MM): ")
    print("  Uri ng insidente:")
    incident_type = choose_from(BLOTTER_TYPES, "    Pumili: ")
    location = prompt_value("  Lugar ng pangyayari: ")
    narrative = prompt_value("  Salaysay ng pangyayari: ")
    recorded_by = prompt_value("  Sino ang nagtala (Pangalan): ")
    try:
        brgy_db.add_blotter(
            blotter_no,
            complainant,
            respondent,
            incident_date,
            incident_time,
            incident_type,
            location,
            narrative,
            recorded_by,
        )
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    print(f"\n  [NAITALA] Blotter {blotter_no} - status: Bagong Reklamo.")


# Menu 10
def show_blotters():
    print("\n  Filter: [A] Lahat")
    for i, name in enumerate(BLOTTER_STATUS, start=1):
        print(f"          [{i}] {name}")
    f = input("  Pumili: ").strip().upper()
    status = None
    if f.isdigit() and 1 <= int(f) <= len(BLOTTER_STATUS):
        status = BLOTTER_STATUS[int(f) - 1]
    try:
        rows = brgy_db.list_blotters(status=status)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not rows:
        print("\n  Walang blotter record na nahanap.")
        return
    print("\n--- LISTAHAN NG BLOTTER RECORDS ---")
    print(f"  {'BLOTTER #':<16} {'PETSA':<11} {'NAGREKLAMO':<20} {'STATUS':<24} URI")
    print("  " + "-" * 90)
    for b in rows:
        print(
            f"  {b['blotter_no']:<16} {b['incident_date']} "
            f"{short(b['complainant'], 20)} {short(b['status'], 24)} "
            f"{b['incident_type']}"
        )
    print("  " + "-" * 90)
    print(f"  Kabuuan: {len(rows)}")


# Menu 11
def show_blotter_detail():
    blotter_no = prompt_value("  Blotter #: ").upper()
    try:
        b = brgy_db.find_blotter(blotter_no)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not b:
        print("  [WALA] Hindi matagpuan ang blotter record.")
        return
    render_blotter_card(b)


# Menu 12
def update_blotter_record():
    print("\n--- UPDATE NG BLOTTER (UPDATE) ---")
    blotter_no = prompt_value("  Blotter #: ").upper()
    try:
        b = brgy_db.find_blotter(blotter_no)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not b:
        print("  [WALA] Hindi matagpuan ang blotter record.")
        return
    render_blotter_card(b)
    action = prompt_value("  Aksyon na ginawa (detalyado): ")
    print("  Bagong kalagayan:")
    status = choose_from(BLOTTER_STATUS, "    Pumili: ", current=b["status"])
    try:
        brgy_db.update_blotter(blotter_no, action, status)
        print(f"\n  [NA-UPDATE] {blotter_no} - status: {status}.")
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")


# Menu 13
def edit_resident():
    print("\n--- I-UPDATE ANG RESIDENTE (UPDATE) ---")
    code = prompt_value("  Resident Code: ").upper()
    try:
        r = brgy_db.find_resident(code)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not r:
        print("  [WALA] Hindi matagpuan ang residente.")
        return
    render_resident_card(r)
    print("  (Pindutin lang ang ENTER para panatilihin ang kasalukuyang sagot.)")
    name = prompt_optional(f"  Pangalan [{r['full_name']}]: ", r["full_name"])
    purok = prompt_optional(f"  Purok [{r['purok']}]: ", r["purok"])
    contact = prompt_optional(
        f"  Contact [{r['contact_no'] or '---'}]: ", r["contact_no"]
    )
    current_birth = r["birthdate"].strftime("%Y-%m-%d") if r["birthdate"] else ""
    birth_input = input(f"  Kaarawan [{current_birth or '---'}]: ").strip()
    if birth_input == "":
        birthdate = r["birthdate"]
    else:
        try:
            datetime.strptime(birth_input, "%Y-%m-%d")
            birthdate = birth_input
        except ValueError:
            print("  * Mali ang petsa, hindi na-update.")
            return
    print("  Civil Status:")
    civil = choose_from(CIVIL_STATUS, "    Pumili: ", current=r["civil_status"])
    try:
        brgy_db.update_resident(code, name, purok, contact, birthdate, civil)
        print("\n  [NA-UPDATE] Na-update na ang impormasyon ng residente.")
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")


# Menu 14
def delete_resident_record():
    print("\n--- TANGGALIN ANG RESIDENTE (DELETE) ---")
    code = prompt_value("  Resident Code na tatanggalin: ").upper()
    try:
        r = brgy_db.find_resident(code)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not r:
        print("  [WALA] Hindi matagpuan ang residente.")
        return
    links = brgy_db.resident_links(r)
    render_resident_card(r, links)
    print(f"  [PAALALA] Matatanggal din ang {links['requests']} certificate request niya.")
    konf = input("  Sigurado ka bang tanggalin? (oo/hindi): ").strip().lower()
    if konf not in ("oo", "o", "yes", "y"):
        print("  Kinansela.")
        return
    try:
        brgy_db.delete_resident(code)
        print("  [TINANGGAL] Natanggal na ang residente at mga request niya.")
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")


# Menu 15
def delete_request_record():
    print("\n--- TANGGALIN ANG CERTIFICATE REQUEST (DELETE) ---")
    request_no = prompt_value("  Request # na tatanggalin: ").upper()
    try:
        c = brgy_db.find_request(request_no)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not c:
        print("  [WALA] Hindi matagpuan ang request.")
        return
    render_request_card(c)
    konf = input("  Sigurado ka bang tanggalin? (oo/hindi): ").strip().lower()
    if konf not in ("oo", "o", "yes", "y"):
        print("  Kinansela.")
        return
    try:
        brgy_db.delete_request(request_no)
        print("  [TINANGGAL] Natanggal na ang certificate request.")
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")


# Menu 16
def delete_blotter_record():
    print("\n--- TANGGALIN ANG BLOTTER RECORD (DELETE) ---")
    blotter_no = prompt_value("  Blotter # na tatanggalin: ").upper()
    try:
        b = brgy_db.find_blotter(blotter_no)
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
        return
    if not b:
        print("  [WALA] Hindi matagpuan ang blotter record.")
        return
    render_blotter_card(b)
    konf = input("  Sigurado ka bang tanggalin? (oo/hindi): ").strip().lower()
    if konf not in ("oo", "o", "yes", "y"):
        print("  Kinansela.")
        return
    try:
        brgy_db.delete_blotter(blotter_no)
        print("  [TINANGGAL] Natanggal na ang blotter record.")
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")


# Menu 17
def purge_all():
    print("\n--- TANGGALIN ANG LAHAT (FULL RESET) ---")
    print("  [BABALA] Mabubura ang lahat ng residente, certificate requests,")
    print("            at blotter records. Hindi na ito maibabalik.")
    konf = input("  Tanggalin ang LAHAT? (oo/hindi): ").strip().lower()
    if konf not in ("oo", "o", "yes", "y"):
        print("  Kinansela.")
        return
    konf2 = input("  I-type ang TANGGALIN para kumpirmahin: ").strip().upper()
    if konf2 != "TANGGALIN":
        print("  Kinansela.")
        return
    try:
        c = brgy_db.delete_all_data()
        print(f"  [TINANGGAL] Natanggal ang {c} residente at lahat ng datos.")
    except mysql.connector.Error as e:
        print(f"  [MALI] {e}")
