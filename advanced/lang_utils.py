"""
lang_utils.py — Language detection utility for patent classifiers.

Used by ipc_classifier.py to avoid keyword mismatches on non-English abstracts
(garbled Japanese / Russian / German machine-translated text).
"""

try:
    from langdetect import detect as _detect
    _HAS_LANGDETECT = True
except ImportError:
    _HAS_LANGDETECT = False


def is_english(text: str, min_len: int = 30) -> bool:
    """Return True if text is detected as English.
    Returns False if text is too short or detection fails."""
    text = str(text or "").strip()
    if len(text) < min_len:
        return False
    if not _HAS_LANGDETECT:
        return True  # assume usable when library unavailable
    try:
        return _detect(text) == "en"
    except Exception:
        return True


def build_classification_text(title: str, abstract: str) -> str:
    """
    Build text for keyword classification.
    Always includes title (usually English on Google Patents even for JP/CN/RU patents).
    Appends abstract only when detected as English — non-English abstracts are
    dropped to prevent garbled characters from causing keyword mismatches.
    """
    title    = str(title    or "").strip()
    abstract = str(abstract or "").strip()

    if is_english(abstract):
        return f"{title} {abstract}".strip()
    return title
