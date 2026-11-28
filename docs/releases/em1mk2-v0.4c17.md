**Bản cần thử: v0.4c17.** Chỉ cho **Olympus OM-D E-M1 Mark II đang ở firmware 3.7**, Windows 64 bit.

> Đừng nạp v0.4c24 trở đi: làm máy **lặp khởi động**. Bản này chưa chạy trên máy thật, có thể làm máy treo.

1. **Sao lưu** ảnh trên thẻ và cài đặt máy. Sạc đầy pin.
2. **Tải `caduceus-build.exe`** ở dưới, bỏ vào thư mục trống rồi **nhấp đúp**. Windows cảnh báo thì chọn
   *More info → Run anyway*.
3. Gõ `yes` để đồng ý giấy phép OM. Cắm thẻ SD, gõ số của thẻ rồi gõ `y` để chương trình tự chép. **Giữ lại** thư mục `out`.
4. Tắt máy, lắp thẻ vào **khe 1**, **giữ OK rồi bật máy**. Đèn sáng liên tục là đang nạp: không tắt máy, không rút
   pin/thẻ. Đèn nháy đều là xong. Tắt máy, xoá `DCOLYMP/E1259999.BIN` trên thẻ, bật lại.
5. **Báo lại** máy có lên không. Nếu lặp khởi động, cho biết từ lúc bật đến lúc tắt mất khoảng 1, 10 hay 30 giây.

**Máy lặp khởi động?** Chép `out/.../restore/E1259999.BIN` vào thư mục `DCOLYMP/` trên thẻ, giữ OK + bật máy. Máy về
firmware gốc 3.7.

v0.4c17: look / Color Creator, XPan 65:24 và 21:9, video 9 giờ, focus stacking. Không có halation.
SHA-256 của `DCOLYMP/E1259999.BIN` sau khi dựng: `6da28f37d7e9ec25bdf660d4708d3f4ab6e5a29f445f50029b8e539d8eb97d54`.
Tệp `SHA256SUMS` ghi mã của EXE và ZIP. Có Python 3.10+ thì dùng `caduceus-em1mk2-source.zip`.

[Hướng dẫn đầy đủ](https://github.com/xtruong88/caduceus-em1ii/blob/main/README.vi.md#cài-nhanh)
