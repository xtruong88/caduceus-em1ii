---
phase: 3
title: "Trang Wheel trong Color Creator"
status: completed
priority: P1
effort: "1-2 phiên"
dependencies: [1, 2]
---

# Phase 03: Trang Wheel và kích hoạt vẽ

## Overview
Thêm **một trang Wheel** ngay sau Film trong vòng trang INFO/TRASH của `color_creator_wheel.s`.
Vào trang Wheel: `P_WAXIS = 0` (S), `P_WCUR = 255`, bật `P_WON`, rồi **stop type 0** (fwOpe slot +32 `0x60826201`, cmd 7)
→ **start type 4** (slot +28 `0x60826587`, cmd 10) → **draw** (slot +48, d0 = 5, cmd 11). **Nút xuống** trên trang Wheel:
`P_WAXIS` S → H → L → S và chỉ draw lại (slot +48). Rời trang Wheel hoặc thoát trình chỉnh: tắt `P_WON`, **stop type 4** (cmd 12) → **start type 0**
(cmd 5) → draw (cmd 6). d1 = giá trị GUI gốc dùng (1, hoặc 2 ở vài màn).
**Bắt buộc stop trước start:** mở kind 5 khi kind 1 còn mở làm treo task C3d [V phase 01].
<!-- Updated: phase 01 results - safe open/close sequence -->
<!-- Updated: 2026-11-27 - single Wheel page, DOWN cycles axis (supersedes three pages; idea from Meghnus/om10mi-mods) -->

## Requirements
- `N_PAGES` tăng 1. Thứ tự mới: Film(0) → Wheel(1) → Chroma(2) → Luminance(3) → Strength(4) (→ Halo 5).
  **Đánh số lại trang:** thay mọi số trang cứng bằng hằng `.equ` (PG_FILM, PG_WHEEL, PG_CHROMA…), gồm cả chỗ đọc
  `P_PAGE` ngoài `color_creator_wheel.s` (grep `P_PAGE` trong `patches/omdem1mk2/`).
- Chỉ **hiển thị**: trên trang Wheel, chỉ nút xuống có tác dụng (đổi trục). Lên, trái/phải và hai dial là no-op
  (để dành cho phase 05). Nếu dial sau dùng chung đường xử lý với nút xuống, chỉ phím mũi tên được đổi trục.
- Dòng chữ `cc_guide`: `Wheel S` / `Wheel H` / `Wheel L` (và tên look).
- Thoát trình chỉnh từ trang Wheel (OK, MENU, nửa cò, tắt máy) không được để surface kind 5 mở hay `P_WON=1`.
- Build flag riêng (ví dụ `EM1_CC_WHEEL=1`) để bản không có trang Wheel giữ nguyên byte.

## Related Code Files
- Modify: `patches/omdem1mk2/color_creator_wheel/color_creator_wheel.s`, `.../build.py`
- Modify: `tools/omdem1mk2_emu_color_creator.py` (thêm kịch bản trang Wheel), `tools/omdem1mk2_emu_color_wheel_probe.py`

## Implementation Steps
1. Thêm trang và chuỗi guide.
2. Gọi fwOpe khi đổi trang; xử lý mọi đường thoát (`cc_init` lần sau cũng reset `P_WON`).
3. Emulator: vòng trang INFO/TRASH (cả hai đều đi tới, như code hiện tại) Film → Wheel → Chroma …; nút xuống ×4 trên
   Wheel (S→H→L→S, chỉ draw); kiểm chuỗi message/state đúng như phase 01; kiểm build không cờ bằng byte với bản trước.
4. Chạy lại toàn bộ harness hiện có của Color Creator, look memory, look WB, halation; cập nhật harness nào đang dùng số
   trang cứng.

## Success Criteria
- [ ] Emulator: vào Wheel → kind 5 mở với 12 giá trị S của look; nút xuống đổi trục, chỉ draw lại; rời Wheel → kind 1
  mở lại; `P_WON` về 0.
- [ ] Các trang Chroma/Luminance/Strength/Halo hoạt động như trước ở số trang mới.
- [ ] Mọi harness cũ PASS; build không cờ giống bản trước byte-by-byte.

## Risk Assessment
- **Treo GUI** nếu một đường đổi trang/thoát nào đó start mà chưa stop. Harness phải chạy mọi đường (INFO, TRASH,
  OK, MENU, nửa cò, `cc_init` lần sau) và kiểm state word `0xa26da4f4` không bao giờ bị chặn.
- Chưa emulator được: bên trong `startVariousDraw`, phát GUI msg 12987, draw task và hiển thị → chỉ thấy trên máy.
- Đánh số lại trang có thể sót một chỗ đọc số trang cứng → grep toàn bộ, chạy lại mọi harness Color Creator.
- Đường thoát thiếu sót → surface kẹt trên màn hình. Giảm rủi ro: reset ở `cc_init` và ở hook thoát đã có.
- Code space: code trong vùng 100 KB sau phần nhớ look, assert trước `0x61300000` (xem phase 02). Phần hook trong cave
  Section 6 (`0x612e6900..0x612e7000`) chỉ thêm tối thiểu.

## Kết quả (2026-11-27)
- Cờ `EM1_CC_WHEEL=1`: Film 0 → Wheel 1 → Chroma 2 → Luminance 3 → Strength 4 → Halo 5. Nút xuống (`cw_down`) đổi
  S → H → L, chỉ draw; dial (P_DIAL = 1) và lên/trái/phải là no-op. Hook OK mới: record+40 `0x61259c68` → `cw_ok`.
- Code: cave Section 6 `0x612e6900..0x612e6f6c` (1644 B); `.cwui` `0x612f1900..0x612f1b30` (560 B). Build:
  `color_creator_wheel/edits_halo_lookmem_wheel.json`.
- Emulator `tools/omdem1mk2_emu_color_wheel_page.py <spec>` → `RESULT PASS` (chạy lại độc lập): stop luôn trước start,
  `P_WON` về 0 ở mọi lối thoát đã thử, các trang khác giống c26t ở số trang mới. Cờ tắt: `edits*.json` giống HEAD.
- Chưa: nửa cò / tắt máy (dựa vào stop của GUI + `cc_init`), dial loop thật (mô phỏng bằng P_DIAL = 1), chuỗi fwOpe →
  C3d đầy đủ, hiển thị. `halo_page` chưa chạy được trên bản có cờ (đã có `color_wheel_page` thay).
