# E-M1 II v0.4c24: máy lặp khởi động. Chẩn đoán bằng emulator

Ngày 2026-11-28. Chỉ dùng emulator và đọc tĩnh, không dựng bản nào cho máy thật.
Ký hiệu: **[V]** đã chạy trong emulator, **[S]** đọc tĩnh hoặc tính bằng Python trên ảnh, **[I]** suy luận.

## Kết luận ngắn

- **Chưa xác định được một edit duy nhất gây lặp khởi động.** Emulator không chạy được toàn bộ quá trình boot, và
  mọi phần của đường boot chạy được đều cho kết quả đúng ý đồ.
- Đã thu hẹp được rõ: so với v0.4c15 (bản cuối chạy trên máy, base cũ `f0c25dd8…`), trên đường boot c24 **chỉ khác 3
  điểm**, cộng với việc đổi base:
  1. **Đổi base sang tệp catalog `691a8a8e…`** (từ c16). Chưa bản nào trên base này được thử trên máy.
  2. **End-word Section 1** `0x60257000 → 0x60257800` (từ c16). Chưa thử trên máy với bất kỳ base nào.
  3. **End-word Section 6** `0x612e7000 → 0x61300000` (từ c22t). Đã thử trên máy với sp1, nhưng trên base cũ.
  4. **Watchdog 10 → 30 s** ở hai chỗ (từ c22t). Chưa thử trên E-M1 II.
- Nghi vấn mạnh nhất **[I]**: (1)+(2), tức base catalog cùng phần nạp thêm 2 KiB ở đuôi Section 1. Đây là những thay đổi
  mới duy nhất trên đường boot mà chưa bản nào thử trên máy, và chúng có từ c16. Watchdog đứng thứ hai, Section 6 thứ ba.
- **Khuyến nghị: rút v0.4c24 (và c25t/c26t/c27t, vì chúng mang cùng 4 điểm này).** Muốn chia đôi trên máy thì theo
  thứ tự ở mục "Đề xuất sửa".

## Bằng chứng

### Gói tin đúng như spec [S]

Tôi giải mã `out/em1mk2-thu-may/4-v0.4c24/DCOLYMP/E1259999.BIN` (SHA `cd26414b…`, trùng `releases/em1mk2/v0.4c24`) và
so từng component với stock catalog:
- 0x100 khác đúng 12 744 byte, đúng bằng tập byte các edit thay đổi;
- 0x101, 0x106, 0x10e, 0x102 giống hệt stock;
- header không đổi, chỉ trailer được reseal.

`tools/build_package.py` (dùng cho c15) và `caduceus.py` (dùng cho c24) reseal theo cùng một cách. Vậy lỗi không nằm ở
khâu đóng gói.

### Khác biệt trên đường boot, stock và từng bản chạy song song [V]

Harness mới: `tools/omdem1mk2_emu_boot_delta.py`.

```
wsl -d Ubuntu-24.04 -u root --cd /mnt/d/em1_ii/caduceus/tools -- python3 omdem1mk2_emu_boot_delta.py \
  ../releases/em1mk2/v0.4c16/edits.json ../releases/em1mk2/v0.4c17/edits.json \
  ../releases/em1mk2/v0.4c22t/edits.json ../releases/em1mk2/v0.4c24/edits.json
```

- **Khối chép lúc khởi động** `0x6002116f..0x6002127b`: chạy thật, routine chép `0x6002249f` được thay bằng `ret`.
  Có 6 lần chép, **giống hệt stock ở mọi bản**:
  - vùng thường trú `0x60030000` (`0xa8800`);
  - `.data` từ ảnh `0x60266000 → RAM 0x61f8b540` (`0x3569c`);
  - `0x6029e000 → 0x61fc3540`, `0x602a6000 → 0x61fcb540`, `0x602aa000 → 0x61fcf540`;
  - `0x61470000` (`0x1800`).

  Vậy RAM sau Section 1 (`0x60257000..0x602ae000`) chỉ là nơi chứa bản gốc của `.data` trong ảnh, không phải đích chép.
- **Loader `0x60042b96` cho S1..S9**, dừng ở yêu cầu đọc flash `0x60042bce`: c24 chỉ khác stock ở
  - S1: độ dài `0x179000 → 0x179800`, nạp thêm RAM `0x60257000..0x60257800`;
  - S6: độ dài `0x6f6000 → 0x70f000`, nạp thêm RAM `0x612e7000..0x61300000`.

  Nguồn, đích và kiểu (`0x101`) không đổi. Không vùng nạp hoặc vùng chép nào chồng lên nhau.
- **Watchdog**: SYS_WDT on và nhánh khôi phục sau thao tác flash chạy đến lệnh handshake. Field 6 bit đổi từ `(10, 10)`
  thành `(30, 30)`, đúng ý đồ.
- **Phân loại byte thay đổi trong c24**:
  - vùng thường trú: 5 byte, gồm 2 end-word và 2 byte watchdog;
  - `.data`: 110 byte, gồm bảng aspect và word guide-label, giống hệt c15;
  - phần còn lại nằm trong code các section. Code này chỉ có tác dụng khi được gọi tới.
- **Con trỏ vào vùng mới nạp** (word căn 4 byte trong mọi vùng được khởi tạo lúc boot, cả alias `0x6/0xa/0x8`):
  - 3 hit vào đuôi S1 và 45 hit vào khe S6;
  - xem từng hit **[S]**: tất cả là ASCII, byte giữa lệnh, số float hoặc bảng giá trị 24-bit (`0x613bd7xx`, giá trị tới
    `0x826d…`, vượt ngoài RAM);
  - không có con trỏ thật. Kết quả khớp với `omdem1mk2_check_gap_refs.py` (chỉ quét operand lệnh, chỉ khe S6).

### Thứ tự boot và cơ chế nạp [S]

- Thứ tự nạp trong `0x600422a8..0x6004255x`: **S1, S7, S2, trailer phiên bản (32 B từ `0x41b5ffe0`), S3, S4, S5,
  S6, S8, S9**. Tất cả chạy trong cùng một task, xen giữa có chờ các bit ở `0xa2767ae8`.
- Loader gọi `0x6005ae5b` với kiểu `0x101`. Kiểu này đi nhánh `0x600cdfba → 0x60059efd → 0x6002249f` (đọc NAND theo
  trang 2 KiB, khối 128 KiB) và **không chạm watchdog**. Nhánh có `mov 10/30` ở `0x6005aecc` chỉ chạy với thao tác ghi
  hoặc xóa flash.
- Nếu đọc lỗi, loader chỉ in `UserSub_FlashReadErr` / `LoadNo:` rồi chạy tiếp, không reset. Độ dài là bội của `0x800`,
  giống S2/S3/S5/S9 của stock.
- Các lời gọi đặt watchdog = 1 đều là nhánh "reboot soon" (touch panel sem/i2c lỗi ở `0x6024e866`, reset do người dùng
  ở `0x6021c516`, …). Nhánh `mov 10; bra .` ở `0x600cdfac` để nguyên stock.

### Các hook mới của c24 chỉ chạy khi chụp hoặc khi mở editor [S]

- `hl_flag` (`0x6042285e`) chỉ có hai caller, là hai hàm điền params khi chụp (`0x6041dde2`, `0x60420af1`).
- Còn lại:
  - `hl_route` / `hl_ob` / `hl_c11` / `hl_c12` nằm trên đường capture job;
  - các word record +12..+44 của Color Creator, View Part 3 và Halo page chạy trong editor;
  - hook ô SCP chạy khi mở SCP.
- `d0` tại entry converter là dead, nên `hl_flag` không phá thanh ghi của caller.

Vậy với Halo Off và không chụp ảnh, không hook halation nào chạy lúc boot **[I, vì chưa emulate toàn boot]**.

## Nghi vấn đã loại hoặc hạ bậc

| Nghi vấn | Trạng thái | Cách loại |
|---|---|---|
| Đóng gói / checksum / component khác | Loại | So byte toàn gói với stock + spec [S]; reseal giống c15 [S] |
| Card loader, LOOKS.BIN | Loại | Máy vẫn lặp khi tháo thẻ (quan sát) |
| Hook halation, Halo, Color Creator chạy lúc boot | Hạ bậc mạnh | Caller chỉ nằm trên đường capture hoặc UI [S] |
| Encoding watchdog sai, ghi đè bit khác | Loại | Emulator: field = 30, bit trên giữ nguyên, handshake đúng [V] |
| Watchdog 30 làm reset sớm hơn | Khó xảy ra [I] | Chỉ kéo dài giới hạn. Chuỗi debug của E-M1 II ghi đơn vị giây (`time XXX: timer change XXXsec`). Bản E-P7 v0.31b/c ship 30 s và khởi động được. Cùng thanh ghi `0x98e0008c` |
| S6 nạp thêm đè dữ liệu đang dùng | Khó xảy ra [I] | sp1 (base cũ) cho `S+` trên máy. Không có con trỏ thật vào khe trên base catalog [S]. Không chồng vùng nào [V] |
| Phần chép `.data` lúc boot khác c15 | Loại | 6 lần chép giống stock [V]; byte thay đổi trong `.data` trùng c15 [S] |
| Đuôi S1 nạp thêm chồng lên `.data` hoặc bss | Loại phần chồng vùng | Không phải đích chép [V], không con trỏ thật [S]. Còn mở: RAM ở đó có được dùng động không |

## Nghi vấn còn lại, theo thứ tự

1. **Base catalog cùng đuôi S1 (c16+)** [I].
   - c15 dựng trên `f0c25dd8…`. Không còn tệp này để so toàn ảnh.
   - Các `expect` của 215 edit cũ đều khớp base catalog, nhưng đó chỉ là byte tại chỗ hook. Hàm stock mà code của ta gọi
     tới hoặc dữ liệu nó đọc ở nơi khác thì chưa được so.
   - Trên base cũ, OM có một hàm ở `0x60256ff0..0x60257578` mà base catalog đã bỏ. Vậy hai bản build có khác nhau.
   - RAM `0x60257000..0x60257800` không có con trỏ, nhưng vẫn có thể được cấp phát động.
2. **Watchdog 30 s** [I].
   - Chỉ có E-P7 làm bằng chứng. Nếu bộ điều khiển `0x98e0…` trên E-M1 II hiểu field khác (ví dụ giá trị hợp lệ có
     giới hạn, hoặc là mã chứ không phải số giây), thì giá trị 30 có thể gây tắt máy ngay sau khi SYS_WDT bật.
   - Điều này khớp với triệu chứng: màn hình lên, cửa trập kêu, rồi tắt.
3. **Section 6 nạp thêm trên base catalog** [I]. Bằng chứng camera (sp1) có, nhưng trên base cũ.

## Đề xuất sửa (chưa build)

1. **Rút ngay** v0.4c24 khỏi release public. Ghi chú: c25t/c26t/c27t mang cùng 4 điểm. Hướng dẫn người dùng nạp
   `restore/E1259999.BIN`: người thử đã xác nhận OK+bật nguồn vẫn vào được updater khi máy đang lặp.
2. Nếu người thử đồng ý chia đôi trên máy, mỗi bước một lần nạp và đều cứu được bằng restore:
   - **T1 = v0.4c17** (base catalog + bộ c15 + đuôi S1; không watchdog, không S6). Nếu lặp, lỗi nằm ở base hoặc đuôi
     S1; chạy T1b. Nếu chạy, sang T2.
   - **T1b** = stock catalog + chỉ edit end-word S1 (đuôi toàn `0xFF`). Phân biệt "nạp thêm S1" với "code c15 trên base
     catalog".
   - **T2** = v0.4c17 + chỉ 2 byte watchdog 30.
   - **T3** = v0.4c17 + chỉ end-word S6 (khe `0xFF`, giống sp1 trên base catalog).
3. Hướng sửa theo kết quả:
   - **Đuôi S1**: bỏ edit `0x60042b4d`, chuyển cave aspect (626 B) và nhãn sang chỗ đã được nạp sẵn. Phần đuôi S1 đang
     nạp `0x60256ce8..0x60257000` chỉ còn khoảng 80 B, nên phải dùng khe S6 hoặc đuôi S2 sau sd_loader.
   - **Watchdog**: giữ 10 s và giới hạn thời gian pass halation (cap hoặc tắt WDT quanh pass như §21 E-P7).
   - **S6**: dời halation sang vùng đã nạp được chứng minh.
4. Trước bất kỳ bản mới nào, chạy `omdem1mk2_emu_boot_delta.py` để xác nhận delta trên đường boot đúng như bước chia
   đôi định thử.

## Phần chưa emulate

- Toàn bộ boot từ entry tới khi app chạy (RTOS, NAND, các CPU con). Đây là lý do không chỉ ra được một edit duy nhất.
- Bộ điều khiển watchdog thật (đơn vị, giá trị hợp lệ).
- RAM `0x60257000..0x60257800` và `0x612e7000..0x61300000` có bị cấp phát động trên base catalog không.
- So toàn ảnh `f0c25dd8…` với `691a8a8e…`: không có tệp cũ trên máy này.

## Bổ sung 08:15: trace sâu hơn và so với E-P7

- **Watchdog 30 s đã chạy trên máy E-P7** [S, WORKLOG]: E-P7 v0.31b (`mov 10,d0 → mov 30,d0` ở cùng hai chỗ) được
  thử trên máy dưới tên 0.31b4, khởi động và chụp bình thường. Cùng thanh ghi `0x98e0008c`, đơn vị giây, tối đa 63.
  Hạ watchdog xuống nghi vấn thấp.
- **Khe S6 `0x612e7000..0x61300000` chính là vùng sp1** đã cho `S+` trên E-M1 II thật (base cũ). Hạ xuống thấp.
- **Hook halation khi live view** [V]: chạy lại harness trên c24. Kết quả PASS:
  - `artflags`: 160 ca của bộ chuyển cờ có hook giống bảng stock. Hook chỉ đọc những trường mà stock vốn đọc (request+28,
    capture+24951); sid 961 và `p_get` chỉ được gọi khi kind là 0x1000/0x1001.
  - `combiner`: job không đánh dấu dùng đúng bank stock.
  - Cũng PASS: `capture_kind`, `job_marker`, `work_list`, `plain_route`, `blend_setup`, `halation_pass`, `halo_page`,
    `spare_setting` (boot thường giữ sid 961), `watchdog`, `aspect`.
  - Không chạy trọn: `halation_route` (chỉ nhận bản stage cố định, c24 đọc sid 961), `halation_flag` (quá 240 s),
    `space` (cần bản probe).
- **Vùng RAM sau S1 (`0x60257000..0x602ae000`)** [S]: không có `mov imm32`/abs32 nào (mọi alias) trỏ vào, ngoài các
  word kết thúc chép lúc startup và chính end-word. Không có bảng pool/heap trong `.data` trỏ vào. Bộ nạp ban đầu
  (0x10e) không chứa độ dài S1 (hit `0x179000` là bảng ID). Đọc tĩnh không thấy ai dùng vùng này.
- **Bài học từ E-P7/OM-3** (FIRMWARE_GUIDE): lặp khởi động trước đây do code chạy *trước phát chụp đầu tiên* (aperture
  ring trên E-P7) hoặc hook gọi vào section chưa nạp (OM-3). Hook mới của c24 nằm ở S2/S6 và đều chạy sau boot; Color
  Creator S1→S6 giống c15. Không thấy trường hợp tương tự.

**Xếp hạng mới:** (1) base catalog + đuôi S1 + bộ c15 trên base catalog (c16+, chưa máy nào chạy) — cao nhất;
(2) hook halation — thấp; (3) watchdog, S6 — rất thấp.

**Chia đôi bằng bản đã có sẵn (không cần build mới):**

| Bước | Bản | Có gì so với stock catalog |
|---|---|---|
| T1 | v0.4c17 | bộ c15 + đuôi S1. Không S6, không halation, không watchdog |
| T2 | v0.4c18t | T1 + S6 + hook bộ chuyển cờ. Không watchdog, không combiner |
| T3 | v0.4c22t | đủ như c24 (watchdog, combiner, route) |

T1 lặp → lỗi ở base/đuôi S1/bộ c15 trên base catalog, cần bản T1b (stock + chỉ end-word S1) mới tách được.
T1 chạy, T2 lặp → hook bộ chuyển cờ hoặc S6. T2 chạy, T3 lặp → watchdog/combiner/route.

## Câu hỏi còn mở

1. Từ lúc bật tới lúc tắt mất bao lâu? Khoảng 1 s gợi ý nhánh "reboot soon" (WDT = 1). Khoảng 10 s hoặc 30 s gợi ý
   watchdog hết hạn. Tắt ngay sau khi màn hình lên gợi ý fault.
2. Máy của người thử có từng chạy v0.4c15 / v0.4c17 không, hay nạp thẳng c24 từ stock?
3. Còn ai giữ tệp `f0c25dd8…` (máy hertzel, bản sao cũ) để so toàn ảnh với base catalog không?
4. Người thử có đồng ý chạy 2–4 lần nạp chia đôi (T1..T3) không?

Status: DONE_WITH_CONCERNS
Summary: Emulator cho thấy trên đường boot c24 chỉ khác stock ở end-word S1 và S6 cùng watchdog 30 s, tất cả đúng ý đồ,
không chồng vùng và không có con trỏ thật vào vùng nạp thêm. Không chỉ ra được edit đơn lẻ; nghi vấn mạnh nhất là base
catalog cùng đuôi S1 (từ c16, chưa thử trên máy), rồi tới watchdog.
Concerns: emulator không chạy toàn bộ boot; cần chia đôi trên máy (T1..T3) hoặc tệp base cũ để chốt.
