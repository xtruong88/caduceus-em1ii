---
phase: 5
title: "Chỉnh từng vùng trên vòng"
status: pending
priority: P2
effort: "1-2 phiên + 1 bản thử"
dependencies: [4]
---

# Phase 05: Chỉnh vùng trên vòng (sau khi phase 04 xác nhận trên máy)

## Overview
Trên trang Wheel (theo cách bố trí phím của bản E-M10 I đã chạy trên máy): **dial trước** di con trỏ giữa các vùng,
**dial sau** đổi giá trị của trục đang chọn, **nút xuống** đổi trục (đã có từ phase 03), **nút lên** chọn/đánh dấu vùng
(có thể đánh dấu nhiều vùng để chỉnh cùng lúc), **giữ OK** reset. Giống ảnh tham khảo.
<!-- Updated: 2026-11-27 - key map from Meghnus/om10mi-mods; credit in NOTICE if adopted -->
Nếu dùng cách bố trí phím này, ghi công om10mi-mods (Meghnus) trong `NOTICE` là nguồn tham khảo thiết kế.
<!-- Updated: Validation Session 1 - axis by page, not TRASH -->

## Requirements
- Sửa trực tiếp `P_SAT/P_HUE/P_LIGHT` của look đang áp; ảnh chụp dùng giá trị mới ngay.
- Chỉ trong phiên bật máy: **không** ghi LOOKS.BIN, không thêm field; look memory giữ chỉ số look như hiện tại.
  (Lưu chỉnh sửa lâu dài = việc riêng, cần đề xuất format chung trước.)
- Khoảng: S −5..+5; H/L ±15, mỗi bước 1 (hình trên vòng = chia 3, làm tròn, như phase 02, nên có khi 3 bước mới
  thấy đổi; số trên dòng guide là giá trị thật).
- Guide: `Red S+2` (tên vùng, trục, giá trị).

## Related Code Files
- Modify: `color_creator_wheel.s` (handler mũi tên/dial ở các trang Wheel), `cw.s`
- Modify: harness Color Creator + probe

## Implementation Steps
1. Xác nhận ánh xạ con trỏ → sector (phase 01) và vẽ lại sau mỗi lần đổi (gửi lại kind 5).
2. Viết handler; giữ nguyên handler các trang khác.
3. Emulator: chuỗi phím → P đổi đúng → buffer kind 5 đổi đúng → request ảnh đọc giá trị mới.
4. Bản thử trên máy riêng (một nhóm tính năng).

## Success Criteria
- [ ] Emulator: mỗi phím đổi đúng một vùng/trục; giới hạn kẹp đúng.
- [ ] Trên máy: đa giác vẽ lại theo phím, ảnh chụp phản ánh thay đổi.

## Risk Assessment
- Redraw timing (gửi kind 5 mỗi phím) có thể giật/chậm → giới hạn tần suất nếu cần.
- Người dùng tưởng chỉnh được lưu → guide/tài liệu nói rõ "mất khi tắt máy".
