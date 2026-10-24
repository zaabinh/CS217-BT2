# Biên bản bàn giao — Bài tập 2

**Môn:** Các hệ cơ sở tri thức · **Giảng viên:** PGS.TS Nguyễn Đình Hiển · **Ngày:** 24/10/2026.

- [Phân công công việc Excel](<../Bảng phân công công việc.xlsx>): bốn thành viên theo thông tin được cung cấp; không tự thêm số nhóm.
- [Bài 1](../Bai1/README.md): mã Python/FastAPI và React, báo cáo PDF, tài liệu, kiểm thử và [video demo trình duyệt](../Bai1/Demo/README.md).
- [Bài 2](../Bai2/README.md): mã Streamlit, CSTT JSON, kiểm thử và hướng dẫn; [báo cáo PDF](../Bai2/Bao_cao_Bai_2.pdf) và [video demo](../Bai2/Demo_Bai2.mp4) đã được bổ sung sau phiên bàn giao ban đầu.

## Quy trình Git

Nhánh bàn giao `feat/bai1-handover` được tạo từ nhánh hiện tại `master`, tại `20c82a8`. Commit này đồng thời là đầu `origin/Bai_2` khi fetch. Vì vậy lịch sử Bài 2 đã nằm trong nhánh hiện tại trước khi thực hiện công việc, không có lý do tạo lại hoặc sửa các commit của Bài 2.

Các thay đổi Bài 1 và bộ tài liệu nộp được chia commit theo nhóm, giữ nguyên lịch sử, không rebase hay force push:

| Commit | Nội dung |
|---|---|
| `a419f75` | `feat(bai1): implement triangle knowledge base and shared inference API` |
| `bf66e4b` | `test(bai1): cover rule inventory validation inference and API contracts` |
| `42b9a64` | `feat(bai1): add interactive triangle visualization and browser workflows` |
| `a5e34dd` | `docs(bai1): publish report usage guides and recorded local demo` |
| `b01e5d0` | `docs(delivery): add Vietnamese overview and formatted assignment workbook` |
| `6236df0` | `merge(bai1): integrate completed triangle solver and delivery artifacts` |

Merge Bài 1 sử dụng `--no-ff`, không có conflict. Lệnh merge nhánh local `Bai_2` vào master trả **Already up to date**, vì `20c82a8` đã là tổ tiên của master. `git diff Bai_2 master -- Bai2` không có khác biệt. Năm commit lịch sử ban đầu được bảo toàn. Commit ghi nhận kết quả kiểm tra sau merge được thêm riêng trên master sau `6236df0`; xem `git log --oneline --graph --all` để tra đầy đủ.

## Kiểm tra

Đã chạy trên master sau merge `6236df0`:

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Backend Bài 1 | **240 passed** | [Log](kiem_tra/bai1-backend.txt) |
| Frontend unit/component | **41 passed** | [Log](kiem_tra/bai1-frontend-unit.txt) |
| Frontend integration, backend thật | **9 passed** | [Log](kiem_tra/bai1-integration.txt) |
| E2E Chromium | **13 passed** | [Log](kiem_tra/bai1-e2e.txt) |
| TypeScript và production build | Thành công | [Log](kiem_tra/bai1-frontend-build.txt) |
| Pytest Bài 2 | **30 passed** | [Log](kiem_tra/bai2-pytest.txt) |
| Tình huống điều chế Bài 2 | **15/15 đạt**, trùng 15 ca đã nằm trong Pytest | [Log](kiem_tra/bai2-cases.txt) |
| Excel và liên kết Markdown local | Đã xác minh | [Log](kiem_tra/artifacts.txt) |

Tổng cộng **333 test đạt** trong các suite cuối cùng (không cộng trùng 15 tình huống Bài 2); thêm một kịch bản ghi video đã đạt trước merge. Metadata và ghi chú các lần chạy: [verification.json](kiem_tra/verification.json).

Lần kiểm tra đầu sau merge chạy đồng thời nhiều suite: một test component quá timeout 5 giây; chạy riêng lại đạt đủ 41 test mà không đổi chương trình hoặc kết quả kỳ vọng. Lần integration đầu không có backend vì E2E đã dừng server; sau khi khởi động backend riêng, cả 9 test đạt. Giữ lại log [timeout ban đầu](kiem_tra/bai1-frontend-unit-initial-timeout.txt) và [backend chưa chạy](kiem_tra/bai1-integration-initial-server-stopped.txt) để minh bạch quá trình kiểm tra.

Backend có cảnh báo deprecation Starlette TestClient/HTTPX; Playwright có cảnh báo môi trường màu terminal. Các cảnh báo không làm test thất bại. File tạm, venv, node_modules, dist, test-results, tsbuildinfo và secrets không được đưa vào các commit mới.

Excel được tạo bằng `scripts/create_assignment.py` với openpyxl 3.1.5, mở lại để kiểm tra nội dung, các vùng merge, font, border, căn chỉnh và A4. Dùng Python có openpyxl để chạy lại từ repository root:

```powershell
python -m pip install -r Tai_lieu_nop_bai/requirements.txt
python scripts/create_assignment.py
python scripts/check_markdown_links.py
```

Kiểm tra liên kết chỉ xác minh file/thư mục và heading Markdown local; không yêu cầu mạng để mở các URL localhost hoặc URL ngoài.

## Demo và giới hạn bàn giao

[Video Bài 1](../Bai1/Demo/triangle-solver-demo.webm) dài **87,16 giây**, Chromium thật 1440×1000, VP9/WebM, không âm thanh. Đây là ghi viewport trình duyệt headless, không phải quay toàn bộ desktop. Ảnh và metadata phụ trợ của phiên ghi đã được dọn; giữ video và [hướng dẫn ghi lại](../Bai1/Demo/README.md). Các số liệu kiểm thử ở trên ghi nhận phiên bàn giao trước khi dọn ba test chỉ dùng để chụp ảnh; test chức năng vẫn được giữ nguyên.

Các báo cáo học thuật của hai bài được liên kết trong README chính. Tài liệu này giữ lịch sử kiểm tra bàn giao; hướng dẫn và cấu trúc Bài 1 hiện tại được cập nhật tại [README Bài 1](../Bai1/README.md).
