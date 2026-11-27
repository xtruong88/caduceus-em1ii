---
phase: 6
title: "Vòng ±7"
status: pending
priority: P3
effort: "1 phiên + 1 bản thử"
dependencies: [4, 5]
---

# Phase 06: Mở rộng vòng từ ±5 lên ±7

## Overview
Bản E-M10 I dùng ±7 cho mỗi trục. Renderer stock của E-M1 II vẽ mã 0..10 (±5). Mở rộng lên ±7 (mã 0..14) bằng các edit
geometry giống E-P7 phase 1b (`docs/HSL_PORT.md` dòng ~197–204, `docs/LOOK_EDITOR.md` "Phase 1b").

## Requirements
- Builder `0x603103ea`: nhận −7..+7 (bảng nhảy `0x604fa9e8`, kiểm khoảng).
- Renderer `0x60cad39d`: polygon_step `0x60cad485` (`f90009` → bước nhỏ hơn), polygon_origin `0x60cad490`, ticks
  `0x60cad60e` / `0x60cad61c`, theo tỷ lệ E-P7 (9 → 6, 23 → 26, cùng tick step 9.0 → 6.0) [S, research §Phase 01].
- `cw_get`: kẹp ±7 thay vì ±5; H/L (±15) chia 2 (làm tròn) thay vì chia 3; S (±10) kẹp ±7.
- Không đổi định dạng look (S, H, L trong look giữ khoảng cũ).

## Related Code Files
- Modify: `patches/omdem1mk2/color_wheel/cw.s`, `build.py`
- Modify: `tools/omdem1mk2_emu_color_wheel_probe.py`, `tools/omdem1mk2_emu_color_wheel_feed.py`

## Implementation Steps
1. Xác nhận từng site geometry trên E-M1 II (byte + vai trò) bằng emulator renderer.
2. Edit builder + renderer; chạy probe với mã 0..14, kiểm bán kính vẫn trong canvas 256×256.
3. Đổi mapping trong `cw_get`; chạy feed harness.

## Success Criteria
- [ ] Emulator: −7 và +7 vẽ ở bán kính tối thiểu/tối đa trong canvas; 0 vẫn ở vòng giữa; tick đúng số lượng.
- [ ] Trên máy: vòng ±7 hiện đúng, không tràn khỏi nền.

## Risk Assessment
- Hệ số ×9 vẫn là suy luận [I] → phase 04 phải xác nhận trên máy trước khi đổi geometry.
- Bitmap nền 210 có vạch cố định cho ±5 → vạch có thể lệch với ±7; xem trên máy.
