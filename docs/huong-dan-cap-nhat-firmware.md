# Hướng dẫn cập nhật firmware Olympus PEN E-P7 với Caduceus

Hướng dẫn này dùng **Olympus PEN E-P7** với firmware nền **1.1** và Caduceus **v0.31c beta**, phiên bản có trong kho mã này. Bạn có thể cài Caduceus lần đầu, cập nhật từ bản Caduceus cũ hoặc khôi phục firmware gốc 1.1.

**Nếu thân máy ghi Olympus OM-D E-M1 Mark II**, hãy làm theo hướng dẫn OM Workspace dành cho model đó. Tuyệt đối không nạp tệp `E1429999.BIN` của E-P7 lên E-M1 Mark II hay bất kỳ model nào khác. [Hướng dẫn cập nhật chính hãng qua OM Workspace](huong-dan-cap-nhat-firmware-om-workspace.md)

> [!WARNING]
> Caduceus là bản sửa đổi firmware thử nghiệm. Máy có thể treo, mất dữ liệu hoặc không khởi động được. Chuẩn bị pin đầy, sao lưu thẻ và giữ tệp khôi phục trên máy tính trước khi nạp. Trong lúc máy đang ghi firmware, giữ nguyên nguồn, pin và thẻ SD.

## 1. Kiểm tra máy và sao lưu

1. Xác nhận tên **PEN E-P7** trên thân máy. Bật máy, vào **MENU → Setup** (biểu tượng cờ lê) **→ Firmware** và ghi lại phiên bản thân máy. Nếu máy còn nguyên bản, phiên bản phải là **1.1**. Nếu thấp hơn, cập nhật chính hãng lên 1.1 trước. Nếu máy đã chạy Caduceus trên nền 1.1, có thể cập nhật trực tiếp qua thẻ. [Đưa E-P7 nguyên bản lên 1.1 bằng OM Workspace](huong-dan-cap-nhat-firmware-om-workspace.md#pen-e-p7-firmware-goc)
2. Sạc đầy pin. Chuẩn bị một thẻ SD mà E-P7 đọc được và đầu đọc thẻ. Dùng thẻ đã được định dạng trong máy. Nếu cần định dạng lại, sao lưu dữ liệu trước vì thao tác này xóa nội dung thẻ.
3. Chép ảnh và video, nhất là thư mục `DCIM`, sang máy tính. Kiểm tra mở được một vài tệp đã sao lưu. Nếu thẻ đã có Caduceus, chép **toàn bộ `EP7MOD`** sang máy tính, gồm cả các tệp `.BAK` nếu có.
4. Chuẩn bị máy tính Windows, macOS hoặc Linux có **Python 3.10 trở lên**, kết nối Internet và thư mục làm việc có quyền ghi. Trên Windows, khi cài Python từ trang chính thức, chọn **Add python.exe to PATH** nếu trình cài có tùy chọn này. [Tải Python](https://www.python.org/downloads/)

## 2. Tạo và kiểm tra gói cập nhật trên máy tính

Tải **Source code (zip)** của đúng bản **v0.31c** ở mục **Assets** rồi giải nén cả thư mục. Làm việc trong thư mục chứa `caduceus.py` và `releases/v0.31c`. Bộ tạo gói tải firmware gốc `OLY_E_142_1100_0000_0000.BIN` của E-P7 từ máy chủ OM, kiểm SHA-256, áp dụng bản vá và kiểm gói đầu ra với bản phát hành. [Caduceus v0.31c trên GitHub](https://github.com/cakelesscoder/caduceus-ep7/releases/tag/v0.31c)

### Dùng trình chạy có sẵn

| Hệ điều hành | Cách chạy |
| --- | --- |
| Windows | Bấm đúp `Build Caduceus (Windows).bat`. |
| macOS | Mở `Build Caduceus (Mac).command` từ Finder. Lần đầu, nếu macOS yêu cầu xác nhận, dùng menu chuột phải **Open** cho tệp đã tải từ bản phát hành. |
| Linux | Chạy `./build-caduceus-linux.sh` trong terminal tại thư mục mã nguồn, hoặc `sh build-caduceus-linux.sh` nếu tệp thiếu quyền thực thi. |

Trình chạy tự chọn bản cao nhất có sẵn **trong bản mã nguồn đang mở**. Kiểm tra dòng `Caduceus one-press build: v0.31c` và thư mục `Caduceus-v0.31c/`. Nếu có đúng một ổ thẻ được nhận diện qua thư mục `DCIM`, trình chạy hỏi có chép tệp vào thẻ hay không. Đối chiếu ký tự ổ hoặc tên thẻ trước khi đồng ý. Nếu dùng lệnh bên dưới hoặc chọn chép thủ công, tiếp tục theo mục 3.

### Dùng dòng lệnh để chọn chính xác v0.31c

Mở terminal tại thư mục chứa `caduceus.py`. Trên Windows, có thể mở thư mục bằng File Explorer, gõ `cmd` vào thanh địa chỉ rồi nhấn Enter.

Windows

```powershell
py --version
py caduceus.py list
py caduceus.py build --release v0.31c
py caduceus.py verify out
```

Nếu `py` báo `No installed Python found!` nhưng `python --version` trả về Python 3.10 trở lên, thay `py` bằng `python` trong các lệnh trên.

macOS hoặc Linux

```sh
python3 --version
python3 caduceus.py list
python3 caduceus.py build --release v0.31c
python3 caduceus.py verify out
```

- Lệnh `build` mặc định ghi vào `out/`. Nếu thư mục đã có dữ liệu, thêm `--out out-v031c` và dùng `verify out-v031c`. Để kiểm gói do trình chạy tạo, dùng `verify Caduceus-v0.31c`.
- Nếu đã có firmware gốc đúng bản, thêm `--stock "đường-dẫn-tới-tệp-gốc.BIN"` vào lệnh `build`. Tên tệp chính thức là `OLY_E_142_1100_0000_0000.BIN`. SHA-256 yêu cầu là `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`.
- Chỉ tiếp tục khi tạo gói thành công. Khi chạy `verify`, kết quả cần hiển thị `All good.` và xác nhận khớp `releases/v0.31c/SHA256SUMS`.

### Nhận diện tệp đầu ra

| Tệp trong thư mục kết quả | Công dụng |
| --- | --- |
| `DCOLYMP/E1429999.BIN` | Gói **cài hoặc cập nhật Caduceus**. |
| `restore/E1429999.BIN` | Gói **khôi phục firmware gốc 1.1**. Giữ trên máy tính trong thư mục `restore`. |
| `EP7MOD/LOOKS.BIN` | Thư viện giả lập phim của bản phát hành. |
| `EP7MOD/BUNDLES.BIN` | Bốn cấu hình màu ảnh tĩnh. Máy có thể ghi lại tệp này khi lưu chỉnh sửa. |
| `EP7MOD/MOVIE.BIN` | Cấu hình màu cho chế độ Movie. |
| `EP7MOD/AP.BIN` | Cấu hình màu cho chế độ AP. |
| `SHA256SUMS`, `RELEASE` | Danh sách mã kiểm tra và thông tin phiên bản để dùng trên máy tính. |

Hai tệp `E1429999.BIN` **cùng tên**. Trước khi chép, kiểm tra thư mục nguồn `DCOLYMP` hay `restore` theo đúng mục đích.

## 3. Chép tệp vào thẻ SD

1. Tắt E-P7, lấy thẻ ra và cắm vào đầu đọc. Mở **thư mục gốc của thẻ**, cùng cấp với `DCIM`. Tạo `DCOLYMP` và `EP7MOD` nếu chưa có.
2. Chép **`DCOLYMP/E1429999.BIN` từ gói cài** vào `DCOLYMP` trên thẻ. Nếu có tệp cập nhật `.BIN` khác trong `DCOLYMP`, chuyển chúng ra máy tính để chỉ còn đúng một `E1429999.BIN`.
3. Chép tệp trong `EP7MOD` theo tình trạng thẻ.

   | Tình trạng | Việc cần làm |
   | --- | --- |
   | Cài lần đầu, thẻ chưa có `EP7MOD` | Chép đủ bốn tệp `LOOKS.BIN`, `BUNDLES.BIN`, `MOVIE.BIN`, `AP.BIN` từ gói. |
   | Đã dùng Caduceus | Chép `LOOKS.BIN` từ bản mới. Giữ `BUNDLES.BIN`, `MOVIE.BIN` và `AP.BIN` đang có để bảo toàn cấu hình. Tệp nào thiếu thì chép tệp tương ứng từ gói. Nếu đã tự xuất `LOOKS.BIN` từ Control Panel, lưu một bản riêng trước khi chép đè để có thể dùng lại với bản firmware tương thích. |

   Nếu đã đồng ý cho trình chạy chép tự động, kiểm tra cấu trúc thẻ bên dưới. Trình chạy chép lại `LOOKS.BIN`, giữ ba tệp cấu hình đã có và báo nếu thấy tệp cập nhật `.BIN` khác cần dọn khỏi `DCOLYMP`.

4. Bật hiển thị phần mở rộng tệp nếu cần. Kiểm tra đúng `E1429999.BIN`, tránh các tên do hệ điều hành thêm như `E1429999 (1).BIN` hoặc `E1429999.BIN.BIN`. Cấu trúc thẻ trước khi nạp cần như sau.

   ```text
   (gốc thẻ SD)
   ├── DCIM/
   ├── DCOLYMP/
   │   └── E1429999.BIN
   └── EP7MOD/
       ├── LOOKS.BIN
       ├── BUNDLES.BIN
       ├── MOVIE.BIN
       └── AP.BIN
   ```

5. Nếu chép thủ công, có thể kiểm SHA-256 của tệp trên thẻ trước khi tháo. Ví dụ trên Windows PowerShell, với thẻ ở ổ `E:` và kết quả lệnh `build` ở `out/`, hai dòng phải có cùng giá trị `Hash`. Đổi ký tự ổ và thư mục kết quả cho phù hợp.

   ```powershell
   Get-FileHash -Algorithm SHA256 -Path 'E:\DCOLYMP\E1429999.BIN', '.\out\DCOLYMP\E1429999.BIN'
   ```

6. Chờ chép xong rồi chọn **Eject** trên Windows/macOS hoặc **Unmount/Eject** trên Linux. Giữ `restore/` và thư mục kết quả trên máy tính.

## 4. Nạp firmware vào E-P7

1. Để máy **OFF**, lắp thẻ đã chuẩn bị và pin đầy. Đóng nắp pin và thẻ.
2. **Giữ nút OK**, gạt công tắc sang **ON** và tiếp tục giữ **OK** đến khi đèn báo sáng.
3. Khi đèn **sáng liên tục**, máy đang đọc hoặc ghi firmware. **Không tắt máy, mở nắp pin, tháo pin hoặc rút thẻ.** Theo dõi đèn để xác định trạng thái hoàn tất.
4. Khi đèn chuyển từ sáng liên tục sang **nhấp nháy khoảng hai lần mỗi giây**, gạt công tắc sang **OFF**. Nếu đèn nháy nhanh ngay từ đầu hoặc khác trình tự này, xem mục xử lý lỗi bên dưới.
5. Bật máy bình thường. Mở **Setup → Firmware** và kiểm tra dòng **`Caduceus: 0.31c`**.
6. Tắt máy, đưa thẻ sang máy tính và xóa **`DCOLYMP/E1429999.BIN`** khỏi thẻ đã nạp xong. Giữ `EP7MOD` và sao lưu ảnh như thường lệ. Dùng **Eject/Unmount** trước khi tháo thẻ.

## 5. Kiểm tra sau cập nhật

1. Lắp lại thẻ, bật máy bình thường và **nhấn nửa cò chụp** để nạp cấu hình từ `EP7MOD`.
2. Gạt cần profile sang **COLOR**, chọn một **Colour Profile** và mở vòng màu. Kiểm tra trang **Film** có tên giả lập phim. Dùng **INFO** để chuyển trang nếu cần. [Hướng dẫn sử dụng Caduceus](../README.md#using-it)
3. Nếu cập nhật từ bản cũ, kiểm tra các cấu hình màu, Movie và AP mà bạn đang dùng. Chụp một ảnh JPEG và xem lại. Nếu thường quay phim, quay và phát lại một đoạn ngắn.
4. Giữ thư mục gói đã kiểm SHA-256, tệp `restore/E1429999.BIN` và bản sao `EP7MOD` trên máy tính để dùng khi cần khôi phục.

## 6. Khôi phục firmware gốc 1.1

1. Nếu máy hoạt động bình thường, tắt máy trước khi lấy thẻ. Nếu máy lặp khởi động sau khi đợt ghi đã kết thúc, thử tắt máy. Khi công tắc không phản hồi **và đã xác định máy không còn ghi firmware**, có thể tháo và lắp lại pin để ngắt vòng lặp. Một máy E-P7 đã được khôi phục bằng cách này trong thử nghiệm của dự án. [Ghi nhận phục hồi của dự án](FIRMWARE_GUIDE.md)
2. Trên máy tính, sao lưu `EP7MOD` nếu cần. Lấy **`restore/E1429999.BIN`** từ gói đã kiểm tra và chép lên thẻ thành **`DCOLYMP/E1429999.BIN`**. Thay tệp cài Caduceus nếu còn trên thẻ và bảo đảm đây là tệp `.BIN` duy nhất trong `DCOLYMP`. Dùng **Eject/Unmount**.
3. Với pin đầy và máy đang **OFF**, lắp thẻ, giữ **OK** rồi bật máy. Chờ đèn sáng liên tục chuyển sang nhấp nháy khoảng hai lần mỗi giây rồi tắt máy, như ở mục 4.
4. Bật máy bình thường. **Setup → Firmware** cần hiển thị firmware thân máy **1.1**, đồng thời dòng **Caduceus** biến mất. Tắt máy, xóa tệp nạp trong `DCOLYMP` khỏi thẻ, rồi kiểm tra chụp và xem lại ảnh.
5. Nếu máy không vào được chế độ cập nhật SD hoặc vẫn không khởi động sau khi thử khôi phục, liên hệ dịch vụ sửa chữa OM SYSTEM và báo rõ firmware đã nạp, trình tự đèn và thao tác đã thử. Khả năng cứu máy phụ thuộc vào việc trình cập nhật SD còn chạy được.

Để tạm ngừng dùng các cấu hình màu trên thẻ, tắt máy và dùng thẻ khác, hoặc chuyển `EP7MOD` khỏi thẻ sau khi đã sao lưu. Firmware Caduceus vẫn ở trong thân máy, cùng các thay đổi như Log video, XPan và giới hạn thời lượng quay. Muốn về nguyên bản, dùng gói `restore` theo các bước trên.

## 7. Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| Báo lỗi tải firmware gốc | Kiểm tra mạng và thử lại. Với Python tải từ python.org trên macOS, chạy `Install Certificates.command` trong thư mục cài đặt Python nếu lỗi liên quan chứng chỉ. Nếu đã có đúng tệp chính hãng, dùng `--stock`. |
| Báo `stock firmware SHA-256 is ... expected ...` | Kiểm tra lại nguồn, đúng model E-P7 và đúng bản 1.1. Tải lại tệp và chỉ dùng gói đã qua kiểm tra SHA-256. |
| Báo `edits.json does not match ... SHA256SUMS` | Tải lại ZIP đúng phiên bản rồi giải nén vào thư mục mới. Trên Windows, Git có thể tự chuyển xuống dòng LF thành CRLF khi checkout, làm mã kiểm tra của `edits.json` sai. ZIP của bản phát hành giữ nội dung tệp như khi phát hành. |
| Trình chạy không tìm thấy hoặc không ghi được vào thẻ | Kiểm tra đúng ổ, khóa chống ghi trên thẻ hoặc adapter và quyền ghi. Trên macOS, cấp quyền **Removable Volumes** cho Terminal nếu được hỏi, hoặc chép thủ công bằng Finder. |
| Đèn không sáng theo trình tự nạp, hoặc nháy nhanh ngay khi bật | Việc nạp có thể chưa bắt đầu hoặc tệp đã bị từ chối. Khi đã xác định máy không ghi, tắt máy và kiểm tra pin, thẻ, vị trí tệp ngay dưới `DCOLYMP`, tên và hash gói. Đưa các tệp cập nhật cũ ra khỏi thư mục rồi chép lại và thử lại. |
| Đèn vẫn sáng liên tục hoặc trạng thái ghi chưa rõ | Giữ nguyên nguồn, pin và thẻ. Tránh tự ngắt nguồn dựa vào số giây đã trôi qua. Nếu tình trạng kéo dài, ghi lại diễn biến đèn để hỏi hỗ trợ trước khi can thiệp. |
| Máy bật được nhưng không có `Caduceus: 0.31c` | Kiểm tra phiên bản hiện tại và thư mục nguồn của file đã chép. Tệp trong `restore/` đưa máy về 1.1 gốc. Tạo và kiểm lại gói cài, sau đó thực hiện mục 3 và 4. |
| Có đúng phiên bản Caduceus nhưng vòng màu vẫn như máy gốc | Nhấn nửa cò một lần sau khi bật, rồi mở lại vòng màu. Kiểm tra `EP7MOD` ở gốc thẻ. Với tệp mặc định của v0.31c, `LOOKS.BIN` là 2.112 byte, `BUNDLES.BIN` là 680 byte, `MOVIE.BIN` và `AP.BIN` là 96 byte mỗi tệp. Chép lại tệp bị thiếu hoặc bị cắt dở và tháo thẻ an toàn. |
| Sau cập nhật bị mất cấu hình màu | Tắt máy, sao lưu thư mục `EP7MOD` hiện tại rồi chép lại tệp tương ứng từ bản sao trước cập nhật. Nếu dùng bản dự phòng do máy lưu, chép `BUNDLES.BAK`, `MOVIE.BAK` hoặc `AP.BAK` sang máy tính trước, sau đó dùng bản sao mang đuôi `.BIN` đúng tên. |

Nếu cần báo lỗi cho dự án, ghi model, bản firmware trước và sau, kích thước và định dạng thẻ, tên tệp đã chép, kết quả `verify` và trình tự đèn. Nếu máy vẫn khởi động, kèm ảnh màn hình **Setup → Firmware**. [Kênh báo lỗi Caduceus](https://github.com/cakelesscoder/caduceus-ep7/issues)

## Câu hỏi thường gặp

- **Cần khôi phục 1.1 gốc trước mỗi lần lên bản Caduceus mới?** Có thể cập nhật trực tiếp từ bản Caduceus cũ trên E-P7 nền 1.1. Sao lưu `EP7MOD`, cập nhật gói firmware và chép thư viện `LOOKS.BIN` phù hợp với bản đích.
- **Chỉ muốn cập nhật công thức màu thì có cần nạp firmware?** Nếu đang dùng bản firmware tương thích với tệp xuất, có thể sao lưu và thay tệp trong `EP7MOD` theo hướng dẫn của Control Panel. [Caduceus Control Panel](https://cakelesscoder.github.io/caduceus-ep7/)
- **Có thể quay lại bản Caduceus cũ hơn?** Đọc ghi chú của bản đích và dùng các tệp thẻ tương thích. Ví dụ, `Sharp Off` làm cấu hình bị từ chối trên v0.27 trở xuống. Grain khác `Off` làm cấu hình bị từ chối trên v0.26 trở xuống. Hãy đưa các tùy chọn về giá trị tương thích khi bản mới còn chạy hoặc dùng bản sao `EP7MOD` tương ứng với bản đích. [Changelog Caduceus](../CHANGELOG.md)
