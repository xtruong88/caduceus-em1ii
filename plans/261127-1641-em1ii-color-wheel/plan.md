---
title: "E-M1 II: vòng màu đồ họa 12 vùng (kiểu Color Profile Control E-P7) trong Color Creator"
status: pending
created: 2026-11-27
branch: docs/huong-dan-em1ii
blockedBy: []
blocks: []
---

# E-M1 II: vòng màu đồ họa 12 vùng

Mục tiêu: trong trình chỉnh Color Creator, thêm trang **Wheel** hiện đa giác 12 vùng của look (giống ảnh tham khảo chụp
trên E-M10 I). Bước sau: chỉnh từng vùng ngay trên vòng.

Nguồn: [brainstorm](../reports/brainstorm-261127-1557-em1ii-color-wheel.md) ·
[research](../reports/research-261127-1557-em1ii-color-wheel-osd.md) (kết luận FEASIBLE: code vẽ có sẵn, là dead code).

| Phase | Nội dung | Ưu tiên | Rủi ro | Phụ thuộc | Trạng thái |
|---|---|---|---|---|---|
| [01](phase-01-emulate-draw-flow.md) | Emulator: luồng fwOpe → draw task, trạng thái mở/đóng surface, con trỏ | P1 | vừa | — | completed (gate: CONTINUE) |
| [02](phase-02-value-feed.md) | Hook getter của producer: đưa S/H/L của look (P) vào đa giác | P1 | thấp–vừa | 01 | completed (emulator) |
| [03](phase-03-wheel-page-trigger.md) | Một trang Wheel ngay sau Film, nút xuống đổi trục S/H/L: bật/tắt vẽ kind 5 | P1 | vừa | 01, 02 | completed (emulator) |
| [04](phase-04-camera-display-build.md) | Bản thử trên máy (chỉ hiển thị) + ghi chú phát hành | P1 | vừa | 03 | v0.4c27t sealed, chờ thử trên máy |
| [05](phase-05-sector-edit.md) | Chỉnh từng vùng trên vòng (con trỏ, trục S/H/L) | P2 | vừa | 04 xác nhận trên máy | pending |
| [06](phase-06-range-seven.md) | Mở rộng vòng từ ±5 lên ±7 (geometry như E-P7 phase 1b) | P3 | vừa | 04, 05 | pending |

**Gate sau phase 01:** nếu emulator cho thấy surface kind 5 không thể mở khi Color Creator (kind 1) đang mở, và không có
cách đóng/mở xen kẽ an toàn → dừng, báo lại người dùng trước khi làm 02–03.

**Kết quả gate (2026-11-27): CONTINUE** ([research §Phase 01](../reports/research-261127-1557-em1ii-color-wheel-osd.md)).
Mở kind 5 khi kind 1 (Color Creator) đang mở làm **treo task C3d** [V]. Thứ tự an toàn [V]: vào Wheel = stop type 0
(fwOpe slot +32, cmd 7) → start type 4 (slot +28, cmd 10) → draw (slot +48, d0 = 5, cmd 11); ra = stop type 4 (cmd 12)
→ start type 0 (cmd 5) → draw (cmd 6). Giống stock GUI (`0x60f09d40` / `0x60f09e18`).

## Quyết định thiết kế

- Không vẽ code mới: dùng nguyên producer `0x6097a1b5` → builder `0x603103ea` → cmd 11 → renderer `0x60cad39d`.
- Kích hoạt bằng cách gọi API fwOpe slot +28 (`0x60826587`, type 4) từ code trang Caduceus; **không** sửa bảng
  `0x612c373c` (không còn chỗ, count là immediate).
- Giá trị: hook các lời gọi getter `0x602da802` trong producer (cách của E-P7 test13 `ed_poly`); **không ghi** vào các
  setting ngủ 906/925..960 (tránh thay đổi trạng thái lưu của máy).
- Ngoài trang Wheel, máy phải chạy như bản nền c26t (vòng Color Creator gốc ở Film và các trang còn lại).
- Không đổi định dạng look, share code hay webapp. Không thêm field LOOKS.BIN.
- State mới trong P dùng vùng trống 84..95 (`p_layout.inc`).
- Code mới đặt ở **vùng 100 KB** (`0x612e7000..0x61300000`, chỉ được máy nạp khi có patch halation, vì patch này nới
  vùng nạp), trong một section riêng sau phần nhớ look (`0x612f0800`) và trước `0x61300000`, có assert giới hạn.
  Bản build có vòng màu **bắt buộc** đi kèm patch halation.
- **Một trang Wheel**, đặt **ngay sau Film** (Film → Wheel → Chroma → Luminance → Strength → Halo). Trên trang Wheel,
  **nút xuống đổi trục S → H → L** (như bản E-M10 I đã chạy trên máy). Lên, trái/phải và hai dial để dành cho phase 05.
  Các trang cũ bị đánh số lại. Chuyển trang vẫn bằng INFO/TRASH.
<!-- Updated: 2026-11-27 - single Wheel page after reviewing Meghnus/om10mi-mods (supersedes 3 pages) -->
- H/L (±15) hiển thị bằng cách chia 3 và làm tròn rồi kẹp về ±5 (giữ hình dạng). S kẹp ±5.
<!-- Updated: Validation Session 1 - code location, wheel pages, H/L display mapping -->

## Phối hợp với plan khác

[261123-2331-em1ii-look-quality](../261123-2331-em1ii-look-quality/plan.md) cũng sửa
`color_creator_wheel.s` và `p_layout.inc`, và đang chờ thử trên máy (v0.4c25t, v0.4c26t). Không chặn nhau ở mức
emulator. **Bản lên máy của plan này build trên nền v0.4c26t** (người dùng chọn), kể cả khi c26t chưa được xác nhận
trên máy. Hệ quả: nếu bản thử có lỗi, trước hết phải so với c26t trên cùng máy để biết lỗi do vòng màu hay do look
memory/WB. Việc đánh số lại trang đụng code `P_PAGE` mà c25t/c26t dùng, nên mọi harness của c25t/c26t phải chạy lại.
<!-- Updated: Validation Session 1 - release base c26t -->

## Tiêu chí hoàn thành

- Harness emulator chạy bản patched vs stock trên toàn bộ luồng đã mô phỏng được, nằm trong bước seal bản build.
- Trên máy: trang Wheel hiện đa giác theo trục của look, nút xuống đổi trục; rời trang Wheel thì vòng Color Creator gốc
  trở lại; vòng nằm đúng chỗ trên cả LCD và EVF; ảnh chụp không đổi so với cùng look trên c26t.
- Ghi chú phát hành nói rõ phần nào đã emulator, phần nào chưa.

## Validation Log

### Session 1 (2026-11-27)

Câu hỏi: 4. Quyết định:
1. Chỗ đặt code: vùng 100 KB, sau phần nhớ look, phải có patch halation (khuyến nghị, đã chọn).
2. Đổi trục: 3 trang Wheel S/H/L, không thêm phím (khuyến nghị, đã chọn).
3. Vị trí trang: **ngay sau Film** (khác khuyến nghị "cuối vòng"). Chấp nhận việc đánh số lại trang và đụng nhiều code
   cùng harness hơn.
4. Bản nền: **luôn build trên c26t** (khác khuyến nghị "bản ổn định mới nhất"). Chấp nhận rủi ro khó tách lỗi.
Mặc định không hỏi: hiển thị H/L = chia 3, làm tròn, kẹp ±5.

### Verification Results
- Claims checked: 14
- Verified: 12 | Failed: 2 | Unverified: 0
- Tier: Full (5 phase; rút gọn, chỉ kiểm các claim về file, ký hiệu, layout)
- Failures:
  - Phase 02 ghi "vùng trống Section 6 / 100 KB, kết thúc trước `0x612f0000`". Thực tế đuôi Section 6
    `0x612e6900..0x612e7000` (~1,8 KB) là cave Color Creator; vùng 100 KB chỉ được nạp khi có halation
    (`patches/omdem1mk2/halation/build.py:8`); `0x612f0000` là trang Halo, `0x612f0800` là phần nhớ look
    (`color_creator_wheel/build.py:55`, `sd_loader/build.py:39`). → sửa theo quyết định 1.
  - Phase 05 dùng TRASH để đổi trục, nhưng TRASH (`0x9016`) đang dùng để chuyển trang
    (`color_creator_wheel.s:204-217`). → sửa theo quyết định 2.
- Verified (mẫu): các tool `omdem1mk2_emu_rules.py`, `_color_creator.py`, `_catalog_release.py`, `_look_memory.py`,
  `_look_wb.py`; `docs/OMD-EM1-II/thu-may-look-wb.md`; `patches/omdem1mk2/CHANGELOG.md`;
  `external/oly_fw_analysis/docs/tooling/ida`; P 84..95 trống (P_LMEM=83, P_LGON=96); `N_PAGES = 4 + HALO`; `cc_init`
  và `cc_guide` có trong `color_creator_wheel.s`; probe `omdem1mk2_emu_color_wheel_probe.py` chạy ra `OK`.

### Whole-Plan Consistency Sweep
- Đã đọc lại plan.md + 5 phase; grep các cụm cũ (`0x612f0000` làm giới hạn code, "TRASH đổi trục", "c25t/c26t có kết
  quả", "ổn định gần nhất", "trang Wheel" số ít, checklist 1–5).
- Đã sửa: plan.md (quyết định, phối hợp, tiêu chí), phase 02 (chỗ đặt code, mapping H/L, trục theo trang), phase 03
  (3 trang sau Film, đánh số lại, rủi ro, code space), phase 04 (nền c26t, checklist 0–6, rủi ro tách lỗi), phase 05
  (trục theo trang, bước H/L).
- `0x612f0000` chỉ còn trong Verification Results (mô tả lỗi cũ). Mâu thuẫn còn lại: 0.

### Session 2 (2026-11-27): tham khảo bản E-M10 I

Nguồn: [Meghnus/om10mi-mods](https://github.com/Meghnus/om10mi-mods) (firmware E-M10 I 1.4, vòng màu đã chạy trên máy từ
bản 87). Dữ liệu patch là byte thô của máy khác, giấy phép CC BY-NC-SA → **chỉ học thiết kế, không chép dữ liệu/code**.
Quyết định của người dùng:
1. **Một trang Wheel, nút xuống đổi trục** (thay quyết định 2 của Session 1). Phase 03 làm lại; bản 3 trang đã chạy
   emulator nhưng bị thay.
2. Thêm **rủi ro lệch tâm EVF** vào checklist phase 04 (bản E-M10 I phải sửa riêng vì vòng lệch trong kính ngắm).
3. Thêm **phase 06: khoảng ±7**.
Không chọn: ghi công trong NOTICE (chưa dùng gì ngoài ý tưởng chung; xem lại nếu phase 05 lấy cách bố trí phím của họ).
Bài học khác ghi nhận: chữ gợi ý vẽ trên layer 0 bị xám/trong suốt, phải dùng layer 1 (chỉ liên quan nếu thêm HUD).

## Câu hỏi mở

- Vòng hue là bitmap 210 (256×256, atlas 0 tại (256,0)), msg 5 tự vẽ [S/V]. Chưa kiểm atlas có hình thật ở đó không;
  nếu trống thì chỉ thiếu nền vòng, đa giác/icon/vạch vẫn vẽ. → xem trên máy (phase 04).
- 3 profile (906, 925..960) là dormant: không code gốc nào ghi, chỉ đường vòng màu đọc [S; chưa quét truy cập qua bảng id].
- Hệ số bán kính ×9 vẫn là suy luận [I] (khớp với edit range PEN-F/E-P7).
- `0x602f9583` (client send) có chờ trả lời không: chưa rõ.
- Thoát bằng nửa cò / tắt máy từ trang Wheel không có hook riêng; dựa vào stop của GUI + reset ở `cc_init` → kiểm trên máy.
