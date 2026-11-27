---
title: "E-M1 II: look gần với Fujifilm hơn (nhớ look, B&W thật, WB, tương phản/độ nét, grain)"
status: pending
created: 2026-11-23
branch: docs/huong-dan-em1ii
blockedBy: [261123-0838-em1ii-halation-step4]
---

# E-M1 II: look gần với Fujifilm hơn

Mục tiêu: chụp JPEG ra là đẹp, không cần hậu kì. Người dùng chọn look một lần, sau đó chỉ chỉnh sáng/tối.
Năm tính năng người dùng yêu cầu, xếp theo **giá trị / rủi ro** (khác thứ tự gốc), cộng một phase đề xuất format:

| Phase | Tính năng | Ưu tiên | Rủi ro | Phụ thuộc | Trạng thái |
|---|---|---|---|---|---|
| [00](phase-00-format-proposal.md) | Đề xuất mở rộng format chung (contrast, sharpness, mono filter, grain) | P1 | thấp (chỉ là đề xuất) | — | pending |
| [01](phase-01-remember-look.md) | Nhớ look sau khi tắt máy, áp ngay không cần mở trình chỉnh | P1 | thấp–vừa | baseline máy | emulator xong (v0.4c25t), chờ máy |
| [02](phase-02-look-white-balance.md) | WB shift theo look (A-B, G-M; field đã có trong pack) | P1 | vừa | 01 | emulator xong (v0.4c26t), chờ máy |
| [03](phase-03-true-mono.md) | B&W thật cho look đơn sắc (Acros, Tri-X) | P2 | vừa–cao | 00 (filter), 01 | pending |
| [04](phase-04-look-contrast-sharpness.md) | Tương phản và độ nét theo look | P2 | vừa | 00, 01; `sharp_scale` thử riêng trước | pending |
| [05](phase-05-grain.md) | Grain (hạt phim), có thể cắt | P3 | **cao** | 00; bản nền ổn định trên máy | pending |
| [06](phase-06-release-camera-ladder.md) | Bản thử từng tính năng, bản phát hành, tài liệu | P1 | — | từng phase | pending |

Phase 00 chỉ chặn phần **lên máy** của 03 (filter), 04 và 05. Nghiên cứu và emulator của chúng làm được trước.

## Điều kiện trước (gate)

- **Baseline trên máy:** người dùng làm bước 0 (nạp firmware gốc), nạp v0.4c24, đánh giá các look, và ghi lại một điều:
  tắt rồi bật máy thì mức Halo (sid 961) có được giữ không. Đây là phase step 4 của
  [halation](../261123-0838-em1ii-halation-step4/plan.md). Mọi phase đều nghiên cứu và chạy emulator được trước gate
  này. Chỉ bước đưa bản build lên máy là phải chờ.
- **Quy tắc repo (AGENTS.md, FIRMWARE_GUIDE §10):**
  - mọi thay đổi chạy trên emulator trước khi lên máy, patched vs stock;
  - **mỗi lần nạp chỉ thêm một nhóm tính năng**;
  - field mới của look phải đề xuất vào format chung trước (phase 00), kèm giá trị mặc định mà firmware cũ bỏ qua an
    toàn;
  - không ghi vào vùng image đã nạp; `.balign` mọi bảng dữ liệu.

## Sự thật đã kiểm (sau red-team)

- Record LOOKS.BIN 64 byte **đã dùng hết** (+0..47 field, +48..63 tên). Không có byte trống.
- Byte +24 là **noise reduction**, không phải grain. `film_grain` là field riêng của OM-3, chưa có trong record.
- Contrast ±2 và sharpness −5 (Off)..+2 là nghĩa đã có trong `advice` của pack; không đặt khoảng mới.
- WB (+25..27) đã nằm trong record và encoder chung đã xuất; firmware E-M1 II hiện bỏ qua.
- Sid 961 đã dành cho mức Halo; 965 (−7..+7) và 981 (0..3) không đủ khoảng cho phase 01.
- Ghi grain ở request +1828 cho job màu là không đủ (`GRAIN_PORT.md:30-38`).

## Quyết định thiết kế chung

- Look chỉ được áp khi picture mode là **Color Creator** (như hiện tại). Không mở rộng sang mode khác.
- Ưu tiên ghi **setting gốc qua facade**, hoặc đổi giá trị mà builder ảnh đọc. Hạn chế pass xử lý pixel mới.
- **Không dùng lại sid 961.**
- Khi Halo Off và không có look nào được chọn, máy phải chụp như firmware gốc (giống cam kết của v0.4c24).
- Mã trong khoảng trống 100 KB phải kết thúc trước trang Halo `0x612f0000`.

## Tiêu chí hoàn thành (toàn plan)

- Mỗi tính năng có harness emulator riêng, nằm trong bước seal của bản build tương ứng.
- Mỗi tính năng có một bản thử riêng trên máy, với tiêu chí đo được (R/B thẻ xám, R−G/B−G, histogram, high-pass), và
  người dùng xác nhận trên máy.
- Có bản phát hành gộp các tính năng đạt. Hướng dẫn HTML tiếng Việt và README được cập nhật.

## Nguồn

Hai báo cáo khảo sát và một vòng red-team trong phiên (2026-11-23):
- `p_layout.inc`, `color_creator_wheel.s:87-139/849-896`, `sd_loader.s:370-420`;
- `HALATION.md:118-139`, `MONO_COLOUR.md`, `WB_PATCH.md`, `SHARPENING_OFF.md`, `GRAIN_PORT.md`, `OM3_NOTES.md`;
- `make_looks_bin.py:7-11/89-95`, `format.ts:150-175`, `pack.ts`, `om3.ts`, `cameras.ts:20`, `targets/em1mk2.ts`.

## Câu hỏi còn mở

1. ~~Sid nào giữ được 1..64?~~ Sid 965 (emulator). Còn lại: flash có ghi khi tắt máy không (chỉ máy trả lời được).
2. Monotone (pipeline 5) có dùng được cho look đơn sắc không, hay phải ép key 12? Phase 03 sẽ quyết.
3. Upstream chọn phương án nào cho phần mở rộng format (LOOKS.BIN v4, file phụ, hay chỉ em1mk2)? Phase 00 sẽ hỏi.
4. Contrast trên E-M1 II lưu theo picture mode hay dùng chung? Phase 04 bước 2.
5. E-M1 II có đường texture grain như OM-3 v0.25 không? Phase 05 bước 1; không có thì cắt phase.
