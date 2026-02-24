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
    GET /api/lcc-sn?chineses=創&chapter=1          (all available verses)
    GET /api/lcc-sn?chineses=創&chapter=1&verse=1   (single verse)
"""

import http.server
import json
import os
import subprocess
import sys
import urllib.parse

from shared.data.book_data_loader import load_books

PORT = 8080
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
PARSER_DIR = os.path.join(REPO_ROOT, "sn_within_unv_selfgroup_segmentation")
OUTPUT_DIR = os.path.join(PARSER_DIR, "output")
PARSER_SCRIPT = os.path.join(PARSER_DIR, "run_parser_temp.py")
LCC_SN_DIR = os.path.join(REPO_ROOT, "llm_direct_sn_unv2lcc", "output")

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
        elif parsed.path == "/api/lcc-sn":
            self._handle_lcc_sn_api(parsed.query)
        else:
            super().do_GET()

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

    def _handle_lcc_sn_api(self, query_string):
        """Handle GET /api/lcc-sn?chineses=創&chapter=1[&verse=1]"""
        params = urllib.parse.parse_qs(query_string)

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

        chapter_dir = os.path.join(LCC_SN_DIR, book, str(chapter))

        if verse is not None:
            # Single verse mode
            file_path = os.path.join(chapter_dir, f"{verse}.json")
            if not os.path.isfile(file_path):
                self._send_json(404, {
                    "error": f"No LCC+SN data for {book} {chapter}:{verse}",
                    "book": book, "chapter": chapter, "verse": verse
                })
                return
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._send_json(200, {
                "book": book, "chapter": chapter, "verse": verse,
                "lcc_sn": data.get("lcc_sn", ""),
                "confidence": data.get("confidence", 0.0),
                "notes": data.get("notes", [])
            })
        else:
            # Chapter mode — read all verse JSON files
            if not os.path.isdir(chapter_dir):
                self._send_json(404, {
                    "error": f"No LCC+SN data for {book} chapter {chapter}",
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
                            "lcc_sn": data.get("lcc_sn", ""),
                            "confidence": data.get("confidence", 0.0),
                            "notes": data.get("notes", [])
                        }

            self._send_json(200, {
                "book": book, "chapter": chapter,
                "verses": verses, "count": len(verses)
            })

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
    print(f"  Dual reader:  http://localhost:{port}/dual_reader_right_editor/")
    print(f"  Viewer v2:    http://localhost:{port}/sn_within_unv_selfgroup_segmentation/viewer_v2/")
    print(f"  Parse API:    http://localhost:{port}/api/parse?chineses=創&chapter=1&verse=1")
    print(f"  LCC+SN API:   http://localhost:{port}/api/lcc-sn?chineses=創&chapter=1")
    print(f"\nPress Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
