# Hoàn thiện Caduceus cho Olympus E‑M1 Mark II

Mục tiêu là build được từ firmware OM 3.70, có gói cập nhật và khôi phục xác minh được, rồi hoàn thiện các tính năng đã ghi trong [current.todo](../../current.todo).

| Mốc | Trạng thái | Điều kiện hoàn thành |
| --- | --- | --- |
| [1. Build từ firmware OM](phase-01-build-from-om.md) | Đã build và verify v0.4c17 | Bản vá qua các kiểm tra giả lập. CLI tạo đúng manifest, file SD và file khôi phục. |
| [2. Xác nhận trên E‑M1 II](phase-02-camera-validation.md) | Chờ thử v0.4c17 trên máy thật | Máy khởi động, chụp ảnh và đọc looks. Ghi lại kết quả SCP, AF và RAW+JPEG. |
| [3. Hoàn thiện tính năng còn thiếu](phase-03-remaining-features.md) | Cần nền ổn định từ mốc 2 | Từng nhóm tính năng có kết quả giả lập và thử trên máy trước khi gộp vào bản cuối. |

Nguồn firmware là gói E‑M1 Mark II 3.70 từ OM. Repo chỉ giữ các edit và checksum để tái tạo gói.

Đã kiểm tra trên PC hai trường hợp chép thẻ E‑M1 II. Cài lần đầu sẽ chép pack đi kèm. Khi cập nhật,
trình chép giữ `EM1MOD/LOOKS.BIN` đang có. CLI từ chối manifest checksum rỗng và xác minh thành công
cả gói cập nhật, pack đi kèm và gói khôi phục của v0.4c17. Đã tái hiện và sửa lỗi lệch tên với màu
khi thẻ nạp sau lúc mở Color Creator. Ca này đã qua giả lập và có bước kiểm tra trên máy thật.
