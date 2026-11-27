---
phase: 5
title: "Grain (hạt phim)"
status: pending
priority: P3
effort: "2d research + 1w emulator + 1-2 camera builds"
dependencies: [0]
---

# Phase 05: Grain (hạt phim)

## Overview
Hạt phim theo `film_grain` của look (1 Low / 2 Med / 3 High; field của format chung, xem phase 00) cho JPEG ở Color
Creator. **Rủi ro cao nhất.** Chỉ làm khi có bản nền đã ổn định trên máy. Có thể cắt phase này (YAGNI) nếu người dùng
thấy không cần.

## Requirements
- Functional: grain theo `film_grain`; RAW, movie và các chế độ chụp đặc biệt giữ nguyên.
- Non-functional:
  - **không dùng byte +24**: đó là noise reduction (`pack.ts:7-15`);
  - chưa cho bật cùng Halo, và chưa cho dùng với RAW+JPEG, cho tới khi thử trên máy (OM-3 #12 Glow+grain, #18 RAW+JPEG
    bị đứng máy).

## Architecture
- **Đường đã bị bác:** chỉ ghi mức ở request +1828 cho job màu là không đủ. Có ba cổng riêng chặn grain trên job COLOR:
  key 11 nhận work list mặc định, và combiner 31/32 chỉ dùng cho key 12 (`docs/GRAIN_PORT.md:30-38`).
- **Hướng đi:** đường texture của OM-3 v0.25 (`OM3_NOTES.md:56-72`).
  - Nghiên cứu trước trên E-M1 II: firmware có đúng đường texture này không, và gọi ở đâu.
  - Hai lỗi treo máy đã biết của OM-3 phải được chặn sẵn trong thiết kế.
- **Bài học crash** (`FIRMWARE_GUIDE` §10): căn lề bảng; marker phải ghi trước khi dựng work list; buffer ảnh phải đi qua
  mapper, lock, flush; mọi lời gọi phải có ô return.

## Related Code Files
- Create:
  - `plans/reports/research-…-em1ii-grain-route.md`;
  - `patches/omdem1mk2/look_grain/`;
  - `tools/omdem1mk2_emu_look_grain.py`.

## Implementation Steps
1. **Nghiên cứu (cổng):** tìm đường texture tương ứng trên E-M1 II, rồi chạy thử trên emulator với một job màu. Không
   tìm ra thì dừng phase và báo lại.
2. Viết hook: đọc `film_grain` từ P lúc chuyển đổi, trước khi dựng work list. Chặn Halo + grain và RAW+JPEG.
3. Emulator: job có grain hợp lệ; các trường hợp bị chặn giống stock. Kiểm tĩnh căn lề, lệnh ghi, ô return.
4. Dựng bản thử riêng, nạp ngay sau một bản đã ổn định.

## Success Criteria
- [ ] Cổng nghiên cứu: có đường texture kèm bằng chứng, hoặc kết luận dừng.
- [ ] Máy:
  - độ lệch chuẩn high-pass của Y ở 100 % tăng rõ ở mức Med so với Off;
  - chụp 20 ảnh liên tiếp không treo;
  - RAW+JPEG không đổi.

## Risk Assessment
- **Rủi ro treo máy cao nhất:** chỉ nạp riêng một mình nó; có sẵn tệp khôi phục.
- **Không có đường texture trên E-M1 II:** dừng. Không làm pass CPU, trừ khi người dùng đồng ý riêng.
