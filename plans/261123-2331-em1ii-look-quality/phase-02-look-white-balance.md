---
phase: 2
title: "WB shift theo look"
status: in-progress
priority: P1
effort: "3-4d emulator + 1 camera build"
dependencies: [1]
---

# Phase 02: WB shift theo look

## Overview
Mỗi look mang độ lệch cân bằng trắng riêng (A-B, G-M, ±7), như các mô phỏng phim của Fujifilm. Look ghi gì thì áp
nấy khi đang ở Color Creator. WB của người dùng không bị đổi. Không cần phase 00: field đã có trong format chung.

## Requirements
- Functional:
  - dùng các byte đã có trong record: cờ WB +25, a_b +26, g_m +27 (`make_looks_bin.py:91-95`);
  - encoder chung **đã xuất** ba byte này (`format.ts:152`, `targets/em1mk2.ts:17-20`), nên webapp không phải sửa
    encoder;
  - áp lệch WB của look khi picture mode là Color Creator, `P_ACTIVE = 1` và cờ +25 bật;
  - ngoài các trường hợp trên thì WB như stock.
- Non-functional: không ghi đè sid WB toàn cục của người dùng; ra khỏi Color Creator là WB quay về như cũ.

## Architecture
- E-P7 (`docs/WB_PATCH.md`): 16 chỗ gọi getter WB `0x6005e971` được trỏ sang stub `wb_get`; stub trả fine-tune của
  slot (A-B ở capture+24098, G-M ở +24100).
- E-M1 II: chưa biết sid/key WB và các chỗ gọi. Dùng `tools/omdem1mk2_ep7_match.py` (tìm theo chữ ký có mask) để tìm
  các chỗ tương ứng với 16 chỗ của E-P7. Getter thuộc tính là `0x6005e6cf`.
- Stub `wb_get` của E-M1:
  - nếu đủ điều kiện (Color Creator, `P_ACTIVE`, cờ +25) thì trả giá trị của look;
  - nếu không, nhảy về getter stock.
  - Đặt trong khoảng trống 100 KB (`0x612e7000..0x61300000`), **trước trang Halo `0x612f0000`**, hoặc phần đuôi
    section 3.
- **Live view:** trên E-P7, live view không hiện lệch WB, chỉ JPEG có (`WB_PATCH.md:136,166`). E-M1 II nhiều khả năng
  giống vậy. Ghi rõ trong hướng dẫn thử để người dùng không tưởng là lỗi.
- **Look cũ đã có wb_shift:** khi tính năng lên máy, các look này sẽ đổi màu JPEG so với trước. Phải ghi trong release
  notes, và bỏ mục WB khỏi danh sách `em1Dropped` của target em1mk2 (hiện panel báo WB bị bỏ qua trên E-M1 II).

## Related Code Files
- Create:
  - `patches/omdem1mk2/look_wb/` (`wb.s`, `build.py`);
  - `tools/omdem1mk2_emu_look_wb.py`.
- Modify:
  - `webapp/src/targets/em1mk2.ts` (`em1Dropped`, `toEm1`, chú thích; encoder giữ nguyên) và test của nó;
  - `docs/OMD-EM1-II/ARCHITECTURE_AND_MEMORY_MAP.md` (các chỗ gọi WB);
  - `tools/omdem1mk2_catalog_release.py`.

## Implementation Steps
1. Tìm getter WB và các chỗ gọi trên E-M1 bằng `ep7_match`. Chạy getter trên emulator với key thật. Ghi lại các chỗ đó
   trong ARCHITECTURE_AND_MEMORY_MAP.
   - **2026-11-27 (tĩnh, chưa emulator):** quét byte tìm được 16 chỗ gọi `0x6005e6cf` với key A-B/G-M, ghi ở
     ARCHITECTURE_AND_MEMORY_MAP §7.8: 12 chỗ ở khối chụp `0x6033a209..0x6033a58a` (6 cặp, E-P7 có 5), cặp compact
     slot `0x60343734/47`, cặp RAW `0x60cc3803/17` (để stock). Không thấy cặp params builder thứ hai của E-P7.
   - objdump (cùng ngày): cả 14 chỗ không phải RAW đều có `a0 = 0` và d1 đặt ngay trước lệnh gọi, đúng hợp đồng stub
     của E-P7. Khối chụp ghi A/G vào `capture+24248/24250`, rẽ nhánh theo `capture+24158` (6 nhánh, E-P7 có 5).
   - **CWB = category 3** (key 33057, sid 9), giống E-P7. Nhánh 3 lấy Kelvin từ key `0x8F22`; validator gốc chạy trên
     emulator cho sid 107 đúng 56 giá trị 2000..14000 K. Khác E-P7: E-M1 II vẫn đọc fine-tune trong CWB (cặp thừa).
     Stub giữ quy tắc của E-P7: category 3 thì để stock.
   - Môi trường: WSL `Ubuntu-24.04` (user root). Binutils mn10300 build từ `toolchains/mn103-gnu-src`, cài vào
     `/home/hertzel/ep7fw-toolchains/mn10300` (đường dẫn các harness đang dùng). Chạy harness bằng
     `wsl -d Ubuntu-24.04 -u root --cd /mnt/d/em1_ii/caduceus -- python3 tools/<harness>.py ...`.
     Đã kiểm: `emu_look_memory` trên v0.4c25t cho `RESULT PASS`.
2. Viết stub. Emulator: với mọi chỗ gọi, mọi tổ hợp (mode, `P_ACTIVE`, cờ) thì giá trị trả về đúng thiết kế, các
   thanh ghi được giữ.
   - **Xong trên emulator (2026-11-27):** `patches/omdem1mk2/look_wb/wb.s` + `build.py`, 222 B tại `0x612f1000`
     (sau `.lmem`, không phải trước trang Halo như dự tính ban đầu, vì khoảng trống sau `.lmem` còn trống). Đọc
     record của look qua `P_INIT` / `P_LOOK`, nên không cần thêm field vào P. Build: `EM1_LOOKMEM=1 python3
     patches/omdem1mk2/look_wb/build.py` (cần bản halation trong spec). Harness `tools/omdem1mk2_emu_look_wb.py`:
     PASS 27 trạng thái × 14 chỗ gọi; bản đột biến bỏ điều kiện CWB bị bắt. `omdem1mk2_audit_opcodes.py` đã kiểm
     khối này; `check_loaded` đạt trên spec gộp v0.4c25t + look_wb.
3. Chạy thử đường tạo request màu (`tools/omdem1mk2_emu_work_list.py`): với look có WB, các field WB trong request thay
   đổi; không có look thì request giống stock từng byte.
   - **Xong phần khối chụp (2026-11-27):** harness look WB chạy native segment `0x6033a1d2 → 0x6033a5ab` (19 lượt
     category/preset). Không look: giống stock từng byte. Có look +5/−4: giống hệt stock khi fine-tune lưu là +5/−4.
     CWB: stock. Review độc lập: không lỗi nghiêm trọng; đã thêm kiểm `mov 0,a0` vào build.py, sửa số stack (+28 B).
     Còn lại: bracketing và bộ tính gain sau segment, live view.
4. Target em1mk2: bỏ `'WB shift'` khỏi `em1Dropped` (`em1mk2.ts:26`), giữ `wb` trong `toEm1` cho look màu
   (`em1mk2.ts:42`, hiện đặt `wb: null`), sửa chú thích đầu file; vitest đạt.
   - Hoãn tới khi WB được xác nhận trên máy: panel đang mô tả firmware đã phát hành.
5. Dựng bản thử riêng.
   - **v0.4c26t seal xong (2026-11-27):** 23 bước kiểm, `E1259999.BIN` `26135ee0…`; gồm cả sửa thứ tự `P_ACTIVE`
     trong wheel. Hướng dẫn thử: `docs/OMD-EM1-II/thu-may-look-wb.md`. Chờ v0.4c25t đạt trên máy rồi mới nạp.

## Success Criteria
- [ ] Emulator: các chỗ gọi đều được chuyển hướng; ngoài Color Creator thì stock.
- [ ] Máy: chụp thẻ xám cùng ánh sáng:
  - look có A-B +3 cho tỉ lệ R/B trung bình cao hơn rõ so với cùng look A-B 0;
  - đổi sang Natural thì R/B như stock;
  - EXIF vẫn ghi WB của người dùng.

## Risk Assessment
- **WB được áp ở bước chụp chứ không ở request ảnh:** khi đó stub phải nằm ở chỗ đọc của bước chụp. Bước 3 sẽ phát hiện.
- **WB ảnh hưởng tới AWB hoặc live view theo cách khác E-P7:** cần kiểm trên máy.
