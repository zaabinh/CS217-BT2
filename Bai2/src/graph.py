"""
graph.py - Sinh sơ đồ mạng tính toán (ngôn ngữ DOT của Graphviz).

Mạng được vẽ dưới dạng đồ thị hai phía:
  * nút hình elip  = chất (biến trong M)
  * nút hình hộp   = phản ứng (quan hệ trong F)
  * cung chất -> phản ứng  : chất tham gia u(f)
  * cung phản ứng -> chất  : chất tạo thành v(f)
"""
from __future__ import annotations

from formula import pretty
from knowledge_base import KnowledgeBase, Reaction

C_HYP = "#cdeccf"       # chất ban đầu
C_GOAL = "#ffe08a"      # chất cần điều chế
C_MID = "#dbe9f7"       # chất trung gian
C_BY = "#eeeeee"        # sản phẩm phụ
C_RX = "#ffffff"


def _q(s: str) -> str:
    return '"' + s.replace('"', '\\"') + '"'


def _header(rankdir="LR") -> list[str]:
    return [
        "digraph G {",
        f"  rankdir={rankdir}; bgcolor=transparent; nodesep=0.25; ranksep=0.45;",
        '  node [fontname="Arial", fontsize=12, style=filled];',
        '  edge [color="#555555", arrowsize=0.7];',
    ]


def solution_dot(H, G, steps, rankdir: str = "TB") -> str:
    """Sơ đồ của một lời giải (danh sách Step đã phân tích)"""
    H, G = set(H), set(G)
    needed = set().union(*[s.needed for s in steps]) if steps else set()
    used_inputs = set().union(*[s.reaction.hyp for s in steps]) if steps else set()
    lines = _header(rankdir)
    subs = set(H) | set(G)
    for s in steps:
        subs |= s.reaction.hyp | s.reaction.goal
    for x in sorted(subs):
        if x in G:
            color, extra = C_GOAL, ", penwidth=2"
        elif x in H:
            color, extra = C_HYP, ""
        elif x in needed or x in used_inputs:
            color, extra = C_MID, ""
        else:
            color, extra = C_BY, ', fontcolor="#777777", style="filled,dashed"'
        lines.append(f'  {_q(x)} [label={_q(pretty(x))}, shape=ellipse, fillcolor="{color}"{extra}];')
    for s in steps:
        r = s.reaction
        cond = r.conditions if len(r.conditions) <= 28 else r.conditions[:26] + "…"
        lab = f"Bước {s.index}: {r.id}\\n{cond}" if r.condition_tags else f"Bước {s.index}: {r.id}"
        node = f"step{s.index}"
        lines.append(f'  {node} [label={_q(lab)}, shape=box, fillcolor="{C_RX}", '
                     f'color="#3b6ea5", fontsize=10, style="rounded,filled"];')
        for x in r.reactants:
            lines.append(f"  {_q(x)} -> {node};")
        for x in r.products:
            style = ' [style=dashed, color="#aaaaaa"]' if x in s.byproducts else ""
            lines.append(f"  {node} -> {_q(x)}{style};")
    lines.append("}")
    return "\n".join(lines)


def network_dot(kb: KnowledgeBase, reactions: list[Reaction], highlight: set | None = None) -> str:
    """Sơ đồ một phần mạng tính toán của CSTT (các phản ứng được chọn)"""
    highlight = highlight or set()
    lines = _header()
    subs = set()
    for r in reactions:
        subs |= r.hyp | r.goal
    for x in sorted(subs):
        color = C_GOAL if x in highlight else C_MID
        lines.append(f'  {_q(x)} [label={_q(pretty(x))}, shape=ellipse, fillcolor="{color}"];')
    for r in reactions:
        node = f"rx_{r.id}"
        lines.append(f'  {node} [label={_q(r.id)}, shape=box, fillcolor="{C_RX}", '
                     f'color="#3b6ea5", fontsize=10, style="rounded,filled", '
                     f'tooltip={_q(r.equation())}];')
        for x in r.reactants:
            lines.append(f"  {_q(x)} -> {node};")
        for x in r.products:
            lines.append(f"  {node} -> {_q(x)};")
    lines.append("}")
    return "\n".join(lines)
