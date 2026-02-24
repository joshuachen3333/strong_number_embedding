"""
Shared book data loader for Python scripts.

Loads canonical book data from shared/data/books.json and provides
lookup dictionaries used across the project.

Usage:
    from shared.data.book_data_loader import load_books

    books = load_books()
    chi_to_eng = books["CHI_TO_ENG"]     # {"創": "Gen", "出": "Exod", ...}
    eng_to_chi = books["ENG_TO_CHI"]     # {"Gen": "創", "Exod": "出", ...}
    book_order = books["BOOK_ORDER"]     # ["Gen", "Exod", "Lev", ...]
    chapters = books["CHAPTERS"]         # {"Gen": 50, "Exod": 40, ...}
    all_books = books["ALL"]             # raw list from books.json
"""

import json
import os

_BOOKS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "books.json")
_cache = None


def load_books() -> dict:
    """Load book data from books.json. Result is cached after first call."""
    global _cache
    if _cache is not None:
        return _cache

    with open(_BOOKS_JSON, "r", encoding="utf-8") as f:
        all_books = json.load(f)

    chi_to_eng = {}
    eng_to_chi = {}
    book_order = []
    chapters = {}

    for b in all_books:
        chi_to_eng[b["chi"]] = b["eng"]
        eng_to_chi[b["eng"]] = b["chi"]
        book_order.append(b["eng"])
        chapters[b["eng"]] = b["chapters"]

    _cache = {
        "CHI_TO_ENG": chi_to_eng,
        "ENG_TO_CHI": eng_to_chi,
        "BOOK_ORDER": book_order,
        "CHAPTERS": chapters,
        "ALL": all_books,
    }
    return _cache
