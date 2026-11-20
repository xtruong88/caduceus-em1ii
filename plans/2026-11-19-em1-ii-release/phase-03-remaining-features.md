# Hoàn thiện tính năng còn thiếu

- Ưu tiên [halation](../../docs/OMD-EM1-II/HALATION.md). Xác định setting ghi nhớ và các đường Soft Focus, CPU pass, watchdog. Xác minh độ mạnh toàn cục, màu theo look và điều kiện chỉ áp dụng cho ảnh tĩnh màu.
- Xác định và kiểm chứng đường xử lý riêng cho Blacks/Whites, monochrome, grain, sharpening off, NR và thêm chức năng nút. Chốt hợp đồng look dùng chung trước khi thay đổi Control Panel.
- Hoàn thành các lỗi thực tế từ [mốc thử máy](phase-02-camera-validation.md). Chỉ mở lại debug logger sau khi có hook sự kiện và điều kiện HLS đã kiểm chứng.
- Tái tạo release từ stock đã ghim và chạy lại toàn bộ kiểm tra. Mỗi chức năng cần bằng chứng giả lập và kết quả từ E‑M1 Mark II trước khi được ghi là hoàn thiện.
