# ===== PROBLEMA =====
# Mano-mano pa ang pagtala ng mga residente, certificate requests, at blotter
# sa barangay. Nawawala ang record ng bayad, hindi alam kung ilan ang pending
# na certificate, at walang malinaw na status ng bawat blotter case.
#
# ===== SOLUSYON =====
# Barangay Certificate & Blotter System na may resident CRUD, certificate
# request at release, blotter records, at reports.

import brgy_db
import brgy_desk


def brgy_menu():
    print("\n" + "=" * 62)
    print("   BARANGAY CERTIFICATE & BLOTTER SYSTEM")
    print("=" * 62)
    print("  [1] Mag-register ng Residente - CREATE")
    print("  [2] Listahan ng mga Residente - READ")
    print("  [3] Profile ng Residente - READ")
    print("  [4] Request ng Certificate - CREATE")
    print("  [5] Release ng Certificate - UPDATE")
    print("  [6] Kanselahin ang Certificate Request - UPDATE")
    print("  [7] Listahan ng Certificate Requests - READ")
    print("  [8] Certificate Report (Bayad at Bilang) - READ")
    print("  [9] File ng Blotter Record - CREATE")
    print("  [10] Listahan ng Blotter Records - READ")
    print("  [11] Detalye ng Blotter - READ")
    print("  [12] Update ng Blotter (Aksyon/Status) - UPDATE")
    print("  [13] I-update ang Residente - UPDATE")
    print("  [14] Tanggalin ang Residente - DELETE")
    print("  [15] Tanggalin ang Certificate Request - DELETE")
    print("  [16] Tanggalin ang Blotter Record - DELETE")
    print("  [17] Tanggalin ang LAHAT (Full Reset) - DELETE")
    print("  [0] Lumabas - EXIT")
    print("=" * 62)


def brgy_cli():
    ok, msg = brgy_db.test_connection()
    print(f"\n  {msg}")
    if not ok:
        print("  Paki-import muna ang 'schema_brgy.sql' sa XAMPP/MySQL.")
        return
    while True:
        brgy_menu()
        ch = input("\n  Ano'ng aksyon ang gagawin? : ").strip()
        if ch == "1":
            brgy_desk.register_resident()
        elif ch == "2":
            brgy_desk.show_residents()
        elif ch == "3":
            brgy_desk.show_resident_profile()
        elif ch == "4":
            brgy_desk.request_certificate()
        elif ch == "5":
            brgy_desk.release_certificate()
        elif ch == "6":
            brgy_desk.cancel_certificate()
        elif ch == "7":
            brgy_desk.show_requests()
        elif ch == "8":
            brgy_desk.certificate_report()
        elif ch == "9":
            brgy_desk.file_blotter()
        elif ch == "10":
            brgy_desk.show_blotters()
        elif ch == "11":
            brgy_desk.show_blotter_detail()
        elif ch == "12":
            brgy_desk.update_blotter_record()
        elif ch == "13":
            brgy_desk.edit_resident()
        elif ch == "14":
            brgy_desk.delete_resident_record()
        elif ch == "15":
            brgy_desk.delete_request_record()
        elif ch == "16":
            brgy_desk.delete_blotter_record()
        elif ch == "17":
            brgy_desk.purge_all()
        elif ch == "0":
            print("\n  Isinasara ang koneksyon sa database...")
            print("  Program terminated successfully.")
            print("  Sige, paalam!")
            break
        else:
            print("\n  * Hindi tamang pagpili.")


if __name__ == "__main__":
    brgy_cli()
