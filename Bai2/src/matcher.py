"""
matcher.py - So khớp sự kiện và xử lý dữ kiện đầu vào.

Người dùng có thể nhập chất theo nhiều cách:
  * Công thức chính xác     : H2SO4, NaCl            -> so khớp chính xác
  * Sai chữ hoa / thường    : h2so4, nacl            -> so khớp không chính xác
  * Chỉ số Unicode          : H₂SO₄                  -> chuẩn hóa rồi so khớp
  * Tên tiếng Việt / Anh    : axit sunfuric, muối ăn, sulfuric acid  -> so khớp ngữ nghĩa
  * Tên không dấu           : axit sunfuric, muoi an -> chuẩn hóa bỏ dấu

Dữ kiện không hợp lệ (ký tự lạ, ký hiệu nguyên tố sai, chất chưa có trong CSTT) được báo lỗi kèm gợi ý các chất gần giống nhất.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

from formula import FormulaError, normalize_formula_text, parse_formula
from knowledge_base import KnowledgeBase

_SEP = re.compile(r"[,;\n+]+")


def strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    nfd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def norm_name(text: str) -> str:
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9() ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class MatchItem:
    raw: str
    formula: str | None = None
    how: str = ""            # cách so khớp
    error: str = ""
    suggestions: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    formulas: list[str] = field(default_factory=list)
    items: list[MatchItem] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[MatchItem]:
        return [i for i in self.items if i.error]

    @property
    def ok(self) -> bool:
        return not self.errors


class Matcher:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.by_lower: dict[str, list[str]] = {}
        self.by_name: dict[str, str] = {}
        for f, c in kb.chemicals.items():
            self.by_lower.setdefault(f.lower(), []).append(f)
            for n in c.names:
                self.by_name.setdefault(norm_name(n), f)
        self._choices = list(kb.chemicals) + [n for c in kb.chemicals.values() for n in c.names]

    def suggest(self, text: str, k: int = 3) -> list[str]:
        cand = difflib.get_close_matches(text, self._choices, n=8, cutoff=0.5)
        cand += difflib.get_close_matches(norm_name(text), list(self.by_name), n=5, cutoff=0.6)
        out: list[str] = []
        for c in cand:
            f = c if c in self.kb.chemicals else self.by_name.get(norm_name(c))
            if f and f not in out:
                out.append(f)
        return out[:k]

    def match_one(self, raw: str) -> MatchItem:
        item = MatchItem(raw=raw)
        text = normalize_formula_text(raw)
        if not text:
            item.error = "Dữ kiện rỗng"
            return item
        # 1) So khớp chính xác theo công thức
        if text in self.kb.chemicals:
            item.formula, item.how = text, "chính xác"
            return item
        # 2) So khớp không phân biệt hoa/thường (chỉ khi duy nhất)
        lower = self.by_lower.get(text.lower(), [])
        if len(lower) == 1:
            item.formula, item.how = lower[0], "công thức (sửa chữ hoa/thường)"
            return item
        # 3) So khớp ngữ nghĩa theo tên gọi (tiếng Việt / tiếng Anh, có hoặc không dấu)
        name_key = norm_name(raw)
        if name_key in self.by_name:
            item.formula, item.how = self.by_name[name_key], "tên gọi"
            return item
        # 4) Không khớp -> phân loại lỗi
        item.suggestions = self.suggest(raw)
        try:
            parse_formula(text)
            item.error = f"'{raw}' đúng cú pháp công thức nhưng chất này chưa có trong CSTT"
        except FormulaError as e:
            if re.search(r"[a-zA-Z]", raw) and " " in raw.strip():
                item.error = f"Không nhận dạng được tên chất '{raw}'"
            else:
                item.error = f"'{raw}' không hợp lệ: {e}"
        return item

    def parse(self, text: str) -> ParseResult:
        """Tách chuỗi nhập (phân cách bởi dấu phẩy, chấm phẩy, dấu +, xuống dòng)."""
        res = ParseResult()
        tokens = [t.strip() for t in _SEP.split(text or "") if t.strip()]
        for tok in tokens:
            item = self.match_one(tok)
            # Người dùng có thể ngăn cách bằng dấu cách: "S H2O NaCl"
            if item.error and " " in tok:
                parts = [self.match_one(p) for p in tok.split()]
                if all(not p.error for p in parts):
                    res.notes.append(f"Đã tách '{tok}' theo dấu cách.")
                    for p in parts:
                        self._accept(res, p)
                    continue
            self._accept(res, item)
        return res

    def _accept(self, res: ParseResult, item: MatchItem) -> None:
        res.items.append(item)
        if item.error:
            return
        if item.formula in res.formulas:
            res.notes.append(f"Bỏ dữ kiện trùng: '{item.raw}' ({item.formula}).")
            return
        res.formulas.append(item.formula)
        if item.how != "chính xác":
            res.notes.append(f"'{item.raw}' → {self.kb.label(item.formula)} (so khớp theo {item.how}).")
