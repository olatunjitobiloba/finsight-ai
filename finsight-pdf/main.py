# pdf_service/main.py
# FinSight AI - PDF Statement Parser
# Supports: UBA, GTBank, Access, Zenith, FirstBank,
#           Stanbic, Fidelity, Sterling, Polaris, FCMB, Wema, Ecobank
# Owner: Margaret

import re
import io
import os
import hashlib
import httpx
import json
from groq import Groq
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from supabase import create_client, Client

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pikepdf
    ENCRYPT_AVAILABLE = True
except ImportError:
    ENCRYPT_AVAILABLE = False

# -------------------------------------------------
# SUPABASE CLIENT
# -------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://sfmosgngefdnvmposqml.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_KEY else None

app = FastAPI(title="FinSight AI - PDF Parser")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# -------------------------------------------------
# REQUEST MODEL
# -------------------------------------------------
class ParseStatementRequest(BaseModel):
    user_id: str
    file_url: str
    password: Optional[str] = ""


class InsightsRequest(BaseModel):
    user_id: str


# -------------------------------------------------
# BANK CONFIGS
# -------------------------------------------------
BANK_CONFIGS = {
    "UBA": {
        "date_keys": ["trans", "date", "day"],
        "desc_keys": ["narration", "remarks", "remark", "description"],
        "debit_keys": ["debit", "withdrawal", "dr"],
        "credit_keys": ["credit", "deposit", "cr"],
        "bal_keys": ["balance", "bal"],
    },
    "GTBank": {
        "date_keys": ["date", "trans date", "day"],
        "desc_keys": ["details", "narration", "description", "particulars"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "Access": {
        "date_keys": ["date", "trans date", "value date"],
        "desc_keys": ["narration", "description", "details", "remarks"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "Zenith": {
        "date_keys": ["date", "trans date"],
        "desc_keys": ["particulars", "narration", "description", "details"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "FirstBank": {
        "date_keys": ["date", "trans date", "posting date"],
        "desc_keys": ["description", "narration", "details", "particulars"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "Stanbic": {
        "date_keys": ["date", "transaction date", "trans date"],
        "desc_keys": ["transaction details", "description", "narration", "details"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal", "running balance"],
    },
    "Fidelity": {
        "date_keys": ["date", "trans date"],
        "desc_keys": ["remarks", "narration", "description", "details"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "Sterling": {
        "date_keys": ["date", "trans date", "value date"],
        "desc_keys": ["narration", "description", "details", "remarks"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "Polaris": {
        "date_keys": ["date", "trans date"],
        "desc_keys": ["description", "narration", "details", "particulars"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "FCMB": {
        "date_keys": ["date", "trans date", "value date"],
        "desc_keys": ["narration", "description", "details", "remarks"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "Wema": {
        "date_keys": ["date", "trans date"],
        "desc_keys": ["narration", "description", "details", "remarks"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal"],
    },
    "Ecobank": {
        "date_keys": ["date", "transaction date", "trans date"],
        "desc_keys": ["description", "narration", "details", "particulars"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal", "running balance"],
    },
    "Unknown": {
        "date_keys": ["date", "trans", "day", "value date", "transaction date"],
        "desc_keys": ["narration", "description", "details", "particulars",
                      "remarks", "remark", "memo", "reference", "ref"],
        "debit_keys": ["debit", "dr", "withdrawal"],
        "credit_keys": ["credit", "cr", "deposit"],
        "bal_keys": ["balance", "bal", "running balance"],
    },
}


# -------------------------------------------------
# CATEGORY MAP
# -------------------------------------------------
CATEGORY_MAP = {
    "Food": ["shoprite", "chicken republic", "dominos", "kfc", "food",
             "restaurant", "eatery", "bukka", "mr biggs", "tastee", "buttery",
             "cafeteria", "canteen", "burrito"],
    "Transport": ["uber", "bolt", "fuel", "petrol", "filling station",
                  "total", "oando", "ardova", "conoil", "transport", "atm wd", "atm"],
    "Bills": ["dstv", "gotv", "electricity", "airtime", "data", "mtn",
              "airtel", "glo", "9mobile", "subscription", "nepa", "phcn",
              "sms charge", "sms/sms", "sms alert", "bank charge",
              "stamp duty", "fgn stamp", "vat"],
    "Shopping": ["jumia", "konga", "slot", "mall", "shopping", "market", "store",
                 "pos pur", "pos purchase", "bookshop", "pos pymt"],
    "Entertainment": ["cinema", "bar", "club", "lounge", "event", "hotel", "ticket",
                      "netflix", "spotify", "web pymt spotify"],
    "Savings": ["piggyvest", "cowrywise", "savings", "stash", "investment",
                "mutual fund", "dollar investment"],
    "Transfer": ["transfer to", "trf to", "nip", "neft", "rtgs", "interbank",
                 "tnf", "tnf-", "mobile trf to", "mobile trf from", "commission mobile"],
    "Income": ["salary", "transfer from", "payment from", "received",
               "credit alert", "reversal", "refund", "dividend",
               "allowance", "remainder", "gift", "ibironke", "fiyinfoluwa", "erioluwa"]
}


# -------------------------------------------------
# NARRATION-BASED TYPE RULES
# -------------------------------------------------
NARRATION_DEBIT_RE = re.compile(
    r"^(VAT\s+MOBILE\s+TRF\s+TO"
    r"|MOBILE\s+TRF\s+TO"
    r"|POS\s+PUR"
    r"|POS\s+PYMT"
    r"|WEB\s+PYMT"
    r"|WEB\s+PUR"
    r"|ATM\s+WD"
    r"|FGN\s+STAMP\s+DUTY"
    r"|SMS\s+ALERT\s+FEE"
    r"|SMS/SMS\s+CHARGES"
    r"|COMMISSION\s+MOBILE\s+TRF\s+TO\s+(?!UBA|COVENANT))",
    re.IGNORECASE
)

NARRATION_CREDIT_RE = re.compile(
    r"^(MOBILE\s+TRF\s+FROM"
    r"|TRANSFER\s+FROM"
    r"|TRF\s+FROM"
    r"|COMMISSION\s+MOBILE\s+TRF\s+TO\s+(UBA|COVENANT|PAY|PPL|AMB))",
    re.IGNORECASE
)


# -------------------------------------------------
# REGEX PATTERNS
# -------------------------------------------------
DATE_RE = re.compile(
    r"\b(\d{1,2}[-\/]\w{3,9}[-\/]\d{2,4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b"
)
AMOUNT_RE = re.compile(r"^[\d,]+\.\d{2}$")
ALL_AMOUNTS_RE = re.compile(r"([\d,]+\.\d{2})")

UBA_LINE_RE = re.compile(
    r"(\d{1,2}-\w{3}-\d{4})"
    r"\s+(\d{1,2}-\w{3}-\d{4})"
    r"\s*(.*?)\s*"
    r"([\d,]+\.\d{2})\s+"
    r"([\d,]+\.\d{2})"
)

JUNK_LINE_RE = re.compile(
    r"^("
    r"\d{10,}"
    r"|\d{4,9}"
    r"|\d{4}\s*-\s*[A-Z]{3}\s+\d+\w*\s+\d{4}"
    r"|Opening Balance|Closing Balance"
    r"|Total Debit|Total Credit"
    r"|TRANS\s+VALUE|DATE\s+DATE\s+NO"
    r"|DATE\s+DATE"
    r"|NARRATION\s+DEBIT|CHQ\."
    r"|Bank Statement|YOUR BANK STATEMENT"
    r"|Retail Accounts|Channel Interaction"
    r"|Channel Usage"
    r")$",
    re.IGNORECASE
)

HEADER_LINE_RE = re.compile(
    r"(hello\s|account\s+type|account\s+no|currency:|opening\s+balance"
    r"|closing\s+balance|total\s+debit|total\s+credit"
    r"|africa.s\s+global|bank\s+statement|covenant\s+university"
    r"|idiroko\s+road|\(\s*\d{2}-\w{3}-\d{4}"
    r"|your\s+bank\s+statement|retail\s+accounts"
    r"|channel\s+interaction|channel\s+usage"
    r"|access\s+bank\s+plc|access\s+bank"
    r"|date\s+date\s+no|date\s+date)",
    re.IGNORECASE
)

LEADING_REF_RE = re.compile(r"^(\d{4,}\s*[\/\-]?\s*)+")
ACCOUNT_FRAG_RE = re.compile(
    r"\d{3}x+\d{2,}-?\(?\w[\w\s\-]*\)?[\s\-]*NGN\s*",
    re.IGNORECASE
)
LEADING_DATE_RE = re.compile(r"^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\s+")


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def _detect_bank(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["access bank plc", "access bank",
                             "retail accounts", "channel interaction",
                             "channel usage frequency",
                             "your bank statement\naccount"]):
        return "Access"
    if any(k in t for k in ["guaranty trust", "gtbank", "gtco", "gt bank"]):
        return "GTBank"
    if "zenith bank" in t:
        return "Zenith"
    if any(k in t for k in ["first bank", "firstbank", "1st bank"]):
        return "FirstBank"
    if "stanbic" in t:
        return "Stanbic"
    if "fidelity bank" in t:
        return "Fidelity"
    if "sterling bank" in t:
        return "Sterling"
    if "polaris bank" in t:
        return "Polaris"
    if any(k in t for k in ["fcmb", "first city"]):
        return "FCMB"
    if "wema bank" in t:
        return "Wema"
    if "ecobank" in t:
        return "Ecobank"
    if any(k in t for k in ["uba", "united bank for africa",
                             "united bank", "u.b.a",
                             "africa's global bank", "africa's global"]):
        return "UBA"
    if re.search(r"\b2\d{9}\b", text):
        return "UBA"
    return "Unknown"


def _extract_account_name(text: str) -> Optional[str]:
    m = re.search(r"Hello\s+([A-Z][A-Z\s]+)!", text)
    if m:
        return m.group(1).strip()
    for line in text.split("\n"):
        line = line.strip()
        if re.match(r"^[A-Z][A-Z\s]{5,}$", line) and len(line) > 8:
            if line in ("YOUR BANK STATEMENT", "BANK STATEMENT",
                        "ACCOUNT STATEMENT", "RETAIL ACCOUNTS",
                        "DATE DATE NO", "DATE DATE"):
                continue
            return line
    return None


def _detect_category(text: str) -> str:
    t = text.lower()
    for cat, kws in CATEGORY_MAP.items():
        if any(kw in t for kw in kws):
            return cat
    return "Uncategorized"


def _clean_amount(raw: str) -> float:
    cleaned = re.sub(r"[₦,\s]", "", str(raw))
    try:
        return abs(float(cleaned))
    except ValueError:
        return 0.0


def _parse_date(raw: str) -> str:
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
        "%d/%m/%y", "%d-%b-%Y", "%d-%b-%y",
        "%d %b %Y", "%d %B %Y", "%d-%B-%Y",
        "%d/%b/%Y", "%d %b %y", "%d/%B/%Y",
        "%Y/%m/%d", "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return str(date.today())


def _is_junk_line(line: str) -> bool:
    return bool(JUNK_LINE_RE.match(line.strip()))


def _clean_uba_description(desc: str, account_name: Optional[str]) -> str:
    if account_name:
        name_pattern = re.compile(
            re.escape(account_name) + r"\s*\(?\s*[-–]?\s*\)?",
            re.IGNORECASE
        )
        desc = name_pattern.sub("", desc)
    desc = ACCOUNT_FRAG_RE.sub("", desc)
    desc = LEADING_REF_RE.sub("", desc)
    desc = DATE_RE.sub("", desc)
    desc = re.sub(r"^[\s\-\/\.]+", "", desc)
    desc = re.sub(r"[\s\-\/\.]+$", "", desc)
    desc = re.sub(r"\s{2,}", " ", desc).strip()
    return desc if len(desc) > 2 else ""


def _infer_type_from_balance(prev: float, curr: float) -> str:
    return "credit" if curr > prev else "debit"


def _narration_type(narration: str) -> Optional[str]:
    if NARRATION_DEBIT_RE.match(narration.strip()):
        return "debit"
    if NARRATION_CREDIT_RE.match(narration.strip()):
        return "credit"
    return None


def _decrypt_pdf(pdf_bytes: bytes, password: str) -> Optional[bytes]:
    if not ENCRYPT_AVAILABLE:
        return pdf_bytes
    try:
        with pikepdf.open(io.BytesIO(pdf_bytes), password=password) as pdf:
            output = io.BytesIO()
            pdf.save(output)
            return output.getvalue()
    except pikepdf.PasswordError:
        return None
    except Exception:
        return pdf_bytes


# -------------------------------------------------
# UBA PARSER
# -------------------------------------------------
def _parse_uba_text(full_text: str) -> list:
    transactions = []
    lines = [l.strip() for l in full_text.split("\n") if l.strip()]
    account_name = _extract_account_name(full_text)
    print(f"[DEBUG] Account name detected: {account_name}")

    pending_narration = []
    prev_balance = None
    table_started = False

    table_header_signal = re.compile(
        r"narration.*debit.*credit.*balance", re.IGNORECASE
    )

    for line in lines:
        if table_header_signal.search(line):
            table_started = True
            pending_narration = []
            continue

        if not table_started:
            continue

        if HEADER_LINE_RE.search(line) or _is_junk_line(line):
            continue

        m = UBA_LINE_RE.match(line)
        if m:
            trans_date = _parse_date(m.group(1))
            inline_narr = m.group(3).strip()
            amount = _clean_amount(m.group(4))
            balance = _clean_amount(m.group(5))

            all_parts = []
            for part in pending_narration:
                cleaned = _clean_uba_description(part, account_name)
                if cleaned and not _is_junk_line(cleaned):
                    all_parts.append(cleaned)

            if inline_narr:
                cleaned_inline = _clean_uba_description(inline_narr, account_name)
                if cleaned_inline and not _is_junk_line(cleaned_inline):
                    all_parts.append(cleaned_inline)

            full_narr = re.sub(r"\s{2,}", " ", " ".join(all_parts)).strip()

            if "opening balance" in full_narr.lower():
                prev_balance = balance
                pending_narration = []
                continue

            if not full_narr:
                full_narr = "Transaction"

            txn_type = _infer_type_from_balance(prev_balance, balance) if prev_balance is not None else "debit"

            if amount > 0:
                transactions.append({
                    "amount": amount,
                    "type": txn_type,
                    "description": full_narr,
                    "category": _detect_category(full_narr),
                    "transaction_date": trans_date,
                    "balance": balance,
                    "bank": "UBA",
                    "source": "pdf"
                })

            prev_balance = balance
            pending_narration = []

        else:
            if (not _is_junk_line(line)
                    and not HEADER_LINE_RE.search(line)
                    and not AMOUNT_RE.match(line.replace(",", ""))
                    and len(line) > 2):
                pending_narration.append(line)

    return transactions


# -------------------------------------------------
# ACCESS BANK PARSER
# -------------------------------------------------
def _parse_access_text(full_text: str) -> list:
    transactions = []
    lines = [l.strip() for l in full_text.split("\n") if l.strip()]
    prev_balance = None
    table_started = False

    access_header = re.compile(
        r"(narration|description).*(debit|withdrawal).*(credit|deposit).*(balance)",
        re.IGNORECASE
    )

    skip_re = re.compile(
        r"(opening balance|closing balance|total debit|total credit"
        r"|brought forward|carried forward|page \d|statement of account"
        r"|account number|account name|sort code|branch|date printed"
        r"|retail accounts|channel interaction|channel usage"
        r"|your bank statement|access bank"
        r"|date\s+narration|narration\s+ref|ref\s+no)",
        re.IGNORECASE
    )

    for line in lines:
        if access_header.search(line):
            table_started = True
            continue

        if not table_started:
            continue

        if skip_re.search(line):
            continue

        date_match = re.match(
            r"^(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\s+(.+)$", line
        )
        if not date_match:
            continue

        txn_date = _parse_date(date_match.group(1))
        rest = date_match.group(2).strip()

        amounts_found = ALL_AMOUNTS_RE.findall(rest)
        if len(amounts_found) < 2:
            continue

        balance = _clean_amount(amounts_found[-1])
        txn_amount = _clean_amount(amounts_found[-2])

        narration = ALL_AMOUNTS_RE.sub("", rest).strip()
        narration = re.sub(r"\s+\w{10,}\s*$", "", narration).strip()
        narration = LEADING_DATE_RE.sub("", narration).strip()
        narration = re.sub(r"\s{2,}", " ", narration)
        if not narration or len(narration) < 3:
            narration = "Transaction"

        narr_type = _narration_type(narration)
        if narr_type:
            txn_type = narr_type
        elif prev_balance is not None:
            txn_type = _infer_type_from_balance(prev_balance, balance)
        else:
            txn_type = "debit"

        if txn_amount > 0:
            transactions.append({
                "amount": round(txn_amount, 2),
                "type": txn_type,
                "description": narration,
                "category": _detect_category(narration),
                "transaction_date": txn_date,
                "balance": balance,
                "bank": "Access",
                "source": "pdf"
            })

        prev_balance = balance

    return transactions


# -------------------------------------------------
# TABLE EXTRACTION
# -------------------------------------------------
def _extract_from_tables(tables: list, bank: str) -> list:
    transactions = []
    config = BANK_CONFIGS.get(bank, BANK_CONFIGS["Unknown"])

    for table in tables:
        if not table or len(table) < 2:
            continue

        headers = [str(h).lower().strip() if h else "" for h in table[0]]
        print(f"[DEBUG] Bank: {bank} | Headers: {headers}")

        def find_col(keys):
            return next((i for i, h in enumerate(headers) if any(k in h for k in keys)), None)

        date_idx = find_col(config["date_keys"])
        desc_idx = find_col(config["desc_keys"])
        debit_idx = find_col(config["debit_keys"])
        credit_idx = find_col(config["credit_keys"])
        bal_idx = find_col(config["bal_keys"])

        prev_balance = None

        for row in table[1:]:
            if not row or all(not c for c in row):
                continue
            try:
                txn_date = (_parse_date(str(row[date_idx]))
                            if date_idx is not None and row[date_idx]
                            else str(date.today()))
                desc = (str(row[desc_idx]).strip()
                        if desc_idx is not None and row[desc_idx] else "") or "Transaction"
                debit = (_clean_amount(row[debit_idx])
                         if debit_idx is not None and row[debit_idx] else 0)
                credit = (_clean_amount(row[credit_idx])
                          if credit_idx is not None and row[credit_idx] else 0)
                balance = (_clean_amount(row[bal_idx])
                           if bal_idx is not None and row[bal_idx] else None)

                if debit > 0:
                    txn_type, amount = "debit", debit
                elif credit > 0:
                    txn_type, amount = "credit", credit
                elif balance is not None and prev_balance is not None:
                    txn_type = _infer_type_from_balance(prev_balance, balance)
                    amount = abs(balance - prev_balance)
                else:
                    prev_balance = balance
                    continue

                if amount > 0:
                    transactions.append({
                        "amount": amount,
                        "type": txn_type,
                        "description": desc,
                        "category": _detect_category(desc),
                        "transaction_date": txn_date,
                        "balance": balance,
                        "bank": bank,
                        "source": "pdf"
                    })
                prev_balance = balance

            except Exception as e:
                print(f"[DEBUG] Row error: {e} | row: {row}")
                continue

    return transactions


# -------------------------------------------------
# GENERIC TEXT FALLBACK
# -------------------------------------------------
def _extract_from_text(full_text: str, bank: str) -> list:
    transactions = []
    pA = re.compile(
        r"(\d{1,2}[-\/]\w{3,9}[-\/]\d{2,4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})"
        r"(?:\s+\d{1,2}[-\/]\w{3,9}[-\/]\d{2,4}|\s+\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})?"
        r"\s+(.{0,80}?)\s+"
        r"([\d,]+\.\d{2})?\s*"
        r"([\d,]+\.\d{2})?\s+"
        r"([\d,]+\.\d{2})"
    )
    prev_balance = None

    for line in full_text.split("\n"):
        line = line.strip()
        if len(line) < 10:
            continue

        m = pA.search(line)
        if m:
            txn_date = _parse_date(m.group(1))
            desc = m.group(2).strip() or "Transaction"
            col3 = _clean_amount(m.group(3)) if m.group(3) else 0
            col4 = _clean_amount(m.group(4)) if m.group(4) else 0
            balance = _clean_amount(m.group(5)) if m.group(5) else None

            if prev_balance is not None and balance is not None:
                txn_type = _infer_type_from_balance(prev_balance, balance)
                amount = col3 if col3 > 0 else col4 if col4 > 0 else abs(balance - prev_balance)
            elif col3 > 0:
                txn_type, amount = "debit", col3
            elif col4 > 0:
                txn_type, amount = "credit", col4
            else:
                prev_balance = balance
                continue

            if amount > 0:
                transactions.append({
                    "amount": amount,
                    "type": txn_type,
                    "description": desc,
                    "category": _detect_category(desc),
                    "transaction_date": txn_date,
                    "balance": balance,
                    "bank": bank,
                    "source": "pdf"
                })
            prev_balance = balance

    return transactions


# -------------------------------------------------
# SHARED PDF PARSE LOGIC
# -------------------------------------------------
def _parse_pdf_bytes(pdf_bytes: bytes, password: str = "", filename: str = "file.pdf") -> dict:
    decrypted = _decrypt_pdf(pdf_bytes, password)
    if decrypted is None:
        return {
            "success": False,
            "filename": filename,
            "reason": "Wrong password or encrypted PDF. Enter the correct password.",
            "transactions": []
        }

    try:
        transactions = []
        with pdfplumber.open(io.BytesIO(decrypted)) as pdf:
            full_text = ""
            all_tables = []

            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n"
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)

            bank = _detect_bank(full_text)
            print(f"[DEBUG] Detected bank: {bank} | Pages: {len(pdf.pages)} | "
                  f"Text: {len(full_text)} | Tables: {len(all_tables)}")

            if bank == "UBA":
                transactions = _parse_uba_text(full_text)
            elif bank == "Access":
                transactions = _parse_access_text(full_text)
                if not transactions and all_tables:
                    transactions = _extract_from_tables(all_tables, bank)
            else:
                if all_tables:
                    transactions = _extract_from_tables(all_tables, bank)
                if not transactions and full_text.strip():
                    transactions = _extract_from_text(full_text, bank)

        if not transactions:
            return {
                "success": False,
                "filename": filename,
                "bank": bank,
                "reason": f"Bank: {bank}. Could not extract transactions.",
                "transactions": []
            }

        return {
            "success": True,
            "filename": filename,
            "bank": bank,
            "transactions": transactions
        }

    except Exception as e:
        return {
            "success": False,
            "filename": filename,
            "reason": f"Parse error: {str(e)}",
            "transactions": []
        }


# -------------------------------------------------
# SUPABASE SAVE HELPER
# -------------------------------------------------
def _save_to_supabase(user_id: str, transactions: list) -> dict:
    saved = 0
    errors = []

    if supabase is None:
        return {"saved": 0, "errors": ["Supabase is not configured. Missing SUPABASE_SERVICE_KEY."]}

    for txn in transactions:
        try:
            txn_date = str(txn.get("transaction_date", ""))
            txn_amount = txn.get("amount", 0)
            txn_type = txn.get("type", "")
            txn_desc = str(txn.get("description", ""))
            txn_desc_prefix = txn_desc[:50]

            # Build a stable, user-scoped transaction fingerprint.
            raw = (
                f"{user_id}|{txn_date}|{txn_amount}|{txn_type}|{txn_desc_prefix}"
            )
            txn_hash = hashlib.sha256(raw.encode()).hexdigest()

            # Fast path: skip if an exact hash already exists.
            existing = (
                supabase.table("transactions")
                .select("id")
                .eq("hash", txn_hash)
                .limit(1)
                .execute()
            )
            if existing.data:
                continue

            # Legacy fallback: match by transaction content for rows created before hash existed.
            content_matches = (
                supabase.table("transactions")
                .select("id,description,hash")
                .eq("user_id", user_id)
                .eq("transaction_date", txn_date)
                .eq("amount", txn_amount)
                .eq("type", txn_type)
                .limit(20)
                .execute()
            )

            matched_row = None
            for row in (content_matches.data or []):
                row_desc_prefix = str(row.get("description") or "")[:50]
                if row_desc_prefix == txn_desc_prefix:
                    matched_row = row
                    break

            if matched_row:
                if not matched_row.get("hash"):
                    supabase.table("transactions").update({"hash": txn_hash}).eq("id", matched_row["id"]).execute()
                continue

            row = {
                "user_id": user_id,
                "amount": txn_amount,
                "type": txn_type,
                "description": txn.get("description"),
                "category": txn.get("category"),
                "transaction_date": txn_date,
                "balance": txn.get("balance"),
                "bank": txn.get("bank"),
                "source": "pdf",
                "hash": txn_hash,
            }
            supabase.table("transactions").insert(row).execute()
            saved += 1
        except Exception as e:
            errors.append(str(e))

    return {"saved": saved, "errors": errors}


# -------------------------------------------------
# GOOGLE DRIVE DOWNLOAD HELPER
# -------------------------------------------------
def _normalize_gdrive_url(url: str) -> str:
    """
    Convert Google Drive viewer/share URL to direct download URL.
    NOTE: Google Drive is unreliable for server downloads.
          Prefer Supabase Storage URLs in production.
    """
    match = re.search(r"drive\.google\.com/file/d/([a-zA-Z0-9_\-]+)", url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


async def _download_pdf(url: str) -> bytes:
    """
    Download a PDF from any public URL.

    Supported sources:
      - Supabase Storage (recommended)
      - Direct PDF links
      - Dropbox (?dl=0 -> ?dl=1)
      - Google Drive (unreliable; prefer Supabase Storage)
    """
    url = _normalize_gdrive_url(url)

    if "dropbox.com" in url:
        url = url.replace("?dl=0", "?dl=1").replace("?dl=0", "?raw=1")

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(url)

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Could not download PDF. HTTP {response.status_code}"
            )

        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The URL returned an HTML page instead of a PDF. "
                    "Please upload the file to Supabase Storage and use that URL instead. "
                    "Example: https://your-project.supabase.co/storage/v1/object/public/statements/file.pdf"
                )
            )

        content = response.content
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Downloaded file is not a valid PDF."
            )

        return content


# -------------------------------------------------
# ROUTE 1 - Direct Upload
# -------------------------------------------------
@app.post("/api/parse/pdf")
async def parse_pdf(
    files: List[UploadFile] = File(...),
    password: str = Form(default="")
):
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="PDF parsing library not available.")

    all_transactions = []
    results = []

    for file in files:
        pdf_bytes = await file.read()
        result = _parse_pdf_bytes(pdf_bytes, password, file.filename)

        if result["success"]:
            all_transactions.extend(result["transactions"])
            results.append({
                "filename": result["filename"],
                "success": True,
                "bank": result["bank"],
                "transactions": len(result["transactions"])
            })
        else:
            results.append({
                "filename": result["filename"],
                "success": False,
                "reason": result.get("reason", "Unknown error"),
                "transactions": 0
            })

    if not all_transactions:
        raise HTTPException(status_code=422, detail={
            "message": "No transactions extracted.",
            "files": results
        })

    return {
        "success": True,
        "total_transactions": len(all_transactions),
        "files": results,
        "transactions": all_transactions
    }


# -------------------------------------------------
# ROUTE 2 - URL Upload + Save to Supabase
# -------------------------------------------------
@app.post("/parse-statement")
async def parse_statement(request: ParseStatementRequest):
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=503,
                            detail="PDF parsing library not available.")
    if supabase is None:
        raise HTTPException(status_code=503,
                            detail="Supabase is not configured. Set SUPABASE_SERVICE_KEY.")

    try:
        pdf_bytes = await _download_pdf(request.file_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400,
                            detail=f"Failed to download PDF: {str(e)}")

    result = _parse_pdf_bytes(
        pdf_bytes,
        password=request.password or "",
        filename=request.file_url.split("/")[-1]
    )

    if not result["success"]:
        raise HTTPException(status_code=422, detail={
            "message": result.get("reason", "Could not extract transactions."),
            "user_id": request.user_id
        })

    transactions = result["transactions"]
    save_result = _save_to_supabase(request.user_id, transactions)

    return {
        "success": True,
        "user_id": request.user_id,
        "bank": result["bank"],
        "total_transactions": len(transactions),
        "saved_to_db": save_result["saved"],
        "db_errors": save_result["errors"],
        "transactions": transactions
    }


# -------------------------------------------------
# ROUTE 3 - Fetch User Transactions
# -------------------------------------------------
@app.get("/transactions/{user_id}")
async def get_transactions(user_id: str):
    if supabase is None:
        raise HTTPException(status_code=503,
                            detail="Supabase is not configured. Set SUPABASE_SERVICE_KEY.")

    try:
        result = (
            supabase.table("transactions")
            .select("*")
            .eq("user_id", user_id)
            .order("transaction_date", desc=True)
            .execute()
        )
        return {
            "success": True,
            "user_id": user_id,
            "total_transactions": len(result.data),
            "transactions": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to fetch transactions: {str(e)}")


# -------------------------------------------------
# ROUTE 4 - AI Insights
# -------------------------------------------------
@app.post("/insights")
async def get_insights(request: InsightsRequest):
    """
    Fetch user transactions from Supabase and generate financial insights via Groq.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        result = (
            supabase.table("transactions")
            .select("*")
            .eq("user_id", request.user_id)
            .order("transaction_date", desc=True)
            .limit(50)
            .execute()
        )
        transactions = result.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")

    if not transactions:
        return {
            "user_id": request.user_id,
            "insights": "No transactions found for this user. Please upload a bank statement first.",
            "transaction_count": 0,
        }

    total_credit = 0.0
    total_debit = 0.0
    category_totals = {}

    for t in transactions:
        amount = float(t.get("amount", 0) or 0)
        txn_type = str(t.get("type", "")).lower().strip()

        if txn_type == "credit":
            total_credit += amount
        elif txn_type == "debit":
            total_debit += amount
        else:
            total_credit += float(t.get("credit", 0) or 0)
            total_debit += float(t.get("debit", 0) or 0)

        cat = t.get("category", "Uncategorized") or "Uncategorized"
        if txn_type == "debit":
            category_totals[cat] = category_totals.get(cat, 0.0) + amount

    category_lines = "\n".join(
        f"  - {cat}: N{amt:,.2f}"
        for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    )

    summary = f"""
User Financial Summary ({len(transactions)} transactions):
- Total Income (Credits):  N{total_credit:,.2f}
- Total Spending (Debits): N{total_debit:,.2f}
- Net Balance Change:      N{total_credit - total_debit:,.2f}

Spending by Category:
{category_lines or '  - No categorized debit transactions found.'}

Sample Transactions (most recent 5):
{json.dumps(transactions[:5], indent=2, default=str)}
"""

    ai_used = True
    ai_warning = None
    insights_text = ""

    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise RuntimeError("GROQ_API_KEY not set")

        client = Groq(api_key=groq_key)
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are FinSight AI, a smart personal finance advisor for Nigerians. "
                        "Analyze the user's bank statement data and give clear, practical, "
                        "friendly insights. Be specific with numbers. Use N for amounts. "
                        "Structure your response with these sections:\n"
                        "1. Income & Spending Overview\n"
                        "2. Top Spending Categories\n"
                        "3. Spending Warnings (if any)\n"
                        "4. 3 Actionable Tips to improve finances\n"
                        "Keep it under 300 words. Be encouraging but honest."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Here is my financial data:\n{summary}",
                },
            ],
            temperature=0.7,
            max_tokens=500,
        )
        insights_text = chat.choices[0].message.content
    except Exception as e:
        ai_used = False
        ai_warning = f"AI insights unavailable: {str(e)}"
        insights_text = (
            "AI insights are temporarily unavailable. Here is a quick summary: "
            f"Income N{total_credit:,.2f}, spending N{total_debit:,.2f}, "
            f"net change N{(total_credit - total_debit):,.2f}. "
            "Review the spending_by_category field for your top debit categories."
        )

    return {
        "user_id": request.user_id,
        "transaction_count": len(transactions),
        "total_income": round(total_credit, 2),
        "total_spending": round(total_debit, 2),
        "net_change": round(total_credit - total_debit, 2),
        "spending_by_category": {k: round(v, 2) for k, v in category_totals.items()},
        "ai_used": ai_used,
        "ai_warning": ai_warning,
        "insights": insights_text,
    }


# -------------------------------------------------
# ROUTE 5 - Health Check
# -------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "pdf_available": PDF_AVAILABLE,
        "encrypt_available": ENCRYPT_AVAILABLE,
        "supabase_configured": bool(SUPABASE_KEY),
        "supported_banks": ["UBA", "Access", "GTBank", "Zenith", "FirstBank",
                            "Stanbic", "Fidelity", "Sterling", "Polaris",
                            "FCMB", "Wema", "Ecobank"]
    }
