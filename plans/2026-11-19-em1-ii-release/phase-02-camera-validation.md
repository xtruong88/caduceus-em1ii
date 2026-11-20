# Xác nhận trên máy thật

- Xác nhận model Olympus OM‑D E‑M1 Mark II và firmware 3.70 theo [hướng dẫn port](../../docs/PORT_EM1MK2.md). Dùng bản thử v0.4c17 trong `out/em1mk2-v0.4c17` và đối chiếu checksum trước khi dùng thẻ.
- Xác nhận máy khởi động lại, menu hoạt động, chụp và lưu ảnh ở 4:3. Kiểm tra Color Creator với preset tích hợp khi thẻ chưa có pack.
- Sao lưu pack đang dùng rồi chép [file thử LOOKS.BIN](../../out/em1mk2-v0.4c16-look-test/EM1MOD/LOOKS.BIN) vào `EM1MOD/` trên thẻ. File thử chứa hai look `SD Velvia` và `SD Bleach` lấy từ pack E‑P7 v0.31c và đã qua kiểm tra định dạng v3. Giữ file thử riêng khỏi thư mục gói firmware đã có checksum.
- Tắt bật máy, nhấn nửa cò, mở Color Creator, ghi mã `C…` và xác nhận hai tên look lần lượt hiển thị. Chụp cùng một cảnh có màu đỏ và xanh với cả hai look. Giữ cố định ánh sáng, phơi sáng và cân bằng trắng để so sánh live view và JPEG.
- Nếu máy cho mở Color Creator trước lần nhấn nửa cò đầu tiên, thử thứ tự đó sau khi tắt bật máy. Khi thẻ vừa nạp và editor vẫn mở, tên và màu phải còn khớp preset đang dùng dù đã báo `C1`. Thoát rồi mở lại Color Creator. Xác nhận `SD Velvia` xuất hiện cùng màu đã chụp ở ca nhấn nửa cò trước. Kiểm tra tên trên SCP, chuyển sang `SD Bleach` rồi mở lại editor để xác nhận lựa chọn được giữ trong phiên.
- Thử 65:24 và 21:9 trong menu, SCP, AF, tracking, Live Control, Rec View và grid. Kiểm tra kích thước JPEG, RAW+JPEG, lưu tỷ lệ qua lần tắt máy, và quay phim ngắn.
- Ghi lại bản build, lens, thẻ và chế độ cho từng vấn đề. Kiểm tra checksum và giữ gói stock khôi phục khi cần quay về 3.70.
