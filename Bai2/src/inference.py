"""
inference.py - Bộ suy diễn trên Mạng tính toán các phản ứng hóa học

Mạng suy diễn (M, F):
  * M : tập các chất
  * F : tập các phản ứng f : u(f) -> v(f)  (quan hệ KHÔNG đối xứng)
        f áp dụng được trên tập chất A  <=>  u(f) ⊆ A
Bài toán điều chế: cho tập chất ban đầu H, tìm dãy phản ứng để có tập chất G (H -> G)

Các thuật toán sử dụng:
  * closure()              Tìm bao đóng Closure(H)  -> tính giải được        
  * apply_sequence()       Tính D(A) của một dãy quan hệ D                     
  * forward_chaining()     Suy diễn tiến tìm một lời giải                      
  * good_solution()        Lời giải tốt: loại bỏ các phản ứng thừa             
  * analyze_solution()     Phân tích quá trình giải (chất cần tính mỗi bước)   
  * astar_optimal()        Lời giải tối ưu trên mạng suy diễn có trọng số - A*
  * backward_chaining()    Suy diễn lùi từ mục tiêu về giả thiết               
  * suggest_hypotheses()   Bổ sung giả thiết khi bài toán không giải được 
"""
from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field

from knowledge_base import CONDITION_LABELS, KnowledgeBase, Reaction

METHODS = {
    "forward": "Suy diễn tiến",
    "good": "Suy diễn tiến + lời giải tốt",
    "optimal": "Lời giải tối ưu (A*)",
    "backward": "Suy diễn lùi",
}


# --------------------------------------------------------------------------- cấu trúc kết quả
@dataclass
class Step:
    index: int
    reaction: Reaction
    known_before: frozenset
    new: frozenset            # chất mới sinh ra ở bước này
    known_after: frozenset
    needed: frozenset = frozenset()     # B'_i: chất thực sự cần tính ở bước này
    byproducts: frozenset = frozenset()  # sản phẩm không dùng tới


@dataclass
class SolveResult:
    method: str
    H: list[str]
    G: list[str]
    solvable: bool = False
    steps: list[Step] = field(default_factory=list)
    message: str = ""
    closure: frozenset = frozenset()
    missing: list[str] = field(default_factory=list)
    suggestions: list[list[str]] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    raw_solution: list[Reaction] = field(default_factory=list)  # trước khi tối ưu
    reason_code: str = ""
    goal_reachable: bool | None = None

    @property
    def solution(self) -> list[Reaction]:
        return [s.reaction for s in self.steps]

    @property
    def total_cost(self) -> int:
        return sum(r.cost for r in self.solution)


# --------------------------------------------------------------------------- tiện ích cơ bản
def applicable(r: Reaction, known: set | frozenset) -> bool:
    """Luật u -> v áp dụng được trên A khi u ⊆ A."""
    return r.hyp <= known


def produces_new(r: Reaction, known: set | frozenset) -> bool:
    return not r.goal <= known


def closure(H, rules: list[Reaction]) -> tuple[frozenset, list[Reaction]]:
    """Thuật toán tìm bao đóng (trường hợp quan hệ không đối xứng).

    B <- A ; lặp: với mỗi f chưa xét, nếu u(f) ⊆ B thì B <- B ∪ M(f), loại f.
    Trả về (Closure(H), các luật đã dùng theo thứ tự).
    """
    B = set(H)
    remaining = list(rules)
    used: list[Reaction] = []
    while True:
        B1 = set(B)
        for f in list(remaining):
            if applicable(f, B):
                B |= f.goal
                remaining.remove(f)
                used.append(f)
        if B == B1:
            break
    return frozenset(B), used


def apply_sequence(H, seq: list[Reaction]) -> frozenset:
    """Tính D(A): lần lượt áp dụng các quan hệ áp dụng được"""
    A = set(H)
    for f in seq:
        if applicable(f, A):
            A |= f.goal
    return frozenset(A)


def is_solution(H, G, seq: list[Reaction]) -> bool:
    """D là lời giải của H -> G khi D áp dụng được trên H và D(H) ⊇ G"""
    A = set(H)
    for f in seq:
        if not applicable(f, A):
            return False
        A |= f.goal
    return set(G) <= A


def build_steps(H, seq: list[Reaction]) -> list[Step]:
    steps, known = [], frozenset(H)
    for i, r in enumerate(seq, 1):
        after = known | r.goal
        steps.append(Step(i, r, known, after - known, after))
        known = after
    return steps


# --------------------------------------------------------------------------- suy diễn tiến
def forward_chaining(H, G, rules: list[Reaction], trace: list[str] | None = None):
    """Suy diễn tiến:
        Solution = []; Known = H
        while G ⊄ Known:
            tìm luật r: u(r) ⊆ Known và v(r) ⊄ Known
            nếu không có -> dừng, không tìm được lời giải
            Solution += r ; Known = Known ∪ v(r)
    """
    trace = trace if trace is not None else []
    known, solution = set(H), []
    trace.append(f"Khởi tạo: Known = {{{', '.join(sorted(known))}}}, Solution = []")
    while not set(G) <= known:
        r = next((f for f in rules if applicable(f, known) and produces_new(f, known)), None)
        if r is None:
            trace.append("Không còn phản ứng nào áp dụng được để sinh chất mới → dừng.")
            return None, trace
        new = r.goal - known
        known |= r.goal
        solution.append(r)
        trace.append(f"Bước {len(solution)}: áp dụng {r.id}: {r.equation()} "
                     f"→ thêm {{{', '.join(sorted(new))}}}")
    trace.append(f"G ⊆ Known → tìm được lời giải gồm {len(solution)} phản ứng.")
    return solution, trace


def good_solution(H, G, seq: list[Reaction], trace: list[str] | None = None) -> list[Reaction]:
    """Lời giải tốt: for i = m downto 1: nếu D \\ {f_i} vẫn là lời giải thì bỏ f_i"""
    trace = trace if trace is not None else []
    D = list(seq)
    for i in range(len(D) - 1, -1, -1):
        cand = D[:i] + D[i + 1:]
        if is_solution(H, G, cand):
            trace.append(f"Bỏ {D[i].id} ({D[i].equation()}) vì không cần thiết.")
            D = cand
    return D


def analyze_solution(H, G, steps: list[Step]) -> list[Step]:
    """Phân tích quá trình giải

    Đi ngược từ B_m = G: ở bước i, B'_i = (v(f_i) ∩ B_i) \\ A_{i-1} là các chất thật sự
    cần tính; B_{i-1} = (B_i \\ B'_i) ∪ u(f_i). Các sản phẩm còn lại là sản phẩm phụ.
    """
    need = set(G)
    for st in reversed(steps):
        useful = (st.reaction.goal & need) - st.known_before
        st.needed = frozenset(useful)
        st.byproducts = frozenset(st.new - useful)
        need = (need - useful) | set(st.reaction.hyp)
    return steps


# --------------------------------------------------------------------------- A* (lời giải tối ưu)
def relevant_rules(H, G, rules: list[Reaction]) -> list[Reaction]:
    """Thu gọn không gian tìm kiếm: chỉ giữ phản ứng áp dụng được trong Closure(H)
    và có đóng góp (trực tiếp hoặc gián tiếp) vào việc sinh ra G"""
    clo, usable = closure(H, rules)
    need, keep, changed = set(G), set(), True
    while changed:
        changed = False
        for r in usable:
            if r.id not in keep and r.goal & need:
                keep.add(r.id)
                need |= r.hyp
                changed = True
    return [r for r in rules if r.id in keep]


def astar_optimal(H, G, rules: list[Reaction], trace: list[str] | None = None,
                  max_expand: int = 200_000):
    """Tìm lời giải tối ưu trên mạng suy diễn có trọng số (A, D, w) bằng A*

    * Đỉnh  : tập chất đã biết N;  cạnh r : N -> N ∪ v(r), độ dài w(r)
    * Đích  : đỉnh chứa G
    * g(N)  : tổng trọng số từ H đến N
    * h(N)  : h(N) = min{ w(r) | u(r) ⊆ N }; ở đây lấy max với max_{x ∈ G\\N} min{ w(r) | x ∈ v(r) } - cả hai đều không vượt quá chi phí thật nên A* vẫn cho lời giải tối ưu.
    """
    trace = trace if trace is not None else []
    G = frozenset(G)
    rules = relevant_rules(H, G, rules)
    trace.append(f"Thu gọn mạng: còn {len(rules)} phản ứng liên quan đến mục tiêu.")
    cheapest_for = {}
    for r in rules:
        for x in r.goal:
            cheapest_for[x] = min(cheapest_for.get(x, 10 ** 9), r.cost)

    def h(N: frozenset) -> float:
        if G <= N:
            return 0
        app = [r.cost for r in rules if applicable(r, N) and produces_new(r, N)]
        if not app:
            return float("inf")
        h1 = min(app)
        h2 = max((cheapest_for.get(x, float("inf")) for x in G - N), default=0)
        return max(h1, h2)

    start = frozenset(H)
    counter = itertools.count()
    g = {start: 0}
    parent: dict = {start: (None, None)}
    open_heap = [(h(start), 0, next(counter), start)]
    closed: set = set()
    expanded = 0
    while open_heap:
        f, depth, _, N = heapq.heappop(open_heap)   # Bước 2.1: đỉnh có f nhỏ nhất
        if N in closed:
            continue
        closed.add(N)                               # Bước 2.2: chuyển N sang Close
        expanded += 1
        if expanded <= 15:
            trace.append(f"Xét đỉnh #{expanded}: g = {g[N]}, f = {f:g}, "
                         f"|N| = {len(N)} chất, mới nhất: "
                         f"{', '.join(sorted(N - start)) or '(xuất phát)'}")
        if G <= N:                                   # Bước 2.3: N là mục tiêu
            path, cur = [], N
            while parent[cur][0] is not None:
                prev, r = parent[cur]
                path.append(r)
                cur = prev
            path.reverse()
            trace.append(f"Đạt mục tiêu sau khi xét {expanded} đỉnh. "
                         f"Tổng trọng số tối ưu w(S) = {g[N]}.")
            return path, trace, {"expanded": expanded, "generated": len(g), "termination_reason": "GOALS_REACHED"}
        if expanded >= max_expand:
            trace.append("Đạt giới hạn mở rộng; chưa tìm được đường đi, không kết luận vô nghiệm.")
            return None, trace, {"expanded": expanded, "generated": len(g), "termination_reason": "SEARCH_LIMIT_REACHED"}
        for r in rules:                              # Bước 2.4: sinh các đỉnh kế
            if not applicable(r, N) or not produces_new(r, N):
                continue
            S = N | r.goal
            if S in closed:
                continue
            ng = g[N] + r.cost
            if ng < g.get(S, float("inf")):
                g[S] = ng
                parent[S] = (N, r)
                hs = h(S)
                if hs != float("inf"):
                    heapq.heappush(open_heap, (ng + hs, depth + 1, next(counter), S))
    trace.append("Open rỗng → chưa tìm được lời giải.")
    return None, trace, {"expanded": expanded, "generated": len(g), "termination_reason": "SEARCH_EXHAUSTED"}


# --------------------------------------------------------------------------- suy diễn lùi
def backward_chaining(H, G, rules: list[Reaction], trace: list[str] | None = None,
                      max_depth: int = 25, prune: bool = True):
    """Suy diễn lùi: xuất phát từ chất cần điều chế, thay nó bằng các chất
    tham gia của một phản ứng sinh ra nó; lặp lại đến khi mọi chất đều thuộc H.

    Ưu tiên thử phản ứng có trọng số nhỏ (heuristic); chống vòng lặp bằng tập các
    mục tiêu đang chứng minh; ghi nhớ chất đã điều chế được / chắc chắn không được.
    """
    trace = trace if trace is not None else []
    H = set(H)
    if prune:
        # Heuristic cắt nhánh: chỉ xét phản ứng áp dụng được trong Closure(H)
        _, rules = closure(H, rules)
        trace.append(f"Heuristic: chỉ xét {len(rules)} phản ứng áp dụng được trong Closure(H)")
    producers: dict[str, list[Reaction]] = {}
    for r in rules:
        for x in r.goal:
            producers.setdefault(x, []).append(r)
    for x in producers:
        producers[x].sort(key=lambda r: (r.cost, len(r.hyp)))

    proved: set = set(H)
    failed: set = set()
    solution: list[Reaction] = []
    counter = {"calls": 0, "depth_limit_hits": 0}

    def prove(x: str, stack: tuple, depth: int) -> tuple[bool, bool]:
        """Trả về (thành công, có cắt vòng lặp trong nhánh)"""
        counter["calls"] += 1
        ind = "    " * depth
        if x in proved:
            if depth and x in H:
                trace.append(f"{ind}• {x}: có sẵn trong giả thiết ✔")
            elif depth:
                trace.append(f"{ind}• {x}: đã điều chế được ở trên ✔")
            return True, False
        if x in failed:
            trace.append(f"{ind}• {x}: đã biết là không điều chế được ✘")
            return False, False
        if x in stack:
            trace.append(f"{ind}• {x}: đang chứng minh ở mức trên → vòng lặp, bỏ nhánh")
            return False, True
        if depth > max_depth:
            counter["depth_limit_hits"] += 1
            return False, True
        cyc = False
        cands = producers.get(x, [])
        if not cands:
            trace.append(f"{ind}• {x}: không có phản ứng nào tạo ra ✘")
        for r in cands:
            if len(trace) < 600:
                trace.append(f"{ind}• Cần {x}: thử {r.id}: {r.equation()} "
                             f"→ cần {', '.join(r.reactants)}")
            ok = True
            for y in r.reactants:
                s, c = prove(y, stack + (x,), depth + 1)
                cyc |= c
                if not s:
                    ok = False
                    break
            if ok:
                if r not in solution:
                    solution.append(r)
                proved.update(r.goal)
                trace.append(f"{ind}  ⇒ {x} điều chế được nhờ {r.id} ✔")
                return True, cyc
        if not cyc:
            failed.add(x)
        return False, cyc

    all_ok = True
    for x in G:
        trace.append(f"Mục tiêu: {x}")
        s, _ = prove(x, (), 0)
        all_ok &= s
        if not s:
            trace.append(f"⇒ Chưa chứng minh được cách điều chế {x}.")
    if not all_ok or not is_solution(H, G, solution):
        return None, trace, {**counter, "termination_reason": "SEARCH_LIMIT_REACHED"
                            if counter["depth_limit_hits"] else "SEARCH_EXHAUSTED"}
    return solution, trace, {**counter, "termination_reason": "GOALS_REACHED"}


# --------------------------------------------------------------------------- bổ sung giả thiết
def suggest_hypotheses(H, G, rules: list[Reaction], all_formulas: list[str],
                       max_size: int = 3, limit: int = 5) -> list[list[str]]:
    """Bài toán 3 - Bổ sung giả thiết: tìm các tập chất X nhỏ nhất sao cho
    G ⊆ Closure(H ∪ X). Ứng viên là các chất tham gia của những phản ứng có thể
    góp phần sinh ra chất còn thiếu (dò ngược trên mạng)."""
    H = set(H)
    clo, _ = closure(H, rules)
    missing = set(G) - clo
    if not missing:
        return []
    # dò ngược để tìm ứng viên
    need, cands, changed = set(missing), set(missing), True
    while changed:
        changed = False
        for r in rules:
            if r.goal & need and not r.hyp <= need:
                need |= r.hyp
                cands |= r.hyp
                changed = True
    cands = [c for c in cands if c not in clo and c in all_formulas]
    # ưu tiên chất xuất hiện nhiều lần ở vế trái (chất "nguyên liệu" phổ biến)
    freq = {c: sum(c in r.hyp for r in rules) for c in cands}
    cands.sort(key=lambda c: (-freq[c], c))
    cands = cands[:30]
    found: list[tuple] = []
    for size in range(1, max_size + 1):
        pool = cands if size <= 2 else cands[:20]
        for combo in itertools.combinations(pool, size):
            c2, _ = closure(H | set(combo), rules)
            if set(G) <= c2:
                sol, _ = forward_chaining(H | set(combo), G, rules)
                sol = good_solution(H | set(combo), G, sol or [])
                found.append((size, len(set(combo) & missing), len(sol), list(combo)))
        if found:
            break
    found.sort()
    out = [c for *_, c in found[:limit]]
    if not out:
        # Tham lam: mỗi lần thêm chất giúp điều chế được nhiều mục tiêu nhất
        X: set = set()
        while not set(G) <= closure(H | X, rules)[0]:
            cur = closure(H | X, rules)[0]
            best = max(cands + sorted(missing),
                       key=lambda c: (len(set(G) & closure(H | X | {c}, rules)[0]) - len(set(G) & cur),
                                      c not in missing))
            if best in X:
                break
            X.add(best)
        if set(G) <= closure(H | X, rules)[0]:
            out = [sorted(X)]
    if not any(set(o) == missing for o in out):
        out.append(sorted(missing))   # luôn đúng: cho trực tiếp các chất còn thiếu
    return out[:limit]


# --------------------------------------------------------------------------- hàm giải tổng hợp
def filter_rules(kb: KnowledgeBase, enabled_tags: set[str] | None) -> list[Reaction]:
    return [r for r in kb.reactions if r.allowed(enabled_tags)]


def solve(kb: KnowledgeBase, H: list[str], G: list[str], method: str = "good",
          enabled_tags: set[str] | None = None, suggest: bool = True, *,
          max_expand: int = 200_000, max_depth: int = 25) -> SolveResult:
    res = SolveResult(method=method, H=list(H) if isinstance(H, (list, tuple)) else [],
                      G=list(G) if isinstance(G, (list, tuple)) else [])
    t0 = time.perf_counter()

    def finish(code: str, message: str) -> SolveResult:
        res.reason_code, res.message = code, message
        res.solvable = code in ("GOALS_REACHED", "GOALS_ALREADY_KNOWN")
        res.stats.setdefault("rules_used", 0)
        res.stats.update(termination_reason=code, steps=len(res.steps),
                         time_ms=round((time.perf_counter() - t0) * 1000, 1))
        return res

    if (not isinstance(H, (list, tuple)) or not isinstance(G, (list, tuple))
            or any(not isinstance(x, str) or not x.strip() for x in [*H, *G])):
        return finish("INVALID_INPUT", "H và G phải là danh sách công thức chất.")
    if (not isinstance(method, str) or method not in METHODS
            or type(max_expand) is not int or max_expand < 1
            or type(max_depth) is not int or max_depth < 0
            or (enabled_tags is not None and (not isinstance(enabled_tags, (set, frozenset))
                                             or not enabled_tags <= CONDITION_LABELS.keys()))):
        return finish("INVALID_INPUT", "Phương pháp, điều kiện hoặc giới hạn tìm kiếm không hợp lệ.")

    # ----- xử lý dữ kiện thiếu
    if not H:
        return finish("INVALID_INPUT", "Thiếu dữ kiện: chưa nhập chất ban đầu (giả thiết H).")
    if not G:
        return finish("INVALID_INPUT", "Thiếu dữ kiện: chưa nhập chất cần điều chế (mục tiêu G).")
    errors = kb.ensure_valid()
    if errors:
        res.stats["validation_errors"] = errors
        return finish("INVALID_KNOWLEDGE_BASE", "CSTT không hợp lệ: " + "; ".join(errors))
    unknown = [x for x in list(H) + list(G) if x not in kb.chemicals]
    if unknown:
        return finish("INVALID_INPUT", f"Dữ kiện không hợp lệ: {', '.join(unknown)} không có trong CSTT.")
    rules = filter_rules(kb, enabled_tags)
    res.stats["rules_used"] = len(rules)

    # ----- Bài toán 1: tính giải được qua bao đóng
    res.closure, _ = closure(H, rules)
    res.missing = [x for x in G if x not in res.closure]
    res.goal_reachable = not res.missing
    if set(G) <= set(H):
        return finish("GOALS_ALREADY_KNOWN", "Các chất cần điều chế đã có sẵn trong giả thiết → lời giải rỗng.")
    if res.missing:
        if suggest:
            res.suggestions = suggest_hypotheses(H, G, rules, list(kb.chemicals))
        res.trace.append(f"Closure(H) gồm {len(res.closure)} chất, không chứa "
                         f"{', '.join(res.missing)} → G ⊄ Closure(H).")
        return finish("GOAL_NOT_IN_CLOSURE", "Bài toán KHÔNG giải được với CSTT và điều kiện hiện tại: "
                      f"không thể điều chế {', '.join(res.missing)}.")

    # ----- Bài toán 2: tìm lời giải
    trace = res.trace
    trace.append(f"Closure(H) gồm {len(res.closure)} chất và chứa G → bài toán giải được.")
    seq = None
    if method in ("forward", "good"):
        trace.append("— Suy diễn tiến —")
        seq, _ = forward_chaining(H, G, rules, trace)
        res.raw_solution = list(seq or [])
        if method == "good" and seq:
            trace.append("— Tìm lời giải tốt (duyệt từ cuối về đầu) —")
            seq = good_solution(H, G, seq, trace)
    elif method == "optimal":
        trace.append("— Thuật giải A* trên mạng suy diễn có trọng số —")
        seq, _, st = astar_optimal(H, G, rules, trace, max_expand=max_expand)
        res.stats.update(st)
    elif method == "backward":
        trace.append("— Suy diễn lùi —")
        seq, _, st = backward_chaining(H, G, rules, trace, max_depth=max_depth)
        res.stats.update(st)
        res.raw_solution = list(seq or [])
        if seq:
            pruned = good_solution(H, G, seq, [])
            if len(pruned) < len(seq):
                trace.append(f"Rút gọn: bỏ {len(seq) - len(pruned)} phản ứng thừa.")
            seq = pruned
    if not seq and seq != []:
        reason = res.stats.get("termination_reason", "SEARCH_EXHAUSTED")
        return finish(reason, "Chưa tìm được lời giải trong giới hạn tìm kiếm; mục tiêu thuộc bao đóng."
                      if reason == "SEARCH_LIMIT_REACHED" else "Thuật toán chưa tìm được lời giải; mục tiêu thuộc bao đóng.")
    res.steps = analyze_solution(H, G, build_steps(H, seq))
    return finish("GOALS_REACHED", f"Tìm được lời giải gồm {len(res.steps)} phản ứng "
                  f"(tổng trọng số {res.total_cost}).")
