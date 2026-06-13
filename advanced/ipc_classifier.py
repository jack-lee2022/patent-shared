#!/usr/bin/env python3
"""
ipc_classifier.py — IPC/CPC code → tech/effect dimension mapper.

Solves the "矩陣空白" problem by classifying patents using IPC codes
(which are always present) rather than title keywords alone.

Usage:
    from advanced.ipc_classifier import classify_tech, classify_effect, TECH_DIMS, EFFECT_DIMS
"""

try:
    from langdetect import detect as _ld_detect, LangDetectException as _LDE
    _HAS_LANGDETECT = True
except ImportError:
    _HAS_LANGDETECT = False


def _build_text(title: str, abstract: str) -> str:
    """Always include title; append abstract only when detected as English."""
    title    = str(title    or "").strip()
    abstract = str(abstract or "").strip()
    if len(abstract) < 30:
        return title
    if not _HAS_LANGDETECT:
        return f"{title} {abstract}"
    try:
        return f"{title} {abstract}" if _ld_detect(abstract) == "en" else title
    except Exception:
        return f"{title} {abstract}"

# ── IPC prefix → Technology Dimension ───────────────────────────────────────
# Ordered longest-first so more specific codes match before general prefixes.
IPC_TO_TECH = [
    # Electronic cigarette atomizers
    ("A24F40/10", "電阻加熱式"),
    ("A24F40/40", "超聲波壓電"),
    ("A24F40/42", "網孔振動"),
    ("A24F40/44", "陶瓷加熱"),
    ("A24F40/46", "感應加熱"),
    ("A24F40",    "電子煙通用"),
    # Medical nebulizers
    ("A61M11/06", "噴射式(壓縮空氣)"),
    ("A61M11/04", "超聲波壓電"),
    ("A61M11/00", "醫療霧化通用"),
    ("A61M15",    "吸入器"),
    # Ultrasonic / piezo
    ("B06B1/06",  "超聲波壓電"),
    ("B06B1",     "超聲波產生"),
    ("B06B",      "超聲波通用"),
    # Spray / nozzle
    ("B05B17/06", "超聲波霧化噴嘴"),
    ("B05B17",    "超聲波噴霧"),
    ("B05B1",     "噴嘴/氣流"),
    ("B05B7",     "噴嘴/氣流"),
    ("B05B",      "工業噴霧通用"),
    # MEMS / microstructure
    ("B81B",      "MEMS/微結構"),
    ("B81C",      "MEMS/微結構"),
    # Heating elements
    ("H05B3",     "電阻加熱式"),
    ("H05B6",     "感應/微波加熱"),
    # Ceramics / materials
    ("C04B",      "陶瓷材料"),
]

# ── IPC prefix → Effect / Functional Objective ──────────────────────────────
IPC_TO_EFFECT = [
    ("A61M",      "藥物遞送/醫療"),
    ("A24F",      "消費性吸入"),
    ("B05B17",    "精準粒徑控制"),
    ("B06B",      "精準粒徑控制"),
    ("B81B",      "縮小體積/微型化"),
    ("B81C",      "縮小體積/微型化"),
    ("H05B3",     "降低耗能"),
    ("H05B6",     "降低耗能"),
    ("C04B",      "長效壽命"),
]

# ── Title/abstract keyword → Technology Dimension (fallback) ─────────────────
TITLE_TO_TECH = [
    (["heating coil", "resistance wire", "resistive heater", "heating element",
      "resistive heating", "electric resistance", "ohmic heating",
      "nichrome", "kanthal", "wick heater"],                                       "電阻加熱式"),
    (["ceramic", "porous ceramic", "ceramic heater", "alumina",
      "silicon carbide", "zirconia", "ceramic substrate",
      "sintered ceramic", "ceramic element"],                                      "陶瓷加熱"),
    (["vibrating mesh", "mesh plate", "aperture plate", "oscillating mesh",
      "vibrating membrane", "perforated membrane", "mesh nebulizer",
      "vibrating orifice", "mesh atomizer"],                                       "網孔振動"),
    (["ultrasonic", "piezoelectric", "piezo", "acoustic transducer",
      "piezo transducer", "acoustic wave", "high-frequency vibration",
      "ultrasound", "piezocrystal"],                                               "超聲波壓電"),
    (["induction heat", "electromagnetic induction", "inductive heating",
      "rf heating", "eddy current", "susceptor"],                                  "感應加熱"),
    (["nozzle", "pneumatic", "air-blast", "venturi", "compressor",
      "jet nebulizer", "pressurized air", "impactor", "airstream",
      "twin-fluid", "effervescent"],                                               "噴嘴/氣流"),
    (["mems", "microstructure", "micro-fabricat", "silicon chip",
      "micromachined", "photolithography", "etching", "silicon wafer"],            "MEMS/微結構"),
]

# ── Title/abstract keyword → Effect (fallback) ────────────────────────────────
TITLE_TO_EFFECT = [
    (["energy efficient", "power consumption", "low power", "battery life",
      "power saving", "reduced power", "energy saving", "lower energy",
      "heat dissipation", "thermal management"],                                    "降低耗能"),
    (["particle size", "droplet size", "aerosol size", "uniform distribution",
      "droplet diameter", "aerosol generation", "fine mist", "spray uniformity",
      "atomization efficiency", "mist consistency"],                               "精準粒徑控制"),
    (["compact", "portable", "miniatur", "handheld", "wearable",
      "small size", "lightweight", "slim", "micro", "integrated"],                 "縮小體積/微型化"),
    (["low cost", "cost reduc", "manufacturing cost", "inexpensive",
      "affordable", "mass production", "simplified structure",
      "reduced component", "fewer parts"],                                          "降低成本"),
    (["leak", "seal", "anti-leak", "prevent spill", "safety",
      "leakage prevention", "sealing structure", "waterproof",
      "child-proof", "tamper", "overflow"],                                        "安全性/防漏"),
    (["durability", "lifespan", "long-term", "wear resistant",
      "longevity", "lifetime", "reliability", "anti-corrosion",
      "corrosion resistant", "oxidation resistant", "robust"],                     "長效壽命"),
    (["drug delivery", "pulmonary", "inhalation therapy", "nebulization",
      "medication", "pharmaceutical", "therapeutic", "bronchial",
      "respiratory", "inhaler", "aerosol therapy", "medical device"],             "藥物遞送/醫療"),
    (["flavor", "taste", "aroma", "nicotine", "tobacco",
      "e-liquid", "vaping", "vape", "electronic cigarette",
      "smoking experience", "throat hit"],                                         "消費性吸入"),
]

# All known dimension labels (for matrix axes)
TECH_DIMS = [
    "電阻加熱式", "陶瓷加熱", "感應加熱", "網孔振動",
    "超聲波壓電", "噴嘴/氣流", "MEMS/微結構",
    "電子煙通用", "醫療霧化通用", "其他",
]

EFFECT_DIMS = [
    "降低耗能", "精準粒徑控制", "縮小體積/微型化",
    "降低成本", "安全性/防漏", "長效壽命",
    "藥物遞送/醫療", "消費性吸入", "未分類",
]


def _match_ipc(ipc_str: str, mapping: list) -> str | None:
    """Return first matching label from IPC mapping list (longest-prefix wins).

    ipc_str may be a semicolon-separated list of codes; each code is tested.
    """
    if not ipc_str:
        return None
    codes = [c.strip().upper().replace(" ", "") for c in str(ipc_str).split(";") if c.strip()]
    for code in codes:
        for prefix, label in mapping:
            if code.startswith(prefix.upper()):
                return label
    return None


def _match_title(text: str, mapping: list) -> str | None:
    """Return first matching label from keyword mapping list."""
    t = str(text).lower()
    for keywords, label in mapping:
        if any(kw in t for kw in keywords):
            return label
    return None


def classify_tech(ipc_str: str, title: str = "", abstract: str = "") -> str:
    """
    Classify patent into a technology dimension.
    Priority: IPC code > title keywords > abstract keywords (English only) > fallback.
    """
    result = _match_ipc(ipc_str, IPC_TO_TECH)
    if result:
        return result
    combined = _build_text(title, abstract)
    result = _match_title(combined, TITLE_TO_TECH)
    return result or "其他"


def classify_effect(ipc_str: str, title: str = "", abstract: str = "") -> list:
    """
    Classify patent into one or more effect dimensions.
    Returns a list (patents can serve multiple functional goals).
    All IPC codes in ipc_str are checked so multi-purpose patents get multiple effects.
    Abstract is used only when detected as English.
    """
    effects = []

    # Check every IPC code in the (possibly semicolon-joined) string
    if ipc_str:
        for code in str(ipc_str).split(";"):
            code = code.strip()
            if not code:
                continue
            for prefix, label in IPC_TO_EFFECT:
                if code.upper().replace(" ", "").startswith(prefix.upper()):
                    if label not in effects:
                        effects.append(label)

    combined = _build_text(title, abstract)
    for keywords, label in TITLE_TO_EFFECT:
        if any(kw in combined.lower() for kw in keywords):
            if label not in effects:
                effects.append(label)

    return effects or ["未分類"]


if __name__ == "__main__":
    # Quick self-test
    tests = [
        ("A24F40/10", "Electronic cigarette with resistance heating coil", ""),
        ("B06B1/06",  "Ultrasonic piezoelectric atomizer",                 ""),
        ("A61M11/00", "Nebulizer for drug delivery pulmonary",             ""),
        ("B05B17/06", "Ultrasonic nozzle for uniform particle size",       ""),
        ("B81B",      "MEMS microstructure portable inhaler",              ""),
        ("",          "Vaporizer device",                                  "ceramic heater low power"),
    ]
    print(f"{'IPC':<15} {'Tech':<20} {'Effects'}")
    print("-" * 60)
    for ipc, title, abstract in tests:
        tech    = classify_tech(ipc, title, abstract)
        effects = classify_effect(ipc, title, abstract)
        print(f"{ipc:<15} {tech:<20} {', '.join(effects)}")
