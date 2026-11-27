# Thử trên máy: v0.4c27t, vòng màu trong Color Creator (E-M1 Mark II)

Bản thử v0.4c27t = v0.4c26t (nhớ look + WB theo look) cộng **một** tính năng: trang **Wheel** trong Color Creator vẽ
look đang chọn lên vòng màu 12 ô (S, H hoặc L), giống vòng màu của E-P7 / PEN-F. Bản này chỉ hiển thị: không đổi
setting nào, không đổi ảnh chụp. Cách nạp và khôi phục theo
[huong-dan-firmware-em1-ii.html](../huong-dan-firmware-em1-ii.html).

Nền là v0.4c26t, kể cả khi v0.4c26t chưa được thử trên máy. Vì vậy bước 0 bên dưới thử v0.4c26t trước, để lỗi của nhớ
look / WB không bị nhầm với lỗi của vòng màu.

## Cách hoạt động

- Thứ tự trang (INFO đi tới): **Film → Wheel → Chroma → Luminance → Strength → Halo → Film**. Trang Wheel nằm ngay sau
  Film; các trang khác chạy như v0.4c26t, chỉ lùi số trang một bậc.
- Vào trang Wheel: vòng Color Creator gốc được thay bằng vòng màu 12 ô của máy (bề mặt C3d "kind 5", có sẵn trong
  firmware nhưng máy gốc không dùng). Đa giác vẽ trục **S** của look trước.
- Trên trang Wheel, **nút xuống** hoặc **TRASH (Xoá)** đổi trục **S → H → L → S** (giống phím Delete trên E-P7 / PEN-F
  và nút xuống trên E-M10 I). Dòng guide hiện `Wheel S <tên look>`, `Wheel H …`, `Wheel L …`.
- **INFO** trên trang Wheel sang trang Chroma.
- **Lên, trái, phải** và hai **vòng xoay** không làm gì trên trang Wheel (để dành cho bản sau).
- **OK**, **MENU** và các sự kiện khác của máy (ví dụ nút tuỳ biến) từ trang Wheel: vòng màu đóng, vòng Color Creator
  gốc mở lại, trình chỉnh về Film, rồi máy xử lý phím đó như máy gốc.
- Trên các trang khác, TRASH vẫn đi tới trang kế tiếp như v0.4c26t.

## Đã kiểm trên giả lập

Seal chạy mọi bước kiểm của v0.4c26t (trừ `emu_halo_page`, vì Halo đã sang trang 5: trang này được kiểm trong
`emu_color_wheel_page`), cộng:
- `tools/omdem1mk2_emu_color_wheel_probe.py`: luồng của máy gốc từ producer → builder → renderer tới tác vụ C3d; mở bề
  mặt khi đang có bề mặt khác mở thì treo, nên luôn phải đóng trước rồi mới mở;
- `tools/omdem1mk2_emu_color_wheel_feed.py`: giá trị đưa vào vòng (12 ô, profile, con trỏ) lấy đúng từ look, trục S/H/L;
- `tools/omdem1mk2_emu_color_wheel_page.py`: các trang chạy thật trong ảnh firmware:
  - INFO ×6: vào Wheel thì đóng 0 → mở 4 → vẽ; rời Wheel thì đóng 4 → mở 0 → vẽ; luôn đóng trước khi mở;
  - nút xuống ×4 và TRASH ×4 trên Wheel: trục H, L, S, H, mỗi lần chỉ vẽ lại, không đóng/mở, vẫn ở trang Wheel;
  - lên, trái, phải và các nấc vòng xoay: không đổi gì;
  - thoát bằng OK / MENU từ cả ba trục: đóng 4 → mở 0 → vẽ rồi mới tới xử lý gốc; mở lại editor: sạch;
  - các sự kiện khác (0x972b, 0x903e, 0x900d, 0x900e và một mã không có trong bảng của máy): đóng 4 → mở 0 → vẽ, làm
    mới widget con và màn hình như khi đổi trang, rồi mới tới xử lý gốc; dòng guide hiện tên look của trang Film;
  - Chroma, Luminance, Strength, Halo ở trang mới cho kết quả giống hệt v0.4c26t ở trang cũ.

**Chưa kiểm được trên giả lập:**
- chuỗi thật từ trang tới tác vụ C3d chạy liền một mạch (các đoạn đã chạy riêng trong probe; ở harness trang, lệnh
  đóng/mở/vẽ là stub ghi log);
- hình trên màn: đa giác có hiện không, nằm ở đâu, có bị OSD che không, vòng Color Creator có trở lại không;
- thoát bằng **nửa cò** và **tắt máy** từ trang Wheel: không có hook riêng, dựa vào lệnh đóng của chính GUI và việc mở
  lại editor tự xoá cờ vòng màu;
- vòng xoay thật: giả lập chỉ mô phỏng cách vòng lặp vòng xoay gọi phím (cờ P_DIAL), không chạy vòng lặp gốc;
- bán kính ×9 trên máy và hình vòng nền (bitmap 210) có khớp màu với ô 0 hay không.

## Các bước thử

0. **Nếu chưa thử v0.4c26t:** nạp `out/em1mk2-thu-may/6-v0.4c26t` trước, làm các bước trong
   [thu-may-look-wb.md](thu-may-look-wb.md) (và nhớ look trong [thu-may-nho-look.md](thu-may-nho-look.md)), ghi kết
   quả để có mốc so sánh.
1. Nạp `out/em1mk2-thu-may/7-v0.4c27t`, khởi động. Mở Color Creator, nhấn INFO **một lần** từ Film tới Wheel:
   - có đa giác không, nằm ở đâu, có bị OSD che không; chụp màn hình (chụp bằng điện thoại cũng được).
2. Nhấn **nút xuống** ba lần, rồi **TRASH** ba lần: dòng guide đổi Wheel S → H → L → S, đa giác đổi theo trục.
3. Nhấn INFO cho tới khi về Film, đổi look bằng mũi tên, rồi INFO một lần tới Wheel: đa giác đổi theo look mới (lại bắt
   đầu ở S).
4. INFO tiếp tới Chroma, Luminance, Strength, Halo: vòng Color Creator gốc trở lại, các trang chạy như v0.4c26t; TRASH
   trên các trang này vẫn sang trang kế.
5. Từ trang Wheel, thoát lần lượt bằng **OK**, **MENU**, **nửa cò**, **tắt máy** (mỗi lần mở lại Color Creator, INFO tới
   Wheel rồi mới thoát):
   - không treo, không sót hình vòng màu trên màn;
   - mở lại Color Creator: vòng gốc bình thường, vào Wheel lại được.
   - Thêm một lần với sự kiện lạ: ở trang Wheel bấm một **nút tuỳ biến** (Fn, nút xem lại, nút ghi hình… nút nào máy
     cho phép trong Color Creator). Màn hình phải về **Film** (vòng Color Creator gốc, dòng guide là tên look), không còn
     ghi `Wheel …`; bấm nút xuống sau đó phải đổi look như ở trang Film, và đó là đúng.
6. Chụp cùng một look trên bản này và trên v0.4c26t: JPEG phải giống nhau (vòng màu chỉ hiển thị).
7. Xem trang Wheel trong **kính ngắm (EVF)**, không chỉ màn LCD: vòng có nằm giữa không, có bị cắt không (bản E-M10 I
   từng bị lệch tâm trong EVF).

Gửi lại ảnh màn hình của bước 1, 2, 7 và ghi chú các bước 3–6. Nếu máy treo khi thoát: tháo pin, nạp lại v0.4c26t. Nếu
máy không khởi động: nạp `restore/E1259999.BIN`.
