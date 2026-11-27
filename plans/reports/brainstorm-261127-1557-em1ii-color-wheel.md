# Brainstorm: color wheel cho E-M1 II

Ngày: 2026-11-27 · Nhánh: docs/huong-dan-em1ii

## Vấn đề
Người dùng muốn màn hình Color Profile Control kiểu E-P7/PEN-F trên E-M1 II: vòng 12 màu + đa giác 12 đỉnh (S/H/L từng vùng), RESET, H/S/L.

## Hiện trạng (scout)
- Engine màu: đã có. Look Caduceus trên E-M1 II chạy engine COLOR 12 vùng S/H/L của E-P7 (`patches/omdem1mk2/color_creator_wheel/color_creator_wheel.s`, sd_loader).
- UI trên máy: chỉ Color Creator gốc (vòng Hue 617 / Vividness 618) + dòng chữ kind-5 (`cc_guide`) hiện tên look/số. Không có màn đa giác.
- OSD E-M1 II đã làm được: thay chữ (kind 5), thay icon trong bảng ảnh (ASPECT.md, v0.4c3–c7 mất nhiều bản thử). Chưa tìm thấy hàm vẽ đường/hình tròn.
- Webapp: 12 thanh trượt/tab, không có vòng (`webapp/src/main.ts` `sectorPanel`).

## Các cách đã xét
| | Cách | Ưu | Nhược |
|---|---|---|---|
| A | Vòng màu trên webapp | Rủi ro thấp, không đụng firmware | Không chỉnh trên máy |
| B | Trang Sector bằng chữ trong Color Creator | Dùng lại cơ chế trang/chữ đã chạy | Không có hình vòng |
| C | Vòng đồ họa thật trên máy | Giống E-P7 | Chưa biết khả thi; OSD E-M1 II tốn nhiều bản thử |

## Quyết định
Người dùng chọn C, giới hạn là **vòng nghiên cứu khả thi**, làm luôn (không lập plan riêng).

## Phạm vi nghiên cứu
1. E-P7: màn Color Profile Control vẽ vòng/đa giác bằng gì (primitive vẽ hay ảnh nền + đường), địa chỉ, cấu trúc.
2. E-M1 II 3.70: tìm hàm tương ứng (mẫu byte, chuỗi, bảng gọi).
3. Emulator: gọi hàm vẽ vào bộ đệm giả, xác nhận pixel đổi.
4. Dự phòng: ảnh vòng nạp vào bảng ảnh + 12 icon đỉnh; xét vẽ đường nối.

Ngoài phạm vi: build cho máy, sửa webapp, đổi định dạng look.

## Tiêu chí xong
Báo cáo `research-261127-*-em1ii-color-wheel-osd.md`: địa chỉ, bằng chứng emulator, kết luận khả thi/không, ước lượng công sức. Nói rõ phần nào emulator, phần nào chỉ đọc tĩnh.

## Câu hỏi mở
- Ảnh tham khảo chụp trên **E-M10 Mark I** (người dùng xác nhận). Máy này không có sẵn COLOR profile, nên nhiều khả năng đang chạy firmware mod. Nếu đúng, có thể đời firmware cũ cũng có dịch vụ vẽ C3d, nghĩa là E-M1 II cũng có khả năng có [I].
- Firmware gốc hay mod trên E-M10 I, và nguồn của bản mod? Nếu có nguồn thì đối chiếu được cách vẽ.
