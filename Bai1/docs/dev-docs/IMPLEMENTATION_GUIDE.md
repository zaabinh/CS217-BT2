# IMPLEMENTATION GUIDE — Mạng tính toán biểu diễn tri thức tam giác

> **Bài 1 · Môn Các hệ cơ sở tri thức**<br>
> **Vai trò:** Tài liệu triển khai dành cho người phụ trách lập trình, đối chiếu với người viết báo cáo.<br>
> **Phạm vi:** Phiên bản cơ sở gồm **13 biến, 10 nhóm quan hệ, 46 luật có hướng**, suy diễn tiến và kiểm thử.<br>
> **Nguyên tắc:** Tài liệu chỉ mô tả yêu cầu, thiết kế, thứ tự thực hiện, kết quả mong đợi và tiêu chí nghiệm thu; **không chứa mã nguồn hay mã giả**.

> **Ghi nhận triển khai:** Bản mã hiện tại dùng Python 3.11+, Pydantic v2, kiến trúc phân lớp trong `triangle_knowledge_base/app`, CLI và FastAPI dùng chung `SolverService`. Xem [README](../../README.md), [báo cáo bàn giao](DELIVERY_REPORT.md) và [log kiểm thử thực tế](../../evidence/pytest-results.txt). Checklist bên dưới là đặc tả gốc; kết quả nghiệm thu được ghi riêng trong báo cáo bàn giao. PDF hiện có 15 trang: thuật toán trang 7–8, thiết kế trang 9, T01–T12 trang 11, Phụ lục A trang 13–14 và Phụ lục B trang 15.

## 0. Mục tiêu, phạm vi và quy ước

### 0.1. Mục tiêu cuối cùng

Xây dựng một chương trình Python biểu diễn tri thức hình học tam giác bằng mạng tính toán **(M, F)**. Người dùng cung cấp một tập các đại lượng đã biết **H** và một tập mục tiêu cần tính **G**. Hệ thống phải xác định luật có thể áp dụng, tính các đại lượng mới, giải thích chuỗi suy luận và kết luận một trong bốn trạng thái: **SOLVED**, **UNRESOLVED**, **INVALID**, **INCONSISTENT**.

Đây là **hệ suy luận theo luật**, không phải chương trình nhập ba cạnh rồi áp dụng một công thức cố định. Kho luật phải độc lập với thuật toán và hỗ trợ bổ sung luật về sau.

### 0.2. Phạm vi đã chốt với báo cáo

| Hạng mục | Đặc tả |
|---|---|
| Tập biến | `a`, `b`, `c`, `A`, `B`, `C`, `ha`, `hb`, `hc`, `S`, `p`, `r`, `R` |
| Độ đo góc | Độ (°) ở giao diện và dữ liệu; đổi sang radian bên trong phép lượng giác |
| Tập quan hệ | Q01–Q10 |
| Tập luật | R01–R46, mỗi luật có đúng **một đầu ra** |
| Bộ suy luận | Forward chaining, thứ tự luật xác định theo mã tăng dần |
| Độ chính xác đối chiếu | Sai số tuyệt đối `1e-8`, sai số tương đối `1e-7` |
| Kết quả | Trạng thái, tập giá trị tìm được, mục tiêu còn thiếu, dấu vết suy luận, thông báo |
| Kiểm thử bắt buộc | T01–T12 và kiểm thử bổ sung dữ liệu biên |
| Giới hạn | Không tự giải hệ phương trình tổng quát, không suy ngược Heron, không phân nhánh `arcsin` trong 46 luật cơ sở |

**Không mở rộng** sang trung tuyến, phân giác hoặc 19 biến trong giai đoạn này: các nội dung đó thuộc hướng phát triển về sau, không có trong tập 13 biến của báo cáo đã cung cấp. Khi thay đổi phạm vi phải cập nhật báo cáo và kiểm thử cùng lúc.

### 0.3. Quy ước tên biến và ý nghĩa

| Biến | Ý nghĩa | Miền hợp lệ |
|---|---|---|
| `a`, `b`, `c` | Cạnh đối diện với `A`, `B`, `C` | Số thực hữu hạn, dương |
| `A`, `B`, `C` | Ba góc trong tam giác | Số thực hữu hạn, nằm trong (0°, 180°) |
| `ha`, `hb`, `hc` | Đường cao tương ứng `a`, `b`, `c` | Số thực hữu hạn, dương |
| `S` | Diện tích | Số thực hữu hạn, dương |
| `p` | Nửa chu vi | Số thực hữu hạn, dương |
| `r` | Bán kính đường tròn nội tiếp | Số thực hữu hạn, dương |
| `R` | Bán kính đường tròn ngoại tiếp | Số thực hữu hạn, dương |

Tên biến **phân biệt hoa/thường**: `A` là góc, `a` là cạnh; `r` khác `R`. Tất cả độ dài sử dụng cùng một đơn vị, diện tích dùng bình phương đơn vị đó. Đầu vào không được là giá trị Boolean, NaN, vô cực hay chuỗi giả dạng số trong tầng xử lý tri thức.

### 0.4. Phân công và giao diện phối hợp

- **Người phụ trách code:** Thiết kế mô hình dữ liệu, kho luật, bộ kiểm tra, bộ suy luận, CLI, kiểm thử và hướng dẫn chạy. Cung cấp kết quả chạy thật để bổ sung vào báo cáo.
- **Người phụ trách báo cáo:** Duy trì định nghĩa (M, F), bảng luật, sơ đồ, mô tả thuật toán và bảng kiểm thử thống nhất với hiện thực.
- **Điểm chốt chung:** Tên biến, đơn vị, danh sách/ID 46 luật, quy tắc phân loại lỗi, định dạng trace và tiêu chí SOLVED phải giống nhau tuyệt đối.

---

## 1. Cấu trúc dự án và trách nhiệm từng tệp

Cấu trúc mục tiêu:

| Tệp / thư mục | Trách nhiệm | Tiêu chí đầu ra |
|---|---|---|
| `models.py` | Mô tả tập biến, cấu trúc một luật và đối tượng kết quả | Dữ liệu rõ ràng, không chứa thuật toán tính hình học |
| `knowledge_base.py` | Đăng ký Q01–Q10, R01–R46 và hàm tính của từng luật | 46 luật đúng ID, thứ tự, công thức, đầu vào và đầu ra |
| `validator.py` | Kiểm tra miền dữ liệu, điều kiện hình học và mâu thuẫn | Phân biệt INVALID và INCONSISTENT có lý do cụ thể |
| `inference_engine.py` | Suy diễn tiến, kiểm tra luật khả dụng, sinh trace, kết luận | Kết quả tái lập được với cùng H và G |
| `main.py` | Tiếp nhận H/G, gọi bộ suy luận, hiển thị kết quả | Giao diện dòng lệnh dễ demo, báo lỗi rõ ràng |
| `tests/test_inference.py` | Kiểm thử tích hợp, trường hợp kỳ vọng và trường hợp biên | T01–T12 cùng các kiểm thử bổ sung được tự động hóa |
| `README.md` | Hướng dẫn sử dụng và giới hạn thực tế | Người khác có thể chạy bằng hướng dẫn, không cần hỏi tác giả |
| `IMPLEMENTATION_GUIDE.md` | Kế hoạch triển khai và kiểm tra tiến độ | Có thể dùng trực tiếp để giao việc, review và nghiệm thu |

**Thiết kế phụ thuộc:** `models` → `knowledge_base` → `validator` → `inference_engine` → `main`; bộ `tests` kiểm tra từng tầng lẫn toàn bộ đường đi. Tránh để `knowledge_base` phụ thuộc vào giao diện hoặc phụ thuộc ngược vào `inference_engine`.

---

## 2. Giai đoạn 1 — Thiết kế mô hình tri thức (M, F)

### Việc cần làm

- [ ] Khai báo tập **M** đúng 13 biến và không phát sinh tên biến tự do.
- [ ] Thiết kế một cấu trúc dữ liệu luật có tối thiểu: **ID**, **nhóm Q**, **tập đầu vào**, **biến đầu ra**, **biểu thức mô tả**, **hàm tính** và **điều kiện áp dụng** (được biểu diễn trực tiếp hoặc qua validator).
- [ ] Bảo đảm một luật chỉ sinh **một** biến đầu ra.
- [ ] Tách **quan hệ không hướng** khỏi **luật suy luận có hướng**; nhiều chiều tính của một quan hệ là nhiều luật khác nhau.
- [ ] Quy định thứ tự luật ổn định theo R01–R46.
- [ ] Quy định định dạng dữ kiện H là ánh xạ *tên biến → giá trị thực*; G là tập tên biến duy nhất.
- [ ] Quy định trace đủ thông tin giải thích, không chỉ trả số cuối cùng.

### Định dạng thông tin tối thiểu cho mỗi bước suy luận

| Trường | Ý nghĩa |
|---|---|
| `step` | Số thứ tự bước được áp dụng |
| `rule` | ID R01–R46 |
| `group` | Nhóm Q01–Q10 |
| `inputs` | Những tên biến và giá trị đã được dùng |
| `formula` | Công thức mô tả cho người đọc |
| `output` | Tên biến mới được suy ra |
| `value` | Giá trị tính được **chưa làm tròn** |

**Nghiệm thu giai đoạn 1:** Người viết báo cáo có thể đọc mô hình và truy ra chính xác quan hệ nào tạo thành luật nào; không có tên biến hoặc kiểu thông tin ngầm định.

---

## 3. Giai đoạn 2 — Cài đặt kho tri thức 46 luật

Mục tiêu là hiện thực **đúng danh sách luật trong phụ lục báo cáo**, không tự ý thêm chiều suy ngược làm thay đổi hành vi kỳ vọng. Những công thức dưới đây dùng ký hiệu toán học; khi lập trình, các phép lượng giác phải dùng **độ** ở đầu vào/đầu ra.

### Q01 — Tổng ba góc (R01–R03; 3 luật)

Quan hệ: **A + B + C = 180°**.

| Luật | Đã biết | Tính |
|---|---|---|
| R01 | B, C | A = 180 − B − C |
| R02 | A, C | B = 180 − A − C |
| R03 | A, B | C = 180 − A − B |

Yêu cầu: Góc suy ra thuộc khoảng (0°, 180°); tổng ba góc khi đầy đủ phải nhất quán.

### Q02 — Nửa chu vi (R04–R07; 4 luật)

Quan hệ: **2p = a + b + c**.

| Luật | Đã biết | Tính |
|---|---|---|
| R04 | a, b, c | p = (a + b + c)/2 |
| R05 | p, b, c | a = 2p − b − c |
| R06 | p, a, c | b = 2p − a − c |
| R07 | p, a, b | c = 2p − a − b |

Yêu cầu: Cạnh suy ra phải dương; khi biết đủ ba cạnh phải kiểm tra bất đẳng thức tam giác.

### Q03 — Định lý sin, chiều tính cạnh (R08–R13; 6 luật)

Quan hệ: **a/sin A = b/sin B = c/sin C**.

| Luật | Đã biết | Tính |
|---|---|---|
| R08 | b, A, B | a = b·sin A/sin B |
| R09 | c, A, C | a = c·sin A/sin C |
| R10 | a, B, A | b = a·sin B/sin A |
| R11 | c, B, C | b = c·sin B/sin C |
| R12 | a, C, A | c = a·sin C/sin A |
| R13 | b, C, B | c = b·sin C/sin B |

Yêu cầu: Mẫu số khác 0; vì góc hợp lệ nằm trong (0°, 180°), vẫn phải xử lý sai số số học đối với sin gần 0. **Không thêm luật suy góc bằng arcsin** vào bộ cơ sở.

### Q04 — Định lý cos (R14–R19; 6 luật)

Quan hệ: **a² = b² + c² − 2bc cos A**, cùng hai hoán vị cho b/B và c/C.

| Luật | Đã biết | Tính |
|---|---|---|
| R14 | b, c, A | a = √(b² + c² − 2bc cos A) |
| R15 | a, b, c | A = arccos[(b² + c² − a²)/(2bc)] |
| R16 | a, c, B | b = √(a² + c² − 2ac cos B) |
| R17 | a, b, c | B = arccos[(a² + c² − b²)/(2ac)] |
| R18 | a, b, C | c = √(a² + b² − 2ab cos C) |
| R19 | a, b, c | C = arccos[(a² + b² − c²)/(2ab)] |

Yêu cầu: Biểu thức dưới căn không âm, mẫu số dương, đối số arccos trong [−1, 1]. Chỉ hiệu chỉnh đối số vượt biên một lượng **rất nhỏ vì sai số số học**; sai lệch thực phải được phát hiện, không che giấu.

### Q05 — Heron (R20; 1 luật)

Quan hệ: **S = √[p(p−a)(p−b)(p−c)]**.

| Luật | Đã biết | Tính |
|---|---|---|
| R20 | p, a, b, c | S = √[p(p−a)(p−b)(p−c)] |

Yêu cầu: Trước khi sử dụng, các giá trị p và ba cạnh phải nhất quán; không cho tam giác suy biến hoặc căn âm có ý nghĩa hình học. Không triển khai suy ngược công thức Heron trong bản cơ sở.

### Q06 — Diện tích theo cạnh và đường cao (R21–R29; 9 luật)

Quan hệ: **S = a·ha/2 = b·hb/2 = c·hc/2**.

| Luật | Đã biết | Tính |
|---|---|---|
| R21 | a, ha | S = a·ha/2 |
| R22 | S, a | ha = 2S/a |
| R23 | S, ha | a = 2S/ha |
| R24 | b, hb | S = b·hb/2 |
| R25 | S, b | hb = 2S/b |
| R26 | S, hb | b = 2S/hb |
| R27 | c, hc | S = c·hc/2 |
| R28 | S, c | hc = 2S/c |
| R29 | S, hc | c = 2S/hc |

Yêu cầu: Đường cao dương, mẫu số dương, không ghi đè biến đã biết.

### Q07 — Diện tích theo hai cạnh và góc xen giữa (R30–R32; 3 luật)

| Luật | Đã biết | Tính |
|---|---|---|
| R30 | b, c, A | S = bc·sin A/2 |
| R31 | a, c, B | S = ac·sin B/2 |
| R32 | a, b, C | S = ab·sin C/2 |

Yêu cầu: Luôn dùng góc xen giữa hai cạnh, không tráo vị trí cạnh/góc.

### Q08 — Đường tròn nội tiếp (R33–R35; 3 luật)

Quan hệ: **S = p·r**.

| Luật | Đã biết | Tính |
|---|---|---|
| R33 | p, r | S = p·r |
| R34 | S, p | r = S/p |
| R35 | S, r | p = S/r |

### Q09 — Diện tích và bán kính ngoại tiếp (R36–R40; 5 luật)

Quan hệ: **4RS = abc**.

| Luật | Đã biết | Tính |
|---|---|---|
| R36 | a, b, c, R | S = abc/(4R) |
| R37 | a, b, c, S | R = abc/(4S) |
| R38 | S, R, b, c | a = 4SR/(bc) |
| R39 | S, R, a, c | b = 4SR/(ac) |
| R40 | S, R, a, b | c = 4SR/(ab) |

Yêu cầu: Các đại lượng dương; sau khi tính cạnh phải đối chiếu lại các quan hệ đã đủ dữ kiện.

### Q10 — Cạnh và bán kính ngoại tiếp theo góc (R41–R46; 6 luật)

Quan hệ: **a = 2R sin A**, **b = 2R sin B**, **c = 2R sin C**.

| Luật | Đã biết | Tính |
|---|---|---|
| R41 | R, A | a = 2R·sin A |
| R42 | a, A | R = a/(2sin A) |
| R43 | R, B | b = 2R·sin B |
| R44 | b, B | R = b/(2sin B) |
| R45 | R, C | c = 2R·sin C |
| R46 | c, C | R = c/(2sin C) |

### Checklist kho luật

- [ ] Tổng số luật bằng **46**, chia nhóm theo số lượng **3 + 4 + 6 + 6 + 1 + 9 + 3 + 3 + 5 + 6**.
- [ ] Mỗi ID R01–R46 xuất hiện đúng một lần và đúng thứ tự.
- [ ] Mỗi luật có đầu ra nằm trong M và không đồng thời nằm trong tập đầu vào của chính luật.
- [ ] Tên nhóm, biến đầu vào, biến đầu ra và biểu thức đối chiếu đúng phụ lục trang 13–14 của báo cáo.
- [ ] Phép tính trả về số hữu hạn hoặc thông báo không thể áp dụng; không được âm thầm sinh NaN/vô cực.
- [ ] Kiểm thử đại diện cho từng nhóm Q01–Q10, nhất là các chiều tính ngược và điều kiện mẫu số/căn.

**Nghiệm thu giai đoạn 2:** Kho tri thức có thể được duyệt và dùng bởi một bộ suy luận chung mà không cần viết các nhánh xử lý riêng cho từng bài toán mẫu.

---

## 4. Giai đoạn 3 — Bộ kiểm tra dữ kiện và tính nhất quán

### 4.1. Kiểm tra cấu trúc và miền dữ liệu — INVALID

- [ ] Phát hiện tên biến không thuộc M (ở dữ kiện và mục tiêu).
- [ ] Phát hiện đầu vào không phải giá trị số hữu hạn: chuỗi chưa chuyển đổi được, Boolean, NaN, vô cực.
- [ ] Phát hiện độ dài, diện tích, p, r hoặc R không dương.
- [ ] Phát hiện góc ≤ 0° hoặc ≥ 180°.
- [ ] Phát hiện bộ ba cạnh vi phạm bất đẳng thức tam giác; tam giác suy biến cũng là INVALID theo báo cáo.
- [ ] Ngăn các kết quả tính mới nằm ngoài miền hợp lệ đi vào tập tri thức.

### 4.2. Kiểm tra các dữ kiện hợp lệ riêng lẻ nhưng mâu thuẫn — INCONSISTENT

- [ ] Nếu biết hai góc, tổng của chúng phải nhỏ hơn 180°.
- [ ] Nếu biết ba góc, tổng phải bằng 180° trong sai số cho phép.
- [ ] Nếu biết p và ba cạnh, kiểm tra 2p = a + b + c.
- [ ] Nếu biết S và ba cạnh, kiểm tra diện tích Heron, kể cả khi p chưa được cung cấp.
- [ ] Với mọi luật đã biết đầy đủ đầu vào và **đầu ra**, tính lại để **đối chiếu**, không ghi đè giá trị sẵn có.
- [ ] Thông báo mâu thuẫn ghi rõ mã luật, biến liên quan, giá trị hiện có và giá trị mong đợi.

### 4.3. So sánh số thực và xử lý lỗi số học

Sai số tương đối **1e−7** và tuyệt đối **1e−8** là cấu hình mặc định để kiểm tra hai giá trị gần bằng nhau. Không làm tròn ở bước suy luận, chỉ làm tròn khi trình bày.

Cần kiểm soát riêng:

- Mẫu số bằng 0 hoặc quá sát 0 so với độ chính xác máy.
- Căn số âm thực sự và số âm cực nhỏ do sai số làm tròn.
- Đối số arccos lệch nhẹ khỏi biên ±1 vì số học dấu phẩy động.
- Trường hợp độ lớn số cực lớn/cực nhỏ có thể gây tràn, mất chính xác hoặc sai phân hủy số.

**Nguyên tắc phân biệt:** Không áp dụng được một luật vì chưa đủ đầu vào không phải là INVALID. Một hướng suy luận không xác định được duy nhất nghiệm cũng không tự động là INCONSISTENT. Ngược lại, một quan hệ có đủ dữ kiện mà mâu thuẫn thì phải trả INCONSISTENT dù mục tiêu đã có trong H.

### 4.4. Điểm kiểm tra chất lượng đặc biệt

- [ ] Chạy validator **trước khi** kiểm tra mục tiêu đã đạt.
- [ ] Kiểm tra lại sau mỗi biến mới và trước mọi lần trả SOLVED.
- [ ] Các giá trị tính không hợp lệ không được thêm vào H/K.
- [ ] Nếu một công thức không áp dụng được trong trạng thái dữ kiện hiện có, có thể bỏ qua luật đó; nhưng không được bỏ qua xung đột đã được chứng minh từ các luật đủ dữ kiện.
- [ ] Xây dựng ví dụ chứng minh T09 trả INCONSISTENT dù `S` đã xuất hiện từ đầu trong H.

**Nghiệm thu giai đoạn 3:** Có thể giải thích rõ vì sao một kết quả là INVALID, INCONSISTENT hoặc chỉ chưa suy ra được; dữ kiện người dùng không bị sửa âm thầm.

---

## 5. Giai đoạn 4 — Bộ suy luận tiến (Inference Engine)

### 5.1. Đầu vào và đầu ra

**Đầu vào:** H (danh sách dữ kiện đã biết có giá trị), G (danh sách mục tiêu), F (46 luật có hướng).

**Đầu ra:** Một đối tượng kết quả có tối thiểu các thành phần:

| Trường | Nội dung |
|---|---|
| `status` | SOLVED / UNRESOLVED / INVALID / INCONSISTENT |
| `facts` | Tất cả dữ kiện ban đầu và giá trị mới suy ra |
| `trace` | Chuỗi bước suy luận thực sự đã diễn ra |
| `missing` | Các mục tiêu chưa tìm được |
| `message` | Thông báo kết quả hoặc nguyên nhân lỗi |

### 5.2. Luồng xử lý bắt buộc (không phải mã giả)

1. Chuẩn hóa danh sách tên biến và mục tiêu, không thay đổi chữ hoa/thường.
2. Kiểm tra cấu trúc, miền giá trị và các quan hệ đã có đủ dữ liệu.
3. Khởi tạo **K** là bản sao H; giữ nguyên dữ kiện người dùng nhập.
4. Nếu G đã nằm trọn trong K và dữ kiện nhất quán, trả SOLVED với trace có thể rỗng.
5. Quét lần lượt R01–R46: luật **khả dụng để suy ra giá trị mới** khi toàn bộ đầu vào đã biết, đầu ra chưa biết và điều kiện tính hợp lệ.
6. Tính một đầu ra ứng viên; kiểm tra miền của ứng viên và tính nhất quán của trạng thái K mở rộng **trước khi chấp nhận**.
7. Khi chấp nhận, ghi một bản ghi trace đầy đủ và thêm đầu ra vào K; giá trị trung gian không làm tròn.
8. Tiếp tục quét theo thứ tự xác định. Khi đủ mục tiêu, thực hiện kiểm tra nhất quán trước khi trả SOLVED.
9. Nếu hết một lượt mà không suy ra thêm biến, trả UNRESOLVED kèm danh sách G còn thiếu.
10. Nếu phát hiện dữ liệu hoặc quan hệ không hợp lệ, dừng và trả trạng thái lỗi tương ứng cùng nguyên nhân.

### 5.3. Bất biến cần bảo vệ

- **Không ghi đè:** Mỗi biến được gán giá trị suy diễn tối đa một lần; giá trị từ H luôn được giữ nguyên.
- **Tăng đơn điệu:** Tập tên biến đã biết chỉ tăng hoặc giữ nguyên, không xóa biến.
- **Giải thích được:** Mọi biến mới phải có ít nhất một bước trace chỉ rõ luật đã sinh ra nó.
- **Tái lập:** Cùng H, G và kho luật phải cho cùng đường suy luận trong cùng cấu hình số học.
- **Tính dừng:** Có tối đa **13 − |H|** lần bổ sung biến thành công trong một lần giải; không vòng lặp vô hạn.
- **Tách trách nhiệm:** Bộ suy luận quyết định *khi nào dùng luật*; kho tri thức xác định *luật tính gì*; validator quyết định *dữ liệu có hợp lệ/nhất quán không*.

### 5.4. Trace và giải thích lời giải

Mỗi dòng giải thích cần thể hiện: “Dựa trên các giá trị đầu vào …, áp dụng Rxx thuộc Qyy với công thức …, suy ra biến … = …”.

Với dữ kiện **a = 3, b = 4, p = 6**, mục tiêu **c, S, hc**, đường phụ thuộc chính trong báo cáo là:

1. **R07:** Tính c = 5 từ p, a, b.
2. **R20:** Tính S = 6 từ p, a, b, c.
3. **R28:** Tính hc = 2,4 từ S, c.

**Lưu ý:** Trace thực tế có thể có **nhiều bước hơn** vì thuật toán quét R01–R46 và có thể suy ra các góc hay đại lượng trung gian khác. Không viết kiểm thử buộc trace chỉ có ba bước này, trừ khi sau này bổ sung chế độ giải tối giản.

### 5.5. Tính đúng đắn và giới hạn

Bộ suy luận cơ sở không giải được mọi bài toán tam giác có nghiệm hình học. Đặc biệt, dữ kiện **A = 30°, a = 5, b = 8** tạo trường hợp SSA có hai cấu hình hợp lệ; vì không có các chiều giải `arcsin` trong F, việc yêu cầu B, C, c phải trả **UNRESOLVED**. Không chọn một nghiệm tùy tiện.

Khi trạng thái là UNRESOLVED, cách diễn đạt đúng là **“chưa suy ra được từ 46 luật hiện tại”**, không phải “bài toán toán học vô nghiệm”.

**Nghiệm thu giai đoạn 4:** Mọi kết quả suy ra đều có nguồn luật và giải thích; thuật toán dừng; 4 trạng thái được phân loại nhất quán với validator.

---

## 6. Giai đoạn 5 — Giao diện dòng lệnh (CLI) và trải nghiệm demo

### 6.1. Chức năng tối thiểu

- [ ] Người dùng nhập H dưới dạng danh sách `tên_biến=giá_trị`.
- [ ] Người dùng nhập G dưới dạng danh sách tên biến, có thể gồm nhiều mục tiêu.
- [ ] Hỗ trợ số thực và giá trị góc theo **độ**.
- [ ] Báo lỗi dễ hiểu khi sai cú pháp, sai tên biến, thiếu mục tiêu hoặc giá trị không phải số.
- [ ] Hiển thị trạng thái trước, sau đó là thông báo, các bước trace và các giá trị mục tiêu.
- [ ] Với UNRESOLVED, hiển thị rõ các mục tiêu chưa tìm được.
- [ ] Với INVALID hoặc INCONSISTENT, hiển thị nguyên nhân; không công bố kết quả suy luận chưa được xác nhận như lời giải thành công.

### 6.2. Quy ước hiển thị

- Tách tên biến khỏi giá trị và giữ nguyên chính tả (`A` khác `a`, `R` khác `r`).
- Làm tròn hợp lý **chỉ khi in ra**, không thay đổi giá trị nội bộ.
- Hiển thị công thức toán học hoặc chuỗi công thức dễ đọc cho từng bước.
- Nếu mục tiêu là biến có sẵn trong H, ghi nhận được việc không cần suy luận thêm, sau khi kiểm tra dữ kiện.
- Có ít nhất một demo đủ dữ kiện, một demo nhiều bước, một demo UNRESOLVED và một demo INCONSISTENT.

**Nghiệm thu giai đoạn 5:** Người khác có thể nhập H và G, hiểu kết quả và nhận diện luật được áp dụng mà không cần đọc source code.

---

## 7. Giai đoạn 6 — Kiểm thử 12 tình huống bắt buộc

Đây là các **kết quả kỳ vọng** theo mục 9 của báo cáo, dùng để so sánh với chương trình; không mặc định chúng đã qua kiểm thử nếu chưa chạy trên bản mã nguồn đang bàn giao.

| ID | Dữ kiện H | Mục tiêu G | Trạng thái và kết quả kỳ vọng |
|---|---|---|---|
| T01 | a=3, b=4, c=5 | p, S, hc, r, R | **SOLVED**; p=6, S=6, hc=2,4, r=1, R=2,5 |
| T02 | A=50°, B=60°, c=10 | C, a, b | **SOLVED**; C=70°, a≈8,152075, b≈9,216050 |
| T03 | b=3, c=4, A=90° | a, S | **SOLVED**; a=5, S=6 |
| T04 | a=3, b=4, p=6 | c, S, hc | **SOLVED**; c=5, S=6, hc=2,4 |
| T05 | c=10, hc=6 | S | **SOLVED**; S=30 |
| T06 | a=3 | S | **UNRESOLVED**; thiếu dữ kiện/luật khả dụng |
| T07 | a=1, b=2, c=3 | S | **INVALID**; tam giác suy biến |
| T08 | a=−3, b=4, c=5 | S | **INVALID**; cạnh âm |
| T09 | a=3, b=4, c=5, S=7 | S | **INCONSISTENT**; Heron cho S=6, không ghi đè S=7 |
| T10 | A=30°, B=60°, C=90° | a | **UNRESOLVED**; ba góc không xác định kích thước tam giác |
| T11 | A=30°, a=5, b=8 | B, C, c | **UNRESOLVED**; SSA có hai nghiệm, không có luật phân nhánh arcsin |
| T12 | S=6, p=6 | r | **SOLVED**; r=1 |

### 7.1. Kiểm thử bổ sung bắt buộc

- [ ] Nhập tên biến lạ, sai chữ hoa/thường và mục tiêu lạ.
- [ ] Giá trị chuỗi không chuyển được sang số, Boolean, NaN, vô cực.
- [ ] Dữ kiện góc A=100°, B=90° phải phát hiện không nhất quán.
- [ ] Mục tiêu đã nằm trong H nhưng các dữ kiện khác mâu thuẫn: **không** được trả SOLVED.
- [ ] Dữ kiện nhiều đường suy luận cho cùng một đầu ra: các giá trị phải được đối chiếu, không chọn ngẫu nhiên.
- [ ] Công thức lượng giác tại góc nhỏ/gần 180°, đối số arccos sát −1/1, tam giác gần suy biến.
- [ ] Kiểm tra số lượng đúng **46** luật, không thiếu/trùng ID.
- [ ] Kiểm tra ít nhất một phép tính đúng cho mỗi nhóm Q01–Q10.
- [ ] Với T02, T01 và T04, so sánh **giá trị số** bằng sai số cho phép; không chỉ kiểm tra trạng thái.
- [ ] Với kết quả SOLVED có biến mới, kiểm tra trace không rỗng và mỗi đầu ra trong trace có luật tương ứng.

### 7.2. Thủ tục kiểm thử và lưu bằng chứng

1. Chạy toàn bộ bộ kiểm thử tự động trên bản mã nguồn định nộp.
2. Đối chiếu lần lượt **trạng thái**, **giá trị**, **mục tiêu còn thiếu** và **trace**.
3. Ghi phiên bản Python, thời điểm chạy, kết quả tổng và các ca thất bại (nếu có).
4. Chụp ảnh hoặc lưu log chạy thật cho T01, T04, T09 và T11 để minh họa đủ các tính năng quan trọng.
5. Chuyển kết quả thực tế cho người viết báo cáo, thay phần “dự kiến” bằng “đã kiểm thử” **chỉ khi có bằng chứng**.

**Nghiệm thu giai đoạn 6:** T01–T12 đạt trạng thái kỳ vọng, các ca có nghiệm số khớp trong sai số cho phép; kiểm thử bổ sung được ghi nhận rõ ràng.

---

## 8. Giai đoạn 7 — Rà soát hiện trạng mã nguồn và sửa sai

Nếu làm tiếp trên dự án Python đã tạo trước đó, **không viết lại từ đầu** khi chưa rà soát. Hiện trạng dự án có các tệp chính đã liệt kê ở mục 1 và tập luật 46 phần tử. Hãy thực hiện review theo những điểm sau:

### 8.1. Kiểm tra logic thực thi

- [ ] Kiểm chứng R01–R46 bằng **bảng đối chiếu ID–đầu vào–đầu ra–công thức**, không chỉ nhìn số lượng luật.
- [ ] Kiểm tra sự khác nhau giữa “luật chưa áp dụng được” và “mâu thuẫn đã xác nhận”.
- [ ] Kiểm tra thứ tự kiểm tra dữ kiện so với thời điểm trả kết quả, nhất là dữ kiện dư và mục tiêu đã biết.
- [ ] Kiểm tra đường xử lý khi hàm tính phát sinh lỗi số học hoặc kết quả không hữu hạn.
- [ ] Kiểm tra trạng thái ứng viên **trước khi** thêm biến, tránh đưa tri thức không hợp lệ vào K.
- [ ] Kiểm tra thông báo lỗi trỏ đúng luật gây lỗi.
- [ ] Xác nhận tính độc lập của kho luật với CLI và bộ suy luận.

### 8.2. Những cải thiện có thể làm **sau khi đạt đủ yêu cầu**

Các hạng mục dưới đây **không nằm trong 46 luật cơ sở**, không nên triển khai khi chưa hoàn tất bản chuẩn:

| Mở rộng | Lợi ích | Ảnh hưởng cần xem xét |
|---|---|---|
| Lọc các luật liên quan mục tiêu | Giảm suy luận trung gian không cần thiết | Trace và thứ tự áp dụng có thể đổi |
| Tối ưu chuỗi suy luận | Dễ giải thích, ít bước hơn | Phải định nghĩa tiêu chí tối ưu và bổ sung kiểm thử |
| Phân nhánh nghiệm SSA | Giải được các trường hợp arcsin đa nghiệm | Phải đổi kiểu kết quả từ một nghiệm sang tập nghiệm |
| Bổ sung trung tuyến/phân giác | Mở rộng mạng hình học | Phải mở rộng M, F, sơ đồ và báo cáo |
| Giao diện đồ họa hoặc xuất hình mạng | Demo trực quan | Không thay thế kiểm thử suy luận |

**Nghiệm thu giai đoạn 7:** Không còn sai khác không được giải thích giữa hiện thực, README và đặc tả báo cáo; mọi thay đổi đều có test tương ứng.

---

## 9. Giai đoạn 8 — Chuẩn hóa tài liệu, tích hợp với báo cáo, bàn giao

### 9.1. README cần trả lời được

- Dự án giải bài toán gì và sử dụng mô hình (M, F) ra sao?
- Cần phiên bản Python nào? Có cần thư viện ngoài không?
- Chạy một lượt suy luận và chạy toàn bộ kiểm thử bằng cách nào?
- Có những biến nào, dùng đơn vị gì, cú pháp nhập H/G ra sao?
- Kết quả SOLVED / UNRESOLVED / INVALID / INCONSISTENT có ý nghĩa gì?
- Giới hạn chính của 46 luật là gì?
- Làm sao kiểm tra trace và kiểm chứng kết quả?

### 9.2. Gói bàn giao cho người viết báo cáo

| Hạng mục | Nội dung phải gửi |
|---|---|
| Danh mục tri thức | 13 biến; 10 nhóm; 46 luật cùng mô tả |
| Thiết kế phần mềm | Vai trò từng tệp và sơ đồ phụ thuộc |
| Thuật toán thực tế | Cơ chế chọn luật, kiểm tra, dừng và sinh trace |
| Hành vi khi gặp lỗi | Phân biệt INVALID / INCONSISTENT / UNRESOLVED |
| Kết quả kiểm thử | T01–T12, kết quả số thực tế, kết quả so sánh, log lỗi nếu có |
| Demo | Ảnh chụp hoặc bản ghi từ lượt chạy chương trình thật |
| Môi trường | Python, cách chạy, thư viện, các giới hạn đã xác nhận |

### 9.3. Cấu trúc sản phẩm nộp

- Thư mục chung **`[BT2] - Nhóm [SỐ NHÓM]`**.
- Danh sách nhóm dạng Excel theo mẫu giảng viên yêu cầu.
- Thư mục **`Bai 1`** chứa báo cáo hoàn chỉnh, thư mục code, demo và hướng dẫn sử dụng nếu có.
- Tài liệu này là **hướng dẫn triển khai cho nhóm**, không phải bằng chứng hệ thống đã chạy.

**Nghiệm thu giai đoạn 8:** Một người không tham gia lập trình có thể giải nén dự án, chạy test, demo một ví dụ và đối chiếu kết quả với báo cáo.

---

## 10. Kế hoạch thực hiện theo thứ tự phụ thuộc

| Chặng | Trọng tâm | Phải hoàn thành trước khi chuyển chặng |
|---|---|---|
| **P0** | Chốt phạm vi, tên biến, đơn vị, contract | Mọi thành viên đồng ý dùng 13 biến và 46 luật |
| **P1** | Mô hình dữ liệu và 46 luật | Đủ ID, công thức, đầu vào/đầu ra và kiểm thử kho luật |
| **P2** | Validator và phép toán an toàn | Phân biệt được dữ liệu lỗi, mâu thuẫn và luật chưa áp dụng được |
| **P3** | Inference Engine + trace | Tái lập, dừng và đạt đúng trạng thái cơ bản |
| **P4** | CLI + cách hiển thị kết quả | Người dùng nhập H/G và đọc được lời giải |
| **P5** | Kiểm thử tích hợp | T01–T12 và các ca biên quan trọng được kiểm chứng |
| **P6** | Review, tài liệu và bàn giao | README, source, bằng chứng chạy và báo cáo đồng bộ |

### Checklist cuối cùng (Definition of Done)

- [ ] Có đúng 13 biến và 46 luật thuộc Q01–Q10.
- [ ] Từng luật được ánh xạ chính xác sang phụ lục báo cáo.
- [ ] Có suy diễn tiến tổng quát; không hard-code theo từng test case.
- [ ] Có kiểm tra miền giá trị, bất đẳng thức tam giác và đối chiếu mâu thuẫn.
- [ ] Bốn trạng thái trả về đúng ngữ nghĩa.
- [ ] Không tự chọn một nghiệm SSA khi có nhiều khả năng.
- [ ] Có trace với luật, biến vào, công thức, biến ra và giá trị chưa làm tròn.
- [ ] Có CLI sử dụng được và hướng dẫn chạy đầy đủ.
- [ ] T01–T12 đạt kỳ vọng và có bằng chứng chạy trên mã nguồn cuối cùng.
- [ ] Kết quả kiểm thử, sơ đồ/thuật toán và nội dung báo cáo mô tả đúng hành vi chương trình.

---

## 11. Những điều **không** nên làm trong bản cơ sở

1. **Không** triển khai 19 biến, trung tuyến hoặc phân giác chỉ vì từng được đề xuất khi brainstorm; báo cáo đang chốt 13 biến.
2. **Không** mặc định mọi phương trình đều đảo được để tính bất kỳ ẩn nào: có hướng không đơn trị hoặc không thỏa điều kiện hình học.
3. **Không** dùng arcsin chọn một góc duy nhất trong trường hợp SSA.
4. **Không** trả SOLVED ngay khi mục tiêu có trong H mà chưa kiểm tra dữ kiện mâu thuẫn.
5. **Không** làm tròn số trung gian để tạo giá trị đầu vào cho luật kế tiếp.
6. **Không** bắt trace phải giống hệt sơ đồ ba bước nếu hệ đang quét toàn bộ luật theo thứ tự.
7. **Không** đánh dấu test là PASS chỉ vì báo cáo có đáp án kỳ vọng.
8. **Không** viết cứng logic từng test vào inference engine; tất cả phải đi qua kho luật chung.

## 12. Nguồn đối chiếu và quản lý thay đổi

**Nguồn đặc tả chính:** `Bao_cao_Bai_1.pdf` do nhóm cung cấp, đặc biệt:

- Trang 2: Mô hình (M, F), 13 biến và đơn vị góc.
- Trang 3: Q01–Q10 và phân bổ 46 luật.
- Trang 4: Kiểm tra điều kiện, mâu thuẫn và giới hạn arcsin.
- Trang 5–6: Sơ đồ mạng và mạng con suy luận.
- Trang 7–8: Thuật toán tiến và lưu đồ.
- Trang 9: Cấu trúc chương trình và trạng thái.
- Trang 10–11: Ví dụ và T01–T12.
- Trang 12: Giới hạn và hướng mở rộng.
- Trang 13–14: Phụ lục A, danh sách R01–R46.
- Trang 15: Phụ lục B, ghi nhận kiểm thử và demo.

**Quy tắc thay đổi:** Khi thêm biến/luật, thay cách suy luận, đổi ý nghĩa trạng thái hoặc sửa điều kiện kiểm tra, phải sửa đồng thời **kho tri thức → kiểm thử → README → báo cáo**. Khi có khác biệt giữa bản brainstorm trước đó và PDF này, **PDF 13 biến/46 luật là phạm vi đang triển khai** cho đến khi nhóm thống nhất phiên bản mới.
