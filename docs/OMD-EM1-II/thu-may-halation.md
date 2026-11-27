# Thử trên máy: v0.4c24, hoặc từng bước v0.4c17 → v0.4c22t → v0.4c23t → v0.4c24 (E-M1 Mark II)

Đây là quy trình thử trên thân máy, cũng là bước cuối. Mọi bước trước đó đã chạy trên giả lập: kiểm tra từng bản, dựng
lại từ firmware gốc khớp từng byte, và đối chiếu tệp khôi phục với tệp gốc. Cách nạp (giữ **OK** khi bật máy, đọc đèn,
khôi phục) theo [huong-dan-firmware-em1-ii.html](../huong-dan-firmware-em1-ii.html), mục 3, 4 và 6.

## Cách khuyên dùng: nạp một lần v0.4c24

v0.4c24 chứa mọi thứ của các bước 1–3 bên dưới. Ngay sau khi nạp, Halo ở **Off**. Ở trạng thái này, ảnh chụp đi qua
đúng đường của firmware gốc: giả lập cho thấy job chụp giống bản gốc từng byte, chỉ khác ô trỏ tới bước làm mờ của Art
Filter Soft Focus, và ô đó chuyển thẳng sang hàm gốc. Phần mới chạy lúc khởi động chỉ có hai thứ:
- nạp thêm vùng 100 KB: đã thử trên máy với sp1. Trên tệp 3.7 hiện tại không lệnh nào khác dùng vùng này
  (`tools/omdem1mk2_check_gap_refs.py`);
- watchdog 30 s.

Vì vậy, chỉ cần nạp một lần là dùng được:

0. **Nên làm nếu chỉ có một máy:** trước tiên nạp `restore/E1259999.BIN`, tức firmware 3.7 chính hãng của OM, không có bản
   vá. Rủi ro gần như bằng một lần cập nhật chính hãng. Bước này chứng minh trên chính máy bạn rằng thẻ, quy trình nạp và
   đường quay về đều hoạt động, và rằng tệp 3.7 hiện tại (`691a8a8e…`) chạy tốt. Khởi động và chụp thử một ảnh rồi
   mới làm bước 1.
1. Nạp `out/em1mk2-thu-may/4-v0.4c24`.
2. Kiểm như bước 1: khởi động, chụp và xem ảnh 4:3, 65:24 / 21:9, AF, Color Creator `C1.n`.
3. **Kiểm đường xử lý mới:** cảnh ban ngày **không có điểm cháy sáng**, tripod, Vivid. Chụp một ảnh với Halo Off và một
   ảnh với Halo Low. Không có vùng sáng thì quầng gần như bằng 0, nên hai ảnh phải gần như giống nhau. Nếu màu hoặc độ
   tương phản khác rõ, đường xử lý Art đã đổi điểm ảnh. Khi đó để Halo Off và gửi hai ảnh để phân tích.
4. **Kiểm quầng:** cảnh đêm có đèn, Halo Med. Phải thấy quầng quanh điểm sáng, máy không tự khởi động lại, và ghi lại
   thời gian lưu ảnh.
5. Nếu bước 3 hoặc 4 có gì lạ: chuyển Halo về **Off**, không cần nạp lại. Máy chạy như v0.4c17.

Nếu máy **không khởi động** sau khi nạp: nạp `restore/E1259999.BIN` (xem quy tắc bên dưới). Sau đó, nếu muốn biết phần
nào gây lỗi, làm lần lượt các bước 1–4.

## Quy tắc chung

- **Đi theo từng bước khi cần tìm lỗi.** Ở các bước 1–4, mỗi lần nạp chỉ thêm một nhóm thay đổi. Bước sau chỉ làm khi
  bước trước đạt. Nếu một bước hỏng, dừng lại và quay về bước gần nhất đã đạt.
- Pin đầy, thẻ ở **khe 1**, trên thẻ chỉ có một tệp `DCOLYMP/E1259999.BIN`. Đối chiếu hash với `SHA256SUMS` của đúng bản.
- Luôn giữ `restore/E1259999.BIN` trên máy tính. Tệp này là firmware gốc 3.7 của OM, SHA-256 `691a8a8e…`.
- Nếu máy treo hoặc khởi động lại liên tục: tháo pin, lắp lại, giữ **OK** + bật máy với thẻ chứa tệp khôi phục. Cách
  này đã cứu được PEN E-P7 một lần. Trên E-M1 II chưa có ai thử.
- Các thư mục chép thẳng lên thẻ nằm trong `out/em1mk2-thu-may/` (xem cuối trang).

## Bước 1: v0.4c17 (nền, chưa có halation)

v0.4c13 và v0.4c15 đã chạy trên máy. v0.4c17 giữ nguyên các thay đổi đó, chỉ dựng trên tệp 3.7 hiện tại của OM và sửa
Color Creator. Đây là bản đầu tiên dựng trên tệp gốc mới này.

Đạt khi:
- máy khởi động, vào menu, chụp và xem lại được ảnh JPEG 4:3;
- 65:24 / 21:9 cho đúng cỡ ảnh, và chọn được điểm AF ở tỷ lệ mới;
- Color Creator: dòng trạng thái báo `C1.n` khi có pack trên thẻ, và đổi look thì màu đổi theo.

## Bước 2: v0.4c22t (chẩn đoán, không có quầng)

Bản này thêm 4 thay đổi:
- nạp thêm vùng nhớ 100 KB lúc khởi động. Vùng này đã thử trên máy với bản sp1, kết quả `S+`;
- watchdog 30 s;
- trang Halo trong Color Creator;
- ảnh màu thường được chuyển sang đường xử lý Soft Focus với bước trộn trung tính, **không có quầng**.

Mức halation cố định ở Med.

Đạt khi:
- máy khởi động và chụp bình thường như bước 1;
- **chụp cùng một cảnh trên tripod, cùng thông số** (Vivid hoặc Natural, JPEG, 4:3), một lần với v0.4c17 và một lần với
  bản này, thì hai ảnh **giống nhau**. Có thể so trên máy tính;
- Monotone, một Art Filter, chụp liên tiếp và RAW+JPEG vẫn chạy như bản gốc;
- trang Halo: nhấn INFO để sang trang 5, dùng trái/phải để đổi Off/Low/Med/High, tắt rồi bật máy, giá trị vẫn giữ.
  Ở bản thử này giá trị trang Halo **chưa** điều khiển mức.

Ghi lại thời gian lưu một ảnh: từ lúc bấm chụp đến lúc đèn thẻ tắt.

Nếu ảnh khác màu hoặc khác độ tương phản: bước phát triển ảnh Art (combiner 13) đã đổi điểm ảnh. Không làm tiếp bước 3.
Gửi hai ảnh để phân tích.

## Bước 3: v0.4c23t (có quầng, mức Med)

Bản này giống v0.4c22t, chỉ thêm phần vẽ quầng.

Đạt khi:
- cảnh đêm có điểm sáng (đèn đường, đèn xe), Vivid / Natural / Color Creator: quanh điểm sáng có quầng màu, mặc định đỏ;
- ảnh ban ngày không có vùng cháy sáng gần như không đổi;
- Monotone, Art Filter, Art Effect, chụp liên tiếp, High Res và HDR vẫn chạy như bản gốc;
- máy **không tự khởi động lại**. Ghi lại thời gian lưu một ảnh cảnh đêm (ước tính khoảng 4–8 s; giới hạn watchdog 30 s).

Địa chỉ bộ nhớ ảnh thật đã được xác định trên giả lập bằng chính mã của máy. Ảnh nằm trong vùng nhớ ảnh
`0x8dc64e00..0x9f5e7400`, thuộc dải mà mã vẽ quầng xử lý được, và mã vẽ quầng đã chạy đúng từng bit ở các địa chỉ đó. Nếu
vẫn không thấy quầng trong khi máy chạy bình thường, ghi lại cảnh chụp và thông số để phân tích.

## Bước 4: v0.4c24 (ứng viên phát hành)

Giống v0.4c23t, nhưng mức lấy từ trang Halo, mặc định **Off**.

Đạt khi:
- vừa nạp xong, ảnh giống v0.4c17 (Halo ở Off);
- Halo Low / Med / High cho quầng tăng dần; Off cho ảnh như bản gốc;
- mức được giữ sau khi tắt và bật máy.

## Ghi lại cho mỗi bước

Ghi tên bản, đèn khi nạp, khởi động có ổn không, ảnh mẫu kèm thông số, thời gian lưu, có tự khởi động lại không, và mọi
mã `C…`, `E…` trên dòng trạng thái của Color Creator.

## Thư mục chép lên thẻ

Dựng bằng `caduceus.py build`, rồi kiểm bằng `caduceus.py verify` (phải báo `All good.`):

| Thư mục | Bản | Chép lên thẻ |
|---|---|---|
| `out/em1mk2-thu-may/1-v0.4c17` | nền | `DCOLYMP/`, `EM1MOD/` |
| `out/em1mk2-thu-may/2-v0.4c22t` | chẩn đoán | `DCOLYMP/`, `EM1MOD/` |
| `out/em1mk2-thu-may/3-v0.4c23t` | quầng Med | `DCOLYMP/`, `EM1MOD/` |
| `out/em1mk2-thu-may/4-v0.4c24` | ứng viên | `DCOLYMP/`, `EM1MOD/` |
| `out/em1mk2-thu-may/5-v0.4c25t` | v0.4c24 + nhớ look, chỉ sau khi v0.4c24 đạt ([thu-may-nho-look.md](thu-may-nho-look.md)) | `DCOLYMP/`, `EM1MOD/` |
| `out/em1mk2-thu-may/6-v0.4c26t` | v0.4c25t + WB theo look, chỉ sau khi v0.4c25t đạt ([thu-may-look-wb.md](thu-may-look-wb.md)) | `DCOLYMP/`, `EM1MOD/` |

Trong mỗi thư mục đều có `restore/E1259999.BIN`. Tệp này giống nhau ở mọi thư mục và là firmware gốc. Không chép
`restore/` lên thẻ, trừ khi muốn quay về firmware gốc.

Lệnh kiểm tra lại một thư mục trước khi chép:

```powershell
python caduceus.py verify out/em1mk2-thu-may/2-v0.4c22t
```
