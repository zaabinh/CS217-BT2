# Triangle Knowledge Base — Bài 1

Python 3.11+, Pydantic v2, FastAPI. Chạy từ thư mục cha **Bai1**.

## Run

```bash
python -m triangle_knowledge_base --facts "a=3,b=4,c=5" --goals "p,S,hc,r,R"
python -m pytest -v
python -m uvicorn triangle_knowledge_base.app.api.main:app --host 127.0.0.1 --port 8000
```

Variables: `a,b,c,A,B,C,ha,hb,hc,S,p,r,R`. Angles are **degrees**. Rule IDs R01–R46 follow the supplied report. Trace shows the actual deterministic forward-chaining sequence; it may include intermediate steps beyond the minimal mathematical proof.

Statuses: SOLVED, UNRESOLVED, INVALID, INCONSISTENT.

Xem [README chính](../README.md) cho cài đặt, API request/response, đơn vị và bằng chứng kiểm thử; [báo cáo bàn giao](../docs/dev-docs/DELIVERY_REPORT.md) ghi kiến trúc và thay đổi.

Limitations: no inverse-sine branching (SSA), no general symbolic equation solving, no optimization for minimum derivation length. The consistency checker verifies rules whose inputs and output are all known; it is not a complete constraint solver. Numerical comparisons use abs=1e-8 and rel=1e-7.
