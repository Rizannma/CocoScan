"""
Internationalization (i18n) Module for CocoScan Farmer Role.
Loads translation dictionaries and provides translation resolution helper functions.
"""

import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Base directory for localization JSON dictionaries
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N_DIR = os.path.join(BASE_DIR, "static", "i18n")

_TRANSLATIONS_CACHE: Dict[str, Dict[str, Any]] = {}


def load_translations(force_reload: bool = False) -> Dict[str, Dict[str, Any]]:
    """Loads and caches translation JSON files."""
    global _TRANSLATIONS_CACHE
    if _TRANSLATIONS_CACHE and not force_reload:
        return _TRANSLATIONS_CACHE

    translations: Dict[str, Dict[str, Any]] = {"en": {}, "tl": {}}
    for lang in ["en", "tl"]:
        filepath = os.path.join(I18N_DIR, f"farmer_strings_{lang}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    translations[lang] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load translation file {filepath}: {e}")
                translations[lang] = {}
        else:
            logger.warning(f"Translation file not found: {filepath}")

    _TRANSLATIONS_CACHE = translations
    return _TRANSLATIONS_CACHE


def get_all_translations(lang: str = "en") -> Dict[str, Any]:
    """Returns the full translation dictionary for a given language."""
    translations = load_translations()
    return translations.get(lang) or translations.get("en") or {}


def resolve_key(data: Dict[str, Any], key: str) -> Optional[Any]:
    """Resolves a dot-notated key in a nested dictionary with alias support."""
    if not data or not key:
        return None
    if key.startswith("pest_knowledge_base.recommendations.initial_items."):
        item = key[len("pest_knowledge_base.recommendations.initial_items."):]
        if "pest_knowledge_base" in data:
            keys = ["pest_knowledge_base", "recommendations", "initial_items", item]
        else:
            keys = ["recommendations", "initial_items", item]
    elif key.startswith("recommendations.initial_items."):
        item = key[len("recommendations.initial_items."):]
        if "pest_knowledge_base" in data and "recommendations" not in data:
            keys = ["pest_knowledge_base", "recommendations", "initial_items", item]
        else:
            keys = ["recommendations", "initial_items", item]
    else:
        keys = list(key.split("."))
    if keys and keys[0] == "scanner" and "scanner" not in data and "scan_page" in data:
        keys[0] = "scan_page"
    elif keys and keys[0] == "scan_page" and "scan_page" not in data and "scanner" in data:
        keys[0] = "scanner"
    elif keys and keys[0] == "modal" and "modal" not in data and "report_modal" in data:
        keys[0] = "report_modal"
    elif keys and keys[0] == "report_modal" and "report_modal" not in data and "modal" in data:
        keys[0] = "modal"
    elif keys and keys[0] == "drafts" and "drafts" not in data and "drafts_page" in data:
        keys[0] = "drafts_page"
    elif keys and keys[0] == "drafts_page" and "drafts_page" not in data and "drafts" in data:
        keys[0] = "drafts"
    elif keys and keys[0] == "reports" and "reports" not in data and "reports_page" in data:
        keys[0] = "reports_page"
    elif keys and keys[0] == "reports_page" and "reports_page" not in data and "reports" in data:
        keys[0] = "reports"
    elif keys and keys[0] == "recommendations" and "recommendations" not in data and "pest_knowledge_base" in data:
        keys = ["pest_knowledge_base", "recommendations"] + keys[1:]
    elif keys and len(keys) >= 2 and keys[0] == "pest_knowledge_base" and keys[1] == "recommendations" and "pest_knowledge_base" not in data and "recommendations" in data:
        keys = ["recommendations"] + keys[2:]

    current = data
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return None
    return current


def t(key: str, lang: Optional[str] = None, default: Optional[Any] = None, **kwargs) -> Any:
    """
    Translates a key for the given language.
    Falls back to English if the translation is missing in the target language.
    Supports formatted string substitution with kwargs.
    """
    translations = load_translations()

    # Determine requested language or default to en
    target_lang = lang if lang in ["en", "tl"] else "en"

    val = resolve_key(translations.get(target_lang, {}), key)
    if val is None and target_lang != "en":
        # Fallback to English
        val = resolve_key(translations.get("en", {}), key)

    if val is None:
        val = default if default is not None else key

    if isinstance(val, str) and kwargs:
        try:
            return val.format(**kwargs)
        except Exception:
            return val

    if isinstance(val, (dict, list)):
        return val

    return str(val) if val is not None else key
