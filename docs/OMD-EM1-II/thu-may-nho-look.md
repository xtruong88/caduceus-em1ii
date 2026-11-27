# Thử trên máy: v0.4c25t, nhớ look sau khi tắt máy (E-M1 Mark II)

Bản thử v0.4c25t = v0.4c24 cộng **một** tính năng: máy nhớ look đã chọn trong Color Creator và áp lại sau khi tắt rồi
bật máy. Bản này chỉ dùng để thử: chỉ nạp **sau khi v0.4c24 đã chạy tốt trên máy**
([thu-may-halation.md](thu-may-halation.md)). Cách nạp và khôi phục theo
[huong-dan-firmware-em1-ii.html](../huong-dan-firmware-em1-ii.html).

## Cách hoạt động

- Khi bạn đổi look bằng phím mũi tên trong trình chỉnh Color Creator, máy ghi look đó vào một setting còn trống (sid
  965). Setting này nằm cùng khối với các setting mà máy gốc vẫn nhớ khi tắt máy.
- Sau khi bật máy:
  - lần **nhấn nửa cò đầu tiên** sẽ dựng lại look trong RAM;
  - nếu bạn mở trình chỉnh Color Creator trước khi nhấn nửa cò, look được dựng lại ngay lúc mở.
  Tone (Highlights/Shadows) và vividness là setting gốc, nên máy vẫn tự nhớ như trước. Với look màu, máy ghi lại
  vividness đúng bằng giá trị đang có, một lần, giống trình chỉnh vẫn làm. Lần ghi này buộc live view vẽ lại, nên look
  hiện lên live view ngay.
- **Look trên thẻ** chỉ được dựng lại sau khi máy đọc xong `LOOKS.BIN`, tức ở lần nhấn nửa cò nạp được thẻ. Nếu thẻ
  không có pack, hoặc pack có ít look hơn số đã nhớ, máy bỏ qua và chạy như v0.4c24.
- Không nhớ: Strength (luôn về x1), Chroma (về 0).
- Nếu bạn chọn một look có sẵn trước khi máy đọc thẻ, lần mở trình chỉnh sau khi thẻ đã đọc sẽ tự chuyển sang look
  đầu tiên trên thẻ (như v0.4c24). Look được nhớ lúc đó là look trên thẻ ấy.
- Reset toàn bộ máy sẽ xoá look đã nhớ. Khi đó máy chạy như v0.4c24.

## Đã kiểm trên giả lập

Seal chạy mọi bước kiểm của v0.4c24, cộng `tools/omdem1mk2_emu_look_memory.py`:
- **sid 965:** lưu và đọc lại 0..64; giữ được qua cả ba đường reset lúc khởi động; không làm đổi sid 961 (Halo),
  964 và 966;
- **nhấn nửa cò:** dựng lại look có sẵn, look trên thẻ, và look đơn sắc. Kết quả trong RAM giống hệt lúc chọn bằng
  phím mũi tên;
- **khi chưa dựng được:** thẻ chưa đọc thì chờ tới lần sau; thẻ hỏng hoặc vượt số look thì bỏ qua; giá trị sai thì bỏ
  qua;
- **khi dựng lại:** look màu ghi lại đúng một setting (vividness, cùng giá trị) và không đổi setting nào; look đơn sắc,
  các trường hợp bỏ qua và giá trị sai không ghi gì;
- bản không có tính năng này (gốc, v0.4c24) thì không đổi gì.

**Chưa kiểm được:**
- flash có thật sự ghi setting khi tắt máy không;
- live view có vẽ lại thật không (giả lập không có live view);
- lần ghi vividness từ task xử lý nửa cò. Firmware gốc có thể chưa bao giờ ghi setting từ task này. Phần báo thay đổi
  sau khi ghi chỉ gửi đi một message, nhưng chỉ thử trên máy mới chắc chắn.

## Các bước thử

1. Nạp `out/em1mk2-thu-may/5-v0.4c25t`, khởi động, chụp thử một ảnh.
2. Chế độ Color Creator, mở trình chỉnh. Dùng mũi tên chọn **Velvia** (pack trên thẻ) hoặc **Cl. Chrome** (look có sẵn).
   Chụp một ảnh A.
3. Tắt máy, đợi 5 giây, bật lại. **Không** mở trình chỉnh. Nhấn nửa cò rồi chụp ảnh B cùng cảnh.
   - Đạt: ngay sau lần nhấn nửa cò đầu, live view đổi sang màu của look; ảnh B có màu như ảnh A (Velvia bão hoà rõ
     hơn Provia).
   - Nếu nhấn nửa cò mà máy khựng hoặc treo: tháo pin, rồi nạp lại v0.4c24. Lỗi này nghĩa là không được ghi setting từ
     lúc nhấn nửa cò; khi đó bản sau sẽ chuyển bước làm mới live view sang lúc mở trình chỉnh.
   - Nếu live view chưa đổi mà ảnh B đúng: ghi lại. Xoay núm vividness một nấc rồi xoay lại, live view phải đổi.
4. Mở trình chỉnh: tên look phải là look đã chọn ở bước 2, không phải look đầu danh sách.
5. Thử thêm: chọn một look đơn sắc (Tri-X 400), tắt rồi bật máy. Ảnh vẫn gần đen trắng, và trình chỉnh hiện đúng tên.
6. Chuyển sang Natural rồi chụp: ảnh như máy gốc. Chuyển lại Color Creator: look vẫn được áp.

Nếu có gì lạ: nạp lại v0.4c24 (look đã nhớ chỉ là một setting không ai đọc, nên không ảnh hưởng gì). Nếu máy không
khởi động: nạp `restore/E1259999.BIN`.
