---
phase: 3
title: "B&W thật cho look đơn sắc"
status: pending
priority: P2
effort: "1d research + 3-5d emulator + 1 camera build"
dependencies: [0, 1]
---

# Phase 03: B&W thật cho look đơn sắc (Acros, Tri-X)

## Overview
Look đơn sắc cho ảnh JPEG đen trắng thật, thay vì chỉ hạ vividness xuống −4 như hiện tại. Filter màu (đỏ/vàng/xanh) cần
phase 00, vì record hiện chưa có field nào chứa nó.

## Requirements
- Functional:
  - look đơn sắc (class 1) ở Color Creator cho JPEG B&W thật;
  - filter mono lấy từ `advice.mono_filter` sau khi phase 00 xong; trước đó dùng không filter;
  - look màu và các picture mode khác giữ nguyên.
- Non-functional: có một cổng quyết định sau bước nghiên cứu. Chọn đường ít rủi ro nhất; không có đường an toàn thì dừng.

## Architecture
- Đã biết:
  - builder đọc 0x9481; nếu là 12 thì đọc 0xF731 (profile MONO) → request+24233 (ARCH:230);
  - test mono của stock `0x60342c32` trả 1 cho 5, 12, 104, 109;
  - +47 trong record là **tint của hiệu ứng** (`format.ts:54,156`), không phải toning mono.
- **Phương án A (rẻ hơn, nghiên cứu trước):** cho look đơn sắc dùng Monotone của stock (pipeline 5). Đây là job type mà
  stock vẫn tạo ra. Giá trị 5 vẫn cần xác nhận (`HALATION.md:118`).
- **Phương án B:** ép job sang key 12, theo cách của E-P7 (`MONO_COLOUR.md`). Rủi ro theo bài học số 8: đưa một tính năng
  stock vào job type mà stock không bao giờ tạo ra. Chỉ chọn B khi A không làm được.
- **Live view:** giữ vividness −4 (gần B&W). Trên E-P7, key 12 cũng không có đường truyền cho live view.

## Related Code Files
- Create:
  - `plans/reports/research-…-em1ii-mono-route.md`;
  - `patches/omdem1mk2/look_mono/`;
  - `tools/omdem1mk2_emu_look_mono.py`.
- Modify:
  - `color_creator_wheel.s` (nhánh mono của `apply_active_look`);
  - `webapp/src/targets/em1mk2.ts` (bản xem trước mono đang lệch với firmware: sat −5 so với vividness −4).

## Implementation Steps
1. **Nghiên cứu (cổng):** chạy capture entry thật với picture mode 5 và 12. Ghi lại key, builder và các field mono; xác
   nhận Monotone = 5. Đánh giá A trước rồi mới tới B.
2. Viết hook theo phương án đã chọn. Emulator:
   - job của look đơn sắc giống job Monotone thật;
   - look màu và các mode khác giống stock từng byte.
3. Sửa bản xem trước trên webapp cho khớp firmware; vitest đạt.
4. Dựng bản thử riêng.

## Success Criteria
- [ ] Cổng nghiên cứu: có báo cáo chọn A hoặc B, kèm bằng chứng từ emulator; hoặc kết luận "không khả thi".
- [ ] Máy: JPEG của Acros có độ lệch R−G và B−G trung bình xấp xỉ 0 (thật sự xám); Velvia vẫn có màu.

## Risk Assessment
- **EXIF và playback** có thể ghi sai picture mode: kiểm trên máy.
- **Phase 00 bị từ chối:** chỉ có B&W, không có filter.
