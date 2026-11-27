## Cài nhanh cho Olympus OM-D E-M1 Mark II

1. Xác nhận máy đang ở firmware gốc **3.7**, sạc đầy pin, sao lưu cài đặt và thẻ SD.
   [Hướng dẫn sao lưu](https://github.com/xtruong88/caduceus-em1ii/blob/em1mk2-v0.4c24/docs/huong-dan-firmware-em1-ii.md#sao-luu)
2. Tải và nhấp đúp `caduceus-build.exe` trên Windows 64 bit. Với `caduceus-em1mk2-source.zip`, cài Python 3.10+,
   giải nén rồi mở launcher Windows hoặc macOS. Trên Linux, chạy `build-caduceus-linux.sh`.
3. Đọc giấy phép OM Digital Solutions và gõ `yes` nếu đồng ý. Chương trình kiểm file 3.7 gốc từ máy chủ OM và
   dựng gói vào `out/em1mk2-v0.4c24/`.
4. Cắm thẻ có thư mục `DCIM`, chọn đúng ổ và xác nhận chép. Giữ `restore/E1259999.BIN` trên máy tính.
5. Eject thẻ, lắp vào khe 1 khi máy tắt, giữ **OK** và bật máy. Đợi đèn chuyển từ sáng liên tục sang nhấp nháy đều
   khoảng hai lần mỗi giây. Hướng dẫn có bước nạp thử bản gốc 3.7 trước khi nạp Caduceus.
   [Các bước nạp](https://github.com/xtruong88/caduceus-em1ii/blob/em1mk2-v0.4c24/docs/huong-dan-firmware-em1-ii.md#nap)

Windows SmartScreen có thể cảnh báo vì EXE chưa ký. Gói ZIP có launcher Python. Tệp đính kèm `SHA256SUMS` ghi
mã SHA-256 của EXE và ZIP.

| Bản firmware | Trạng thái |
|---|---|
| **v0.4c24** | Mặc định nên dùng. Có halation và watchdog 30 giây. Halo mặc định Off. |
| v0.4c25t | Bản thử nhớ look sau khi tắt máy. Chọn bằng `--release v0.4c25t`. |
| v0.4c26t | Bản thử WB shift theo look. Chọn bằng `--release v0.4c26t`. |
| v0.4c27t | Bản thử trang Wheel. Chọn bằng `--release v0.4c27t`. |

SHA-256 của `DCOLYMP/E1259999.BIN` sau khi dựng v0.4c24

```text
cd26414b88807885c25dde94bb01ac2adc16364cd82fe9e0a6ee4b5947fa25fc
```

**Rủi ro và khôi phục.** v0.4c24 đã qua kiểm tra trên giả lập và đang chờ thử trên máy thật. Firmware sửa đổi
có thể làm máy treo hoặc không khởi động. Tuyệt đối giữ nguyên pin và thẻ trong lúc đèn sáng liên tục. Để quay
về 3.7 gốc, chép `restore/E1259999.BIN` vào `DCOLYMP/E1259999.BIN` trên thẻ và lặp lại quy trình giữ **OK**
khi bật máy. [Hướng dẫn khôi phục](https://github.com/xtruong88/caduceus-em1ii/blob/em1mk2-v0.4c24/docs/huong-dan-firmware-em1-ii.md#khoi-phuc)
