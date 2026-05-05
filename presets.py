"""PMX 表情预设套装。

每条目为 (name, name_e, category)。category ∈ SYSTEM/EYEBROW/EYE/MOUTH/OTHER。
首版只创建空 shape key（顶点零偏移），用户后续手动 sculpt 或从其他 PMX 导入。
"""

STANDARD_38 = [
    # ----- 眉 / Eyebrow -----
    ("真面目",   "serious",   "EYEBROW"),
    ("困る",     "sadness",   "EYEBROW"),
    ("にこり",   "cheerful",  "EYEBROW"),
    ("怒り",     "anger",     "EYEBROW"),
    ("上",       "up",        "EYEBROW"),
    ("下",       "down",      "EYEBROW"),

    # ----- 目 / Eye -----
    ("まばたき", "blink",     "EYE"),
    ("笑い",     "smile",     "EYE"),
    ("ウィンク", "wink",      "EYE"),
    ("ウィンク2", "wink2",    "EYE"),
    ("ウィンク右", "wink_R",  "EYE"),
    ("ウィンク2右", "wink2_R","EYE"),
    ("はぅ",     "howawa",    "EYE"),
    ("なごみ",   "calm",      "EYE"),
    ("びっくり", "surprise",  "EYE"),
    ("じと目",   "stare",     "EYE"),
    ("キリッ",   "shaprp",    "EYE"),
    ("はちゅ目", "starry_eyes","EYE"),

    # ----- 口 / Mouth -----
    ("あ",       "a",         "MOUTH"),
    ("い",       "i",         "MOUTH"),
    ("う",       "u",         "MOUTH"),
    ("え",       "e",         "MOUTH"),
    ("お",       "o",         "MOUTH"),
    ("あ2",      "a2",        "MOUTH"),
    ("ん",       "n",         "MOUTH"),
    ("▲",        "triangle",  "MOUTH"),
    ("∧",        "down_v",    "MOUTH"),
    ("ω",        "omega",     "MOUTH"),
    ("ω□",       "omega_box", "MOUTH"),
    ("はんっ!",  "han",       "MOUTH"),
    ("にやり",   "smirk",     "MOUTH"),
    ("にっこり", "grin",      "MOUTH"),
    ("ぺろっ",   "tongue_out","MOUTH"),
    ("てへぺろ", "tehepero",  "MOUTH"),
    ("口角上げ", "mouth_up",  "MOUTH"),
    ("口角下げ", "mouth_dn",  "MOUTH"),
    ("口横広げ", "mouth_wide","MOUTH"),
    ("歯無し下", "no_teeth",  "MOUTH"),
]

EXTRA_EMOTION_KIT = [
    ("照れ",     "blush",     "OTHER"),
    ("涙",       "tear",      "OTHER"),
    ("青ざめ",   "pale",      "OTHER"),
    ("汗",       "sweat",     "OTHER"),
    ("！",       "exclaim",   "OTHER"),
    ("？",       "question",  "OTHER"),
    ("怒マーク", "anger_mark","OTHER"),
    ("hide",     "hide",      "SYSTEM"),
]


PRESETS = {
    "STANDARD_38": {
        "desc": "MMD 标准 38 表情（眉×6 / 目×12 / 口×20）",
        "items": STANDARD_38,
    },
    "EMOTION_KIT": {
        "desc": "情绪附加（照れ/涙/汗/感叹号 等 8 项）",
        "items": EXTRA_EMOTION_KIT,
    },
    "FULL": {
        "desc": "STANDARD_38 + EMOTION_KIT（46 项全包）",
        "items": STANDARD_38 + EXTRA_EMOTION_KIT,
    },
}
