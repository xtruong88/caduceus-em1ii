---
phase: 0
title: "Đề xuất mở rộng format chung (cổng cho phase 03–05)"
status: pending
priority: P1
effort: "1d draft + chờ upstream"
dependencies: []
---

# Phase 00: Đề xuất mở rộng format chung

## Overview
Đưa các giá trị mà look đã có trong pack chung lên máy: `advice.contrast`, `advice.sharpness`, `advice.mono_filter`,
`film_grain`. Hiện các giá trị này chỉ dùng để xem trước trên Control Panel. Theo AGENTS.md, việc này phải được đề xuất
và thống nhất trong format chung trước, không tự đặt ra format riêng cho E-M1 II.

## Requirements
- **Không đổi nghĩa field cũ.** Byte +24 là noise reduction, không phải grain (`pack.ts:7-15, 26`). Record 64 byte đã
  dùng hết: +0..47 là field, +48..63 là tên (`make_looks_bin.py:7-11`, `format.ts:150-175`).
- Giữ nguyên nghĩa đang có:
  - contrast ±2; sharpness −5 (Off)..+2 (`om3.ts:30, 91, 109-111, 141`);
  - `film_grain` 1 Low / 2 Med / 3 High, không có nghĩa là off (`pack.ts:110`);
  - `mono_filter` theo `MONO_FILTERS` (`pack.ts:43`).
- Firmware và panel cũ phải bỏ qua phần mở rộng một cách an toàn.

## Architecture: các phương án đưa vào đề xuất
1. **LOOKS.BIN v4:** giữ nguyên record 64 byte, thêm một khối mở rộng sau các record (ví dụ 8 byte cho mỗi look), có
   version và CRC riêng. Loader v3 của E-P7 và E-M1 phải từ chối hoặc bỏ qua v4. Cần thay đổi cả ba port.
2. **File phụ chung** (ví dụ `LOOKX.BIN`, cùng thứ tự với LOOKS.BIN): firmware cũ không đọc nên không ảnh hưởng. Panel
   xuất kèm cho mọi camera có hỗ trợ.
3. **Chỉ dành cho E-M1 II** (`targets/em1mk2.ts`): chỉ làm nếu upstream không muốn đưa vào format chung. Đây là phương
   án dự phòng cuối, phải nói rõ trong issue.

## Implementation Steps
1. Viết đề xuất (field, kích thước, giá trị mặc định, nghĩa trên E-P7 / OM-3 / E-M1 II, cách chọn version) và mở issue
   trên `emudojo/caduceus`.
2. Khi đã thống nhất: sửa encoder/decoder (`format.ts`, `make_looks_bin.py`, `tools/ep7_looks_bin.py`) và test round-trip;
   pack cũ phải cho ra đúng từng byte như trước.

## Success Criteria
- [ ] Issue có phương án được maintainer đồng ý, hoặc người dùng quyết định chọn phương án 3.
- [ ] Encoder mới đạt vitest và test Python; pack v3 cũ không đổi một byte nào.

## Risk Assessment
- **Upstream chậm hoặc từ chối:** phase 01 và 02 không phụ thuộc phase này nên vẫn làm được. Phase 03–05 dừng ở mức
  nghiên cứu và emulator.
