# Bài 2: Điều chế chất hóa học

Cho trước một tập phản ứng hóa học, hệ thống giải bài toán điều chế. Ví dụ đề bài: *cho các chất S, H2O, NaCl, hãy tìm các phản ứng để điều chế Na2SO4, H2SO4, HCl, Na.*

- **Mô hình tri thức:** mạng tính toán mở rộng **(M_Frame, F_Conditions)** có trọng số 
- **Bộ suy diễn:** gồm bao đóng, suy diễn tiến, lời giải tốt, phân tích quá trình giải, lời giải tối ưu A*, suy diễn lùi và bổ sung giả thiết
- **Tác vụ trên CSTT:** cập nhật, kiểm tra tính nhất quán, so khớp sự kiện 
- **Cơ sở tri thức:** 82 chất và 94 phản ứng vô cơ, tất cả đã được kiểm tra cân bằng tự động.
- **Giao diện:** web, viết bằng Streamlit, toàn bộ bằng tiếng Việt.

**Báo cáo:** [PDF](Bao_cao_Bai_2.pdf), [nguồn DOCX](Bao_cao_Bai_2.docx), [chuẩn trình bày chung](../Tai_lieu_bao_cao/README.md). Báo cáo được đối chiếu mã nguồn và kiểm thử lại ngày 24/10/2026.

---

## 1. Cài đặt

Yêu cầu **Python 3.11 trở lên**. Dùng môi trường riêng cho từng bài:

```bash
python -m venv .venv
# Kích hoạt môi trường: Windows .venv\Scripts\activate; Linux/macOS source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Chạy chương trình

Chạy lệnh sau tại **thư mục gốc của bài 2**, để chương trình nhận được file cấu hình giao diện `.streamlit/config.toml`:

```bash
python -m streamlit run src/app.py
```

Trình duyệt sẽ tự mở địa chỉ `localhost`. Trên Windows có thể bấm đúp file `run_app.bat`. Trên macOS/Linux thì chạy `./run_app.sh`.

Cách dùng chi tiết xem trong **[docs/HUONG_DAN_SU_DUNG.md](docs/HUONG_DAN_SU_DUNG.md)**.

## 3. Chạy kiểm thử

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v          # tình huống, validation, giới hạn tìm kiếm và giao diện Streamlit
python src/testing.py        # chỉ chạy 15 test case, in kết quả từng mục kiểm tra
```

Kết quả dùng `status`, `reason_code`, `diagnostics` và `stats`; `solvable` được giữ để tương thích và chỉ đúng khi đã có lời giải. `goal_reachable` cho biết mục tiêu có thuộc bao đóng hay chưa được kiểm tra. `missing` giữ nghĩa các mục tiêu ngoài bao đóng, nên có thể rỗng khi A* hết giới hạn mà chưa tìm ra đường đi. Trường hợp này trả `UNRESOLVED / SEARCH_LIMIT_REACHED`, không kết luận vô nghiệm.

CSTT JSON được kiểm tra trước khi nạp/cập nhật; hệ số và chi phí phải là số nguyên dương, không ép boolean hay số thập phân. Giao diện cảnh báo khi thay đổi dữ kiện, mục tiêu, phương pháp, điều kiện hoặc phiên bản CSTT làm kết quả cũ không còn khớp.

## 4. Cấu trúc thư mục

```
Bai2/
├── data/
│   ├── chemicals.json        # M_Frame: 82 chất (Frame)
│   ├── reactions.json        # F_Conditions: 94 phản ứng
│   ├── test_cases.json       # 15 test case
│   └── default/              # bản gốc của CSTT, dùng cho nút "Khôi phục CSTT gốc"
├── src/
│   ├── formula.py            # phân tích công thức, kiểm tra cân bằng, tự cân bằng, khối lượng mol
│   ├── knowledge_base.py     # đọc/ghi CSTT, thêm-sửa-xóa, kiểm tra tính nhất quán
│   ├── matcher.py            # so khớp sự kiện, xử lý dữ kiện thiếu và không hợp lệ
│   ├── inference.py          # bộ suy diễn: bao đóng, suy diễn tiến/lùi, lời giải tốt, A*, ...
│   ├── graph.py              # vẽ sơ đồ mạng tính toán (Graphviz DOT)
│   ├── testing.py            # chạy test case (dùng chung cho pytest và giao diện)
│   └── app.py                # giao diện Streamlit
├── tests/test_cases.py       # pytest
├── docs/
│   ├── HUONG_DAN_SU_DUNG.md  # hướng dẫn sử dụng có ảnh minh họa
│   ├── DANH_SACH_TRI_THUC.md # bảng đầy đủ 94 phản ứng và 82 chất
│   └── images/
├── .streamlit/config.toml    # màu sắc giao diện
├── requirements.txt
└── run_app.bat / run_app.sh
```

## 5. Tổ chức lưu trữ tri thức

Lưu bằng file văn bản có cấu trúc **JSON** 

**Chất hóa học** (`chemicals.json`). Mỗi chất là một Frame:

```json
{
  "Name": ["Sodium chloride", "Natri clorua", "Muối ăn"],
  "Formula": "NaCl",
  "State": "Solid",
  "Type": "Salt",
  "Color": "Trắng",
  "Solubility": "Soluble"
}
```

`Name` gồm tên tiếng Anh, tên tiếng Việt và các tên gọi khác (dùng cho phần so khớp). Riêng các nguyên tố có thêm trường `Atomic mass`.

**Phản ứng** (`reactions.json`). Mỗi phản ứng là một quan hệ f : u(f) → v(f):

```json
{
  "id": "R29",
  "if": ["NaCl", "H2SO4"],
  "then": ["Na2SO4", "HCl"],
  "weights": [2, 1, 1, 2],
  "conditions": "NaCl rắn, H2SO4 đặc, t° ≥ 400°C",
  "condition_tags": ["dac", "t"],
  "properties": [["HCl", "khí"]],
  "cost": 3,
  "group": "Hiđro clorua – axit clohiđric",
  "note": "Phương pháp sunfat"
}
```

- `condition_tags` là các nhãn điều kiện người dùng có thể bật/tắt trên giao diện: `t` đun nóng, `xt` xúc tác, `as` ánh sáng, `dac` axit đặc, `dpdd` điện phân dung dịch, `dpnc` điện phân nóng chảy.
- `cost` là trọng số w(f) = 1 + chi phí của các điều kiện: t, xt, as, dac mỗi loại +1; dpdd +3; dpnc +4.

## 6. Thuật toán

| Chức năng | Hàm (`src/inference.py`) |
|---|---|
| Kiểm tra tính giải được bằng bao đóng Closure(H) | `closure` |
| Tìm lời giải bằng suy diễn tiến | `forward_chaining` |
| Lời giải tốt (loại bước thừa) | `good_solution` |
| Phân tích quá trình giải | `analyze_solution` |
| Lời giải tối ưu bằng A* | `astar_optimal` | 4.4.2 |
| Suy diễn lùi | `backward_chaining` | 4.3.1 |
| Bổ sung giả thiết | `suggest_hypotheses` | 4.4.1 (Bài toán 3) |
| Kiểm tra tính nhất quán | `KnowledgeBase.check_consistency` | 3.4.2 |
| So khớp sự kiện | `Matcher` (`src/matcher.py`) | 3.4.3 |

**Kết quả của bài toán đề bài** (lời giải tốt và lời giải tối ưu A* trùng nhau, 6 phản ứng, tổng trọng số 18):

1. 2NaCl → 2Na + Cl₂ (điện phân nóng chảy) → **Na**
2. 2H₂O → 2H₂ + O₂ (điện phân nước)
3. S + O₂ → SO₂ (đốt cháy)
4. 2SO₂ + O₂ → 2SO₃ (V₂O₅, 450°C)
5. SO₃ + H₂O → **H₂SO₄**
6. 2NaCl + H₂SO₄ → **Na₂SO₄** + 2**HCl** (H₂SO₄ đặc, t° ≥ 400°C)

> Lưu ý: chỉ dùng 8 phản ứng mà đề cho thì **không giải được**, vì từ S, H2O, NaCl chỉ suy ra được HCl. Vì vậy CSTT được mở rộng lên 94 phản ứng để giải quyết được bài toán
