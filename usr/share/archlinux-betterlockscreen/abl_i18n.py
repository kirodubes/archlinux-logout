"""Translations: gettext catalogs from usr/share/locale, in the chosen language or the system's, else English."""

import gettext
import json
import os
from pathlib import Path

DOMAIN = "archlinux-betterlockscreen"
LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"
PREFS_PATH = Path("~/.config/archlinux-betterlockscreen/prefs.json").expanduser()

NAMES = {
    "en": "English", "nl": "Nederlands", "de": "Deutsch", "es": "Español", "fr": "Français",
    "pt_BR": "Português (Brasil)", "ru": "Русский", "hu": "Magyar", "it": "Italiano", "tr": "Türkçe",
    "pl": "Polski", "ro": "Română", "zh_CN": "简体中文", "ja": "日本語",
}


def available():
    """Return the languages with a catalog, with English first."""
    return ["en", *sorted(path.parent.parent.name for path in LOCALE_DIR.glob(f"*/LC_MESSAGES/{DOMAIN}.mo"))]


def name(code):
    """Return a language's name, or its code if it is not in NAMES."""
    return NAMES.get(code) or NAMES.get(code.split("_")[0]) or code


def _load_prefs():
    try:
        with PREFS_PATH.open(encoding="utf-8") as prefs_file:
            prefs = json.load(prefs_file)
    except (OSError, ValueError):
        return {}
    return prefs if isinstance(prefs, dict) else {}


def chosen():
    """Return the saved language, or None to follow the system."""
    code = _load_prefs().get("language")
    return code if code in available() else None


def save_choice(code):
    """Save a language choice; None follows the system on the next start."""
    prefs = _load_prefs()
    prefs["language"] = code
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PREFS_PATH.open("w", encoding="utf-8") as prefs_file:
        json.dump(prefs, prefs_file, indent=2)


def _system_language():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var, "").split(":")[0].split(".")[0]
        if value:
            return value
    return "en"


_SIBLING = {"pt": "pt_BR", "zh": "zh_CN"}


def _shown(code):
    codes = available()
    base = code.split("_")[0]
    for candidate in (code, base, _SIBLING.get(base)):
        if candidate in codes:
            return candidate
    return "en"


SYSTEM = _shown(_system_language())
ACTIVE = os.environ.get("ABL_LANGUAGE") or chosen()
_SYSTEM_LANGUAGE_VAR = os.environ.get("LANGUAGE")
if ACTIVE:
    os.environ["LANGUAGE"] = ACTIVE

_translation = gettext.translation(DOMAIN, localedir=LOCALE_DIR, languages=[ACTIVE or SYSTEM], fallback=True)
_ = _translation.gettext
ngettext = _translation.ngettext


def N_(text):
    """Mark a string for translation without translating it here."""
    return text


def restore_environment():
    """Restore the session's LANGUAGE so a restarted app follows the system language."""
    if _SYSTEM_LANGUAGE_VAR is None:
        os.environ.pop("LANGUAGE", None)
    else:
        os.environ["LANGUAGE"] = _SYSTEM_LANGUAGE_VAR
