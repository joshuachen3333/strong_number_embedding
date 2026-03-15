#!/usr/bin/env python3
"""
Bible Reader Development Server

Serves static files from repo root and provides an on-demand verse parsing API.
Port 8080 (avoids viewer_v2's port 8000).

Usage:
    python start_server.py
    python start_server.py --port 8080

API:
    GET /api/parse?chineses=創&chapter=1&verse=1
    GET /api/parse?book=Gen&chapter=1&verse=1
    GET /api/target-sn?version=lcc&model=sonnet&chineses=創&chapter=1          (all available verses)
    GET /api/target-sn?version=lcc&model=sonnet&chineses=創&chapter=1&verse=1  (single verse)
    GET /api/lcc-sn?chineses=創&chapter=1                          (legacy alias, version=lcc)
"""

import http.server
import json
import os
import random
import smtplib
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from email.mime.text import MIMEText

from shared.data.book_data_loader import load_books

PORT = 8080
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
PARSER_DIR = os.path.join(REPO_ROOT, "sn_within_unv_selfgroup_segmentation")
OUTPUT_DIR = os.path.join(PARSER_DIR, "output")
PARSER_SCRIPT = os.path.join(PARSER_DIR, "run_parser_temp.py")
TARGET_SN_DIR = os.path.join(REPO_ROOT, "output")

# ── Review system paths ──────────────────────────────────────────────────
SHOWOFF_DIR = os.path.join(REPO_ROOT, "showoff_finished_4review")
SMTP_CONFIG_FILE = os.path.join(SHOWOFF_DIR, "smtp_config.json")
REVIEWERS_FILE = os.path.join(SHOWOFF_DIR, "reviewers.json")
REVIEWS_FILE = os.path.join(SHOWOFF_DIR, "reviews.json")
SESSIONS_FILE = os.path.join(SHOWOFF_DIR, "sessions.json")
OTP_FILE = os.path.join(SHOWOFF_DIR, "otp_pending.json")

OTP_EXPIRY_SECONDS = 600       # 10 minutes
SESSION_EXPIRY_SECONDS = 604800  # 7 days
_rng = random.SystemRandom()


# ── Review system helpers ────────────────────────────────────────────────

def _load_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.isfile(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_smtp_config():
    if not os.path.isfile(SMTP_CONFIG_FILE):
        return None
    return _load_json(SMTP_CONFIG_FILE)


def _send_email(to_addr, subject, body):
    """Send email via Gmail SMTP. Returns True on success."""
    cfg = _load_smtp_config()
    if not cfg:
        print(f"[Email] SMTP not configured — would send to {to_addr}: {subject}")
        print(f"[Email] Body: {body}")
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = cfg["gmail_user"]
        msg["To"] = to_addr
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(cfg["gmail_user"], cfg["gmail_app_password"])
            s.send_message(msg)
        print(f"[Email] Sent to {to_addr}: {subject}")
        return True
    except Exception as e:
        print(f"[Email] Failed to send to {to_addr}: {e}")
        return False


def _generate_otp():
    return str(_rng.randint(100000, 999999))


def _generate_token():
    return format(_rng.getrandbits(128), '032x')

# Book data from shared/data/books.json
_books = load_books()
CHI_TO_ENG = _books["CHI_TO_ENG"]
VALID_ENG_BOOKS = set(_books["ENG_TO_CHI"].keys())


class BibleServerHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler: serves static files + /api/parse endpoint."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/parse":
            self._handle_parse_api(parsed.query)
        elif parsed.path == "/api/target-sn" or parsed.path == "/api/lcc-sn":
            self._handle_target_sn_api(parsed.query, parsed.path)
        elif parsed.path == "/api/reviews":
            self._handle_get_reviews(parsed.query)
        elif parsed.path == "/api/auth/status":
            self._handle_auth_status()
        elif parsed.path == "/api/approve":
            self._handle_approve(parsed.query)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/auth/request-access":
            self._handle_request_access()
        elif parsed.path == "/api/auth/verify-otp":
            self._handle_verify_otp()
        elif parsed.path == "/api/reviews":
            self._handle_post_review()
        else:
            self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/reviews":
            self._handle_delete_review(parsed.query)
        else:
            self._send_json(404, {"error": "Not found"})

    def do_OPTIONS(self):
        """CORS preflight for POST/DELETE (required for ngrok cross-origin)."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization, ngrok-skip-browser-warning")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def _handle_parse_api(self, query_string):
        """Handle GET /api/parse?chineses=創&chapter=1&verse=1"""
        params = urllib.parse.parse_qs(query_string)

        # Extract book code
        book = None
        if "book" in params:
            book = params["book"][0]
            if book not in VALID_ENG_BOOKS:
                self._send_json(400, {"error": f"Unknown book code: {book}"})
                return
        elif "chineses" in params:
            chi = params["chineses"][0]
            book = CHI_TO_ENG.get(chi)
            if not book:
                self._send_json(400, {"error": f"Unknown Chinese abbreviation: {chi}"})
                return
        else:
            self._send_json(400, {"error": "Missing 'book' or 'chineses' parameter"})
            return

        # Extract chapter and verse
        try:
            chapter = int(params.get("chapter", [None])[0])
            verse = int(params.get("verse", [None])[0])
        except (TypeError, ValueError):
            self._send_json(400, {"error": "Missing or invalid 'chapter'/'verse' parameter"})
            return

        if chapter < 1 or verse < 1:
            self._send_json(400, {"error": "chapter and verse must be positive integers"})
            return

        # Check for existing parsed file
        file_path = os.path.join(OUTPUT_DIR, book, str(chapter), str(verse))
        uncertain_path = file_path + "_uncertain"

        content = None
        is_uncertain = False
        cached = True

        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif os.path.isfile(uncertain_path):
            with open(uncertain_path, "r", encoding="utf-8") as f:
                content = f.read()
            is_uncertain = True
        else:
            # On-demand parsing
            cached = False
            content, is_uncertain = self._run_parser(book, chapter, verse)

        if content is None:
            self._send_json(404, {
                "error": f"Could not parse {book} {chapter}:{verse}",
                "book": book, "chapter": chapter, "verse": verse
            })
            return

        self._send_json(200, {
            "content": content,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "is_uncertain": is_uncertain,
            "cached": cached
        })

    def _handle_target_sn_api(self, query_string, path):
        """Handle GET /api/target-sn?version=lcc&chineses=創&chapter=1[&verse=1]
        Also handles legacy /api/lcc-sn (defaults version=lcc)."""
        params = urllib.parse.parse_qs(query_string)

        # Determine version: explicit param, or "lcc" for legacy /api/lcc-sn
        version = params.get("version", ["lcc"])[0] if path == "/api/target-sn" else "lcc"
        sn_field = f"{version}_sn"

        # Extract book code (same logic as /api/parse)
        book = None
        if "book" in params:
            book = params["book"][0]
            if book not in VALID_ENG_BOOKS:
                self._send_json(400, {"error": f"Unknown book code: {book}"})
                return
        elif "chineses" in params:
            chi = params["chineses"][0]
            book = CHI_TO_ENG.get(chi)
            if not book:
                self._send_json(400, {"error": f"Unknown Chinese abbreviation: {chi}"})
                return
        else:
            self._send_json(400, {"error": "Missing 'book' or 'chineses' parameter"})
            return

        # Extract model (optional, default "sonnet"; backward compat: accept "brand" param)
        model = params.get("model", params.get("brand", ["sonnet"]))[0]

        # Extract chapter (required)
        try:
            chapter = int(params.get("chapter", [None])[0])
        except (TypeError, ValueError):
            self._send_json(400, {"error": "Missing or invalid 'chapter' parameter"})
            return

        if chapter < 1:
            self._send_json(400, {"error": "chapter must be a positive integer"})
            return

        # Extract verse (optional — omit for whole chapter)
        verse = None
        if "verse" in params:
            try:
                verse = int(params["verse"][0])
            except (TypeError, ValueError):
                self._send_json(400, {"error": "Invalid 'verse' parameter"})
                return

        chapter_dir = os.path.join(TARGET_SN_DIR, version, model, book, str(chapter))

        if verse is not None:
            # Single verse mode
            file_path = os.path.join(chapter_dir, f"{verse}.json")
            if not os.path.isfile(file_path):
                self._send_json(404, {
                    "error": f"No {version.upper()}+SN data for {book} {chapter}:{verse}",
                    "book": book, "chapter": chapter, "verse": verse
                })
                return
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._send_json(200, {
                "book": book, "chapter": chapter, "verse": verse,
                "version": version,
                sn_field: data.get(sn_field, ""),
                "confidence": data.get("confidence", 0.0),
                "notes": data.get("notes", [])
            })
        else:
            # Chapter mode — read all verse JSON files
            if not os.path.isdir(chapter_dir):
                self._send_json(404, {
                    "error": f"No {version.upper()}+SN data for {book} chapter {chapter}",
                    "book": book, "chapter": chapter
                })
                return

            verses = {}
            for filename in os.listdir(chapter_dir):
                if filename.endswith(".json"):
                    verse_num = filename[:-5]  # strip .json
                    if verse_num.isdigit():
                        file_path = os.path.join(chapter_dir, filename)
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        verses[verse_num] = {
                            sn_field: data.get(sn_field, ""),
                            "confidence": data.get("confidence", 0.0),
                            "notes": data.get("notes", [])
                        }

            self._send_json(200, {
                "book": book, "chapter": chapter, "version": version,
                "verses": verses, "count": len(verses)
            })

    # ── Auth helpers ────────────────────────────────────────────────────

    def _read_body_json(self, max_size=10000):
        """Read and parse JSON request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0 or length > max_size:
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _get_session(self):
        """Validate Authorization header, return session dict or None."""
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[7:]
        sessions = _load_json(SESSIONS_FILE, {})
        sess = sessions.get(token)
        if not sess:
            return None
        if time.time() > sess.get("expires", 0):
            del sessions[token]
            _save_json(SESSIONS_FILE, sessions)
            return None
        return sess

    def _get_base_url(self):
        """Detect base URL from Host header (for approval links)."""
        host = self.headers.get("Host", "localhost:8989")
        proto = "https" if "ngrok" in host else "http"
        return f"{proto}://{host}"

    def _is_approved(self, email):
        """Check if email is in the approved reviewers list."""
        data = _load_json(REVIEWERS_FILE, {"approved": [], "pending": []})
        return any(r["email"].lower() == email.lower() for r in data.get("approved", []))

    # ── Auth endpoints ───────────────────────────────────────────────────

    def _handle_request_access(self):
        """POST /api/auth/request-access — request OTP or approval."""
        body = self._read_body_json()
        if not body:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        email = str(body.get("email", "")).strip().lower()
        name = str(body.get("name", "")).strip()[:50]
        if not email or "@" not in email:
            self._send_json(400, {"error": "Valid email required"})
            return
        if not name:
            self._send_json(400, {"error": "Name required"})
            return

        if self._is_approved(email):
            # Send OTP directly
            otp = _generate_otp()
            otps = _load_json(OTP_FILE, {})
            otps[email] = {"otp": otp, "name": name, "expires": time.time() + OTP_EXPIRY_SECONDS}
            _save_json(OTP_FILE, otps)

            _send_email(email,
                        "Your Review Access Code / 審閱驗證碼",
                        f"Your one-time code is: {otp}\n您的驗證碼是：{otp}\n\nExpires in 10 minutes.")
            print(f"[Auth] OTP sent to approved reviewer: {email} (code: {otp})")
            self._send_json(200, {"status": "otp_sent", "message": "OTP sent to your email"})
        else:
            # Add to pending, email admin for approval
            data = _load_json(REVIEWERS_FILE, {"approved": [], "pending": []})
            # Check if already pending
            if not any(p["email"].lower() == email for p in data.get("pending", [])):
                data.setdefault("pending", []).append({
                    "email": email, "name": name,
                    "requested": datetime.now(timezone.utc).isoformat()
                })
                _save_json(REVIEWERS_FILE, data)

            # Generate approval token and email admin
            approval_token = _generate_token()
            otps = _load_json(OTP_FILE, {})
            otps[f"approve_{email}"] = {"token": approval_token, "name": name,
                                         "expires": time.time() + 86400}  # 24h
            _save_json(OTP_FILE, otps)

            base_url = self._get_base_url()
            encoded_email = urllib.parse.quote(email)
            approve_url = f"{base_url}/api/approve?email={encoded_email}&token={approval_token}"

            cfg = _load_smtp_config()
            admin_email = cfg["admin_email"] if cfg else None
            if admin_email:
                _send_email(admin_email,
                            f"New reviewer request: {name} ({email})",
                            f"New reviewer access request:\n\n"
                            f"Name: {name}\nEmail: {email}\n\n"
                            f"Click to approve:\n{approve_url}\n\n"
                            f"Link expires in 24 hours.")

            print(f"[Auth] Access requested by {name} ({email})")
            print(f"[Auth] Approval link: {approve_url}")
            self._send_json(200, {"status": "pending_approval",
                                   "message": "Access request sent to admin"})

    def _handle_approve(self, query_string):
        """GET /api/approve?email=x&token=y — admin clicks to approve reviewer."""
        params = urllib.parse.parse_qs(query_string)
        email = params.get("email", [None])[0]
        token = params.get("token", [None])[0]

        if not email or not token:
            self._send_html(400, "<h2>Missing parameters</h2>")
            return

        email = urllib.parse.unquote(email).lower()
        otps = _load_json(OTP_FILE, {})
        key = f"approve_{email}"
        pending = otps.get(key)

        if not pending or pending.get("token") != token:
            self._send_html(400, "<h2>Invalid or expired approval link</h2>")
            return
        if time.time() > pending.get("expires", 0):
            self._send_html(400, "<h2>Approval link expired</h2>")
            return

        name = pending.get("name", email)

        # Add to approved list
        data = _load_json(REVIEWERS_FILE, {"approved": [], "pending": []})
        if not any(r["email"].lower() == email for r in data.get("approved", [])):
            data["approved"].append({
                "email": email, "name": name,
                "added": datetime.now(timezone.utc).isoformat()
            })
        # Remove from pending
        data["pending"] = [p for p in data.get("pending", []) if p["email"].lower() != email]
        _save_json(REVIEWERS_FILE, data)

        # Clean up approval token
        del otps[key]

        # Auto-send OTP to the newly approved reviewer
        otp = _generate_otp()
        otps[email] = {"otp": otp, "name": name, "expires": time.time() + OTP_EXPIRY_SECONDS}
        _save_json(OTP_FILE, otps)

        _send_email(email,
                    "Access Approved — Your Review Code / 審閱權限已核准",
                    f"Your access has been approved!\n您的審閱權限已核准！\n\n"
                    f"Your one-time code is: {otp}\n您的驗證碼是：{otp}\n\n"
                    f"Enter this code in the viewer to start reviewing.\nExpires in 10 minutes.")

        print(f"[Auth] Approved reviewer: {name} ({email}), OTP sent (code: {otp})")
        self._send_html(200,
                        f"<h2>Approved!</h2>"
                        f"<p><strong>{name}</strong> ({email}) has been approved.</p>"
                        f"<p>An OTP has been sent to their email.</p>")

    def _handle_verify_otp(self):
        """POST /api/auth/verify-otp — verify OTP, create session."""
        body = self._read_body_json()
        if not body:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        email = str(body.get("email", "")).strip().lower()
        otp = str(body.get("otp", "")).strip()

        if not email or not otp:
            self._send_json(400, {"error": "Email and OTP required"})
            return

        otps = _load_json(OTP_FILE, {})
        pending = otps.get(email)

        if not pending or pending.get("otp") != otp:
            self._send_json(401, {"error": "Invalid OTP"})
            return
        if time.time() > pending.get("expires", 0):
            self._send_json(401, {"error": "OTP expired"})
            return

        name = pending.get("name", email)

        # Clean up OTP
        del otps[email]
        _save_json(OTP_FILE, otps)

        # Create session
        token = _generate_token()
        sessions = _load_json(SESSIONS_FILE, {})
        sessions[token] = {
            "email": email, "name": name,
            "expires": time.time() + SESSION_EXPIRY_SECONDS,
            "created": datetime.now(timezone.utc).isoformat()
        }
        _save_json(SESSIONS_FILE, sessions)

        print(f"[Auth] Session created for {name} ({email})")
        self._send_json(200, {
            "token": token,
            "reviewer": {"email": email, "name": name},
            "expires_in": SESSION_EXPIRY_SECONDS
        })

    def _handle_auth_status(self):
        """GET /api/auth/status — check session validity."""
        sess = self._get_session()
        if sess:
            self._send_json(200, {
                "authenticated": True,
                "reviewer": {"email": sess["email"], "name": sess["name"]}
            })
        else:
            self._send_json(200, {"authenticated": False})

    # ── Review endpoints ─────────────────────────────────────────────────

    def _handle_get_reviews(self, query_string):
        """GET /api/reviews?book=Gen&chap=1[&sec=1][&brand=claude] — public, no auth needed."""
        params = urllib.parse.parse_qs(query_string)
        book = params.get("book", [None])[0]
        chap_str = params.get("chap", [None])[0]
        brand = params.get("brand", [None])[0]

        if not book or not chap_str:
            self._send_json(400, {"error": "Missing 'book' and 'chap' parameters"})
            return

        try:
            chap = int(chap_str)
        except ValueError:
            self._send_json(400, {"error": "Invalid 'chap'"})
            return

        data = _load_json(REVIEWS_FILE, {"reviews": []})
        filtered = [r for r in data.get("reviews", [])
                     if r["book"] == book and r["chap"] == chap]

        # Filter by brand (reviews without brand field match "claude" for backward compat)
        if brand:
            filtered = [r for r in filtered
                        if r.get("brand", "claude") == brand]

        # Filter by version (reviews without version field match "lcc" for backward compat)
        version = params.get("version", [None])[0]
        if version:
            filtered = [r for r in filtered
                        if r.get("version", "lcc") == version]

        sec_str = params.get("sec", [None])[0]
        if sec_str:
            try:
                filtered = [r for r in filtered if r["sec"] == int(sec_str)]
            except ValueError:
                pass

        self._send_json(200, {"reviews": filtered, "count": len(filtered)})

    def _handle_post_review(self):
        """POST /api/reviews — create review (auth required)."""
        sess = self._get_session()
        if not sess:
            self._send_json(401, {"error": "Authentication required"})
            return

        body = self._read_body_json()
        if not body:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        book = body.get("book", "")
        if book not in VALID_ENG_BOOKS:
            self._send_json(400, {"error": f"Invalid book: {book}"})
            return

        try:
            chap = int(body.get("chap", 0))
            sec = int(body.get("sec", 0))
        except (TypeError, ValueError):
            self._send_json(400, {"error": "Invalid chap/sec"})
            return

        if chap < 1 or sec < 1:
            self._send_json(400, {"error": "chap and sec must be positive"})
            return

        review_type = body.get("type", "")
        if review_type not in ("comment", "suggestion", "approval", "needs_work"):
            self._send_json(400, {"error": "Invalid type"})
            return

        text = str(body.get("text", "")).strip()[:2000]
        brand = str(body.get("brand", "claude")).strip()
        version = str(body.get("version", "lcc")).strip()

        ts_ms = int(time.time() * 1000)
        rand_hex = format(_rng.randint(0, 0xFFFF), '04x')
        review = {
            "id": f"r_{ts_ms}_{rand_hex}",
            "version": version,
            "brand": brand,
            "book": book, "chap": chap, "sec": sec,
            "reviewer_email": sess["email"],
            "reviewer_name": sess["name"],
            "type": review_type,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        data = _load_json(REVIEWS_FILE, {"reviews": []})
        data.setdefault("reviews", []).append(review)
        _save_json(REVIEWS_FILE, data)

        print(f"[Review] {sess['name']}: {review_type} on {book} {chap}:{sec}")
        self._send_json(201, review)

    def _handle_delete_review(self, query_string):
        """DELETE /api/reviews?id=r_xxx — delete own review or admin."""
        sess = self._get_session()
        if not sess:
            self._send_json(401, {"error": "Authentication required"})
            return

        params = urllib.parse.parse_qs(query_string)
        review_id = params.get("id", [None])[0]
        if not review_id:
            self._send_json(400, {"error": "Missing 'id' parameter"})
            return

        data = _load_json(REVIEWS_FILE, {"reviews": []})
        reviews = data.get("reviews", [])
        target = next((r for r in reviews if r["id"] == review_id), None)

        if not target:
            self._send_json(404, {"error": "Review not found"})
            return

        # Allow deleting own reviews or if admin
        cfg = _load_smtp_config()
        admin_email = cfg.get("admin_email", "") if cfg else ""
        if target["reviewer_email"] != sess["email"] and sess["email"] != admin_email:
            self._send_json(403, {"error": "Can only delete your own reviews"})
            return

        data["reviews"] = [r for r in reviews if r["id"] != review_id]
        _save_json(REVIEWS_FILE, data)

        print(f"[Review] Deleted {review_id} by {sess['name']}")
        self._send_json(200, {"deleted": True, "id": review_id})

    def _send_html(self, status_code, html_body):
        """Send an HTML response."""
        full = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
        body = full.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _run_parser(self, book, chapter, verse):
        """Run the parser for a specific verse. Returns (content, is_uncertain) or (None, False)."""
        try:
            result = subprocess.run(
                [sys.executable, PARSER_SCRIPT, "--book", book, str(chapter), str(verse)],
                capture_output=True, text=True, timeout=30,
                cwd=PARSER_DIR
            )

            if result.returncode != 0:
                print(f"[ParseAPI] Parser failed for {book} {chapter}:{verse}: {result.stderr[:200]}")
                return None, False

            # Check if file was created
            file_path = os.path.join(OUTPUT_DIR, book, str(chapter), str(verse))
            uncertain_path = file_path + "_uncertain"

            if os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read(), False
            elif os.path.isfile(uncertain_path):
                with open(uncertain_path, "r", encoding="utf-8") as f:
                    return f.read(), True
            else:
                print(f"[ParseAPI] Parser ran but no output file for {book} {chapter}:{verse}")
                return None, False

        except subprocess.TimeoutExpired:
            print(f"[ParseAPI] Parser timed out for {book} {chapter}:{verse}")
            return None, False
        except Exception as e:
            print(f"[ParseAPI] Error running parser for {book} {chapter}:{verse}: {e}")
            return None, False

    def _send_json(self, status_code, data):
        """Send a JSON response with CORS headers."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Custom log format."""
        if "/api/" in str(args[0]):
            print(f"[API] {args[0]}")
        # Suppress normal file serving logs for less noise


def main():
    port = PORT
    if len(sys.argv) > 1:
        if sys.argv[1] == "--port" and len(sys.argv) > 2:
            port = int(sys.argv[2])
        elif sys.argv[1].isdigit():
            port = int(sys.argv[1])

    os.chdir(REPO_ROOT)

    server = http.server.HTTPServer(("", port), BibleServerHandler)
    print(f"Bible Reader Dev Server")
    print(f"  Static files: http://localhost:{port}/")
    print(f"  Showoff:      http://localhost:{port}/showoff_finished_4review/")
    print(f"  Dual reader:  http://localhost:{port}/dual_reader_right_editor/")
    print(f"  Viewer v2:    http://localhost:{port}/sn_within_unv_selfgroup_segmentation/viewer_v2/")
    print(f"  Parse API:    http://localhost:{port}/api/parse?chineses=創&chapter=1&verse=1")
    print(f"  Target+SN:    http://localhost:{port}/api/target-sn?version=lcc&model=sonnet&chineses=創&chapter=1")
    print(f"  Reviews API:  http://localhost:{port}/api/reviews?book=Gen&chap=1")
    smtp_ok = os.path.isfile(SMTP_CONFIG_FILE)
    print(f"  SMTP:         {'configured' if smtp_ok else 'NOT configured (create smtp_config.json)'}")
    print(f"\nPress Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
