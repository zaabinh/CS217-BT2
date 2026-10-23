"""
knowledge_base.py - Cơ sở tri thức (CSTT) theo mô hình Mạng tính toán mở rộng (M_Frame, F_Conditions)

  * M_Frame      : tập các chất hóa học, mỗi chất là một Frame (Name, Formula, State, Type, Color, Solubility, Atomic mass)
                   -> lưu trong data/chemicals.json
  * F_Conditions : tập các phản ứng f : u(f) -> v(f) kèm điều kiện, tính chất, chất tạo thành, hệ số cân bằng và trọng số (chi phí)
                   -> lưu trong data/reactions.json

Module này cũng cài đặt các tác vụ cơ bản trên CSTT:
  * Cập nhật CSTT: thêm / sửa / xóa chất và phản ứng, khôi phục bản gốc
  * Kiểm tra tính nhất quán: cân bằng nguyên tố, chất chưa khai báo, luật trùng, luật thừa, phát hiện vòng lặp, ...
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from formula import FormulaError, atom_balance, parse_formula, pretty

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Các nhãn điều kiện phản ứng (người dùng có thể bật / tắt khi giải bài toán)
CONDITION_LABELS = {
    "t": "Đun nóng / nhiệt độ cao",
    "xt": "Chất xúc tác",
    "as": "Ánh sáng",
    "dac": "Axit đặc",
    "dpdd": "Điện phân dung dịch / nước",
    "dpnc": "Điện phân nóng chảy",
}
# Chi phí cộng thêm của từng điều kiện -> trọng số w(f) của mạng suy diễn có trọng số
CONDITION_COST = {"t": 1, "xt": 1, "as": 1, "dac": 1, "dpdd": 3, "dpnc": 4}

CHEMICAL_TYPES = ["Metal", "Non-metal", "Oxide", "Acid", "Base", "Amphoteric", "Salt", "Others"]
TYPE_LABELS = {
    "Metal": "Kim loại", "Non-metal": "Phi kim", "Oxide": "Oxit", "Acid": "Axit",
    "Base": "Bazơ", "Amphoteric": "Lưỡng tính", "Salt": "Muối", "Others": "Khác",
}
STATES = {"Solid": "Rắn", "Liquid": "Lỏng", "Gas": "Khí"}
SOLUBILITY = {
    "Soluble": "Tan", "Slightly soluble": "Ít tan", "Insoluble": "Không tan",
    "Universal solvent": "Dung môi", "Reacts with water": "Phản ứng với nước",
}


def default_cost(tags: list[str]) -> int:
    return 1 + sum(CONDITION_COST.get(t, 0) for t in tags)


# --------------------------------------------------------------------------- Frame chất
@dataclass
class Chemical:
    formula: str
    names: list[str]
    state: str = "Solid"
    type: str = "Others"
    color: str = ""
    solubility: str = "Soluble"
    atomic_mass: float | None = None

    @property
    def name_vi(self) -> str:
        return self.names[1] if len(self.names) > 1 else (self.names[0] if self.names else "")

    @property
    def name_en(self) -> str:
        return self.names[0] if self.names else ""

    def label(self) -> str:
        return f"{self.formula} – {self.name_vi}"

    @classmethod
    def from_dict(cls, d: dict) -> "Chemical":
        return cls(
            formula=d["Formula"],
            names=list(d.get("Name", [])),
            state=d.get("State", "Solid"),
            type=d.get("Type", "Others"),
            color=d.get("Color", ""),
            solubility=d.get("Solubility", "Soluble"),
            atomic_mass=d.get("Atomic mass"),
        )

    def to_dict(self) -> dict:
        d = {"Name": self.names, "Formula": self.formula, "State": self.state,
             "Type": self.type, "Color": self.color, "Solubility": self.solubility}
        if self.atomic_mass is not None:
            d["Atomic mass"] = self.atomic_mass
        return d


# --------------------------------------------------------------------------- Luật (phản ứng)
@dataclass
class Reaction:
    id: str
    reactants: list[str]           # u(f) - phần giả thiết
    products: list[str]            # v(f) - phần kết luận
    weights: list[int]             # hệ số cân bằng
    conditions: str = ""           # mô tả điều kiện
    condition_tags: list[str] = field(default_factory=list)
    properties: list[list[str]] = field(default_factory=list)  # [["HCl","khí"], ...]
    cost: int = 1                  # trọng số w(f)
    group: str = ""
    note: str = ""

    @property
    def hyp(self) -> frozenset:
        return frozenset(self.reactants)

    @property
    def goal(self) -> frozenset:
        return frozenset(self.products)

    def allowed(self, enabled_tags: set[str] | None) -> bool:
        """Phản ứng chỉ được dùng khi mọi điều kiện của nó đang được cho phép."""
        if enabled_tags is None:
            return True
        return all(t in enabled_tags for t in self.condition_tags)

    def equation(self, use_pretty: bool = True) -> str:
        marks = {f: ("↑" if p == "khí" else "↓" if p == "kết tủa" else "")
                 for f, p in self.properties}

        def side(subs, ws):
            parts = []
            for f, w in zip(subs, ws):
                txt = pretty(f) if use_pretty else f
                parts.append(f"{w if w != 1 else ''}{txt}{marks.get(f, '')}")
            return " + ".join(parts)

        n = len(self.reactants)
        return f"{side(self.reactants, self.weights[:n])} → {side(self.products, self.weights[n:])}"

    def tags_text(self) -> str:
        return ", ".join(CONDITION_LABELS.get(t, t) for t in self.condition_tags) or "Không"

    @classmethod
    def from_dict(cls, d: dict) -> "Reaction":
        tags = list(d.get("condition_tags", []))
        return cls(
            id=d["id"],
            reactants=list(d["if"]),
            products=list(d["then"]),
            weights=[int(w) for w in d.get("weights", [1] * (len(d["if"]) + len(d["then"])))],
            conditions=d.get("conditions", ""),
            condition_tags=tags,
            properties=[list(p) for p in d.get("properties", [])],
            cost=int(d.get("cost", default_cost(tags))),
            group=d.get("group", ""),
            note=d.get("note", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "if": self.reactants, "then": self.products,
            "weights": self.weights, "conditions": self.conditions,
            "condition_tags": self.condition_tags, "properties": self.properties,
            "cost": self.cost, "group": self.group, "note": self.note,
        }


# --------------------------------------------------------------------------- JSON gọn
def _dump(obj, indent=0) -> str:
    """Ghi JSON dễ đọc: mỗi phần tử một khối, các danh sách ngắn viết trên một dòng."""
    pad = "  " * indent
    if isinstance(obj, dict):
        items = [f'{pad}  {json.dumps(k, ensure_ascii=False)}: {_dump(v, indent + 1).lstrip()}'
                 for k, v in obj.items()]
        return pad + "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj):
        return pad + "[\n" + ",\n".join(_dump(x, indent + 1) for x in obj) + "\n" + pad + "]"
    return pad + json.dumps(obj, ensure_ascii=False)


# --------------------------------------------------------------------------- CSTT
class KnowledgeBase:
    def __init__(self, data_dir: Path | str = DATA_DIR):
        self.data_dir = Path(data_dir)
        self.chemicals: dict[str, Chemical] = {}
        self.reactions: list[Reaction] = []
        self.load()

    # ----- đọc / ghi
    @property
    def chem_file(self) -> Path:
        return self.data_dir / "chemicals.json"

    @property
    def react_file(self) -> Path:
        return self.data_dir / "reactions.json"

    def load(self) -> None:
        chems = json.loads(self.chem_file.read_text(encoding="utf-8"))
        reacts = json.loads(self.react_file.read_text(encoding="utf-8"))
        self.chemicals = {c["Formula"]: Chemical.from_dict(c) for c in chems}
        self.reactions = [Reaction.from_dict(r) for r in reacts]

    def save(self) -> None:
        self.chem_file.write_text(_dump([c.to_dict() for c in self.chemicals.values()]) + "\n",
                                  encoding="utf-8")
        self.react_file.write_text(_dump([r.to_dict() for r in self.reactions]) + "\n",
                                   encoding="utf-8")

    def reset_default(self) -> None:
        """Khôi phục CSTT gốc từ thư mục data/default."""
        for name in ("chemicals.json", "reactions.json"):
            shutil.copyfile(self.data_dir / "default" / name, self.data_dir / name)
        self.load()

    # ----- truy vấn
    def get_reaction(self, rid: str) -> Reaction | None:
        return next((r for r in self.reactions if r.id == rid), None)

    def reactions_using(self, formula: str) -> list[Reaction]:
        return [r for r in self.reactions if formula in r.reactants or formula in r.products]

    def next_reaction_id(self) -> str:
        nums = [int(r.id[1:]) for r in self.reactions if r.id[:1] == "R" and r.id[1:].isdigit()]
        return f"R{(max(nums) + 1 if nums else 1):02d}"

    def atomic_masses(self) -> dict[str, float]:
        out = {}
        for c in self.chemicals.values():
            if c.atomic_mass is not None:
                symbol = "".join(ch for ch in c.formula if not ch.isdigit())
                out[symbol] = c.atomic_mass
        return out

    def label(self, formula: str) -> str:
        c = self.chemicals.get(formula)
        return c.label() if c else formula

    # ----- kiểm tra một phản ứng trước khi thêm/sửa
    def validate_reaction(self, r: Reaction, editing_id: str | None = None) -> list[str]:
        errs = []
        if not r.reactants or not r.products:
            errs.append("Phản ứng phải có ít nhất một chất tham gia và một chất sản phẩm.")
        for f in r.reactants + r.products:
            if f not in self.chemicals:
                errs.append(f"Chất '{f}' chưa có trong CSTT (hãy thêm chất trước).")
        if len(r.weights) != len(r.reactants) + len(r.products):
            errs.append("Số hệ số cân bằng không khớp với số chất.")
        elif any(w <= 0 for w in r.weights):
            errs.append("Hệ số cân bằng phải là số nguyên dương.")
        else:
            try:
                ok, left, right = atom_balance(r.reactants, r.products, r.weights)
                if not ok:
                    errs.append(f"Phương trình chưa cân bằng: vế trái {dict(left)} ≠ vế phải {dict(right)}.")
            except FormulaError as e:
                errs.append(str(e))
        if set(r.reactants) & set(r.products):
            errs.append("Một chất không thể vừa là chất tham gia vừa là sản phẩm.")
        for t in r.condition_tags:
            if t not in CONDITION_LABELS:
                errs.append(f"Nhãn điều kiện '{t}' không hợp lệ.")
        if r.cost <= 0:
            errs.append("Trọng số (chi phí) phải dương.")
        if not r.id.strip():
            errs.append("Mã phản ứng không được rỗng.")
        elif r.id != editing_id and self.get_reaction(r.id):
            errs.append(f"Mã phản ứng '{r.id}' đã tồn tại.")
        for other in self.reactions:
            if other.id in (editing_id, r.id):
                continue
            if (other.hyp == r.hyp and other.goal == r.goal
                    and set(other.condition_tags) == set(r.condition_tags)):
                errs.append(f"Trùng với phản ứng {other.id} đã có (luật trùng).")
        return errs

    # ----- cập nhật CSTT
    def add_reaction(self, r: Reaction) -> list[str]:
        errs = self.validate_reaction(r)
        if not errs:
            self.reactions.append(r)
            self.save()
        return errs

    def update_reaction(self, old_id: str, r: Reaction) -> list[str]:
        errs = self.validate_reaction(r, editing_id=old_id)
        if not errs:
            idx = next(i for i, x in enumerate(self.reactions) if x.id == old_id)
            self.reactions[idx] = r
            self.save()
        return errs

    def delete_reaction(self, rid: str) -> None:
        self.reactions = [r for r in self.reactions if r.id != rid]
        self.save()

    def validate_chemical(self, c: Chemical, editing: str | None = None) -> list[str]:
        errs = []
        try:
            parse_formula(c.formula)
        except FormulaError as e:
            errs.append(str(e))
        if c.formula != editing and c.formula in self.chemicals:
            errs.append(f"Chất {c.formula} đã có trong CSTT.")
        if not c.names or not any(n.strip() for n in c.names):
            errs.append("Cần ít nhất một tên gọi.")
        if c.type not in CHEMICAL_TYPES:
            errs.append(f"Loại chất '{c.type}' không hợp lệ.")
        if editing and c.formula != editing and self.reactions_using(editing):
            errs.append("Không đổi được công thức vì chất đang được dùng trong phản ứng.")
        return errs

    def add_chemical(self, c: Chemical) -> list[str]:
        errs = self.validate_chemical(c)
        if not errs:
            self.chemicals[c.formula] = c
            self.save()
        return errs

    def update_chemical(self, old_formula: str, c: Chemical) -> list[str]:
        errs = self.validate_chemical(c, editing=old_formula)
        if not errs:
            new = {}
            for f, v in self.chemicals.items():
                new[c.formula if f == old_formula else f] = c if f == old_formula else v
            self.chemicals = new
            self.save()
        return errs

    def delete_chemical(self, formula: str) -> list[str]:
        used = self.reactions_using(formula)
        if used:
            return [f"Không xóa được: {formula} đang được dùng trong "
                    f"{', '.join(r.id for r in used)}. Hãy xóa các phản ứng đó trước."]
        self.chemicals.pop(formula, None)
        self.save()
        return []

    # ----- kiểm tra tính nhất quán
    @staticmethod
    def _closure(start: set, rules: list[Reaction]) -> set:
        known, changed = set(start), True
        while changed:
            changed = False
            for r in rules:
                if r.hyp <= known and not r.goal <= known:
                    known |= r.goal
                    changed = True
        return known

    def check_consistency(self) -> list[dict]:
        """Trả về danh sách vấn đề: {level, kind, target, message}.

        level: 'Lỗi' (phải sửa) | 'Cảnh báo' | 'Thông tin'
        """
        issues: list[dict] = []

        def add(level, kind, target, msg):
            issues.append({"level": level, "kind": kind, "target": target, "message": msg})

        # 1. Công thức các chất
        for f in self.chemicals:
            try:
                parse_formula(f)
            except FormulaError as e:
                add("Lỗi", "Công thức sai", f, str(e))

        # 2. Từng phản ứng: chất chưa khai báo, cân bằng, rút gọn vế phải, điều kiện
        for r in self.reactions:
            for f in r.reactants + r.products:
                if f not in self.chemicals:
                    add("Lỗi", "Chất chưa khai báo", r.id, f"{f} chưa có trong tập chất M.")
            if len(r.weights) != len(r.reactants) + len(r.products):
                add("Lỗi", "Hệ số", r.id, "Số hệ số cân bằng khác số chất.")
            else:
                try:
                    ok, left, right = atom_balance(r.reactants, r.products, r.weights)
                    if not ok:
                        add("Lỗi", "Chưa cân bằng", r.id,
                            f"{r.equation()} : trái {dict(left)} ≠ phải {dict(right)}")
                except FormulaError as e:
                    add("Lỗi", "Công thức sai", r.id, str(e))
            common = r.hyp & r.goal
            if common:
                add("Cảnh báo", "Rút gọn vế phải", r.id,
                    f"{', '.join(common)} xuất hiện ở cả hai vế, nên loại khỏi vế phải.")
            for t in r.condition_tags:
                if t not in CONDITION_LABELS:
                    add("Lỗi", "Điều kiện", r.id, f"Nhãn điều kiện '{t}' không hợp lệ.")
            if r.cost <= 0:
                add("Lỗi", "Trọng số", r.id, "Trọng số phải dương.")

        # 3. Luật trùng
        seen: dict = {}
        for r in self.reactions:
            key = (r.hyp, r.goal, frozenset(r.condition_tags))
            if key in seen:
                add("Cảnh báo", "Luật trùng", r.id, f"Trùng hoàn toàn với {seen[key]}.")
            else:
                seen[key] = r.id

        # 4. Luật thừa: goal(r) ⊆ BaoĐóng(hyp(r), R \ {r})
        for r in self.reactions:
            others = [x for x in self.reactions if x.id != r.id]
            if r.goal <= self._closure(set(r.hyp), others):
                add("Thông tin", "Luật thừa (về logic)", r.id,
                    f"{r.equation()} suy được từ các phản ứng khác. Vẫn giữ lại vì "
                    "trong hóa học đây là một cách điều chế khác (điều kiện/chi phí khác).")

        # 5. Phát hiện vòng lặp: r: X -> Y gây vòng lặp nếu X ⊆ BaoĐóng(Y, R)
        for r in self.reactions:
            others = [x for x in self.reactions if x.id != r.id]
            if r.hyp <= self._closure(set(r.goal), others):
                add("Thông tin", "Vòng lặp", r.id,
                    f"Từ sản phẩm của {r.id} có thể điều chế lại chất tham gia. Bộ suy diễn "
                    "tránh lặp vô hạn vì chỉ áp dụng phản ứng sinh ra chất mới.")

        # 6. Chất không xuất hiện trong phản ứng nào
        used = {f for r in self.reactions for f in r.reactants + r.products}
        for f in self.chemicals:
            if f not in used:
                add("Thông tin", "Chất chưa dùng", f,
                    f"{self.label(f)} chưa xuất hiện trong phản ứng nào "
                    "(vẫn dùng để tra cứu, tính khối lượng mol).")
        return issues
