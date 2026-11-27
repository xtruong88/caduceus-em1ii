---
phase: 1
title: "Emulator: luồng fwOpe → draw task"
status: completed
priority: P1
effort: "1-2 phiên"
dependencies: []
---

# Phase 01: Emulator luồng kích hoạt và surface

## Overview
Research đã chạy riêng producer, builder, renderer. Phase này nối các bước giữa (mailbox) và trả lời các câu hỏi quyết
định có làm tiếp hay không.

## Requirements
- Chạy được: fwOpe slot +28 `0x60826587` (type 4) → `0x607db538` → `drawC3dAsync` `0x607dc8f4/0x607dc9a5` → GUI msg 12987
  → handler `0x60941de7` → vtable +1040 → producer → client `0x6031629a` → API task `0x60cae1bf` (cmd 10 open / cmd 11)
  → draw task `0x60cac29b` msg 5.
- Trả lời: (a) mở kind 5 khi kind 1 (Color Creator, state 2) đang mở thì sao (state `0xa26da4f4`, cmd 5 vs 10)? Cần
  đóng kind 1 trước không? (b) đóng kind 5 và mở lại kind 1 bằng lời gọi nào (type 0)? (c) byte con trỏ → sector qua
  bảng `0x604fa968`; (d) msg 5 có vẽ vòng hue không (nhãn `0x60cadf96` id 0xd3..0xde, bitmap); (e) 906 = 1..3 có mode gốc
  nào đọc không.

## Architecture
Mô phỏng mailbox bằng cách chạy từng task handler với message do harness dựng (không chạy RTOS). Ghi lại state
`0xa26da4f4` và các lệnh OpenVG/surface (alloc, open, close) theo thứ tự.

## Related Code Files
- Modify: `tools/omdem1mk2_emu_color_wheel_probe.py` (thêm các stage), `tools/emu_fixtures/em1_c3d_wheel_stubs.s`
- Đọc: `tools/omdem1mk2_emu_rules.py`, `tools/omdem1mk2_emu_color_creator.py`, `external/oly_fw_analysis/docs/tooling/ida`

## Implementation Steps
1. Dựng chuỗi Color Creator mở bình thường (type 0 → kind 1 → cmd 5/6 → msg 4), ghi state.
2. Từ state đó gọi type 4; ghi các nhánh state (mở được / bị từ chối / lỗi).
3. Thử thứ tự đóng kind 1 → mở kind 5 → đóng kind 5 → mở lại kind 1.
4. Giải mã bảng con trỏ `0x604fa968`; tìm nguồn vòng hue.
5. Kiểm lệnh UDF ×9 bằng ghi chú IDA nếu có.
6. Ghi kết quả vào báo cáo research (mục mới) với nhãn [V]/[S]/[I].

## Success Criteria
- [ ] Harness in thứ tự message + state cho cả hai kịch bản (mở chồng, đóng/mở xen kẽ), kết thúc `OK`.
- [ ] Có câu trả lời (hoặc ghi rõ "chỉ thử trên máy") cho (a)–(e).
- [ ] Quyết định gate: tiếp tục / dừng.

## Risk Assessment
- Một số bước phụ thuộc RTOS thật (timing, surface compositing) không mô phỏng được → ghi rõ, đẩy sang phase 04.
- Nếu kind 5 chỉ chạy khi không có surface nào mở: phương án là đóng ring Color Creator khi vào trang Wheel.
