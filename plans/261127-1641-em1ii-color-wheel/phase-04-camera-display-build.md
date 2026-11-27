---
phase: 4
title: "Bản thử trên máy: chỉ hiển thị"
status: in-progress
priority: P1
effort: "1 phiên + thời gian máy"
dependencies: [3]
---

# Phase 04: Bản thử trên máy (display-only)

## Overview
Đóng gói bản thử `v0.4c27t` (hoặc số kế tiếp lúc đó) **trên nền v0.4c26t**, chỉ thêm các trang Wheel. Người dùng
thử trên máy theo checklist.
<!-- Updated: Validation Session 1 - release base c26t -->

## Requirements
- Nền là c26t (người dùng chọn), kể cả khi c26t chưa được xác nhận trên máy. Ghi chú phát hành nói rõ bản này gồm
  look memory + look WB + vòng màu.
- Có patch halation (vùng 100 KB).
- `releases/em1mk2/<ver>/edits.json`, `build.json`, seal bằng `tools/omdem1mk2_catalog_release.py`.
- Ghi chú phát hành: phần nào emulator (producer, builder, renderer, value feed, trang), phần nào chưa (mailbox thật,
  surface, compositing, pixel).

## Checklist trên máy
0. Nếu chưa thử c26t: nạp c26t trước, ghi lại kết quả các mục của c26t (nhớ look, WB), để có mốc so sánh.
1. Mở Color Creator, INFO một lần từ Film tới Wheel: có đa giác không, ở đâu, có bị OSD che không.
2. Nhấn nút xuống: dòng guide đổi Wheel S → H → L → S, đa giác đổi theo trục.
3. Đổi look ở trang Film rồi quay lại Wheel: đa giác đổi theo look.
4. INFO tiếp tới Chroma, Luminance, Strength (Halo): vòng Color Creator gốc trở lại, các trang chạy như c26t.
5. Thoát bằng OK / MENU / nửa cò / tắt máy từ trang Wheel: không treo, không sót hình; mở lại Color Creator vẫn bình
   thường.
6. Chụp cùng look trên bản này và c26t: JPEG giống nhau.
7. **Xem trang Wheel trong kính ngắm (EVF)**, không chỉ màn LCD: vòng có nằm giữa không, có bị cắt không. (Bản E-M10 I
   bị lệch tâm trong EVF và phải sửa riêng.)
<!-- Updated: 2026-11-27 - single Wheel page; EVF centring check from Meghnus/om10mi-mods -->

## Related Code Files
- Create: `releases/em1mk2/<ver>/`
- Modify: `docs/OMD-EM1-II/` (trang thử máy mới, theo kiểu `thu-may-look-wb.md`), `patches/omdem1mk2/CHANGELOG.md`

## Success Criteria
- [ ] Seal PASS, mọi harness PASS.
- [ ] Người dùng xác nhận checklist 0–7 (hoặc ghi lỗi để sửa).

## Risk Assessment
- Surface không hiện hoặc bị che → fallback: đóng hẳn OSD Color Creator khi ở trang Wheel (phương án từ phase 01).
- Treo máy khi thoát → rút bản, chẩn đoán trong emulator trước, không làm bản chẩn đoán trên máy nếu tránh được.
- Nền c26t chưa thử trên máy → lỗi có thể do look memory/WB. Mục 0 của checklist để tách lỗi.
- Vòng lệch tâm trong EVF → ghi lại vị trí; sửa ở bản sau (vị trí surface), không chặn bản hiển thị trên LCD.
