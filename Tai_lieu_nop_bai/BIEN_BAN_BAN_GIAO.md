# Biên bản bàn giao — Bài tập 2

**Môn:** Các hệ cơ sở tri thức · **Giảng viên:** PGS.TS Nguyễn Đình Hiển · **Ngày:** 24/10/2026.

- [Phân công công việc Excel](Bang_phan_cong_cong_viec.xlsx): bốn thành viên theo thông tin được cung cấp; không tự thêm số nhóm.
- [Bài 1](../Bai1/README.md): mã Python/FastAPI và React, báo cáo PDF, tài liệu, kiểm thử và [video demo trình duyệt](../Bai1/Demo/README.md).
- [Bài 2](../Bai2/README.md): mã Streamlit, CSTT JSON, kiểm thử và hướng dẫn. Chưa có báo cáo PDF/Word riêng trong repository tại thời điểm kiểm tra.

## Quy trình Git

Nhánh bàn giao `feat/bai1-handover` được tạo từ nhánh hiện tại `master`, tại `20c82a8`. Commit này đồng thời là đầu `origin/Bai_2` khi fetch. Vì vậy lịch sử Bài 2 đã nằm trong nhánh hiện tại trước khi thực hiện công việc, không có lý do tạo lại hoặc sửa các commit của Bài 2.

Các thay đổi Bài 1 và bộ tài liệu nộp được chia commit theo nhóm: backend, kiểm thử, frontend và tài liệu/demo, tài liệu nộp chung. Merge giữ nguyên lịch sử, không rebase hay force push. Kết quả cuối cùng và các mã commit được bổ sung sau bước xác minh trên master.

## Kiểm tra

Kết quả trước merge: backend Bài 1 240 test đạt; frontend 41 unit/component test đạt và build thành công; Bài 2 30 test đạt. Kết quả sau merge được ghi riêng khi thực hiện.

Excel được tạo bằng `scripts/create_assignment.py` với openpyxl 3.1.5, mở lại để kiểm tra nội dung, các vùng merge, font, border, căn chỉnh và A4. Dùng Python có openpyxl để chạy lại từ repository root:

```powershell
python -m pip install -r Tai_lieu_nop_bai/requirements.txt
python scripts/create_assignment.py
python scripts/check_markdown_links.py
```

Kiểm tra liên kết chỉ xác minh file/thư mục và heading Markdown local; không yêu cầu mạng để mở các URL localhost hoặc URL ngoài.
