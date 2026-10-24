# Quy chuẩn báo cáo CS217

Hai báo cáo có cùng hệ thống trình bày, giữ riêng nội dung chuyên môn và độ dài phù hợp từng bài:

| Bài | Bản đọc/in | Nguồn chỉnh sửa |
|---|---|---|
| Bài 1 — Tri thức tam giác | [PDF](<../Bai1/Báo cáo.pdf>) | [DOCX](../Bai1/Bao_cao_Bai_1.docx) |
| Bài 2 — Điều chế hóa học | [PDF](../Bai2/Bao_cao_Bai_2.pdf) | [DOCX](../Bai2/Bao_cao_Bai_2.docx) |

[Mẫu báo cáo DOCX](Mau_bao_cao_CS217.docx) cung cấp sẵn page setup và các style. Có thể dùng hai bản nguồn hoàn chỉnh làm mẫu cho bảng và trang bìa.

## Định dạng

- A4 dọc; lề trái 3 cm, phải 2 cm, trên/dưới 2,5 cm.
- Times New Roman, màu đen; nội dung 13 pt, giãn dòng 1,3, căn đều hai bên.
- `Heading 1`: tiêu đề chương 16 pt, đậm, bắt đầu trang mới; `Heading 2`: tiêu đề mục 14 pt, đậm.
- Bảng: khung đơn đủ cạnh và đường kẻ trong, header đậm nền `D9D9D9`; lặp header khi sang trang, giữ từng hàng nguyên vẹn. Nội dung ô căn trái để đọc dữ liệu và công thức.
- Bảng đánh số/chú thích phía trên; hình phía dưới; công thức có số bên phải. Mỗi loại dùng bộ đếm riêng `chương.số`; phần đầu dùng `0.số`, phụ lục dùng `A.số`, `B.số`.
- Trích dẫn `[n]` đối chiếu danh mục cuối báo cáo; đường dẫn mã nguồn tính từ thư mục bài tương ứng. Tài liệu bài giảng kế thừa từ báo cáo cũ được phân biệt với mã nguồn đã trực tiếp đối chiếu.
- Logo bìa dùng [PNG UIT](../Logo-DH-Cong-Nghe-Thong-Tin-UIT.png), chuyển định dạng từ ảnh WebP có sẵn, giữ nguyên hình ảnh. Logo và ảnh ứng dụng giữ màu gốc; chữ soạn trong báo cáo dùng màu đen.
- Các phép toán tập hợp không có glyph trong bản Times New Roman cài tại máy được viết bằng từ tương đương để tránh Word thay font: “nằm trong”, “thuộc”, “hợp”, “trừ”. Ý nghĩa công thức được giữ nguyên.

## Cấu trúc

Trang bìa → thông tin nhóm/phân công → mục lục → sáu chương (tổng quan; lý thuyết; phân tích/thiết kế; cài đặt; kiểm thử/thực nghiệm; kết luận/hướng phát triển) → tài liệu tham khảo → phụ lục.

Trong DOCX, mục lục và số trang là Word fields. Sau khi chỉnh sửa, mở bằng Microsoft Word, cập nhật toàn bộ mục lục và fields rồi xuất PDF A4. Hình, bảng và công thức hiện đánh số bằng văn bản; khi thêm/bớt cần cập nhật số và tham chiếu trong nội dung. Kiểm tra lại ngắt trang, dòng tiêu đề bảng và chú thích trước khi nộp.

## Căn cứ nội dung

Đối chiếu mã tại commit `2ae25f2` và chạy lại ngày **24/10/2026** trên Windows, Python 3.13.5; frontend dùng Node.js 24.11.0/npm 11.6.1. Những thay đổi sau commit này tại thời điểm soạn là dọn tài liệu/tiện ích, không đổi thuật toán.

| Hạng mục | Kết quả đã chạy |
|---|---|
| Bài 1 — pytest backend | 252 đạt; một cảnh báo deprecation Starlette/HTTPX |
| Bài 1 — Vitest | 44 đạt |
| Bài 1 — tích hợp API thật | 9 đạt |
| Bài 1 — Playwright Chromium | 10 đạt |
| Bài 1 — TypeScript/Vite build | Thành công |
| Bài 2 — pytest | 76 đạt, bao gồm 15 tình huống và 5 Streamlit AppTest |
| Bài 2 — chạy riêng bộ tình huống | 15/15 đạt; là tập con của pytest |

Ảnh minh họa trong hai báo cáo được chụp mới bằng Playwright từ ứng dụng local, sau khi kiểm tra kết quả:

- [Bài 1](../Bai1/docs/images/ket_qua_tam_giac.png): `a=3, b=4, c=5`, mục tiêu `S, hc, R`; `SOLVED`, `6; 2.4; 2.5`.
- [Bài 2](../Bai2/docs/images/19_ket_qua_hien_tai.png): bài toán chính, lời giải tốt gồm 6 phản ứng, chi phí 18. Ảnh 01–18 đã có từ trước không dùng làm bằng chứng chạy lại.

Không thêm số liệu hiệu năng, tỷ lệ coverage hoặc ảnh kết quả chưa xác minh. Bản DOCX và PDF được xuất từ cùng nội dung bằng Word, cập nhật mục lục và số trang trước khi xuất.
