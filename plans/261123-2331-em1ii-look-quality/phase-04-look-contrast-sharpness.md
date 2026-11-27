---
phase: 4
title: "Tương phản và độ nét theo look"
status: pending
priority: P2
effort: "3-4d emulator + 2 camera builds"
dependencies: [0, 1]
---

# Phase 04: Tương phản và độ nét theo look

## Overview
Mỗi look mang mức tương phản và độ nét riêng, theo đúng nghĩa đã có của `advice.contrast` / `advice.sharpness` trong
pack chung. Các giá trị này lên máy qua phase 00.

## Requirements
- Functional:
  - **dùng đúng nghĩa đã có**: contrast ±2; sharpness −5 (Off)..+2 (`om3.ts:30, 91, 109-111, 141`). Không tự đặt khoảng
    −2..+2 mới;
  - chỉ áp khi đang ở Color Creator và có look;
  - không có giá trị thì như stock.
- Non-functional: **thử `sharp_scale` (v0.4c19t) trên máy một mình trước** (bài học số 1: mỗi lần nạp một nhóm).

## Architecture
- **Độ nét:**
  - helper `0x603e8bfa` đọc request +1795, và patch `sharp_scale` đã hook đúng chỗ này;
  - giá trị sharpness của look (đã quy về khoảng của máy) thay cho giá trị của người dùng trong stub `ss_index`;
  - −5 (Off) cho gain 0, như `SHARPENING_OFF.md` của E-P7.
- **Tương phản:**
  - E-M1 II chưa có vị trí nào được ghi lại. Cần tìm sid Contrast và field request tương ứng;
  - kiểm tra contrast có được lưu theo từng picture mode không. Nếu có, ghi vào bản của Color Creator, giống cách 618 là
    setting riêng của Color Creator, và không cần khôi phục khi rời chế độ;
  - nếu contrast là setting chung: đổi giá trị ở chỗ request đọc nó, không ghi sid. Hiện không có hook nào chạy khi rời
    Color Creator để khôi phục lại.

## Related Code Files
- Modify:
  - `patches/omdem1mk2/sharp_scale/ss.s`;
  - `color_creator_wheel.s`;
  - `webapp/src/cameras.ts` (`settings` cho em1mk2);
  - target `em1mk2.ts`.
- Create:
  - `patches/omdem1mk2/look_tone/`;
  - `tools/omdem1mk2_emu_look_contrast.py`.

## Implementation Steps
1. Bản thử `sharp_scale` riêng: v0.4c19t, hoặc dựng lại trên v0.4c24. Chờ máy xác nhận.
2. Lần ra sid/key Contrast và chỗ request đọc nó; xác định contrast được lưu theo picture mode hay dùng chung.
3. Độ nét theo look trong `ss.s`. Emulator: mở rộng `omdem1mk2_emu_sharp_scale.py`, chạy mọi giá trị và trường hợp không
   có look.
4. Tương phản theo look, đúng cách đã chọn ở bước 2. Emulator kiểm request.
5. Dựng bản thử riêng cho phần theo look (sau bước 1).

## Success Criteria
- [ ] Emulator: request có đúng giá trị theo look; không có look thì giống stock từng byte.
- [ ] Máy:
  - độ lệch chuẩn histogram độ sáng của contrast +2 lớn hơn contrast 0 trên cùng cảnh;
  - sharpness −5 không có viền (độ lệch chuẩn high-pass của Y thấp hơn rõ so với 0).

## Risk Assessment
- **Phase 00 bị từ chối:** chỉ còn chỉnh tay (Extras), không theo look.
- **Contrast dùng chung mà không có cách đổi ở chỗ đọc:** bỏ phần tương phản, chỉ giữ độ nét.
