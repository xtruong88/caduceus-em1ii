# Build từ firmware OM 3.70

- Bắt đầu từ [v0.4c15](../../releases/em1mk2/v0.4c15/build.json), giữ các look trong Color Creator, đọc looks từ thẻ, 65:24 và 21:9, AF/SCP, bỏ giới hạn quay và mở khóa focus stacking.
- Gói OM có SHA-256 bắt đầu bằng `691a8a8e`. Phần đã nạp của Section 1 có dữ liệu icon 21:9, nên giữ bố cục v0.4c15 và khôi phục 2 KiB đệm vào phạm vi nạp của Section 1. Xác thực byte gốc, đối số truyền, pointer, lệnh nhảy và các vùng chồng lấn.
- Đọc giới hạn section từ từng ảnh firmware trong audit và bộ giả lập. Chạy so sánh stock và patched cho validator, interlock, AF, SCP, nhãn, đọc thẻ, đường dẫn tỷ lệ ảnh và các hook có trong release. Nạp OSD 0x101 trong những ca đọc tài nguyên OSD.
- Ghim checksum của gói OM và hai đầu ra riêng cho release mới. Chạy builder qua CLI phổ thông, kiểm tra bằng `verify`, và kiểm tra file khôi phục khớp từng byte với gói OM.
- Giao thư mục `DCOLYMP` và `EM1MOD` đã kiểm tra cùng thư mục `restore` để giữ trên máy tính. Ghi rõ kết quả giả lập và phần còn phụ thuộc vào camera.

v0.4c17 đã qua kiểm tra loader, validator và interlock, đường tỷ lệ ảnh, SCP, 768 ca AF, đọc looks, giới hạn quay và nhánh focus stacking. Ca giả lập Color Creator so sánh firmware gốc, v0.4c16 và v0.4c17, bao gồm tên ở editor và SCP, tone và các vùng màu khi thẻ nạp muộn. Gói build ở `out/em1mk2-v0.4c17` đã qua `verify`. Xem các checksum trong [manifest release](../../releases/em1mk2/v0.4c17/SHA256SUMS).
