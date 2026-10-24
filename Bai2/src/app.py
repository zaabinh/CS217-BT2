"""
app.py - Giao diện Streamlit cho Hệ cơ sở tri thức điều chế chất hóa học.

Chạy:  streamlit run src/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from formula import FormulaError, balance, molar_mass, parse_equation, pretty  # noqa: E402
from graph import network_dot, solution_dot  # noqa: E402
from inference import METHODS, solve  # noqa: E402
from knowledge_base import (CHEMICAL_TYPES, CONDITION_COST, CONDITION_LABELS,  # noqa: E402
                            SOLUBILITY, STATES, TYPE_LABELS, Chemical, KnowledgeBase,
                            Reaction, default_cost)
from matcher import Matcher  # noqa: E402
from testing import load_cases, run_case  # noqa: E402

st.set_page_config(page_title="Hệ CSTT điều chế chất hóa học", page_icon="🧪", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 3.2rem; padding-bottom: 2rem;}
.chip {display:inline-block; padding:2px 10px; margin:2px 4px 2px 0; border-radius:12px;
       font-size:0.88rem; border:1px solid rgba(128,128,128,.35);}
.chip-ok {background:rgba(46,160,67,.12);}
.chip-goal {background:rgba(255,193,7,.18);}
.chip-err {background:rgba(220,53,69,.12);}
.chip-mid {background:rgba(59,110,165,.14);}
.chip-by {background:rgba(128,128,128,.12); border-style:dashed;}
.eq {font-family: "Cambria Math", "Times New Roman", serif; font-size:1.05rem;}
.small {font-size:0.85rem; opacity:.8;}
</style>
""", unsafe_allow_html=True)


# =============================================================================== trạng thái
def get_kb() -> KnowledgeBase:
    if "kb" not in st.session_state:
        st.session_state.kb = KnowledgeBase()
    return st.session_state.kb


def reload_kb():
    try:
        st.session_state.kb = KnowledgeBase()
    except (OSError, ValueError) as error:
        st.error(f"Không nạp được CSTT: {error}")
        return False
    return True


try:
    kb = get_kb()
except (OSError, ValueError) as error:
    st.error(f"Không nạp được CSTT: {error}")
    st.stop()
matcher = Matcher(kb)

DEFAULTS = {
    "hyp_text": "S, H2O, NaCl",
    "goal_text": "Na2SO4, H2SO4, HCl, Na",
    "method": "good",
    "last": None,
    "auto_solve": False,
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
for t in CONDITION_LABELS:
    st.session_state.setdefault(f"cond_{t}", True)

METHOD_OPTIONS = list(METHODS) + ["compare"]
METHOD_LABELS = {**METHODS, "compare": "So sánh cả 4 phương pháp"}


def chip(text, kind="ok"):
    return f'<span class="chip chip-{kind}">{text}</span>'


def enabled_tags() -> set[str]:
    return {t for t in CONDITION_LABELS if st.session_state.get(f"cond_{t}")}


# =============================================================================== callbacks
def cb_load_example(case: dict):
    st.session_state.hyp_text = case["hyp"]
    st.session_state.goal_text = case["goal"]
    st.session_state.method = case["method"]
    tags = case.get("enabled_tags")
    for t in CONDITION_LABELS:
        st.session_state[f"cond_{t}"] = True if tags is None else (t in tags)
    st.session_state.last = None


def cb_set_all_conditions(value: bool):
    for t in CONDITION_LABELS:
        st.session_state[f"cond_{t}"] = value


def cb_add_hypotheses(subs: list[str]):
    cur = st.session_state.hyp_text.strip().rstrip(",")
    st.session_state.hyp_text = (cur + ", " if cur else "") + ", ".join(subs)
    st.session_state.auto_solve = True


# =============================================================================== sidebar
with st.sidebar:
    st.markdown("## Bài 2: Điều chế chất hóa học")
    c1, c2 = st.columns(2)
    c1.metric("Chất (M)", len(kb.chemicals))
    c2.metric("Phản ứng (F)", len(kb.reactions))
    st.markdown(
        "**Mô hình:** Mạng tính toán mở rộng *(M_Frame, F_Conditions)* có trọng số.\n\n"
        "**Bài toán:** cho tập chất ban đầu **H**, tìm dãy phản ứng điều chế tập chất **G**."
    )
    if st.button("Tải lại CSTT từ file", width="stretch"):
        if reload_kb():
            st.rerun()
    with st.expander("Hướng dẫn nhanh"):
        st.markdown(
            "1. Nhập **chất ban đầu** và **chất cần điều chế** (công thức hoặc tên).\n"
            "2. Chọn **phương pháp suy diễn** và các **điều kiện** được phép.\n"
            "3. Bấm **Giải bài toán** để xem từng bước, sơ đồ và diễn biến suy luận.\n"
            "4. Tab **Cơ sở tri thức** để xem/thêm/sửa/xóa chất, phản ứng và kiểm tra nhất quán.\n"
            "5. Tab **Kiểm thử** để chạy toàn bộ test case."
        )

tab_solve, tab_kb, tab_test, tab_about = st.tabs(
    ["Giải bài toán", "Cơ sở tri thức", "Kiểm thử", "Mô hình & thuật toán"])


# =============================================================================== hiển thị kết quả
def show_parse(res, kind):
    html = []
    for it in res.items:
        if it.error:
            html.append(chip(f"✘ {it.raw}", "err"))
        else:
            html.append(chip(f"{pretty(it.formula)} – {kb.chemicals[it.formula].name_vi}", kind))
    if html:
        st.markdown(" ".join(html), unsafe_allow_html=True)


def render_steps_table(res):
    rows = []
    for s in res.steps:
        r = s.reaction
        rows.append({
            "Bước": s.index,
            "Mã": r.id,
            "Phương trình phản ứng": r.equation(),
            "Điều kiện": r.conditions,
            "Chất cần tính (B'ᵢ)": ", ".join(pretty(x) for x in sorted(s.needed)) or "—",
            "Sản phẩm phụ": ", ".join(pretty(x) for x in sorted(s.byproducts)) or "—",
            "w(f)": r.cost,
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def render_result(res, key: str):
    H, G = res.H, res.G
    st.markdown(
        "**Bài toán:** " + ", ".join(pretty(x) for x in H) + " ⟶ " + ", ".join(pretty(x) for x in G)
        + f" &nbsp; <span class='small'>({METHODS.get(res.method, res.method)})</span>",
        unsafe_allow_html=True)
    if res.status == "SOLVED":
        st.success(res.message)
    elif res.status == "UNRESOLVED":
        st.warning(res.message)
    else:
        st.error(res.message)
    st.caption(f"Trạng thái: {res.status.value}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Số phản ứng", len(res.steps))
    m2.metric("Tổng trọng số w(S)", res.total_cost)
    m3.metric("|Closure(H)|", len(res.closure))
    m4.metric("Thời gian (ms)", res.stats.get("time_ms", "—"))

    if res.solvable and res.steps:
        st.markdown("#### Các bước điều chế")
        render_steps_table(res)

        st.markdown("#### Quá trình giải (phân tích lời giải)")
        lines = []
        for s in res.steps:
            r = s.reaction
            need = ", ".join(pretty(x) for x in sorted(s.needed))
            cond = f" *[{r.conditions}]*" if r.condition_tags else ""
            lines.append(f"{s.index}. Xác định **{need}** – áp dụng **{r.id}**: "
                         f"<span class='eq'>{r.equation()}</span>{cond}")
        st.markdown("\n".join(lines), unsafe_allow_html=True)

        if res.raw_solution and len(res.raw_solution) > len(res.steps):
            st.info(f"Lời giải ban đầu có {len(res.raw_solution)} phản ứng "
                    f"({', '.join(r.id for r in res.raw_solution)}); sau khi loại phản ứng thừa "
                    f"còn {len(res.steps)} phản ứng.")

        st.markdown("#### Sơ đồ mạng của lời giải")
        st.graphviz_chart(solution_dot(H, G, res.steps), width="content")
        st.markdown(
            chip("Chất ban đầu (H)", "ok") + chip("Chất cần điều chế (G)", "goal")
            + chip("Chất trung gian", "mid") + chip("Sản phẩm phụ (nét đứt)", "by"), unsafe_allow_html=True)

    if not res.solvable and res.missing:
        st.markdown("#### Bổ sung giả thiết")
        reach = [x for x in G if x not in res.missing]
        if reach:
            st.write("Điều chế được: " + ", ".join(pretty(x) for x in reach))
        st.write("Không điều chế được: " + ", ".join(f"**{pretty(x)}**" for x in res.missing))
        if res.suggestions:
            st.write("Hệ thống đề xuất bổ sung một trong các tập chất sau vào giả thiết:")
            for i, sug in enumerate(res.suggestions):
                label = ", ".join(kb.label(x) for x in sug)
                st.button(f"Thêm {label} và giải lại", key=f"{key}_sug_{i}",
                          on_click=cb_add_hypotheses, args=(sug,))

    with st.expander("Diễn biến suy luận (vết suy diễn)"):
        st.code("\n".join(res.trace) or "(không có)", language=None)
        if res.stats:
            st.caption(" · ".join(f"{k}: {v}" for k, v in res.stats.items()))
    if res.closure:
        with st.expander(f"Closure(H) – {len(res.closure)} chất suy ra được từ giả thiết"):
            st.markdown(" ".join(chip(f"{pretty(x)} – {kb.chemicals[x].name_vi}",
                                      "ok" if x in H else ("goal" if x in G else "mid"))
                                 for x in sorted(res.closure)), unsafe_allow_html=True)


# =============================================================================== TAB 1
with tab_solve:
    st.markdown("### Bài toán điều chế: H ⟶ G")
    cases = load_cases()
    ex1, ex2 = st.columns([4, 1])
    ex_idx = ex1.selectbox(
        "Nạp nhanh một ví dụ (lấy từ bộ test case)", range(len(cases)),
        format_func=lambda i: f"{cases[i]['id']} – {cases[i]['name']}", label_visibility="collapsed")
    ex2.button("Nạp ví dụ", on_click=cb_load_example, args=(cases[ex_idx],),
               width="stretch")

    cH, cG = st.columns(2)
    with cH:
        st.text_area("**Chất ban đầu (giả thiết H)**", key="hyp_text", height=80,
                     help="Nhập công thức (H2O, NaCl) hoặc tên (nước, muối ăn), cách nhau bởi dấu phẩy.")
        ph = matcher.parse(st.session_state.hyp_text)
        show_parse(ph, "ok")
    with cG:
        st.text_area("**Chất cần điều chế (mục tiêu G)**", key="goal_text", height=80,
                     help="Có thể nhập nhiều chất, cách nhau bởi dấu phẩy.")
        pg = matcher.parse(st.session_state.goal_text)
        show_parse(pg, "goal")

    o1, o2 = st.columns([1, 1])
    with o1:
        st.radio("**Phương pháp suy diễn**", METHOD_OPTIONS, key="method",
                 format_func=lambda m: METHOD_LABELS[m])
    with o2:
        st.markdown("**Điều kiện phản ứng được phép sử dụng**")
        cc = st.columns(2)
        for i, (t, lab) in enumerate(CONDITION_LABELS.items()):
            cc[i % 2].checkbox(f"{lab} (+{CONDITION_COST[t]})", key=f"cond_{t}")
        b1, b2, _ = st.columns([1, 1, 1])
        b1.button("Chọn tất cả", on_click=cb_set_all_conditions, args=(True,), width="stretch")
        b2.button("Bỏ hết", on_click=cb_set_all_conditions, args=(False,), width="stretch")
        st.caption("Phản ứng không cần điều kiện đặc biệt luôn được dùng. "
                   "Số trong ngoặc là chi phí cộng thêm vào trọng số w(f).")

    run = st.button("Giải bài toán", type="primary", width="stretch")
    if st.session_state.auto_solve:
        run, st.session_state.auto_solve = True, False

    request_key = (st.session_state.hyp_text, st.session_state.goal_text,
                   st.session_state.method, tuple(sorted(enabled_tags())), kb.revision)

    if run:
        problems = []
        for res_p, name in ((ph, "chất ban đầu"), (pg, "chất cần điều chế")):
            for it in res_p.errors:
                msg = f"**{name.capitalize()}** – {it.error}."
                if it.suggestions:
                    msg += " Có phải bạn muốn nhập: " + ", ".join(kb.label(s) for s in it.suggestions) + "?"
                problems.append(msg)
        if not ph.formulas and not ph.errors:
            problems.append("Thiếu dữ kiện: chưa nhập **chất ban đầu** (giả thiết H).")
        if not pg.formulas and not pg.errors:
            problems.append("Thiếu dữ kiện: chưa nhập **chất cần điều chế** (mục tiêu G).")
        if problems:
            st.session_state.last = {"errors": problems}
        else:
            tags = enabled_tags()
            if st.session_state.method == "compare":
                out = {m: solve(kb, ph.formulas, pg.formulas, m, tags) for m in METHODS}
            else:
                out = {st.session_state.method: solve(kb, ph.formulas, pg.formulas,
                                                      st.session_state.method, tags)}
            st.session_state.last = {"results": out, "notes": ph.notes + pg.notes}
        st.session_state.last["request_key"] = request_key

    last = st.session_state.last
    if last and last.get("request_key") != request_key:
        st.warning("Dữ kiện, mục tiêu, phương pháp, điều kiện hoặc CSTT đã thay đổi. Hãy giải lại để cập nhật kết quả.")
        last = None
    if last:
        st.divider()
        if "errors" in last:
            st.markdown("### Dữ kiện chưa hợp lệ")
            for p in last["errors"]:
                st.error(p)
        else:
            for n in last.get("notes", []):
                st.caption("So khớp dữ kiện: " + n)
            results = last["results"]
            if len(results) == 1:
                (m, res), = results.items()
                render_result(res, key=m)
            else:
                st.markdown("### So sánh các phương pháp suy diễn")
                rows = [{
                    "Phương pháp": METHODS[m],
                    "Tìm được lời giải": "✔" if r.solvable else "✘",
                    "Trạng thái": r.status.value,
                    "Mục tiêu trong bao đóng": "✔" if r.goal_reachable else "✘" if r.goal_reachable is False else "—",
                    "Số phản ứng": len(r.steps),
                    "Tổng trọng số": r.total_cost,
                    "Dãy phản ứng": " → ".join(x.id for x in r.solution) or "—",
                    "Thời gian (ms)": r.stats.get("time_ms", "—"),
                } for m, r in results.items()]
                st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
                sub = st.tabs([METHODS[m] for m in results])
                for t, (m, r) in zip(sub, results.items()):
                    with t:
                        render_result(r, key=f"cmp_{m}")


# =============================================================================== TAB 2
def chem_rows():
    am = kb.atomic_masses()
    rows = []
    for c in kb.chemicals.values():
        try:
            mm = round(molar_mass(c.formula, am), 2)
        except FormulaError:
            mm = None
        rows.append({
            "Công thức": c.formula, "Tên tiếng Việt": c.name_vi, "Tên tiếng Anh": c.name_en,
            "Tên khác": ", ".join(c.names[2:]), "Trạng thái": STATES.get(c.state, c.state),
            "Loại": TYPE_LABELS.get(c.type, c.type), "Màu": c.color,
            "Độ tan": SOLUBILITY.get(c.solubility, c.solubility),
            "Nguyên tử khối": c.atomic_mass, "M (g/mol)": mm,
            "Số phản ứng": len(kb.reactions_using(c.formula)),
        })
    return pd.DataFrame(rows)


def reaction_form(edit: Reaction | None):
    key = edit.id if edit else "new"
    with st.form(f"form_rx_{key}", clear_on_submit=False):
        c1, c2 = st.columns([1, 3])
        rid = c1.text_input("Mã phản ứng", value=edit.id if edit else kb.next_reaction_id())
        eq_default = edit.equation(use_pretty=False) if edit else ""
        eq = c2.text_input("Phương trình (vd: 2Na + Cl2 -> 2NaCl, dùng ↑ ↓ cho khí/kết tủa)",
                           value=eq_default.replace("→", "->"))
        c3, c4 = st.columns([3, 2])
        cond = c3.text_input("Mô tả điều kiện", value=edit.conditions if edit else "Nhiệt độ thường")
        tags = c4.multiselect("Nhãn điều kiện", list(CONDITION_LABELS), placeholder="Chọn điều kiện...",
                              default=edit.condition_tags if edit else [],
                              format_func=lambda t: CONDITION_LABELS[t])
        c5, c6, c7 = st.columns([1, 1, 2])
        auto_cost = c5.checkbox("Tự tính trọng số", value=edit is None)
        cost = c6.number_input("Trọng số w(f)", min_value=1, max_value=100,
                               value=edit.cost if edit else 1)
        groups = sorted({r.group for r in kb.reactions})
        group = c7.selectbox("Nhóm", groups, index=groups.index(edit.group) if edit and edit.group in groups else 0)
        note = st.text_input("Ghi chú", value=edit.note if edit else "")
        auto_bal = st.checkbox("Tự cân bằng phương trình (bỏ qua hệ số đã nhập)", value=False)
        submitted = st.form_submit_button("Lưu phản ứng", type="primary")
    if submitted:
        try:
            lhs, rhs, ws, props = parse_equation(eq)
            if auto_bal or ws is None:
                ws = balance(lhs, rhs)
                st.info(f"Hệ số cân bằng tự động: {ws}")
        except FormulaError as e:
            st.error(f"Phương trình không hợp lệ: {e}")
            return
        r = Reaction(id=rid.strip(), reactants=lhs, products=rhs, weights=ws, conditions=cond,
                     condition_tags=tags, properties=props,
                     cost=default_cost(tags) if auto_cost else int(cost), group=group, note=note)
        errs = kb.update_reaction(edit.id, r) if edit else kb.add_reaction(r)
        if errs:
            for e in errs:
                st.error(e)
        else:
            st.success(f"Đã lưu {r.id}: {r.equation()}")
            st.session_state.last = None


def chemical_form(edit: Chemical | None):
    key = edit.formula if edit else "new"
    with st.form(f"form_chem_{key}"):
        c1, c2, c3 = st.columns(3)
        f = c1.text_input("Công thức", value=edit.formula if edit else "")
        vi = c2.text_input("Tên tiếng Việt", value=edit.name_vi if edit else "")
        en = c3.text_input("Tên tiếng Anh", value=edit.name_en if edit else "")
        alias = st.text_input("Tên gọi khác (cách nhau bởi dấu phẩy)",
                              value=", ".join(edit.names[2:]) if edit else "")
        c4, c5, c6 = st.columns(3)
        states = list(STATES)
        state = c4.selectbox("Trạng thái", states, format_func=STATES.get,
                             index=states.index(edit.state) if edit and edit.state in states else 0)
        ctype = c5.selectbox("Loại chất", CHEMICAL_TYPES, format_func=TYPE_LABELS.get,
                             index=CHEMICAL_TYPES.index(edit.type) if edit and edit.type in CHEMICAL_TYPES else 0)
        sols = list(SOLUBILITY)
        sol = c6.selectbox("Độ tan", sols, format_func=SOLUBILITY.get,
                           index=sols.index(edit.solubility) if edit and edit.solubility in sols else 0)
        c7, c8 = st.columns(2)
        color = c7.text_input("Màu sắc", value=edit.color if edit else "")
        am = c8.number_input("Nguyên tử khối (chỉ cho nguyên tố, 0 = không có)", min_value=0.0,
                             value=float(edit.atomic_mass or 0) if edit else 0.0, format="%.3f")
        submitted = st.form_submit_button("Lưu chất", type="primary")
    if submitted:
        names = [en.strip() or vi.strip(), vi.strip() or en.strip()] + \
                [a.strip() for a in alias.split(",") if a.strip()]
        c = Chemical(formula=f.strip(), names=names, state=state, type=ctype, color=color,
                     solubility=sol, atomic_mass=am or None)
        errs = kb.update_chemical(edit.formula, c) if edit else kb.add_chemical(c)
        if errs:
            for e in errs:
                st.error(e)
        else:
            st.success(f"Đã lưu chất {c.label()}")


with tab_kb:
    st.markdown("### Cơ sở tri thức (M_Frame, F_Conditions)")
    st.caption(f"Lưu trữ tại `data/chemicals.json` ({len(kb.chemicals)} chất) và "
               f"`data/reactions.json` ({len(kb.reactions)} phản ứng).")
    k1, k2, k3, k4, k5 = st.tabs(["Chất hóa học (M)", "Phản ứng (F)", "Cập nhật CSTT",
                                  "Kiểm tra nhất quán", "Sơ đồ mạng"])

    with k1:
        f1, f2 = st.columns([1, 2])
        types = f1.multiselect("Lọc theo loại", CHEMICAL_TYPES, format_func=TYPE_LABELS.get, placeholder="Tất cả")
        q = f2.text_input("Tìm theo công thức / tên", key="chem_q")
        df = chem_rows()
        if types:
            df = df[df["Loại"].isin([TYPE_LABELS[t] for t in types])]
        if q:
            mask = df.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)
            df = df[mask]
        st.dataframe(df, hide_index=True, width="stretch", height=430)
        sel = st.selectbox("Xem Frame của chất", list(kb.chemicals), format_func=kb.label)
        st.json(kb.chemicals[sel].to_dict(), expanded=True)

    with k2:
        f1, f2, f3 = st.columns(3)
        groups = sorted({r.group for r in kb.reactions})
        g_sel = f1.multiselect("Lọc theo nhóm", groups, placeholder="Tất cả")
        t_sel = f2.multiselect("Lọc theo điều kiện", list(CONDITION_LABELS), placeholder="Tất cả",
                               format_func=CONDITION_LABELS.get)
        s_sel = f3.text_input("Chứa chất (công thức)", key="rx_q")
        rows = []
        for r in kb.reactions:
            if g_sel and r.group not in g_sel:
                continue
            if t_sel and not set(t_sel) & set(r.condition_tags):
                continue
            if s_sel and s_sel.strip() not in r.reactants + r.products:
                continue
            rows.append({"Mã": r.id, "Phương trình": r.equation(), "Điều kiện": r.conditions,
                         "Nhãn điều kiện": r.tags_text(), "w(f)": r.cost, "Nhóm": r.group,
                         "Ghi chú": r.note})
        st.caption(f"Hiển thị {len(rows)} / {len(kb.reactions)} phản ứng")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=430)
        rsel = st.selectbox("Xem bản ghi JSON của phản ứng", [r.id for r in kb.reactions],
                            format_func=lambda i: f"{i}: {kb.get_reaction(i).equation()}")
        st.json(kb.get_reaction(rsel).to_dict(), expanded=True)

    with k3:
        kind = st.radio("Đối tượng cập nhật", ["Phản ứng", "Chất hóa học"], horizontal=True)
        if kind == "Phản ứng":
            opts = ["(Thêm phản ứng mới)"] + [r.id for r in kb.reactions]
            pick = st.selectbox("Chọn phản ứng", opts, format_func=lambda i: i if i.startswith("(")
                                else f"{i}: {kb.get_reaction(i).equation()}")
            edit = None if pick.startswith("(") else kb.get_reaction(pick)
            reaction_form(edit)
            if edit and st.button(f"Xóa phản ứng {edit.id}"):
                kb.delete_reaction(edit.id)
                st.session_state.last = None
                st.success(f"Đã xóa {edit.id}")
                st.rerun()
        else:
            opts = ["(Thêm chất mới)"] + list(kb.chemicals)
            pick = st.selectbox("Chọn chất", opts, format_func=lambda f: f if f.startswith("(") else kb.label(f))
            edit = None if pick.startswith("(") else kb.chemicals[pick]
            chemical_form(edit)
            if edit and st.button(f"Xóa chất {edit.formula}"):
                errs = kb.delete_chemical(edit.formula)
                if errs:
                    st.error(errs[0])
                else:
                    st.success(f"Đã xóa {edit.formula}")
                    st.rerun()
        st.divider()
        with st.expander("Khôi phục CSTT gốc (94 phản ứng ban đầu)"):
            ok = st.checkbox("Tôi muốn xóa mọi thay đổi và khôi phục bản gốc")
            if st.button("Khôi phục", disabled=not ok):
                kb.reset_default()
                st.session_state.last = None
                st.success("Đã khôi phục CSTT gốc.")
                st.rerun()

    with k4:
        st.markdown("Kiểm tra: cân bằng nguyên tố theo hệ số, chất chưa khai báo, rút gọn vế phải, "
                    "luật trùng, luật thừa, vòng lặp, chất chưa dùng (Chương 3.4.2).")
        if st.button("Chạy kiểm tra tính nhất quán", type="primary"):
            st.session_state.issues = kb.check_consistency()
        issues = st.session_state.get("issues")
        if issues is not None:
            levels = ["Lỗi", "Cảnh báo", "Thông tin"]
            cols = st.columns(3)
            for c, lv in zip(cols, levels):
                c.metric(lv, sum(i["level"] == lv for i in issues))
            if not any(i["level"] == "Lỗi" for i in issues):
                st.success("CSTT nhất quán: không có lỗi.")
            show = st.multiselect("Hiển thị mức", levels, default=levels, placeholder="Chọn mức...")
            df = pd.DataFrame([i for i in issues if i["level"] in show])
            if not df.empty:
                df.columns = ["Mức", "Loại", "Đối tượng", "Nội dung"]
                st.dataframe(df, hide_index=True, width="stretch", height=420)

    with k5:
        mode = st.radio("Vẽ theo", ["Một chất", "Nhóm phản ứng"], horizontal=True)
        if mode == "Một chất":
            f = st.selectbox("Chất", list(kb.chemicals), format_func=kb.label,
                             index=list(kb.chemicals).index("NaCl"))
            rs = kb.reactions_using(f)
            st.caption(f"{len(rs)} phản ứng có {f}")
            if rs:
                st.graphviz_chart(network_dot(kb, rs, {f}), width="stretch")
        else:
            groups = sorted({r.group for r in kb.reactions})
            g = st.selectbox("Nhóm", groups)
            rs = [r for r in kb.reactions if r.group == g]
            st.graphviz_chart(network_dot(kb, rs), width="stretch")


# =============================================================================== TAB 3
with tab_test:
    st.markdown("### Kiểm thử hệ thống")
    st.caption("Các test case lưu trong `data/test_cases.json`; chạy bằng dòng lệnh: `python -m pytest -v`.")
    if st.button("Chạy tất cả test case", type="primary"):
        st.session_state.test_out = [(c, run_case(kb, c)) for c in load_cases()]
    out = st.session_state.get("test_out")
    if out:
        npass = sum(o["passed"] for _, o in out)
        (st.success if npass == len(out) else st.warning)(f"Đạt {npass}/{len(out)} test case.")
        st.dataframe(pd.DataFrame([{
            "Mã": c["id"], "Tên": c["name"], "Phương pháp": METHODS[c["method"]],
            "H": c["hyp"], "G": c["goal"] or "(trống)",
            "Điều kiện": "Tất cả" if c.get("enabled_tags") is None else
                         (", ".join(CONDITION_LABELS[t] for t in c["enabled_tags"]) or "Không có"),
            "Kết quả": "✔ Đạt" if o["passed"] else "✘ Không đạt",
        } for c, o in out]), hide_index=True, width="stretch")
        for c, o in out:
            with st.expander(f"{'✔' if o['passed'] else '✘'} {c['id']} – {c['name']}"):
                st.write(c["description"])
                for label, ok in o["checks"]:
                    st.markdown(f"{'✅' if ok else '❌'} {label}")
                res = o["result"]
                ph, pg = o["parse"]
                errs = ph.errors + pg.errors
                if errs:
                    for e in errs:
                        st.caption(f"Lỗi dữ kiện: {e.error}"
                                   + (f" → gợi ý: {', '.join(e.suggestions)}" if e.suggestions else ""))
                if res is not None:
                    st.caption(res.message)
                    if res.steps:
                        st.markdown("\n".join(f"- {s.reaction.id}: {s.reaction.equation()}"
                                              for s in res.steps))
                    if res.suggestions:
                        st.caption("Gợi ý bổ sung: " + " | ".join(", ".join(s) for s in res.suggestions))


# =============================================================================== TAB 4
with tab_about:
    st.markdown("""
### Mô hình biểu diễn tri thức

Tri thức về các phản ứng hóa học được biểu diễn bằng **mạng tính toán mở rộng (M_Frame, F_Conditions)**
, kèm hàm trọng số để thành **mạng suy diễn có trọng số (M, F, w)**

| Thành phần | Ý nghĩa | Lưu trữ |
|---|---|---|
| **M_Frame** | Tập chất; mỗi chất là một Frame: `Name`, `Formula`, `State`, `Type`, `Color`, `Solubility`, `Atomic mass` | `data/chemicals.json` |
| **F_Conditions** | Tập phản ứng f: u(f) → v(f), quan hệ **không đối xứng**; mỗi phản ứng có `id`, `if`, `then`, `weights` (hệ số), `conditions`, `condition_tags`, `properties`, `cost` | `data/reactions.json` |
| **w(f)** | Trọng số = 1 + chi phí các điều kiện (đun nóng +1, xúc tác +1, ánh sáng +1, axit đặc +1, điện phân dung dịch +3, điện phân nóng chảy +4) | trường `cost` |

Phản ứng f **áp dụng được** trên tập chất A khi u(f) ⊆ A và mọi điều kiện của f đang được cho phép.

### Các thuật toán và kiến thức tương ứng

| Chức năng | Thuật toán | Slide |
|---|---|---|
| Tính giải được | Tìm bao đóng Closure(H); giải được ⇔ G ⊆ Closure(H) | 4.4.1 |
| Tìm lời giải | Suy diễn tiến: lặp chọn luật áp dụng được sinh chất mới | 4.3.1, 4.4.1 |
| Lời giải tốt | Duyệt i = m → 1, bỏ fᵢ nếu D \\ {fᵢ} vẫn là lời giải | 4.4.1 |
| Phân tích quá trình giải | Tính ngược Bₘ = G, B'ᵢ = chất thật sự cần tính ở bước i | 4.4.1 |
| Lời giải tối ưu | A* trên đồ thị trạng thái (đỉnh = tập chất đã biết, cạnh = phản ứng, độ dài = w) | 4.4.2 |
| Suy diễn lùi | Từ mục tiêu tìm phản ứng sinh ra nó, đệ quy về các chất tham gia; chống vòng lặp | 4.3.1 |
| Bổ sung giả thiết | Tìm tập chất X nhỏ nhất để G ⊆ Closure(H ∪ X) | 4.4.1 (Bài toán 3) |
| Cập nhật CSTT | Thêm / sửa / xóa chất và phản ứng, tự cân bằng, khôi phục bản gốc | 3.4.1 |
| Kiểm tra nhất quán | Cân bằng nguyên tố, luật trùng, luật thừa, rút gọn vế phải, phát hiện vòng lặp | 3.4.2 |
| So khớp sự kiện | Chính xác, không phân biệt hoa/thường, theo tên Việt/Anh, bỏ dấu, gợi ý gần đúng | 3.4.3 |
""")
