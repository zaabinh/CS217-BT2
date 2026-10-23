# Báo cáo bàn giao — Triangle Knowledge Base

## Audit và quyết định triển khai

Đã đọc toàn bộ `IMPLEMENTATION_GUIDE.md`, PDF 15 trang, hai README và tất cả source trước khi chỉnh sửa. PDF và Guide thống nhất 13 biến, 10 nhóm và 46 hướng tính; Guide dùng số trang của bản PDF cũ, đã bổ sung tham chiếu đúng.

Source ban đầu gồm 3 model Pydantic chưa hoàn chỉnh (import `triangle` sai và cấu hình strict cản trở tên Enum từ JSON); các module knowledge/core/service/API còn trống. Bộ test unittest import `inference_engine` và `knowledge_base` không tồn tại; `Bai1/main.py` đang bị xóa trong working tree và bản HEAD rỗng. README con mô tả Python 3.10 và không dependency, không phản ánh source.

Giữ lại cấu trúc phân lớp, Enum 13 biến và các trường model đã có; mở rộng thay vì đổi sang một dự án khác. Không có implementation suy luận hoạt động để tái sử dụng. Không chỉnh `Bai2`, không sửa PDF hoặc nội dung tham khảo.

Quyết định theo yêu cầu kiến trúc mới: Python 3.11+, Pydantic v2, FastAPI, Pytest; chuỗi công thức tách khỏi callable; HTTP schema error dùng 422, lỗi nghiệp vụ dùng bốn trạng thái trong HTTP 200. Cấu trúc thư mục nhiều tầng thay thế tên file phẳng trong Guide, giữ nguyên mô hình toán học.

## Kiến trúc và trách nhiệm

```text
main.py / __main__.py -> app.cli ───────┐
                                      ├-> SolverService -> InferenceEngine
app.api.main -> app.api.routes.solver ──┘                         │
                                                        TriangleValidator
                                                               │
                                                         RuleRegistry
                                                               │
                                                      metadata + formulas
models: hợp đồng dữ liệu dùng chung cho tất cả các tầng
```

| Module | Trách nhiệm |
|---|---|
| `models/triangle.py` | Enum, request, kiểm tra số hữu hạn, metadata biến |
| `models/rule.py` | Metadata luật bất biến, ràng buộc đầu vào/đầu ra |
| `models/inference.py` | Status, step, response có thể serialize JSON |
| `knowledge/rules.py` | Đăng ký, truy xuất, phân nhóm và thực thi R01–R46 |
| `knowledge/formulas.py` | Lượng giác theo độ, cosin và Heron ổn định số học |
| `core/validator.py` | Miền giá trị, hình học, đối chiếu dữ kiện dư và tolerance |
| `core/inference_engine.py` | Quét luật xác định, kiểm tra ứng viên, trace, điều kiện dừng |
| `services/solver_service.py` | Entry point chung, revalidate input và gọi core |
| `cli.py` | Parse assignments, in kết quả/trace/JSON và exit code |
| `api/main.py`, `api/routes/solver.py` | Factory, HTTP schema/response, metadata endpoints |

Engine không ghi đè dữ kiện. K tăng đơn điệu; ứng viên được kiểm tra trước khi chấp nhận. Trace có số bước, ID, nhóm Q, inputs, formula, output và value. Sau mỗi biến mới, validator đối chiếu tất cả luật có đủ đầu vào và đầu ra. Mục tiêu đã nằm trong H vẫn phải qua validation. Mỗi solve giữ dữ liệu cục bộ, không chia sẻ facts/trace giữa request.

## Danh sách tệp thay đổi

Đường dẫn dưới đây tương đối với `Bai1`. Các file ban đầu chưa được Git theo dõi vẫn được phân loại theo trạng thái thực tế lúc audit.

**Chỉnh sửa/hoàn thiện:**

- `README.md`, `IMPLEMENTATION_GUIDE.md`, `requirements.txt`.
- `main.py`: tạo lại entry point vào CLI từ tệp rỗng đã bị xóa.
- `triangle_knowledge_base/README.md`.
- `triangle_knowledge_base/app/models/{triangle,rule,inference}.py`.
- `triangle_knowledge_base/app/knowledge/{rules,formulas}.py`.
- `triangle_knowledge_base/app/core/{validator,inference_engine}.py`.
- `triangle_knowledge_base/app/services/solver_service.py`.
- `triangle_knowledge_base/app/api/main.py`, `app/api/routes/solver.py`.
- `triangle_knowledge_base/tests/test_inference.py`: chuyển bộ test lỗi import sang Pytest, tách T01–T12 và kiểm tra đầy đủ kết quả/trace.

**Tạo mới:**

- `.gitignore`, `pyproject.toml`, `requirements-lock.txt`, `DELIVERY_REPORT.md`.
- `triangle_knowledge_base/__init__.py`, `__main__.py`.
- Các `__init__.py` trong `app`, `models`, `knowledge`, `core`, `services`, `api`, `api/routes`.
- `triangle_knowledge_base/app/cli.py`.
- `triangle_knowledge_base/tests/{test_models_validation,test_knowledge,test_api,test_cli}.py`.
- `triangle_knowledge_base/tests/report_rules.csv`: bản chép phụ lục độc lập với registry để đối chiếu.
- `scripts/record_evidence.py`.
- `evidence/{environment.json,pytest-results.txt,report-cases.json,demo-T01.txt,demo-T04.txt,demo-T09.txt,demo-T11.txt}`.

Không loại bỏ module nào. `.venv`, cache Python và Pytest được bỏ qua bởi Git.

## Những thay đổi quan trọng

- Giữ đúng 46 luật và metadata Phụ lục A; không có `eval`, không có arcsin hay suy ngược Heron.
- Enum nhận đúng tên từ JSON/Python, phân biệt hoa/thường; số nguyên hợp lệ được nhận nhưng bool, chuỗi số, NaN/inf bị chặn.
- `RuleRegistry` tách metadata có thể xuất API khỏi trusted Python callable; phát hiện ID trùng và khai báo sai cấu trúc.
- Heron được kiểm tra từ ba cạnh ngay cả khi chưa có p, bảo vệ T09 khi mục tiêu đã biết.
- Cosin dùng half-angle/atan2 và Heron dùng dạng Kahan tương đương để giảm mất chữ số có nghĩa. Đây là cách đánh giá số học của cùng quan hệ, không thay đổi luật hoặc miền nghiệm. R20 vẫn yêu cầu p; Q02 kiểm tra p trước khi gọi.
- Kiểm tra thêm điều kiện cần `p > mỗi cạnh đã biết`, giúp phát hiện dữ kiện mâu thuẫn trước khi một luật tính ra cạnh không dương.
- CLI và API gọi chung `SolverService`, không có nhánh giải toán riêng trong presentation.
- API từ chối request sai bằng 422 có diagnostics JSON an toàn, kể cả NaN/inf trong raw JSON; bốn trạng thái nghiệp vụ nằm trong response 200.

## Kết quả thực tế và bằng chứng

**240 passed, 0 failed**, gồm đủ **T01–T12**; Python **3.13.5**, Pydantic **2.14.1**, FastAPI **0.161.1**, Pytest **9.1.1**. Phiên bản đầy đủ, timestamp có múi giờ +07 và nền tảng được lưu trong [environment.json](../../evidence/environment.json); log từng test tại [pytest-results.txt](../../evidence/pytest-results.txt). Có một cảnh báo deprecation từ Starlette TestClient về HTTPX; không ảnh hưởng kết quả hiện tại.

| Nhóm | Số test | Nội dung |
|---|---:|---|
| Knowledge base | 147 | Inventory; đối chiếu 46 metadata; 92 phép tính trên hai tam giác; registry/model lỗi |
| Inference | 17 | T01–T12, tái lập, mục tiêu đã biết, không nhận ứng viên mâu thuẫn, nhiều đường tính, closure |
| Models/validation | 41 | Kiểu dữ liệu, miền, dữ kiện dư, tolerance, overflow/underflow, tam giác mảnh và góc sát biên |
| API | 19 | Bốn trạng thái, HTTP schema, raw NaN/inf, metadata và OpenAPI, service injection |
| CLI | 16 | Subprocess, JSON, cú pháp lỗi, module entry point, text trace |

`pip check` trả **No broken requirements found**. `compileall` hoàn tất không có lỗi import/cú pháp. API được kiểm thử qua ASGI TestClient với application thật; không cần một dịch vụ bên ngoài.

| Ca | Trạng thái | Kết quả chính |
|---|---|---|
| T01 | SOLVED | p=6, S=6, hc=2.4, r=1, R=2.5 |
| T02 | SOLVED | C=70, a≈8.152074691, b≈9.216049851 |
| T03 | SOLVED | a=5, S=6 |
| T04 | SOLVED | c=5, S=6, hc=2.4 |
| T05 | SOLVED | S=30 |
| T06 | UNRESOLVED | Thiếu S |
| T07 | INVALID | Ba cạnh suy biến |
| T08 | INVALID | Cạnh âm |
| T09 | INCONSISTENT | S=7 được giữ nguyên; Heron đòi S=6 |
| T10 | UNRESOLVED | Thiếu a, chưa có kích thước |
| T11 | UNRESOLVED | Thiếu B, C, c; không chọn một nhánh SSA |
| T12 | SOLVED | r=1 |

Giá trị đầy đủ và trace: [report-cases.json](../../evidence/report-cases.json). Demo CLI thực tế: [T01](../../evidence/demo-T01.txt), [T04](../../evidence/demo-T04.txt), [T09](../../evidence/demo-T09.txt), [T11](../../evidence/demo-T11.txt). Dùng `python scripts/record_evidence.py` để chạy lại toàn bộ kiểm thử và tái xuất.

## Chạy CLI, API và ví dụ request/response

Từ `Bai1`:

```powershell
.\.venv\Scripts\python.exe main.py --facts "a=3,b=4,p=6" --goals "c,S,hc"
.\.venv\Scripts\python.exe -m uvicorn triangle_knowledge_base.app.api.main:app --host 127.0.0.1 --port 8000
```

Request `POST /api/v1/solve`:

```json
{"facts":{"S":6,"p":6},"goals":["r"]}
```

Kết quả `SOLVED`, `facts={"S":6.0,"p":6.0,"r":1.0}`, `missing=[]`, một bước R34/Q08. Schema response đầy đủ trong [README](../../README.md), có thể thử tại `/docs`. Các endpoint metadata là `/api/v1/variables`, `/api/v1/rules`, `/api/v1/rules/{id}`.

## Cập nhật báo cáo học thuật

- Thay phần thiết kế dự kiến bằng cấu trúc phân lớp và hợp đồng Pydantic v2 đã triển khai; bổ sung shared service và REST API.
- Ghi nhận validation ứng viên trước khi thêm K và trace; kiểm tra dữ kiện dư trước khi kết luận đạt G.
- Giữ bảng 13 biến/46 luật; mô tả dạng số học tương đương dùng Kahan/atan2, điều kiện p và giới hạn float.
- Phụ lục B: điền T01–T12 từ `report-cases.json`, dẫn log và demo; ghi phiên bản thư viện/môi trường từ `environment.json`.
- Minh họa T04 bằng trace thực tế 8 bước (R07, R15, R17, R19, R20, R22, R25, R28); sơ đồ 3 bước là chuỗi phụ thuộc rút gọn.
- Làm rõ HTTP 422 khác với INVALID nghiệp vụ, và `missing=[]` không tự động có nghĩa SOLVED.
- Các giá trị T02 trong PDF đã được làm tròn; test dùng biểu thức toán học chưa làm tròn, kết quả khớp tolerance gốc.

PDF được giữ nguyên để người viết báo cáo chủ động cập nhật nội dung học thuật và thông tin nhóm.

## Giới hạn và trạng thái nghiệm thu

Các yêu cầu bắt buộc P0–P7 đã triển khai và kiểm thử. Frontend là tùy chọn và chưa triển khai. Không có phân nhánh SSA, đảo Heron, solver ký hiệu hay tối ưu đường suy luận. SOLVED chỉ phản ánh các ràng buộc đủ dữ kiện; không phải chứng minh tồn tại/duy nhất toàn cục. Các phép toán có thể mất độ chính xác ở quy mô float cực đoan; hướng tính không biểu diễn được sẽ bị bỏ qua và nêu trong UNRESOLVED nếu thiếu mục tiêu. Tolerance mặc định cần xem xét khi đổi đơn vị hoặc độ lớn.

Hướng mở rộng: phân tích nhiều nghiệm SSA với kiểu response tương ứng, tối ưu chuỗi suy luận, giao diện gọi API; cập nhật đồng thời M/F, báo cáo và kiểm thử khi thay phạm vi.
