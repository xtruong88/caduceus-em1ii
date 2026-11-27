---
phase: 1
title: "Nhớ look sau khi tắt máy"
status: in-progress
priority: P1
effort: "2-3d emulator + 1 camera build"
dependencies: []
---

# Phase 01: Nhớ look sau khi tắt máy

> **Kết quả (2026-11-23):** bước 1–4 xong trên emulator, bản thử `v0.4c25t` (v0.4c24 + nhớ look). Chờ thử trên máy
> ([thu-may-nho-look.md](../../docs/OMD-EM1-II/thu-may-nho-look.md)).
> - S = **sid 965** (0xF719[1]); Color Creator raw 0x9481 = **9**. Báo cáo:
>   [research-261123-2342-em1ii-look-slot.md](../reports/research-261123-2342-em1ii-look-slot.md).
> - Section 2 và Section 6 đã đầy, nên mã mới nằm trong khoảng trống 100 KB (`.hlui` 0x612f0000, `.lmem`
>   0x612f0800). Vì vậy tính năng cần bản halation (build `EM1_CC_HALO=1 EM1_LOOKMEM=1`). Bản mặc định không đổi byte.
> - Chỉ lưu khi chọn bằng phím mũi tên: look 0 tự động của `cc_init` không bị lưu, nên mở trình chỉnh trước lần nhấn
>   nửa cò đầu không làm mất look thẻ đã nhớ.
> - **Đổi so với thiết kế ban đầu:** look màu sau khi dựng lại ghi lại 618 với chính giá trị của nó, một lần, để live
>   view vẽ lại ngay. Trên máy ở v0.3b3, chỉ đổi P thì live view không đổi. Trường hợp mono, bỏ qua hoặc giá trị sai
>   không ghi gì.
> - Harness: `tools/omdem1mk2_emu_look_memory.py`.

## Overview
Look đã chọn được giữ qua lúc tắt máy, và được áp ngay khi bật máy ở Color Creator, không cần mở trình chỉnh.

## Requirements
- Functional:
  - lưu look đã chọn vào một setting còn giữ được qua lúc tắt máy;
  - khi bật máy, dựng lại trạng thái trong RAM để hook màu áp look đó;
  - giá trị 0 hoặc ngoài khoảng hợp lệ nghĩa là "chưa chọn": máy chạy như hiện tại (áp look khi mở trình chỉnh).
- Non-functional:
  - **khôi phục không gọi SetValue:** chỉ dựng lại P trong RAM;
  - không dùng sid 961;
  - không làm chậm lúc khởi động.

## Architecture
- **Hiện trạng:**
  - P là block heap trong RAM, mất khi tắt máy. Các field: `P_LOOK` @16, `P_INIT` @20, `P_ACTIVE` @30, `P_CCMODE` @32
    (`p_layout.inc`).
  - `cc_init` chỉ chạy khi mở trình chỉnh; khi đó nó lưu `P_CCMODE` = raw 0x9481 (`color_creator_wheel.s:104-110`).
  - Hook màu chỉ áp khi `P_ACTIVE`, `P_CCMODE != 0` và picture mode trùng (`sd_loader.s:370-420`).
  - Firmware gốc tự nhớ 617/618 và các sid tone qua lúc tắt máy (research-261120-1400, mục "Persistence"). Vì vậy không
    cần ghi lại chúng khi khôi phục.
- **Mã hoá giá trị lưu:** `v = 1 + look + 32 × (nguồn là thẻ)`, với look 0..31, nên v nằm trong 1..64. v = 0 nghĩa là
  "chưa chọn"; sau khi reset toàn bộ (hoặc có thể sau khi nạp lại firmware) sid đọc ra 0, và máy chạy như hiện tại.
- **Lưu:** khi chọn look (`color_creator_wheel.s:849`), ghi v vào **sid S** qua facade SetValue. Đây đúng là đường mà
  trang Halo đang dùng, chạy trong trình chỉnh (UI task).
- **Khôi phục:** ở lần nhấn nửa cò đầu tiên sau khi bật máy (hook của sd_loader, sau bước nạp thẻ):
  - đọc S bằng getter (đọc thôi, không ghi);
  - nếu v hợp lệ thì đặt `P_LOOK`, `P_INIT`, chạy `look_fill`, đặt `P_ACTIVE` và `P_CCMODE`;
  - `P_CCMODE` = **giá trị raw 0x9481 của Color Creator**. Phải lấy giá trị thật trong pipeline, không phải giá trị GUI 21
    (FIRMWARE_GUIDE §3 "Traps"); bước 1 sẽ lấy nó trên emulator.
  - Look từ thẻ mà pack chưa nạp thì chưa khôi phục; thử lại khi `P_INIT` đổi sang 2.
- **Chọn S:** sid có validator chấp nhận 1..64, không có chỗ đọc, và không nằm trong danh sách reset khi khởi động.
  - 965 (−7..+7) và 981 (0..3) **không đủ khoảng**.
  - Phải xem bước kiểm store lúc khởi động `0x602fc45d` xử lý giá trị ngoài khoảng thế nào.

## Related Code Files
- Modify:
  - `patches/omdem1mk2/color_creator_wheel/color_creator_wheel.s` (lưu);
  - `patches/omdem1mk2/sd_loader/sd_loader.s` (khôi phục, chỉ trong RAM);
  - `p_layout.inc` (cờ "đã khôi phục");
  - `tools/omdem1mk2_catalog_release.py`.
- Create:
  - `tools/omdem1mk2_emu_look_memory.py`;
  - `plans/reports/research-…-em1ii-look-slot.md`.

## Implementation Steps
1. Quét các sid ứng viên: validator, danh sách reset, kiểm store lúc khởi động. Chạy cả ba đường khởi động trên emulator
   với S = 64 và với một giá trị ngoài khoảng. Lấy giá trị raw 0x9481 của Color Creator.
2. Lưu khi chọn look. Emulator: GetValue(S) trả đúng v cho look có sẵn và look từ thẻ.
3. Khôi phục ở hook nửa cò. Emulator kiểm các trường hợp:
   - S = v: P được dựng lại, và không có lời gọi SetValue nào;
   - picture mode không phải Color Creator: hook màu không áp;
   - S = 0 hoặc ngoài khoảng: như stock;
   - look từ thẻ khi pack chưa nạp: hoãn lại.
4. Dựng bản thử riêng (v0.4c24 cộng tính năng này).

## Success Criteria
- [ ] Emulator: mọi trường hợp ở bước 3 đúng; image chạy stock không đổi.
- [ ] Máy: chọn Velvia, tắt rồi bật, nhấn nửa cò: live view và JPEG ra Velvia (bão hoà cao hơn rõ so với Provia khi chụp
  cùng cảnh) mà không mở trình chỉnh. Sau khi reset toàn bộ: máy chạy như v0.4c24.

## Risk Assessment
- **Không có sid đủ khoảng giá trị:** dùng hai sid (look; nguồn), hoặc bỏ phần nhớ nguồn. Dự phòng ghi file lên thẻ
  (`SLOTS.BIN`) có rủi ro riêng (ghi thẻ từ HLS task), nên cần một cổng riêng trước khi làm.
- **Flash không ghi khi tắt máy:** kết quả thử sid 961 ở bước thử halation trên máy sẽ trả lời luôn câu này.
