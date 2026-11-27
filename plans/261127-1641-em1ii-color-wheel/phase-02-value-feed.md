---
phase: 2
title: "Value feed: giá trị look vào đa giác"
status: completed
priority: P1
effort: "1 phiên"
dependencies: [1]
---

# Phase 02: Đưa S/H/L của look vào producer

## Overview
Producer `0x6097a1b5` (kind 5) đọc setting 906, 12 sector và con trỏ qua getter `0x602da802`. Hook các lời gọi đó để trả
giá trị của look trong P thay vì setting ngủ.

## Requirements
- Chỉ khi P hợp lệ và trang Wheel đang hiện (cờ mới `P_WON`): 906 → 1; sector k → giá trị trục đang chọn
  (`P_SAT`/`P_HUE`/`P_LIGHT`, đã nhân strength như look đang áp; S cộng chroma offset); con trỏ → `P_WCUR`
  (1..12 = sector, 255 = không con trỏ; 0 và 13..15 là lỗi, builder bỏ byte 12 [V phase 01]). Phase 03–04: luôn 255.
<!-- Updated: phase 01 results - cursor encoding -->
- H/L ±15 → chia 3, làm tròn, kẹp −5..+5 cho builder. S kẹp −5..+5.
- Trục lấy từ `P_WAXIS` (0 = S, 1 = H, 2 = L), do trang Wheel đặt và nút xuống đổi (phase 03).
- Ngoài điều kiện trên: nhảy về getter gốc, registers/stack như lúc vào (giống `ed_poly`).

## Architecture
Thay các `call 0x602da802` trong vòng đọc của producer bằng `call cw_get`. Code nằm trong section riêng ở vùng 100 KB,
sau phần nhớ look (`LMEM_ADDR 0x612f0800` + kích thước của nó), trước `GAP_END 0x61300000`, có assert giới hạn như
`sd_loader/build.py:221`. Bản build phải có patch halation (nới vùng nạp tới `0x61300000`).
<!-- Updated: Validation Session 1 - code location --> P fields mới: `P_WON` (u8), `P_WAXIS` (u8 0=S,1=H,2=L), `P_WCUR` (u8) ở offset 84..86.

## Related Code Files
- Create: `patches/omdem1mk2/color_wheel/cw.s`, `patches/omdem1mk2/color_wheel/build.py` (hoặc thêm vào
  `color_creator_wheel/` nếu build chung đơn giản hơn — chọn khi xem `build.py` hiện tại)
- Modify: `patches/omdem1mk2/p_layout.inc` (thêm 3 field, cập nhật comment)
- Modify: `tools/omdem1mk2_emu_color_wheel_probe.py` (chạy patched vs stock)

## Implementation Steps
1. Liệt kê chính xác các site gọi getter trong producer kind 5 (906, 12 sector, cursor).
2. Viết `cw_get` (stack-only, không ghi image).
3. Emulator: stock → giá trị setting; patched + `P_WON=0` → y hệt stock; patched + `P_WON=1` → giá trị P.
4. Kiểm mọi kind khác của producer (kind 1 Color Creator...) không đổi.

## Success Criteria
- [ ] Patched với `P_WON=0` cho buffer giống hệt stock (byte-by-byte).
- [ ] Patched với `P_WON=1` cho 12 giá trị = trục chọn của look, đúng thứ tự sector UI.
- [ ] Kind 1 không đổi.

## Risk Assessment
- Thứ tự sector UI vs thứ tự 925..960 có thể khác → kiểm bằng vector không đối xứng trong emulator.
- Đụng chung `p_layout.inc` với plan look-quality → chỉ thêm field, không dời field cũ.

## Kết quả (2026-11-27)
- `patches/omdem1mk2/color_wheel/{cw.s,build.py,edits.json}`: `cw_get` 186 B tại `0x612f1800` (vùng 100 KB, sau look
  memory `0x612f0800` và look WB `0x612f1000`), 38 edit rel32 ở các site getter kind 5 của producer. Fragment opt-in,
  build với `EM1_LOOKMEM=1`; chưa nối vào release (phase 03/04).
- `p_layout.inc`: P_WON 84, P_WAXIS 85, P_WCUR 86.
- S = `P_SAT` (đã gồm strength + chroma, ±10) kẹp ±5 → ở strength cao, đa giác bị cắt ở ±5 (chỉ hiển thị).
- Emulator `tools/omdem1mk2_emu_color_wheel_feed.py` → `OK`: tắt = giống stock byte-by-byte; bật = đúng S/H/L + con
  trỏ; kind 1 không đổi. Harness color_creator, look_memory, look_wb, halation_flag, halo_page PASS.
- `halation_route` fail cả trên c26t chưa sửa (không do patch này); cần xem riêng.
