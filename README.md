# Barangay Certificate & Blotter System

Kini nga sistema maoy para sa **barangay hall**: tala sa mga **residente**,
pag-issue sa **barangay certificates** (clearance, residency, indigency, ug uban
pa) nga naay **bayad ug request number**, ug **blotter records** nga naay
status ug action taken.

**Problema:** mano-mano pa ang listahan sa residente, malimtan ang bayad sa
certificate, ug wala'y klaro nga status ang matag blotter case.

**Solusyon:** resident masterlist, certificate request → release flow, blotter
tala nga naay status, ug report sa pending ug nakolekta nga bayad.

## Unsa ang kinahanglan

- **Python 3.8 o mas bag-o**
- **XAMPP** (MySQL/MariaDB)
- **mysql-connector-python**

## 1) I-install ang MySQL connector

```powershell
pip install mysql-connector-python
```

## 2) Sugdi ang XAMPP

1. Ablihi ang **XAMPP Control Panel**.
2. Pindota ang **Start** tapad sa **MySQL**.
3. Siguroha nga **green** ang kolor sa MySQL.

## 3) I-import ang database

1. Ablihi ang `http://localhost/phpmyadmin`.
2. Pindota ang **Import** tab.
3. Pilia ang `schema_brgy.sql` (naa sa sama nga folder).
4. Pindota ang **Go** o **Import**.
5. Siguroha nga makita ang `barangay_db` sa lista sa wala.

## 4) Koneksyon sa database

| Variable | Default |
| --- | --- |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `3306` |
| `DB_USER` | `root` |
| `DB_PASSWORD` | *(walay password)* |
| `DB_NAME` | `barangay_db` |

Kung lahi ang setup:

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_USER = "root"
$env:DB_PASSWORD = ""
$env:DB_NAME = "barangay_db"
```

## 5) Padagana ang sistema

```powershell
cd "C:\Users\suete\Documents\system for sale\barangay_certificate_system"
python main_brgy.py
```

> Kung ibalhin ang folder sa lain nga computer, ilisi ang `cd` path sa
> aktwal nga lokasyon sa folder.

Dapat makita nimo ang **"Koneksyon sa Barangay database ay maayos na."**

## Mga file

| File | Tumong |
| --- | --- |
| `schema_brgy.sql` | Naghimo sa `barangay_db`, `residents`, `certificate_requests`, `blotter_records` |
| `brgy_db.py` | Tanan nga SQL: resident CRUD, certificates, blotter, reports |
| `brgy_desk.py` | Flow sa menu: register, request, release, blotter, delete |
| `main_brgy.py` | Ang CLI menu |
| `test_compile.py` | Pagsusi kung walay syntax error |

## Menu

| Numero | Aksyon |
| --- | --- |
| `1` | Register og bag-ong residente (CREATE) |
| `2` | Listahan sa residente, makit-an pinaagi sa pangalan/purok (READ) |
| `3` | Profile sa residente: certificates ug blotter (READ) |
| `4` | Request og certificate (CREATE) |
| `5` | Release sa certificate (UPDATE) |
| `6` | Kansel sa certificate request (UPDATE) |
| `7` | Listahan sa certificate requests, naay filter (READ) |
| `8` | Certificate report: bilang ug bayad (READ) |
| `9` | File og blotter record (CREATE) |
| `10` | Listahan sa blotter records, naay filter (READ) |
| `11` | Detalye sa blotter (READ) |
| `12` | Update sa blotter: action ug status (UPDATE) |
| `13` | Update sa impormasyon sa residente (UPDATE) |
| `14` | Papasa sa residente, apil ang requests (DELETE) |
| `15` | Papasa sa certificate request (DELETE) |
| `16` | Papasa sa blotter record (DELETE) |
| `17` | Papasa sa **tanan** — full reset (DELETE) |
| `0` | Gula |

> **Pasidaan:** Ang `17` mopapas sa tanan: residente, certificates, ug
> blotter. Kinahanglan i-type ang `oo` ug dayon ang `TANGGALIN`.

## Unsaon paggamit

1. Pindota ang `1` para makarehistro og residente. Awtomatiko ang Resident
   Code (`RES-0001`, `RES-0002`, ...).
2. Pindota ang `4` para mag-request og certificate:
   - I-type ang Resident Code sa residente.
   - Pilia ang uri sa certificate — naay default nga bayad ang matag uri
     (mahimong usbon o i-blangko para default).
   - I-type ang purpose, ug naa kini `Pending` status.
3. Kung i-release na, pindota ang `5`, i-type ang Request # ug ang nag-issue.
   Mahimong `Released` ug maapil na ang bayad sa report.
4. Pindota ang `8` para makita ang total nga nakolekta ug ang pending nga bayad.
5. Para sa reklamo, pindota ang `9`. Awtomatiko ang Blotter #
   (`BLT-2026-0001`, ...). Ang status magsugod sa `Bagong Reklamo`.
6. Pindota ang `12` para magtala sa action taken ug mag-usab sa status
   (`Mediation`, `Naayos na`, `Isinangguni sa Pulis`).
7. Pindota ang `3` para makita ang profile sa residente: iyang mga certificate
   ug mga blotter nga naay iyang pangalan.

## Importante nga lagda

- Ang **Resident Code**, **Request #**, ug **Blotter #** awtomatiko — dili na
  kinahanglan i-type.
- Ang certificate request moagi sa `Pending` → `Released`. Ang `Released` ug
  `Cancelled` dili na ma-release pag-usab.
- Ang bayad sa `Released` ra ang maapil sa **bayad na nakolekta**. Ang
  `Pending` naa sa **bayad pa sa pending**.
- Ang pagpapas sa residente (`14`) mopapas usab sa iyang mga certificate
  request (foreign key `ON DELETE CASCADE`), busa gipangutana kini og
  kumpirmasyon.
- Ang blotter dili automatic nga mapapas kung papason ang residente — magpabilin
  kini isip record sa barangay.

## Giunsa pagtipig ang datos

Ang tanan naa sa MySQL sa `barangay_db`:

- `residents` — masterlist sa residente (pangalan, purok, contact, kaarawan)
- `certificate_requests` — matag request (uri, purpose, bayad, status,
  released_at, issued_by)
- `blotter_records` — matag reklamo (complainant, respondent, salaysay,
  action taken, status)

Ang bayad gigamit ang `DECIMAL(10,2)` aron eksakto ang kuwarta.

## Troubleshooting

| Sayop / Mensahe | Solusyon |
| --- | --- |
| `Can't connect to MySQL server on 'localhost:3306'` | Wala nagdagan ang MySQL. Pindota ang **Start** sa XAMPP. |
| `Unknown database 'barangay_db'` | Wala pa na-import ang `schema_brgy.sql`. |
| `Table 'barangay_db.residents' doesn't exist` | I-import pag-usab ang schema. |
| `Access denied for user 'root'@'localhost'` | I-set ang `DB_PASSWORD`. |
| `ModuleNotFoundError: No module named 'mysql'` | `pip install mysql-connector-python` |
| `Wala` o `Hindi matagpuan` | Sayop ang code / request # / blotter #. Gamita ang `2`, `7`, o `10`. |
| `Na-release na ang certificate` | Usa ra ka release ang gitugot sa matag request. |
| `Duplicate entry` sa code | Naa na kini sa listahan. Pindota ang `13` para update. |

## Backup sa datos

1. Adto sa phpMyAdmin.
2. Pilia ang `barangay_db`.
3. **Export** → **Go**.
4. Tipigi ang `.sql` file.

## Sulayi ang code

```powershell
python test_compile.py
```

Dapat `OK` ang mogawas.
