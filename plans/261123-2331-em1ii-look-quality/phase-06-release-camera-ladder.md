---
phase: 6
title: "Bản thử, bản phát hành và tài liệu"
status: pending
priority: P1
effort: "0.5d per build"
dependencies: [0, 1, 2, 3, 4, 5]
---

# Phase 06: Bản thử, bản phát hành và tài liệu

## Overview
Mỗi tính năng có một bản thử riêng trên nền bản ổn định gần nhất. Các tính năng đạt trên máy được gộp vào một bản phát
hành. Phase này chạy song song: mỗi phase 01–05 đạt emulator thì làm phần của nó ở đây.

## Requirements
- Mỗi bản thử chỉ thêm **một** tính năng so với bản nền đã chạy trên máy.
- Tên bản: tiếp nối `v0.4c25t`, `v0.4c26t`… Bản phát hành gộp không có hậu tố `t`.
- Mỗi bản seal qua `omdem1mk2_catalog_release.py`: chạy mọi bước kiểm của bản nền, cộng harness của tính năng mới.

## Implementation Steps
1. Thêm phiên bản vào `omdem1mk2_catalog_release.py`, theo đúng cách đã làm cho `HALO_BUILDS`.
2. Seal, dựng lại, `verify`. Kiểm `check_gap_refs` nếu bản dùng khoảng trống 100 KB, và mã phải kết thúc trước trang
   Halo `0x612f0000`.

Thứ tự thử trên máy (mỗi bản một nhóm, nền là bản trước đó đã đạt):
1. v0.4c24 (baseline, phase step 4 của halation).
2. Nhớ look (01) → WB theo look (02).
3. `sharp_scale` một mình (v0.4c19t hoặc dựng lại trên nền mới), **trước** độ nét/tương phản theo look (04).
4. B&W thật (03), độ nét/tương phản theo look (04), mỗi cái một bản.
5. Grain (05) cuối cùng, nạp riêng, có sẵn tệp khôi phục.
3. Viết hướng dẫn thử của bản đó vào `docs/OMD-EM1-II/thu-may-halation.md`, hoặc một file thử mới cùng kiểu:
   gồm tiêu chí đạt và cách quay về.
4. Sau khi máy xác nhận: cập nhật CHANGELOG, README (bảng trạng thái), hướng dẫn HTML tiếng Việt (mục 2 và 9),
   cameras.ts và target em1mk2 của webapp.

## Success Criteria
- [ ] Mỗi bản thử có `SHA256SUMS` và đóng gói lại khớp từng byte.
- [ ] Bản phát hành: mọi harness đạt, và tài liệu nói đúng tình trạng thử trên máy của từng tính năng.

## Risk Assessment
- **Nhiều tính năng cùng chạm `color_creator_wheel.s`:** làm tuần tự theo thứ tự phase, không làm song song, để không
  ghi đè lẫn nhau.
- **Cạn khoảng trống:** theo dõi dung lượng còn lại của khoảng 100 KB và đuôi các section trong `build.py` của từng patch.
