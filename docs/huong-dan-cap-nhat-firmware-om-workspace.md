# Cập nhật firmware chính thức cho Olympus OM-D E-M1 Mark II

Hướng dẫn này dùng **OM Workspace** trên Windows hoặc macOS để cập nhật firmware thân máy qua USB. Phiên bản mới nhất OM System đang công bố cho **E-M1 Mark II** là **3.7**, phát hành ngày 19/01/2023. [Danh sách firmware chính thức của OM System](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/)

> [!WARNING]
> **Tuyệt đối không nạp tệp Caduceus của PEN E-P7, kể cả tệp khôi phục của E-P7, vào E-M1 Mark II.** Hãy xác nhận tên model trên thân máy trước khi bắt đầu. Khi LCD báo `OK` trên E-M1 Mark II, **giữ nguyên cáp USB** để khởi động lại máy ảnh và nạp lại cài đặt. [Các thân máy được dự án Caduceus hỗ trợ](./BODIES.md) · [Quy trình của OM System cho E-M1 Mark II](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html)

## 1. Xác nhận model và phiên bản hiện tại

1. Đọc đúng tên **E-M1 Mark II** trên thân máy. Các model **E-M1**, **E-M1 Mark III** và **OM-1 Mark II** có firmware riêng.
2. Bật máy ảnh, nhấn **MENU**, mở **Setup Menu** (biểu tượng cờ lê) rồi chọn **Firmware**. Ghi lại số ở dòng **Body**. Nếu có dòng **Lens**, đó là phiên bản của ống kính đang gắn. [Sổ tay E-M1 Mark II, trang 109](https://download.omsystem.com/pages/inst/em1m2/manual_em1m2_ENU.pdf)
3. Nếu **Body** đã là **3.7**, bạn đã có bản hiện được công bố. Nếu số thấp hơn, tiếp tục và chọn bản cập nhật mà OM Workspace cung cấp cho đúng thân máy. OM Workspace không hỗ trợ quay về phiên bản cũ sau khi cập nhật. [Danh sách phiên bản](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/) · [Quy trình cập nhật](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html)

## 2. Chuẩn bị máy ảnh và máy tính

- **Pin và nguồn điện.** Sạc đầy pin **BLH-1**. Nếu dùng laptop, cắm nguồn và đặt máy tính để không tự ngủ trong quá trình cập nhật. Kết nối Internet ổn định, ưu tiên mạng có dây nếu sẵn có. Đăng nhập máy tính bằng tài khoản quản trị. [Thông số E-M1 Mark II](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/em1m2/) · [Yêu cầu cập nhật của OM System](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html)
- **Cáp USB dữ liệu.** Ưu tiên cáp đi kèm **CB-USB11**, đầu USB-C cắm vào thân máy và đầu USB-A cắm vào máy tính. Nếu máy tính chỉ có USB-C, dùng cáp USB-C có truyền dữ liệu và tương thích với hai thiết bị. Cắm trực tiếp vào cổng máy tính nếu có thể. [Bảng cáp USB của OM System](https://support.jp.omsystem.com/jp/support/cs/pen/acce/pen_usb.html)
- **Ảnh và video.** Sao chép dữ liệu cần giữ từ cả hai thẻ, nếu đang dùng hai thẻ. Mở thử vài tệp ở nơi sao lưu. Tắt máy ảnh, chờ đèn truy cập thẻ tắt và tháo toàn bộ thẻ SD trước khi nối USB. Bạn có thể giữ nguyên dữ liệu trên các thẻ đã tháo, không cần định dạng chúng để cập nhật qua OM Workspace. [Hướng dẫn quản lý thẻ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/em1m2/) · [Yêu cầu tháo thẻ trước khi cập nhật](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html)
- **Cài đặt cá nhân.** Chụp lại hoặc ghi ra các thiết lập quan trọng như C1/C2/C3, chức năng nút, AF, cấu hình ảnh/video và khe lưu. OM Workspace có bước tự lưu rồi nạp lại cài đặt trên E-M1 Mark II. Bạn có thể tạo thêm tệp sao lưu riêng theo mục 4. [Quy trình sao lưu tự động](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html)

Bạn có thể cập nhật thân máy khi không gắn ống kính. Nếu để ống kính trên máy, hãy chọn đúng dòng thân máy trong trình cập nhật. [Cập nhật firmware thân máy và ống kính](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/)

## 3. Cài OM Workspace và kết nối USB

1. Mở trang tải chính thức, kiểm tra hệ điều hành được hỗ trợ và nhập số sê-ri của máy ảnh nếu được yêu cầu. Trên **Windows**, chạy `OWSetup_64bit.exe`. Trên **macOS**, mở `OWSetup.dmg` và làm theo trình cài đặt. [Tải OM Workspace](https://download.omsystem.com/pages/owdownload/en/index.html)
2. Mở OM Workspace. Vào **Help → Update Software** để kiểm tra bản mới. Cập nhật ứng dụng hoặc cài lại từ trang tải chính thức nếu phiên bản quá cũ và không kết nối được máy chủ. [Ghi chú cập nhật OM Workspace](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/)
3. Khi máy ảnh đang tắt và đã tháo thẻ SD, nối cáp USB rồi bật máy ảnh. Trên LCD, dùng phím điều hướng chọn **Storage** và nhấn nút **OK** trên thân máy. Nếu menu USB không hiện, trước khi chạy cập nhật hãy ngắt kết nối, đặt **MENU → Custom Menu → D4 → USB Mode → Auto**, rồi kết nối lại. [Quy trình kết nối E-M1 Mark II](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html) · [Sổ tay E-M1 Mark II, trang 117 và 139](https://download.omsystem.com/pages/inst/em1m2/manual_em1m2_ENU.pdf)

## 4. Tạo tệp sao lưu cài đặt riêng nếu cần

E-M1 Mark II hỗ trợ lưu cài đặt ra tệp riêng trên máy tính. Dùng chế độ USB **Storage** cho cả hai thao tác. [Tính năng sao lưu trên E-M1 Mark II](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=006722)

- **Lưu trước khi cập nhật.** Mở **Camera → Custom Settings → Save**. Chọn **Next**, chọn các nhóm cần lưu rồi chọn **Next**. Chọn nơi lưu và tên tệp, nhấn **Save** rồi **Close**. [Các bước lưu tệp](https://explore.omsystem.com/c/en/how-to-download-settings-in-your-camera)
- **Nạp lại từ tệp sau khi cập nhật nếu cần.** Chọn **Camera → Custom Settings → Load** rồi **Next**. Chọn **Load from File** rồi **Next**. Mở tệp, kiểm tra model và số sê-ri, chọn các thiết lập cần nạp rồi nhấn **Load**. Giữ nguyên cáp và nguồn, chờ máy ảnh tự khởi động lại rồi chọn **Close**. [Các bước nạp tệp](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=006722)

## 5. Tải và ghi firmware

1. Trong OM Workspace, chọn **Camera → Update**. Trên Windows, chọn **Yes** nếu hộp thoại **User Account Control** xuất hiện cho trình cập nhật. Trên macOS, nếu được yêu cầu, hãy cài và cho phép trình điều khiển máy ảnh của **OM Digital Solutions** theo chỉ dẫn của hãng. Nếu cần khởi động lại Mac, làm ngay ở bước này rồi mở lại OM Workspace. Khi cửa sổ cập nhật đã sẵn sàng, đọc các lưu ý và chọn **Next** để kiểm tra phiên bản qua Internet. [Quy trình cho E-M1 Mark II](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html) · [Hướng dẫn trình điều khiển trên Mac Apple silicon](https://explore.omsystem.com/gb/en/firmware-update-instructions-mac)
2. Xác nhận dòng **E-M1 Mark II** thuộc về thân máy, kiểm tra phiên bản hiện tại và phiên bản được đề xuất. Chọn **Details** nếu muốn xem thay đổi. Nếu ứng dụng báo đã dùng firmware mới nhất, dừng tại đây.
3. Chọn **Update**, đọc cảnh báo và xác nhận **Yes**. Đọc điều khoản sử dụng rồi chọn **Agree** nếu đồng ý.
4. Ở hộp thoại sao lưu, chọn **OK** để OM Workspace lưu cài đặt máy ảnh vào máy tính. Sau đó phần mềm tải và chuyển firmware. LCD có thể tạm thời không hiển thị nội dung ở giai đoạn lưu cài đặt hoặc truyền tệp. Theo dõi tiến độ trên máy tính.
5. Khi LCD hiện biểu tượng đang ghi firmware, chờ đến lúc chính **LCD của máy ảnh** hiện `OK`. Giữ nguyên cáp và nguồn điện, không dùng nút điều khiển, không mở nắp pin và không đóng trình cập nhật. Nếu thanh tiến độ trên máy tính đã đầy, vẫn chờ `OK` trên máy ảnh. [Các bước tải và ghi firmware từ OM System](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html)

## 6. Khởi động lại khi LCD hiện `OK`

1. Xác nhận LCD máy ảnh đã hiện `OK` và **giữ nguyên cáp USB ở cả hai đầu**.
2. Dùng công tắc nguồn trên máy ảnh để tắt rồi bật lại khi USB vẫn đang cắm. Nếu trước đây bạn gán bật/tắt nguồn cho cần **Fn**, dùng cần này khi công tắc nguồn không phản hồi.
3. Trở về cửa sổ OM Workspace, đánh dấu cả hai ô xác nhận đã cập nhật xong và đã tắt rồi bật máy ảnh. Chọn **Next** và chờ ứng dụng nạp lại cài đặt đã lưu.
4. Khi OM Workspace báo hoàn tất, chọn **Close**, sau đó ngắt cáp USB. [Các bước khởi động lại và nạp cài đặt của OM System](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a1.html)

## 7. Kiểm tra sau cập nhật

1. Vào lại **MENU → Setup Menu → Firmware** và kiểm tra **Body** hiện **3.7**, hoặc đúng phiên bản đã được OM Workspace cung cấp nếu OM System phát hành bản mới.
2. Kiểm tra ngày giờ, ngôn ngữ, C1/C2/C3 và các thiết lập đã ghi lại. Cài lại những mục bị đặt về mặc định, hoặc dùng tệp sao lưu riêng nếu có và cần nạp lại.
3. Tắt máy, lắp lại thẻ SD và ống kính nếu đã tháo. Bật lại, chụp một ảnh, kiểm tra lấy nét và mở lại ảnh vừa chụp. Nếu thường quay video hoặc dùng hai thẻ, quay một đoạn ngắn và kiểm tra máy đang ghi vào đúng khe. [Sổ tay E-M1 Mark II](https://download.omsystem.com/pages/inst/em1m2/manual_em1m2_ENU.pdf)

## Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| **Camera → Update** không nhận máy, trước khi bắt đầu cập nhật | Kiểm tra pin và trạng thái nguồn. Nối lại bằng cáp dữ liệu cắm trực tiếp, chọn **Storage** rồi nhấn **OK**. Kiểm tra **USB Mode → Auto** nếu menu USB không hiện. Thử cổng hoặc cáp dữ liệu khác nếu cần. |
| OM Workspace báo lỗi kết nối máy chủ trước khi truyền firmware | Kiểm tra kết nối Internet và phiên bản OM Workspace. Mở lại trình cập nhật sau khi xác nhận thao tác trước đã dừng và máy ảnh chưa bắt đầu ghi firmware. |
| Mac nhận máy ảnh như thiết bị lưu trữ nhưng OM Workspace báo **Failed to communicate with the camera** | Kiểm tra trình điều khiển OM Digital Solutions và quyền cho tiện ích hệ thống. Một số Mac Apple silicon có thể cần cài đặt bảo mật **Reduced Security** để bật trình điều khiển. Thực hiện theo hướng dẫn của hãng trước khi thử lại. [Hướng dẫn macOS của OM System](https://explore.omsystem.com/gb/en/firmware-update-instructions-mac) |
| LCD trống trong lúc lưu cài đặt hoặc chuyển firmware | Theo dõi tiến độ trên máy tính và giữ nguyên nguồn, cáp. Chờ máy ảnh hiển thị biểu tượng đang ghi rồi `OK`. |
| LCD đã hiện `OK` nhưng **Next** còn mờ | Giữ nguyên USB, tắt rồi bật máy ảnh và đánh dấu đủ hai ô xác nhận. Dùng cần **Fn** nếu công tắc nguồn đã được gán sang cần này. |
| Trình cập nhật báo lỗi khi đang ghi, máy chưa hiện `OK` hoặc không khởi động sau sự cố | Nếu máy còn đang cập nhật hoặc trạng thái chưa rõ, giữ nguồn và kết nối hiện có. Ghi lại nội dung lỗi, phiên bản và trạng thái LCD, rồi liên hệ bộ phận hỗ trợ camera hoặc trung tâm dịch vụ tại khu vực của bạn. [Liên hệ OM System](https://explore.omsystem.com/c/en/contact-us) |

<a id="pen-e-p7-firmware-goc"></a>

## Nếu bạn có PEN E-P7 và cần lên firmware chính thức 1.1

Kiểm tra **MENU → Setup → Firmware**. Nếu thân máy đang chạy bản chính thức cũ hơn **1.1**, ghi lại cài đặt quan trọng, tháo thẻ SD và dùng cáp dữ liệu của PEN E-P7 (**CB-USB12**, đầu USB Micro-B phía máy ảnh). Kết nối USB ở chế độ **Storage**, vào **Camera → Update** và chọn firmware **E-P7 1.1**. Chờ LCD hiện `OK`, chọn **Next** trên OM Workspace, rút cáp USB, tắt máy ảnh rồi chọn **Close**. PEN E-P7 dùng quy trình không tự sao lưu và nạp lại cài đặt. Bật máy lại để xác nhận **Body 1.1**. Nếu máy đã có bản chính thức **1.1**, bỏ qua bước cập nhật này. [Phiên bản firmware E-P7](https://support.jp.omsystem.com/en/support/imsg/digicamera/download/software/firm/e1/) · [Cáp USB E-P7](https://support.jp.omsystem.com/jp/support/cs/pen/acce/pen_usb.html) · [Quy trình chính thức cho máy không có bước sao lưu](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a2.html)

Nếu mục tiêu là cài bản sửa đổi Caduceus, tiếp tục sau khi đã xác nhận **PEN E-P7** chạy firmware chính thức **1.1**. [Hướng dẫn cài và cập nhật Caduceus cho PEN E-P7](./huong-dan-cap-nhat-firmware.md)
