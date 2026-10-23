# Demo Bài 1 — Triangle Solver

[Video demo trình duyệt](triangle-solver-demo.webm) ghi trực tiếp ứng dụng local qua Chromium/Playwright. Video không có âm thanh; ghi viewport thật ở 1440×1000, không ghép hình hoặc tạo kết quả giả. Playwright khởi động FastAPI và Vite bằng cấu hình của dự án.

Nội dung: nhập `a=3, b=4, c=5`; chọn diện tích, đường cao hc và bán kính R; giải ra `S=6, hc=2.4, R=2.5`; xem tam giác, đường cao, đường tròn ngoại tiếp và các bước suy luận; thử tam giác suy biến và dữ kiện thiếu.

| Ảnh chụp từ cùng phiên chạy | Nội dung |
|---|---|
| [01](01-giao-dien.png) | Giao diện ban đầu |
| [02](02-du-kien-muc-tieu.png) | Nhập dữ kiện và chọn mục tiêu |
| [03](03-ket-qua-tam-giac.png) | Kết quả thật từ API và hình tam giác |
| [04](04-duong-cao.png) | Chọn hc, trực quan hóa đường cao |
| [05](05-cac-buoc-suy-luan.png) | Trace suy luận đầy đủ |
| [06](06-tam-giac-khong-hop-le.png) | INVALID cho ba cạnh 1,2,3 |
| [07](07-thieu-du-kien.png) | UNRESOLVED khi chưa đủ dữ kiện |

[recording.json](recording.json) ghi phiên bản trình duyệt, thời điểm UTC, thời lượng thực, các mốc thao tác và ba response từ API. Video là ghi phiên trình duyệt headless, không phải quay toàn bộ desktop; chưa kiểm tra Firefox/WebKit.

Chạy lại từ `Bai1/frontend` sau khi cài các dependencies của Bài 1 và Chromium:

```powershell
npm run demo:record
```

Các khoảng dừng được chủ ý giữ trong kịch bản để người xem đọc dữ kiện, kết quả và trace; demo mất khoảng 1–2 phút. Lệnh sẽ ghi lại các tệp trong thư mục này.
