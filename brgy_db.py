# ===== PROBLEMA =====
# Mano-mano pa ang pagtala ng mga residente, certificate requests, at blotter
# sa barangay. Nawawala ang record ng bayad, hindi alam kung ilan ang pending
# na certificate, at walang malinaw na status ng bawat blotter case.
#
# ===== SOLUSYON =====
# Barangay Certificate & Blotter System na may resident CRUD, certificate
# request at release (may fee at request #), blotter records na may status,
# at mga report ng pending at nakolektang bayad.

import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

import mysql.connector
from mysql.connector import Error


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "barangay_db")


class BrgyError(Exception):
    """Mali sa transaksyon ng barangay (wala ang residente, atbp.)."""


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )


def test_connection():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM residents LIMIT 1")
            cursor.fetchone()
            return True, "Koneksyon sa Barangay database ay maayos na."
        return False, "Hindi makakonekta sa database."
    except Error as error:
        return False, str(error)
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


# Residences
def next_resident_code():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT resident_code FROM residents "
            "ORDER BY LENGTH(resident_code) DESC, resident_code DESC LIMIT 1"
        )
        result = cursor.fetchone()
        if not result:
            return "RES-0001"
        try:
            num = int(result[0].split("-")[1]) + 1
            return f"RES-{num:04d}"
        except (IndexError, ValueError):
            return "RES-0001"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def add_resident(code, full_name, purok, contact_no, birthdate, civil_status):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO residents
                (resident_code, full_name, purok, contact_no, birthdate, civil_status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (code, full_name, purok, contact_no, birthdate, civil_status),
        )
        connection.commit()
        return cursor.lastrowid
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def find_resident(code):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM residents WHERE resident_code = %s", (code,))
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def list_residents(search=None):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        sql = """
            SELECT r.resident_code, r.full_name, r.purok, r.contact_no,
                   r.birthdate, r.civil_status, r.date_registered,
                   (SELECT COUNT(*) FROM certificate_requests c
                    WHERE c.resident_code = r.resident_code) AS request_count
            FROM residents r
        """
        params = ()
        if search:
            sql += " WHERE r.full_name LIKE %s OR r.purok LIKE %s"
            params = (f"%{search}%", f"%{search}%")
        sql += " ORDER BY r.full_name"
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def update_resident(code, full_name, purok, contact_no, birthdate, civil_status):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE residents
            SET full_name = %s, purok = %s, contact_no = %s,
                birthdate = %s, civil_status = %s
            WHERE resident_code = %s
            """,
            (full_name, purok, contact_no, birthdate, civil_status, code),
        )
        connection.commit()
        return cursor.rowcount > 0
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def delete_resident(code):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM residents WHERE resident_code = %s", (code,))
        connection.commit()
        return cursor.rowcount > 0
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def resident_links(resident):
    """Bilang ng certificate requests at blotter na sangkot ang residente."""
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(*) AS requests FROM certificate_requests "
            "WHERE resident_code = %s",
            (resident["resident_code"],),
        )
        requests = cursor.fetchone()["requests"]
        like = f"%{resident['full_name']}%"
        cursor.execute(
            "SELECT COUNT(*) AS blotters FROM blotter_records "
            "WHERE complainant LIKE %s OR respondent LIKE %s",
            (like, like),
        )
        blotters = cursor.fetchone()["blotters"]
        return {"requests": requests, "blotters": blotters}
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


# Certificate requests
def next_request_no():
    year = datetime.now().strftime("%Y")
    prefix = f"CERT-{year}-"
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT request_no FROM certificate_requests "
            "WHERE request_no LIKE %s ORDER BY LENGTH(request_no) DESC, request_no DESC LIMIT 1",
            (f"{prefix}%",),
        )
        result = cursor.fetchone()
        if not result:
            return f"{prefix}0001"
        try:
            num = int(result[0].split("-")[-1]) + 1
            return f"{prefix}{num:04d}"
        except (IndexError, ValueError):
            return f"{prefix}0001"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def add_request(request_no, resident_code, cert_type, purpose, fee, remarks):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO certificate_requests
                (request_no, resident_code, cert_type, purpose, fee, status, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (request_no, resident_code, cert_type, purpose, fee, "Pending", remarks),
        )
        connection.commit()
        return cursor.lastrowid
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def find_request(request_no):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.*, r.full_name, r.purok
            FROM certificate_requests c
            JOIN residents r ON r.resident_code = c.resident_code
            WHERE c.request_no = %s
            """,
            (request_no,),
        )
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def list_requests(status=None, resident_code=None):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        sql = """
            SELECT c.request_no, c.resident_code, r.full_name, r.purok,
                   c.cert_type, c.purpose, c.fee, c.status, c.requested_at,
                   c.released_at, c.issued_by, c.remarks
            FROM certificate_requests c
            JOIN residents r ON r.resident_code = c.resident_code
        """
        conditions = []
        params = []
        if status:
            conditions.append("c.status = %s")
            params.append(status)
        if resident_code:
            conditions.append("c.resident_code = %s")
            params.append(resident_code)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY c.requested_at DESC, c.request_no DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def release_request(request_no, issued_by):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT status FROM certificate_requests WHERE request_no = %s FOR UPDATE",
            (request_no,),
        )
        row = cursor.fetchone()
        if not row:
            raise BrgyError("Hindi matagpuan ang certificate request.")
        if row["status"] == "Released":
            raise BrgyError("Na-release na ang certificate na ito.")
        if row["status"] == "Cancelled":
            raise BrgyError("Nakakansela ang request na ito. Gumawa ng bago.")
        cursor.execute(
            """
            UPDATE certificate_requests
            SET status = 'Released', released_at = NOW(), issued_by = %s
            WHERE request_no = %s
            """,
            (issued_by, request_no),
        )
        connection.commit()
        return True
    except (Error, BrgyError):
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def cancel_request(request_no, remarks=None):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT status FROM certificate_requests WHERE request_no = %s FOR UPDATE",
            (request_no,),
        )
        row = cursor.fetchone()
        if not row:
            raise BrgyError("Hindi matagpuan ang certificate request.")
        if row["status"] == "Released":
            raise BrgyError("Na-release na ito, hindi na makansela.")
        cursor.execute(
            "UPDATE certificate_requests SET status = 'Cancelled', remarks = %s "
            "WHERE request_no = %s",
            (remarks, request_no),
        )
        connection.commit()
        return True
    except (Error, BrgyError):
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def delete_request(request_no):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM certificate_requests WHERE request_no = %s", (request_no,)
        )
        connection.commit()
        return cursor.rowcount > 0
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def certificate_summary():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT COUNT(*) AS total_requests,
                   SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
                   SUM(CASE WHEN status = 'Released' THEN 1 ELSE 0 END) AS released,
                   SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                   COALESCE(SUM(CASE WHEN status = 'Released' THEN fee ELSE 0 END), 0)
                       AS fees_collected,
                   COALESCE(SUM(CASE WHEN status = 'Pending' THEN fee ELSE 0 END), 0)
                       AS fees_pending
            FROM certificate_requests
            """
        )
        summary = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) AS total FROM residents")
        summary["total_residents"] = cursor.fetchone()["total"]
        return summary
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def certificate_by_type():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT cert_type,
                   COUNT(*) AS request_count,
                   SUM(CASE WHEN status = 'Released' THEN 1 ELSE 0 END) AS released,
                   SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
                   COALESCE(SUM(CASE WHEN status = 'Released' THEN fee ELSE 0 END), 0)
                       AS fees_collected
            FROM certificate_requests
            GROUP BY cert_type
            ORDER BY request_count DESC, cert_type
            """
        )
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


# Blotter
def next_blotter_no():
    year = datetime.now().strftime("%Y")
    prefix = f"BLT-{year}-"
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT blotter_no FROM blotter_records "
            "WHERE blotter_no LIKE %s ORDER BY LENGTH(blotter_no) DESC, blotter_no DESC LIMIT 1",
            (f"{prefix}%",),
        )
        result = cursor.fetchone()
        if not result:
            return f"{prefix}0001"
        try:
            num = int(result[0].split("-")[-1]) + 1
            return f"{prefix}{num:04d}"
        except (IndexError, ValueError):
            return f"{prefix}0001"
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def add_blotter(
    blotter_no,
    complainant,
    respondent,
    incident_date,
    incident_time,
    incident_type,
    location,
    narrative,
    recorded_by,
):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO blotter_records
                (blotter_no, complainant, respondent, incident_date, incident_time,
                 incident_type, location, narrative, status, recorded_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                blotter_no,
                complainant,
                respondent,
                incident_date,
                incident_time,
                incident_type,
                location,
                narrative,
                "Bagong Reklamo",
                recorded_by,
            ),
        )
        connection.commit()
        return cursor.lastrowid
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def find_blotter(blotter_no):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM blotter_records WHERE blotter_no = %s", (blotter_no,)
        )
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def list_blotters(status=None, name=None):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        sql = "SELECT * FROM blotter_records"
        conditions = []
        params = []
        if status:
            conditions.append("status = %s")
            params.append(status)
        if name:
            conditions.append("(complainant LIKE %s OR respondent LIKE %s)")
            params.extend([f"%{name}%", f"%{name}%"])
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY recorded_at DESC, blotter_no DESC"
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def update_blotter(blotter_no, action_taken, status):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE blotter_records SET action_taken = %s, status = %s "
            "WHERE blotter_no = %s",
            (action_taken, status, blotter_no),
        )
        connection.commit()
        return cursor.rowcount > 0
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def delete_blotter(blotter_no):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM blotter_records WHERE blotter_no = %s", (blotter_no,)
        )
        connection.commit()
        return cursor.rowcount > 0
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def blotter_summary():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT COUNT(*) AS total_cases,
                   SUM(CASE WHEN status = 'Bagong Reklamo' THEN 1 ELSE 0 END) AS new_cases,
                   SUM(CASE WHEN status = 'Mediation' THEN 1 ELSE 0 END) AS mediation,
                   SUM(CASE WHEN status = 'Naayos na' THEN 1 ELSE 0 END) AS settled,
                   SUM(CASE WHEN status = 'Isinangguni sa Pulis' THEN 1 ELSE 0 END) AS referred
            FROM blotter_records
            """
        )
        return cursor.fetchone()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def delete_all_data():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM residents")
        result = cursor.fetchone()
        total = result[0] if result else 0
        cursor.execute("DELETE FROM certificate_requests")
        cursor.execute("DELETE FROM blotter_records")
        cursor.execute("DELETE FROM residents")
        connection.commit()
        return total
    except Error:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
