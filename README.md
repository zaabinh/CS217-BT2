# CS217 — Các hệ cơ sở tri thức

**Giảng viên:** PGS.TS Nguyễn Đình Hiển · **Bài tập 2**

Xây dựng cơ sở tri thức, biểu diễn các quan hệ trong miền bài toán và triển khai cơ chế suy luận có khả năng giải thích. Repository gồm hai sản phẩm chạy local, tài liệu sử dụng và kiểm thử tự động.

| Nội dung | Bài 1 — Tri thức tam giác | Bài 2 — Điều chế hóa học |
|---|---|---|
| Biểu diễn tri thức | Mạng tính toán `(M, F)`: 13 biến, 10 nhóm quan hệ, 46 luật có hướng | Mạng tính toán mở rộng có trọng số `(M_Frame, F_Conditions)`: 82 chất dạng Frame, 94 phản ứng có điều kiện, hệ số và chi phí; lưu bằng JSON |
| Suy luận | Suy diễn tiến theo thứ tự luật, kiểm tra miền/nhất quán, ghi từng bước suy luận | Bao đóng, suy diễn tiến/lùi, loại bước thừa, A* tối ưu chi phí và đề xuất bổ sung giả thiết |
| Sản phẩm | CLI, FastAPI và React; trực quan hóa tam giác, kết quả và chuỗi luật | Streamlit tiếng Việt; so khớp chất, quản lý CSTT, sơ đồ mạng và các bước điều chế |
| Mã nguồn | [Backend](Bai1/triangle_knowledge_base/app/), [Frontend](Bai1/frontend/) | [Python](Bai2/src/), [Dữ liệu CSTT](Bai2/data/) |
| Cài đặt và chạy local | [README Bài 1](Bai1/README.md) — Python 3.11+, Node.js 20+ | [README Bài 2](Bai2/README.md) — Python 3.11+ |
| Hướng dẫn sử dụng | [Hướng dẫn giao diện](Bai1/docs/USER_GUIDE.md), [CLI/API](Bai1/README.md#cli) | [Hướng dẫn có ảnh](Bai2/docs/HUONG_DAN_SU_DUNG.md) |
| Báo cáo và mô hình | [Báo cáo PDF](<Bai1/Báo cáo.pdf>), [Kiến trúc và suy luận](Bai1/README.md#kiến-trúc-và-suy-luận) | [Báo cáo PDF](Bai2/Bao_cao_Bai_2.pdf), [Danh mục tri thức](Bai2/docs/DANH_SACH_TRI_THUC.md), [Thuật toán](Bai2/README.md#6-thuật-toán) |
| Kiểm thử và demo | [Hướng dẫn kiểm thử](Bai1/README.md#kiểm-thử), [Test backend](Bai1/triangle_knowledge_base/tests/), [Demo trình duyệt](Bai1/Demo/) | [Test tự động](Bai2/tests/), [15 tình huống](Bai2/data/test_cases.json), [Video demo](Bai2/Demo_Bai2.mp4) |

Giới hạn của từng mô hình được ghi trong README riêng; `UNRESOLVED` của Bài 1 không đồng nghĩa bài toán toán học vô nghiệm.

```text
CS217-BT2/
├── Bai1/                 # Backend, frontend, báo cáo PDF, tài liệu và Demo/
├── Bai2/                 # Mã Streamlit, CSTT JSON, tài liệu và kiểm thử
├── Bảng phân công công việc.xlsx
└── README.md
```

**Tài liệu nộp bài:** [Bảng phân công công việc Excel](<Bảng phân công công việc.xlsx>).

Chạy kiểm thử từ từng thư mục bài: Bài 1 dùng `python -m pytest -v` và các lệnh npm trong [hướng dẫn](Bai1/README.md#kiểm-thử); Bài 2 dùng `python -m pytest -v` hoặc `python src/testing.py`. Dùng môi trường Python riêng cho từng bài theo README tương ứng.
