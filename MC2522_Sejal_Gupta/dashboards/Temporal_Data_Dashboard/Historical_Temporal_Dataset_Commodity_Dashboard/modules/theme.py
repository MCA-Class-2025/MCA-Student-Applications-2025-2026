"""Colour themes. Every colour, font and card style used by the CSS and the charts comes from here."""

import colorsys

_LIGHT = ["#2F6BFF", "#FF7A1A", "#10B981", "#8B5CF6", "#EF4444", "#0EA5C6", "#EAB308", "#DB2777", "#65A30D", "#475569"]
_DARK = ["#4CC9F0", "#FFB703", "#2EE6A6", "#B79CFF", "#FF6B8B", "#5EEAD4", "#FDE047", "#F472B6", "#A3E635", "#E2E8F0"]


def _hue(c):
    c = c.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def _palette(mode, accent):
    base = _LIGHT if mode == "light" else _DARK
    far = lambda c: min(abs(_hue(c) - _hue(accent)), 360 - abs(_hue(c) - _hue(accent))) > 40
    return [accent] + [c for c in base if far(c)] + [c for c in base if not far(c)]


def _t(mode, bg, card, text, muted, border, primary, accent, banner, inp, palette,
       font="Inter", page=None, radius=14, shadow=None):
    grid = "rgba(120,130,150,0.20)"
    palette = _palette(mode, accent)
    return dict(mode=mode, bg=bg, card=card, text=text, muted=muted, border=border,
                primary=primary, accent=accent, banner=banner, inp=inp, palette=palette,
                grid=grid, up="#16A34A" if mode == "light" else "#34D399",
                down="#E5484D" if mode == "light" else "#FB7185", other="#9AA5B1", cu="#2563EB" if mode == "light" else "#38BDF8", cd="#F59E0B" if mode == "light" else "#FBBF24",
                font=font, page=page or bg, radius=radius,
                shadow=shadow or ("0 1px 3px rgba(10,30,70,.08)" if mode == "light" else "0 2px 8px rgba(0,0,0,.35)"))

THEMES = {
    "Light Navy": _t("light", "#EEF2F8", "#FFFFFF", "#0B2545", "#4A5E78", "#D8E2EE", "#0B2F6B", "#1F6FEB",
                     "linear-gradient(120deg,#0A1F44 0%,#12306B 60%,#1B4B91 100%)", "#FFFFFF",
                     ["#1F6FEB", "#F28E2B", "#12A150", "#8E5BD0", "#E5484D", "#0C8599", "#E0A800", "#A61E4D", "#59A14F", "#0B2545"],
                     font="Inter"),
    "Dark Navy": _t("dark", "#0A1B35", "#10294D", "#EEF3FB", "#B3C4DE", "#24427A", "#1F6FEB", "#38BDF8",
                    "linear-gradient(120deg,#07142B 0%,#0E2A55 60%,#17407F 100%)", "#0B2140",
                    ["#38BDF8", "#FBBF24", "#34D399", "#C084FC", "#FB7185", "#22D3EE", "#FDE047", "#F472B6", "#A3E635", "#E2E8F0"],
                    font="Inter", page="linear-gradient(160deg,#08162E 0%,#0D2347 100%)"),
    "Deep Teal": _t("dark", "#04201F", "#0B3A3B", "#E8FFFB", "#A9DCD4", "#17666A", "#0F766E", "#2DD4BF",
                    "linear-gradient(120deg,#031817 0%,#0A3536 60%,#0F5C5A 100%)", "#072B2C",
                    ["#2DD4BF", "#FBBF24", "#FB7185", "#60A5FA", "#A3E635", "#C084FC", "#FB923C", "#38BDF8", "#F472B6", "#E5E7EB"],
                    font="Poppins", page="linear-gradient(160deg,#031B1A 0%,#07302F 100%)", radius=18),
    "Charcoal Gold": _t("dark", "#141519", "#22252D", "#F5F5F7", "#B5B8C3", "#3D4150", "#B88700", "#F5B301",
                        "linear-gradient(120deg,#0E0F12 0%,#22252D 60%,#4A3B14 100%)", "#1B1D22",
                        ["#F5B301", "#4FA3FF", "#FF6B6B", "#3DDC97", "#B388FF", "#FF9F43", "#26C6DA", "#F06292", "#C0CA33", "#B0BEC5"],
                        font="IBM Plex Sans", radius=8),
    "Sunrise Sand": _t("light", "#FBF4EA", "#FFFFFF", "#3B2314", "#7A5A44", "#EBD9C4", "#B8470F", "#E8590C",
                       "linear-gradient(120deg,#5A2A0E 0%,#9C3F0D 60%,#E8590C 100%)", "#FFFDF9",
                       ["#E8590C", "#1C7ED6", "#2F9E44", "#9C36B5", "#C92A2A", "#0C8599", "#F59F00", "#862E9C", "#5C940D", "#3B2314"],
                       font="Poppins", page="linear-gradient(160deg,#FFF6EA 0%,#F6E3CC 100%)", radius=20,
                       shadow="0 4px 14px rgba(120,60,10,.12)"),
    "Forest Mint": _t("light", "#EAF5EE", "#FFFFFF", "#12351F", "#4C6B58", "#CFE6D8", "#1B6B3A", "#2F9E44",
                      "linear-gradient(120deg,#0E3B21 0%,#1B6B3A 60%,#2F9E44 100%)", "#FFFFFF",
                      ["#2F9E44", "#1C7ED6", "#F08C00", "#AE3EC9", "#E03131", "#0B7285", "#E8C100", "#C2255C", "#5C7CFA", "#12351F"],
                      font="Nunito", page="linear-gradient(160deg,#EEF8F1 0%,#D7EDDF 100%)", radius=16),
    "Royal Purple": _t("dark", "#17112B", "#251B45", "#F3EEFF", "#C0B2E6", "#42336F", "#7C5CFF", "#A78BFA",
                       "linear-gradient(120deg,#120B26 0%,#2D1E5C 60%,#4B30A3 100%)", "#1D1538",
                       ["#A78BFA", "#FBBF24", "#34D399", "#F472B6", "#60A5FA", "#FB923C", "#22D3EE", "#FDE047", "#F87171", "#E9E5F5"],
                       font="Montserrat", page="linear-gradient(160deg,#130D26 0%,#221840 100%)", radius=18),
    "Slate Mono": _t("light", "#F1F3F6", "#FFFFFF", "#1F2937", "#566170", "#DADFE6", "#1F2937", "#475569",
                     "linear-gradient(120deg,#111827 0%,#1F2937 60%,#374151 100%)", "#FFFFFF",
                     ["#334155", "#2563EB", "#DC2626", "#059669", "#D97706", "#7C3AED", "#0891B2", "#DB2777", "#65A30D", "#94A3B8"],
                     font="IBM Plex Sans", radius=6, shadow="0 1px 2px rgba(0,0,0,.10)"),
}
DEFAULT_THEME = "Light Navy"
