# Thử trên máy: v0.4c26t, WB theo look (E-M1 Mark II)

Bản thử v0.4c26t = v0.4c25t cộng **một** tính năng: look màu mang độ lệch cân bằng trắng (WB shift) riêng, như các mô
phỏng phim. Bản này chỉ dùng để thử: chỉ nạp **sau khi v0.4c25t đã chạy tốt trên máy**
([thu-may-nho-look.md](thu-may-nho-look.md)). Cách nạp và khôi phục theo
[huong-dan-firmware-em1-ii.html](../huong-dan-firmware-em1-ii.html).

## Cách hoạt động

- Mỗi look có thể ghi WB shift `a_b` (Amber-Blue) và `g_m` (Green-Magenta), từ −7 đến +7, trong `LOOKS.BIN` hoặc trong
  bảng look có sẵn. Look không ghi WB thì không đổi gì.
- Khi chụp ở **Color Creator** với một look màu đang bật, máy dùng WB shift của look thay cho fine-tune WB bạn đã đặt.
  Menu vẫn hiện giá trị của bạn và không bị ghi đè. Chuyển sang mode khác là WB như cũ.
- **CWB (đặt nhiệt độ màu bằng Kelvin): giữ nguyên.** Bạn đã chọn nhiệt độ màu thì máy không đổi nó.
- Look đơn sắc: chưa có WB.
- **Năm look có sẵn (cùng tên trong pack trên thẻ) mang WB shift và sẽ đổi màu JPEG so với v0.4c25t**, vì trước đây máy
  bỏ qua giá trị này: Nostalgic A-B +3, Gold 200 +2, Kodachrome64 +1, Portra 400 +1, CineStill800 −3. Không look nào
  có G-M.
- RAW xử lý trong máy (RAW development) vẫn như máy gốc.

## Đã kiểm trên giả lập

Seal chạy mọi bước kiểm của v0.4c25t, cộng `tools/omdem1mk2_emu_look_wb.py`:
- **14 chỗ đọc WB** (12 ở khối chụp, 2 ở compact slot) đều qua stub; hai chỗ đọc của RAW development vẫn như máy gốc;
- **27 trạng thái trên từng chỗ đọc:**
  - không có look, look tắt, sai mode, CWB, look không có WB, thẻ chưa đọc hoặc hỏng, record sai giá trị: giống máy
    gốc ở mọi thanh ghi;
  - look có WB (có sẵn hoặc trên thẻ, kể cả −7 và +7): trả đúng giá trị của look;
- **khối chụp chạy thật** (category 1 với 15 preset, gồm Flash; category 0, 2, 3, 4):
  - không có look: khối capture giống máy gốc từng byte;
  - có look +5/−4: giống hệt máy gốc khi fine-tune đặt +5/−4;
  - CWB: giống máy gốc.

**Chưa kiểm được:** phần sau khối đọc WB (bracketing WB, tính gain), live view, và việc ISP có thật sự ra màu như mong
đợi. Trên E-P7, live view **không** hiện WB shift, chỉ JPEG có. E-M1 II có thể cũng vậy, nên đó không phải lỗi.

## Các bước thử

Cần: một thẻ xám (hoặc tờ giấy trắng), ánh sáng ổn định, WB đặt sẵn một preset (ví dụ Daylight), fine-tune WB = 0.

1. Nạp `out/em1mk2-thu-may/6-v0.4c26t` (dựng như README, mục Install), khởi động, chụp thử một ảnh.
2. Natural, chụp thẻ xám: ảnh **N**.
3. Color Creator, chọn một look **không** có WB shift (ví dụ Provia). Chụp thẻ xám: ảnh **P**. Màu xám phải giống N.
4. Chọn **Nostalgic** (A-B +3). Chụp thẻ xám: ảnh **W**. Rồi chọn **CineStill800** (A-B −3), chụp: ảnh **C**.
   - Đạt: W ấm hơn rõ so với P (trung bình R/B cao hơn), C lạnh hơn P. Nostalgic còn đổi cả bão hoà, nên chỉ so màu
     của thẻ xám.
   - Live view có thể không đổi: ghi lại, không phải lỗi.
5. Đặt WB sang CWB (ví dụ 5300 K), giữ look ở bước 4, chụp: ảnh **K**. Đổi sang Provia, chụp: ảnh **K2**. K và K2 phải
   có cùng màu xám (CWB không bị đổi).
6. Trở lại preset, đặt fine-tune WB của bạn là A+4, chụp với Provia rồi với look ở bước 4. Provia phải ấm theo A+4; look ở
   bước 4 dùng giá trị của look, không cộng thêm A+4.
7. Mở menu WB: fine-tune vẫn là giá trị bạn đặt.

Gửi lại các ảnh N, P, W, C, K, K2 (JPEG gốc). Nếu có gì lạ: nạp lại v0.4c25t (stub chỉ đọc, không ghi setting nào). Nếu
máy không khởi động: nạp `restore/E1259999.BIN`.
