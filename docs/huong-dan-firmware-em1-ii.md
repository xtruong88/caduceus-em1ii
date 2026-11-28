# Hướng dẫn Caduceus cho E-M1 Mark II

Olympus OM-D E-M1 Mark II · nền firmware chính hãng 3.7 (build 3700) · bản cần thử: **v0.4c17** · **đừng nạp v0.4c24, v0.4c25t, v0.4c26t, v0.4c27t** (làm máy lặp khởi động).
Trang này dành cho người mới: Caduceus là gì, cách sao lưu, cách nạp, cách dùng từng tính năng trên máy và cách quay về
firmware gốc.

Bản này có cùng nội dung với [bản HTML](huong-dan-firmware-em1-ii.html) (mở bằng trình duyệt để xem có định dạng).

**Mục lục:** [1. Giới thiệu](#gioi-thieu) · [2. Tính năng](#tinh-nang) · [3. Chuẩn bị](#chuan-bi) ·
[4. Sao lưu](#sao-luu) · [5. Tạo gói](#tao-goi) · [6. Chép lên thẻ](#chep-the) · [7. Nạp](#nap) ·
[8. Kiểm tra](#kiem-tra) · [9. Cách dùng](#su-dung) · [10. Khôi phục](#khoi-phuc) · [11. Xử lý lỗi](#loi) ·
[12. Các bản](#cac-ban)

<a id="gioi-thieu"></a>

## 1. Caduceus là gì

Caduceus là bộ **bản vá firmware mã nguồn mở**, làm ban đầu cho PEN E-P7. Repo này đưa nó sang **E-M1 Mark II chạy
firmware 3.7**. Repo không chứa firmware của OM: công cụ `caduceus.py` tải tệp 3.7 chính hãng từ máy chủ OM, kiểm tra
SHA-256, áp các bản vá đã ghi trong repo, rồi tạo hai tệp:

- **tệp cài** `DCOLYMP/E1259999.BIN`: firmware 3.7 đã vá;
- **tệp khôi phục** `restore/E1259999.BIN`: đúng tệp 3.7 gốc của OM, dùng để quay về.

Máy nạp tệp như một bản cập nhật bình thường, qua thẻ SD, bằng cách giữ <kbd>OK</kbd> khi bật máy.

> [!WARNING]
> **Rủi ro.** Nạp firmware sửa đổi có thể làm máy treo, mất dữ liệu hoặc không khởi động được. Bạn tự chịu trách nhiệm.
> Chỉ dùng cho **E-M1 Mark II nền 3.7**. Không nạp bản của E-P7, OM-3 hay máy khác.

> [!CAUTION]
> **Đừng nạp v0.4c24, v0.4c25t, v0.4c26t hay v0.4c27t.** Các bản này làm một máy E-M1 II **lặp khởi động** (màn hình
> lên, cửa trập kêu rồi tắt). Nạp tệp khôi phục là máy chạy lại ([mục 10](#khoi-phuc)).

> [!NOTE]
> **Mức độ đã kiểm chứng.** v0.4c13 và v0.4c15 đã chạy trên máy thật: tỷ lệ 65:24 / 21:9, AF, look từ thẻ, nhưng dựng
> trên tệp 3.7 cũ OM không còn phát hành. **v0.4c17** là bản đang cần thử: cùng tính năng, dựng trên tệp 3.7 OM đang
> phát hành, đã qua kiểm tra trên giả lập nhưng **chưa nạp vào máy thật**. Hãy làm đúng các bước sao lưu bên dưới.

<a id="tinh-nang"></a>

## 2. Repo này làm được gì

Nhãn: ✅ đã chạy trên máy · 🧪 kiểm trên giả lập · ⏳ chưa thử.

| Tính năng | Làm gì | Trạng thái |
|---|---|---|
| Bỏ giới hạn quay video | Một đoạn quay được tới 9 giờ, thay vì 29 phút. | ✅ từ v0.1 |
| Focus stacking với mọi ống kính | Bỏ danh sách chỉ cho ống PRO; ống AF bất kỳ đều dùng được Focus Stacking. | ✅ từ v0.1 |
| Look phim trong Color Creator | 16 look có sẵn (Provia … Acros), màu theo 12 vùng sắc độ, tone sáng/trung/tối, chỉnh Chroma, Highlights/Shadows, cường độ x1–x3. | ✅ v0.3b5 |
| Look từ thẻ | Đọc tối đa 32 look trong `EM1MOD/LOOKS.BIN` (cùng định dạng E-P7, tạo bằng Control Panel). | ✅ v0.4c15: nạp được · tên/màu từ thẻ ⏳ chưa xác nhận |
| Tỷ lệ 65:24 và 21:9 | Ảnh toàn cảnh 5184×1920 và 5184×2224, có trong Shooting Menu, Super Control Panel, chọn điểm AF. | ✅ v0.4c13 |
| Halation (quầng sáng) | Quầng màu quanh điểm sáng trên ảnh JPEG màu; chỉnh Off/Low/Med/High ở trang Halo. | ⛔ v0.4c24: lặp khởi động, đừng nạp |
| Watchdog 30 s | Máy chờ 30 s thay vì 10 s trước khi tự khởi động lại, để ảnh có quầng kịp lưu. | ⛔ v0.4c22t+: chưa an toàn |
| Nhớ look | Look đã chọn trong Color Creator được giữ sau khi tắt máy và tự áp lại ở lần nhấn nửa cò đầu. | ⛔ v0.4c25t: lặp khởi động, đừng nạp |
| WB theo look | Look màu áp WB shift (A-B, G-M) của riêng nó thay cho fine-tune WB của bạn; CWB và các mode khác giữ nguyên. | ⛔ v0.4c26t: lặp khởi động, đừng nạp |
| Vòng màu | Trang Wheel trong Color Creator vẽ look lên vòng màu 12 ô; nút xuống hoặc TRASH đổi trục S / H / L. Chỉ hiển thị. | ⛔ v0.4c27t: lặp khởi động, đừng nạp |
| Sharpness tuyến tính | −2..+2 thành tắt / 25 / 50 / 75 / 100 %. Chỉ có trong bản thử riêng `v0.4c19t`, không có trong v0.4c17. | 🧪 bản thử |
| Chưa có | B&W thật (look đơn sắc chỉ giảm độ bão hoà), Blacks/Whites, grain, tắt sharpening, NR theo look. | ⏳ chưa port |

Phía máy tính, repo có:

- **Control Panel** (thư mục `webapp/`): tạo, sửa và chia sẻ look, xuất `LOOKS.BIN` cho E-M1 II;
- **bộ dựng gói** `caduceus.py`;
- **bộ kiểm tra giả lập** (`tools/omdem1mk2_*`).

<a id="chuan-bi"></a>

## 3. Cần chuẩn bị

- **Máy E-M1 Mark II ở firmware 3.7.** Kiểm tra ở <kbd>MENU</kbd> → Setup (cờ lê) → **Firmware**, dòng Body. Nếu thấp hơn
  3.7, cập nhật bản chính hãng trước bằng OM Workspace ([hướng dẫn](huong-dan-cap-nhat-firmware-om-workspace.md)).
- **Pin sạc đầy**, tốt nhất thêm một pin dự phòng.
- **Thẻ SD** máy đã đọc được, lắp ở **khe 1** khi nạp.
- **Máy tính** Windows 64 bit để chạy EXE, hoặc máy có [Python 3.10 trở lên](https://www.python.org/downloads/) để
  dùng gói ZIP. Trên Windows, tích “Add python.exe to PATH” khi cài Python.
- Cáp USB và **OM Workspace** để sao lưu cài đặt máy (không bắt buộc nhưng nên làm).

<a id="sao-luu"></a>

## 4. Sao lưu trước khi nạp

### 4.1 Cài đặt của máy

1. Tắt máy, rút thẻ, nối cáp USB, bật máy, chọn **Storage** trên màn hình máy.
2. Trong OM Workspace: **Camera → Custom Settings → Save**, chọn các nhóm cài đặt, lưu tệp vào máy tính.
3. Ghi lại thêm bằng tay các mục quan trọng: C1/C2/C3, nút tuỳ chỉnh, AF.

### 4.2 Ảnh và thư mục trên thẻ

Chép toàn bộ ảnh, video và thư mục `EM1MOD/` (nếu có) sang máy tính. Mở thử vài tệp để chắc bản sao đọc được. Chỉ định
dạng thẻ sau khi đã kiểm tra bản sao.

### 4.3 Giữ đường quay về

- Sau bước 5 bạn sẽ có `restore/E1259999.BIN`, là tệp 3.7 gốc của OM. **Giữ nó trên máy tính** trước khi nạp.
- Nếu máy đang chạy một bản Caduceus cũ, giữ lại cả thư mục gói của bản đó (có `DCOLYMP/` và `SHA256SUMS`).
- v0.4c15 trở về trước dựng trên một tệp 3.7 cũ (`f0c25dd8…`), tệp này không còn tải được. Muốn quay về các bản đó thì
  phải còn giữ gói đã dựng sẵn.

Repo không đọc ngược được firmware đang nằm trong máy. Vì thế tệp khôi phục là bản 3.7 chính hãng, không phải bản sao của
máy bạn.

<a id="tao-goi"></a>

## 5. Tạo gói firmware trên máy tính

1. Tải `caduceus-build.exe` cho Windows 64 bit hoặc `caduceus-em1mk2-source.zip`. [Trang tải v0.4c17](https://github.com/xtruong88/caduceus-em1ii/releases/tag/em1mk2-v0.4c17)
2. Đặt EXE trong thư mục có quyền ghi rồi nhấp đúp. Với ZIP, giải nén toàn bộ và nhấp đúp `Build Caduceus (Windows).bat`
   hoặc `Build Caduceus (Mac).command`. Trên Linux, chạy `build-caduceus-linux.sh` trong Terminal.
3. Đọc giấy phép OM Digital Solutions và gõ `yes` nếu đồng ý. Sau khi tải tệp 3.7 gốc, builder kiểm hash rồi tạo gói
   **v0.4c17** trong `out/em1mk2-v0.4c17/` cạnh chương trình. Nếu đã có tệp OM đúng hash, builder dùng tệp đó.

SmartScreen có thể hiện cảnh báo vì EXE chưa ký. Bạn có thể dùng ZIP và launcher Python.

### Dùng dòng lệnh

Mở PowerShell (Windows) hoặc Terminal (macOS/Linux) trong thư mục repo, nơi có `caduceus.py`. Trên macOS/Linux, thay
`python` bằng `python3` nếu cần.

```powershell
python caduceus.py build --camera em1mk2 --release v0.4c17 --out out/em1mk2-v0.4c17
python caduceus.py verify out/em1mk2-v0.4c17
```

- Lệnh `build` hỏi đồng ý giấy phép trước khi tải tệp 3.7 từ máy chủ OM. Nếu đã có tệp đúng hash, thêm
  `--stock "đường-dẫn\OLY_E_125_3700_0000_0000.BIN"`.
- Thư mục `--out` phải mới hoặc trống.
- **Không** dựng v0.4c24, v0.4c25t, v0.4c26t, v0.4c27t: các bản này làm máy lặp khởi động.
- Chỉ dùng gói khi `verify` báo **All good.** và có dòng khớp `releases/em1mk2/v0.4c17/SHA256SUMS`
  (`E1259999.BIN` = `6da28f37d7e9ec25bdf660d4708d3f4ab6e5a29f445f50029b8e539d8eb97d54`).

| Tệp | Đường dẫn | Dùng làm gì |
|---|---|---|
| Tệp cài | `DCOLYMP/E1259999.BIN` | Chép lên thẻ để nạp. |
| Pack look đi kèm | `EM1MOD/LOOKS.BIN` | 16 look, chép nếu muốn dùng. |
| Tệp khôi phục | `restore/E1259999.BIN` | Firmware gốc. **Giữ trên máy tính**, không chép lên thẻ. |

> [!WARNING]
> Hai tệp firmware cùng tên `E1259999.BIN`. Luôn xem kỹ bạn đang chép từ `DCOLYMP/` hay `restore/`. Tệp
> `E1429999.BIN` là của PEN E-P7: không dùng cho E-M1 II.

<a id="chep-the"></a>

## 6. Chép lên thẻ SD

Chế độ cài nhanh tìm thẻ có thư mục `DCIM`. Đối chiếu đúng ổ rồi xác nhận chép. Builder kiểm lại hash sau khi
chép tệp cài và giữ pack look có định dạng hợp lệ trên thẻ. Nếu không tự nhận diện được thẻ, có thể chỉ định ổ
bằng `caduceus-build.exe --sd E:` (thay `E:` bằng ổ của bạn) hoặc chép tay theo các bước dưới đây.

1. Cắm thẻ vào máy tính, mở **gốc thẻ** (cùng cấp với `DCIM/`).
2. Tạo thư mục `DCOLYMP` nếu chưa có. Chuyển các tệp cập nhật cũ trong đó ra máy tính.
3. Chép `DCOLYMP/E1259999.BIN` từ gói vào `DCOLYMP` trên thẻ. Trên thẻ chỉ để đúng một tệp cập nhật. Bật hiển thị đuôi
   tệp để tránh tên kiểu `.BIN.BIN` hay `(1)`.
4. Tuỳ chọn: chép `EM1MOD/LOOKS.BIN`. Nếu thẻ đã có pack riêng, cứ giữ pack đó. Riêng tệp `LOOKS.BIN` cũ dài đúng 2.080
   byte (định dạng `EM1B` của v0.1–v0.3) thì máy không đọc được và báo `CF.1`: thay nó bằng pack mới.

```text
Gốc thẻ SD/
├── DCOLYMP/
│   └── E1259999.BIN
└── EM1MOD/            (tuỳ chọn)
    └── LOOKS.BIN
```

So hash trước khi rút thẻ. Trong PowerShell, thay `E:` bằng ổ thẻ của bạn; hai giá trị Hash phải giống nhau:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'E:\DCOLYMP\E1259999.BIN', '.\out\em1mk2-v0.4c17\DCOLYMP\E1259999.BIN'
```

Sau đó Eject rồi rút thẻ.

<a id="nap"></a>

## 7. Nạp firmware vào máy

Nếu đã dùng builder để chép thẻ, vẫn kiểm tra trong `DCOLYMP/` chỉ có đúng tệp cập nhật cần nạp.

> [!TIP]
> **Bước 0, nên làm nếu bạn chỉ có một máy:** nạp `restore/E1259999.BIN` trước. Tệp này là firmware 3.7 chính hãng của
> OM, không có bản vá nào, nên rủi ro gần như bằng một lần cập nhật chính hãng. Chép nó lên thẻ thành
> `DCOLYMP/E1259999.BIN` và làm đúng các bước dưới đây. Nếu thành công, bạn biết chắc ba điều trên chính máy mình:
>
> - thẻ và quy trình nạp hoạt động;
> - tệp 3.7 hiện tại của OM (`691a8a8e…`) chạy tốt;
> - đường quay về đã sẵn sàng.
>
> Khởi động và chụp thử một ảnh, rồi mới nạp tệp cài Caduceus (v0.4c17) theo cùng các bước.

1. Để máy ở **OFF**. Lắp pin đầy, cho thẻ vào **khe 1**, đóng mọi nắp.
2. Giữ <kbd>OK</kbd> trong khi gạt công tắc sang **ON**.
3. Đèn báo **sáng liên tục** là máy đang đọc và ghi. Không đụng vào máy.
4. Đèn chuyển sang **nhấp nháy đều khoảng 2 lần mỗi giây** là đã xong.
5. Gạt OFF. Lấy thẻ ra, xoá `DCOLYMP/E1259999.BIN` trên thẻ bằng máy tính (giữ `EM1MOD`), lắp lại và bật máy bình
   thường.

> [!WARNING]
> **Khi đèn đang sáng liên tục:** không tắt máy, không mở nắp pin, không rút thẻ. Nếu đèn nháy nhanh ngay từ đầu, không
> có pha sáng liên tục, nghĩa là máy từ chối tệp và chưa ghi gì. Khi đó kiểm tra lại tên tệp, đường dẫn và hash.

Trước khi ghi, máy tự kiểm tra checksum của mọi phần trong gói, nên một tệp hỏng sẽ bị từ chối. Gói Caduceus chỉ sửa
phần firmware chính; bốn phần còn lại, gồm cả chương trình cập nhật của máy, giữ nguyên byte gốc của OM.

<a id="kiem-tra"></a>

## 8. Kiểm tra sau khi nạp

1. Máy khởi động, vào được menu, chụp và xem lại một ảnh JPEG 4:3.
2. <kbd>MENU</kbd> → Setup → Firmware: dòng Body vẫn là **3.7**. Đó là phiên bản nền; Caduceus nhận ra qua các tính năng
   bên dưới.
3. Picture Mode → **Color Creator**. Nhấn nửa cò một lần, rồi mở trình chỉnh Color Creator: dòng dưới cùng hiện tên look
   và mã trạng thái (xem [9.2](#ma-trang-thai)).
4. Thử 65:24 hoặc 21:9, chọn điểm AF, chụp một ảnh (65:24 cho 5184×1920, 21:9 cho 5184×2224).

Nếu một bước hỏng, xem [Xử lý lỗi](#loi). Máy lặp khởi động thì nạp tệp khôi phục ([mục 10](#khoi-phuc)) và báo lại
khoảng thời gian từ lúc bật đến lúc tắt (1, 10 hay 30 giây).

<a id="su-dung"></a>

## 9. Cách dùng các tính năng mới

### 9.1 Look phim trong Color Creator

Look chỉ áp dụng khi Picture Mode là **Color Creator**, và chỉ sau khi bạn đã mở trình chỉnh Color Creator một lần kể từ
lúc bật máy. Trong trình chỉnh, <kbd>INFO</kbd> chuyển trang (nút Thùng rác cũng chuyển trang):

| Trang | Điều khiển | Tác dụng |
|---|---|---|
| 0 · Film | Mũi tên trái/phải | Chọn look: từ thẻ nếu có, không thì 16 look có sẵn. Hai bánh xe vẫn là vòng màu gốc của Color Creator. |
| 1 · Chroma | Trái/phải | Cộng −5..+5 độ bão hoà cho cả 12 vùng màu (look màu). |
| 2 · Luminance | Bánh trước hoặc trái/phải; bánh sau hoặc lên/xuống | Highlights; Shadows. Midtones lấy theo look. |
| 3 · Strength | Bánh trước hoặc trái/phải | Cường độ look x1 → x3 (bão hoà, sắc độ và độ sáng từng vùng). |
| 4 · Halo | Trái/phải | Off / Low / Med / High (xem 9.5). |

16 look có sẵn: Provia, Velvia, Astia, Classic Chrome, Classic Neg, Nostalgic, Reala Ace, Eterna, Bleach Bypass,
Kodachrome 64, Portra 400, Ektar 100, Gold 200, Tri-X 400, CineStill 800, Acros. Tên look cũng hiện ở ô Color Creator
trên Super Control Panel. Look đơn sắc (Tri-X, Acros) hiện chỉ giảm độ bão hoà, chưa phải B&W thật.

<a id="ma-trang-thai"></a>

### 9.2 Dòng trạng thái của Color Creator

| Mã | Nghĩa |
|---|---|
| `C1.n` | Đã nạp pack từ thẻ sau n lần thử. |
| `C0.n` | Đang thử nạp; nhấn nửa cò thêm. |
| `CF.8` | Không có `EM1MOD/LOOKS.BIN`: dùng 16 look có sẵn. |
| `CF.1` | Tệp lỗi hoặc định dạng cũ `EM1B`. |
| `K…` / `K…+` | Mã look đang chọn; dấu `+` là look đã áp vào ảnh. |
| `E58` / `E16` | Máy từ chối ghi một cài đặt: đang bận / giá trị không hợp lệ. |

Nếu thẻ nạp xong (`C1`) khi trình chỉnh đang mở, hãy thoát rồi mở lại Color Creator để chuyển sang look đầu tiên của thẻ.

### 9.3 Tạo look riêng bằng Control Panel

Control Panel là trang web chạy trên máy tính, trong thư mục `webapp/`. Cần [Node.js](https://nodejs.org/):

```bash
cd webapp
npm ci
npm run dev
```

Mở `http://localhost:5173`, chọn máy **E-M1 II**, chỉnh look rồi xuất `LOOKS.BIN`. Chép tệp vào `EM1MOD/` ở gốc thẻ, tắt
rồi bật máy, nhấn nửa cò. Pack và mã chia sẻ (`pk1_…`) dùng chung với E-P7, nên một pack E-P7 cũng chạy được. Máy thử đọc
thẻ ở khe 1 trước, rồi đến khe 2.

### 9.4 Tỷ lệ 65:24 và 21:9

Chọn ở **Shooting Menu 1 → Image Aspect**, hoặc ô tỷ lệ trên **Super Control Panel**. 65:24 cho ảnh 5184×1920, 21:9 cho
ảnh 5184×2224. Điểm AF dùng bố cục của 16:9. Chưa thử trên máy: khung live view và xem lại ngay sau chụp, RAW+JPEG, giữ
lựa chọn sau khi tắt máy, Live Control, AF tracking, lưới. Nếu gặp lỗi, đặt về 4:3.

<a id="halation"></a>

### 9.5 Halation (quầng sáng)

Mở Color Creator, nhấn <kbd>INFO</kbd> tới trang **Halo**, dùng trái/phải để chọn **Off / Low / Med / High**. Vừa nạp
xong, Halo ở **Off**. Giá trị được nhớ qua lần tắt máy.

- **Áp cho:** ảnh chụp thường ở các picture mode màu (Vivid, Natural, Color Creator…), ảnh JPEG.
- **Không áp cho:** Monotone, Art Filter, Art Effect, và các chế độ chụp đặc biệt (High Res, HDR, bracketing, Live
  Composite…). Những ảnh này giữ nguyên như firmware gốc.
- **Màu quầng:** mặc định đỏ. Pack look có ghi màu quầng thì dùng màu đó: amber, warm hoặc cool.
- **Thời gian lưu:** ảnh có quầng lưu lâu hơn bình thường. Cảnh đêm nhiều đèn ước tính khoảng 4–8 s. Watchdog 30 s để
  máy không tự khởi động lại.

**Lần đầu, nên thử như sau:**

1. Cảnh ban ngày không có điểm cháy sáng, tripod, Vivid: chụp một ảnh Halo Off và một ảnh Halo Low. Hai ảnh phải gần như
   giống nhau. Nếu màu hay độ tương phản khác rõ, để Halo Off và gửi hai ảnh để phân tích.
2. Cảnh đêm có đèn, Halo Med: phải thấy quầng quanh điểm sáng, máy không tự khởi động lại. Ghi lại thời gian lưu.
3. Có gì lạ: đặt Halo về Off, máy chạy như v0.4c17.

Chi tiết: [quy trình thử trên máy](OMD-EM1-II/thu-may-halation.md) ·
[tài liệu kỹ thuật halation](OMD-EM1-II/HALATION.md).

### 9.6 Quay video dài và focus stacking

- **Video:** quay như bình thường; một đoạn không còn dừng ở 29 phút (giới hạn mới 9 giờ). Pin, dung lượng thẻ và nhiệt
  độ vẫn có thể dừng máy sớm hơn.
- **Focus stacking:** bật như bình thường trong menu Focus Bracketing / Focus Stacking. Giờ dùng được với ống AF bất kỳ
  (ống Olympus thường, Panasonic, Sigma…), không chỉ ống PRO.

<a id="nho-look"></a>

### 9.7 Nhớ look sau khi tắt máy (bản thử v0.4c25t)

- Chọn look bằng mũi tên trong trình chỉnh Color Creator như thường. Máy ghi lại look đó.
- Sau khi bật máy, **lần nhấn nửa cò đầu tiên** áp lại look (hoặc lúc mở trình chỉnh, nếu bạn mở trước). Look trên thẻ
  chỉ được áp lại sau khi máy đọc xong `LOOKS.BIN`.
- Không nhớ: Strength (về x1) và Chroma (về 0). Reset toàn bộ máy sẽ xoá look đã nhớ.

Các bước thử: [thu-may-nho-look.md](OMD-EM1-II/thu-may-nho-look.md).

<a id="wb-look"></a>

### 9.8 WB theo look (bản thử v0.4c26t)

- Look màu có ghi WB shift (A-B, G-M, từ −7 đến +7) sẽ dùng giá trị đó thay cho fine-tune WB bạn đã đặt, khi chụp ở
  Color Creator. Menu WB vẫn hiện giá trị của bạn, không bị ghi đè.
- **Giữ nguyên:** CWB (đặt nhiệt độ màu bằng Kelvin), các picture mode khác, look đơn sắc, look không có WB shift, và RAW
  xử lý trong máy.
- Năm look có sẵn mang WB shift nên màu JPEG sẽ khác v0.4c25t: Nostalgic A-B +3, Gold 200 +2, Kodachrome 64 +1, Portra
  400 +1, CineStill 800 −3.
- Live view có thể không hiện WB shift (trên E-P7 cũng vậy), chỉ ảnh JPEG có.

Các bước thử: [thu-may-look-wb.md](OMD-EM1-II/thu-may-look-wb.md).

<a id="vong-mau"></a>

### 9.9 Vòng màu (bản thử v0.4c27t)

- Trong trình chỉnh Color Creator, INFO từ Film sang trang **Wheel**: vòng Color Creator được thay bằng vòng màu 12 ô,
  đa giác vẽ trục S của look đang chọn.
- Trên trang Wheel:
  - **nút xuống** hoặc **TRASH** đổi trục S → H → L → S; dòng guide ghi `Wheel S`, `Wheel H`, `Wheel L` kèm tên look;
  - **INFO** sang trang Chroma;
  - **lên, trái, phải** và hai **vòng xoay** không làm gì;
  - **OK**, **MENU** và các sự kiện khác của máy (ví dụ nút tuỳ biến) rời trang Wheel và đưa trình chỉnh về Film.
- Các trang sau đó vẫn như cũ: Chroma, Luminance, Strength, Halo. Rời trang Wheel là vòng Color Creator gốc trở lại.
- Chỉ hiển thị: không đổi setting, không đổi ảnh chụp.

Các bước thử: [thu-may-color-wheel.md](OMD-EM1-II/thu-may-color-wheel.md).

<a id="khoi-phuc"></a>

## 10. Quay về firmware gốc hoặc bản cũ

- **Về firmware gốc 3.7:** chép `restore/E1259999.BIN` lên thẻ thành `DCOLYMP/E1259999.BIN`, rồi nạp như mục 7. Sau đó
  kiểm tra Body 3.7 và các mục Caduceus đã mất.
- **Về một bản Caduceus khác:** dùng tệp trong `DCOLYMP/` của gói bản đó (đã `verify`), nạp như mục 7.
- **Nạp lại cài đặt:** nối USB ở chế độ Storage, trong OM Workspace chọn **Camera → Custom Settings → Load → Load from
  File**.

> [!WARNING]
> Nếu máy treo hoặc khởi động lại liên tục: tháo pin, lắp lại, giữ <kbd>OK</kbd> và bật máy với thẻ chứa tệp khôi phục.
> Cách này đã cứu được một chiếc PEN E-P7, nhưng trên E-M1 II chưa ai thử. Nếu máy không vào được chế độ cập nhật, liên
> hệ dịch vụ sửa chữa OM System và cho họ biết bản đã nạp cùng diễn biến đèn.

<a id="loi"></a>

## 11. Xử lý lỗi và câu hỏi thường gặp

<details><summary>Đèn không theo trình tự nạp</summary>

Còn sáng liên tục, hoặc chưa rõ máy có đang ghi: giữ nguyên nguồn và thẻ. Khi chắc máy không ghi nữa, tắt máy và kiểm
tra: pin, khe 1, đường dẫn `DCOLYMP/` ở gốc thẻ, tên tệp, SHA-256. Chỉ thử lại với gói đã `verify`.

</details>

<details><summary>Máy bật nhưng không đọc look trên thẻ</summary>

`C0.n`: nhấn nửa cò thêm vài lần. `CF.8`: thiếu tệp, kiểm tra `EM1MOD/LOOKS.BIN` ở gốc thẻ. `CF.1`: tệp lỗi hoặc định
dạng cũ, thay bằng pack mới. Nếu máy chạy bất thường, thử thẻ không có `EM1MOD/`: máy sẽ dùng 16 look có sẵn.

</details>

<details><summary>Màu không đổi khi chọn look</summary>

Look chỉ áp ở Picture Mode Color Creator, sau khi đã mở trình chỉnh một lần. Xem dòng trạng thái: không có `K…` thì nhấn
nửa cò rồi mở lại; có `K…` mà thiếu `+` thì ghi lại mã khi báo lỗi.

</details>

<details><summary>Không thấy quầng sáng</summary>

Kiểm tra trang Halo không ở Off, picture mode là chế độ màu thường (không phải Monotone hay Art Filter), và cảnh có điểm
sáng mạnh. Trên giả lập, vùng nhớ ảnh của máy nằm trong dải mà mã vẽ quầng xử lý được, nên quầng phải hiện. Nếu vẫn không
thấy, gửi ảnh mẫu kèm thông số.

</details>

<details><summary>Tôi có cần nạp lần lượt nhiều bản không?</summary>

Không. Hiện chỉ nạp **một lần v0.4c17**. Đừng nạp v0.4c24 trở đi cho tới khi tìm ra lỗi lặp khởi động.

</details>

<details><summary>Firmware screen vẫn ghi 3.7, có phải chưa nạp?</summary>

Bình thường: Caduceus giữ nguyên số phiên bản. Hãy kiểm tra bằng các tính năng: dòng trạng thái Color Creator, tỷ lệ
65:24.

</details>

<a id="cac-ban"></a>

## 12. Các bản trong repo

| Bản | Dùng khi nào |
|---|---|
| **v0.4c17** | **Bản cần thử.** Look, 65:24 / 21:9, video 9 giờ, focus stacking, look từ thẻ. Không có halation. |
| v0.4c24 / v0.4c25t / v0.4c26t / v0.4c27t | **Đừng nạp**: làm một máy lặp khởi động. |
| v0.4c22t | Bản thử chẩn đoán: đi đường xử lý mới nhưng không vẽ quầng. Chỉ dùng khi tìm lỗi. |
| v0.4c23t | Bản thử: quầng cố định ở mức Med. Chỉ dùng khi tìm lỗi. |
| v0.4c19t | Bản thử Sharpness tuyến tính, không có halation. |
| v0.4c13 / v0.4c15 | Bản cũ đã chạy trên máy, dựng trên tệp 3.7 cũ không còn tải được. |

Có thể xem danh sách bằng `python caduceus.py list --camera em1mk2`.

Tài liệu liên quan: [README](../README.vi.md) · [Changelog E-M1 II](../patches/omdem1mk2/CHANGELOG.md) ·
[Ghi chú port](PORT_EM1MK2.md) · [Quy trình thử halation](OMD-EM1-II/thu-may-halation.md) ·
[Thử nhớ look](OMD-EM1-II/thu-may-nho-look.md) · [Thử WB theo look](OMD-EM1-II/thu-may-look-wb.md) ·
[Thử vòng màu](OMD-EM1-II/thu-may-color-wheel.md) · [Cập nhật firmware chính hãng bằng OM Workspace](huong-dan-cap-nhat-firmware-om-workspace.md) ·
[Firmware guide (tiếng Anh)](FIRMWARE_GUIDE.md)
