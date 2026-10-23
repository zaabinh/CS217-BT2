"""
formula.py - Phân tích công thức hóa học và kiểm tra cân bằng phương trình.

Dùng cho tác vụ "Kiểm tra tính nhất quán": một phản ứng trong
CSTT chỉ hợp lệ khi số nguyên tử mỗi nguyên tố ở hai vế bằng nhau (theo hệ số cân bằng "weights").
"""
from __future__ import annotations

import re
from collections import Counter

# Chuyển chỉ số dưới dạng Unicode (H₂SO₄) về chữ số thường (H2SO4)
_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

_TOKEN = re.compile(r"([A-Z][a-z]?|\(|\)|\[|\]|\d+)")

# Bảng ký hiệu nguyên tố hợp lệ 
ELEMENT_SYMBOLS = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si",
    "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni",
    "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Ag", "Cd", "Sn",
    "Sb", "I", "Xe", "Cs", "Ba", "Pt", "Au", "Hg", "Pb",
}


class FormulaError(ValueError):
    """Công thức hóa học không hợp lệ."""


def normalize_formula_text(text: str) -> str:
    """Chuẩn hóa chuỗi công thức: bỏ khoảng trắng, đổi chỉ số Unicode."""
    return text.translate(_SUBSCRIPTS).replace(" ", "").strip()


def parse_formula(formula: str) -> Counter:
    """Trả về số nguyên tử của từng nguyên tố trong công thức.

    >>> dict(parse_formula("Al2(SO4)3"))
    {'Al': 2, 'S': 3, 'O': 12}
    """
    text = normalize_formula_text(formula)
    if not text:
        raise FormulaError("Công thức rỗng")
    tokens = _TOKEN.findall(text)
    if "".join(tokens) != text:
        raise FormulaError(f"Công thức '{formula}' chứa ký tự không hợp lệ")

    stack: list[Counter] = [Counter()]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in "([":
            stack.append(Counter())
            i += 1
        elif tok in ")]":
            if len(stack) == 1:
                raise FormulaError(f"Công thức '{formula}' thừa dấu đóng ngoặc")
            group = stack.pop()
            i += 1
            mult = 1
            if i < len(tokens) and tokens[i].isdigit():
                mult = int(tokens[i])
                i += 1
            for el, n in group.items():
                stack[-1][el] += n * mult
        elif tok.isdigit():
            raise FormulaError(f"Công thức '{formula}' có chỉ số đặt sai vị trí")
        else:
            if tok not in ELEMENT_SYMBOLS:
                raise FormulaError(f"'{tok}' không phải ký hiệu nguyên tố hợp lệ")
            i += 1
            n = 1
            if i < len(tokens) and tokens[i].isdigit():
                n = int(tokens[i])
                i += 1
            stack[-1][tok] += n
    if len(stack) != 1:
        raise FormulaError(f"Công thức '{formula}' thiếu dấu đóng ngoặc")
    return stack[0]


def is_valid_formula(formula: str) -> bool:
    try:
        parse_formula(formula)
        return True
    except FormulaError:
        return False


def atom_balance(reactants: list[str], products: list[str], weights: list[int]):
    """Kiểm tra cân bằng nguyên tố.

    weights gồm hệ số các chất tham gia rồi đến các chất sản phẩm.
    Trả về (cân_bằng: bool, vế_trái: Counter, vế_phải: Counter).
    """
    if len(weights) != len(reactants) + len(products):
        raise FormulaError(
            f"Số hệ số ({len(weights)}) khác số chất ({len(reactants) + len(products)})"
        )
    left, right = Counter(), Counter()
    for f, w in zip(reactants, weights[: len(reactants)]):
        for el, n in parse_formula(f).items():
            left[el] += n * w
    for f, w in zip(products, weights[len(reactants):]):
        for el, n in parse_formula(f).items():
            right[el] += n * w
    return left == right, left, right


def molar_mass(formula: str, atomic_mass: dict[str, float]) -> float:
    """Khối lượng mol của chất (dùng nguyên tử khối lưu trong Frame nguyên tố)."""
    total = 0.0
    for el, n in parse_formula(formula).items():
        if el not in atomic_mass:
            raise FormulaError(f"Chưa có nguyên tử khối của {el}")
        total += atomic_mass[el] * n
    return total


def pretty(formula: str) -> str:
    """Hiển thị công thức với chỉ số dưới Unicode: H2SO4 -> H₂SO₄."""
    sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    out, prev_alpha = [], False
    for ch in formula:
        if ch.isdigit() and prev_alpha:
            out.append(ch.translate(sub))
        else:
            out.append(ch)
            prev_alpha = ch.isalpha() or ch in ")]"
            continue
        # giữ prev_alpha = True để chỉ số nhiều chữ số (vd. O12) vẫn là chỉ số dưới
    return "".join(out)


def balance(reactants: list[str], products: list[str]) -> list[int]:
    """Tự động cân bằng phương trình bằng phương pháp đại số (khử Gauss trên số hữu tỉ).

    Lập ma trận nguyên tố × chất (chất sản phẩm mang dấu âm) rồi tìm vectơ
    nghiệm nguyên dương nhỏ nhất của hệ A·x = 0.
    Ném FormulaError nếu không cân bằng được hoặc có nhiều cách cân bằng.
    """
    from fractions import Fraction
    from math import gcd

    species = reactants + products
    comps = [parse_formula(f) for f in species]
    elements = sorted({el for c in comps for el in c})
    n = len(species)
    A = [[Fraction(comps[j][el] * (1 if j < len(reactants) else -1)) for j in range(n)]
         for el in elements]
    # Khử Gauss - Jordan
    pivots, row = [], 0
    for col in range(n):
        p = next((i for i in range(row, len(A)) if A[i][col] != 0), None)
        if p is None:
            continue
        A[row], A[p] = A[p], A[row]
        pv = A[row][col]
        A[row] = [v / pv for v in A[row]]
        for i in range(len(A)):
            if i != row and A[i][col] != 0:
                f = A[i][col]
                A[i] = [a - f * b for a, b in zip(A[i], A[row])]
        pivots.append(col)
        row += 1
    free = [c for c in range(n) if c not in pivots]
    if len(free) != 1:
        raise FormulaError("Không cân bằng được duy nhất (kiểm tra lại các chất)")
    x = [Fraction(0)] * n
    x[free[0]] = Fraction(1)
    for i, col in enumerate(pivots):
        x[col] = -A[i][free[0]]
    lcm = 1
    for v in x:
        lcm = lcm * v.denominator // gcd(lcm, v.denominator)
    ints = [int(v * lcm) for v in x]
    if all(v < 0 for v in ints):
        ints = [-v for v in ints]
    if any(v <= 0 for v in ints):
        raise FormulaError("Không tìm được hệ số dương - phản ứng không hợp lý")
    g = 0
    for v in ints:
        g = gcd(g, v)
    return [v // g for v in ints]


def parse_equation(text: str):
    """Đọc phương trình dạng '2Na + Cl2 -> 2NaCl' (chấp nhận ->, →, =, ↑, ↓).

    Trả về (chất_tham_gia, sản_phẩm, hệ_số | None nếu không ghi hệ số, tính_chất).
    """
    import re as _re
    t = normalize_formula_text(text).replace("→", "->").replace("=", "->")
    if t.count("->") != 1:
        raise FormulaError("Phương trình phải có đúng một dấu '->'")
    left, right = t.split("->")
    subs_l, subs_r, ws, props, any_coef = [], [], [], [], False
    for side, out in ((left, subs_l), (right, subs_r)):
        for term in side.split("+"):
            if not term:
                raise FormulaError("Thiếu chất trong phương trình")
            m = _re.match(r"^(\d*)(.+?)([↑↓]?)$", term)
            coef, f, mark = m.group(1), m.group(2), m.group(3)
            parse_formula(f)
            any_coef |= bool(coef)
            out.append(f)
            ws.append(int(coef) if coef else 1)
            if mark == "↑":
                props.append([f, "khí"])
            elif mark == "↓":
                props.append([f, "kết tủa"])
    return subs_l, subs_r, (ws if any_coef else None), props
