# Caduceus cho Olympus OM-D E-M1 Mark II

**[English](README.md)** · **Tiếng Việt**

**Caduceus cho E-M1 II** là bản port của [Caduceus](https://github.com/cakelesscoder/caduceus-ep7) (bộ patch firmware
mã nguồn mở cho Olympus PEN E-P7) sang **Olympus OM-D E-M1 Mark II firmware 3.7** (build 3700, model 0x1250). Nó đưa
các look phim của Caduceus vào picture mode **Color Creator** của máy, qua đúng engine màu mà E-P7 dùng. Ngoài ra còn
ảnh **65:24 (XPan)** và **21:9**, quay video lâu hơn, focus stacking với mọi ống kính, và **halation** (quầng sáng có
màu quanh vùng sáng, chỉnh ở trang **Halo** của Color Creator).

Nó đọc **cùng định dạng look, cùng mã chia sẻ và cùng file trên thẻ** với bản E-P7 và OM-3, nên một look dùng được trên
mọi máy.

**Bản thử công khai: cần người thử.** Có ba bản đã sẵn sàng, mỗi bản thêm một tính năng so với bản trước; chưa bản nào
chạy trên máy thật. **[Tham gia thử](#tham-gia-thử)** · **[Changelog](patches/omdem1mk2/CHANGELOG.md)** (tiếng Anh) ·
**[Ghi chú port](docs/PORT_EM1MK2.md)** (tiếng Anh) ·
Hướng dẫn chi tiết: [tính năng, sao lưu, cài, dùng từng tính năng, khôi phục (HTML)](docs/huong-dan-firmware-em1-ii.html),
[cập nhật firmware gốc 3.7 bằng OM Workspace](docs/huong-dan-cap-nhat-firmware-om-workspace.md)

> [!WARNING]
> **Đang thử nghiệm, tự chịu rủi ro.** Đây là bản sửa firmware không chính thức, đang phát triển, cho một mẫu máy.
> Nạp firmware đã sửa có thể làm máy lỗi, treo hoặc hỏng hẳn, làm hỏng ảnh hoặc dữ liệu trên thẻ SD. **Không ai chịu
> trách nhiệm cho bất kỳ hư hỏng, mất dữ liệu hay thiệt hại nào.** Phần mềm được cung cấp "nguyên trạng", không bảo
> hành dưới bất kỳ hình thức nào (xem [Apache License 2.0](LICENSE), mục 7–8). Việc dùng có thể ảnh hưởng tới bảo hành
> của OM Digital Solutions. Đọc mục [An toàn](#an-toàn) trước khi nạp.
>
> **Chỉ dành cho E-M1 Mark II firmware 3.7.** Không bao giờ nạp bản của E-P7, OM-3 hay máy khác vào máy này, và không
> nạp bản này vào máy khác.

## Tình trạng

Ký hiệu: **[C]** = đã chạy trên E-M1 II thật; **[E]** = đã kiểm trên giả lập (chạy chính mã CPU của máy, bản patch so
với bản gốc); **[S]** = chỉ kiểm tĩnh. Chi tiết từng bản: [CHANGELOG](patches/omdem1mk2/CHANGELOG.md),
[WORKLOG](WORKLOG.md).

| Tính năng | Tình trạng |
|---|---|
| Giới hạn quay video 29 phút → 9 giờ (`rec_limit`) | [C] từ v0.1 |
| Focus stacking với mọi ống kính (`focus_stacking`) | [C] từ v0.1 |
| Look phim trong Color Creator: engine màu E-P7 (bão hoà 12 vùng, hue / light từng vùng), tone của look (highlights / midtones / shadows), Chroma, núm Highlights / Shadows, Strength x1–x3 (`color_creator_wheel`) | [C] v0.3b5: màu đổi, Velvia khớp bản xem trước của Panel, thứ tự HL/SH đúng |
| 16 look có sẵn | [C] |
| Look từ thẻ (`EM1MOD/LOOKS.BIN`, nạp ở lần nhấn nửa cò đầu tiên) (`sd_loader`) | [C] v0.4c15: file được nạp (`C1.1`); tên / màu của look trên thẻ còn phải xác nhận |
| Ảnh 65:24 và 21:9: Shooting Menu, ô và dòng tuỳ chọn trên Super Control Panel, icon, chọn điểm AF (`aspect`, `aspect_icons`) | [C] v0.4c13 |
| 65:24 / 21:9 trên live view, xem lại ảnh, RAW+JPEG, tắt bật máy khi đang chọn 6/7, dải Live Control, AF bám, lưới | chưa thử |
| Halation: quầng có màu trên ảnh JPEG màu, Off / Low / Med / High ở trang **Halo** của Color Creator (mặc định Off) (`halation`) | [E] v0.4c24: đường xử lý, pass (khớp từng bit với mô hình ở đúng địa chỉ heap ảnh của máy), trang Halo, Off = job chụp như gốc; chưa thử trên máy ([chi tiết](docs/OMD-EM1-II/HALATION.md)) |
| Watchdog 10 giây → 30 giây, để lưu ảnh lâu không làm máy khởi động lại | [E] v0.4c24 |
| Nhớ look: look Color Creator vẫn giữ sau khi tắt máy (`sd_loader`, `color_creator_wheel`) | [E] bản thử v0.4c25t |
| WB shift theo look (A-B / G-M lấy từ look; CWB và các mode khác giữ như gốc) (`look_wb`) | [E] bản thử v0.4c26t, gồm cả khối WB lúc chụp chạy thật trên giả lập ([các bước thử](docs/OMD-EM1-II/thu-may-look-wb.md)) |
| Sharpness dạng thang tuyến tính (chỉ bản thử `v0.4c19t`) | [E] |
| Blacks / Whites, look B&W thật, grain, tắt làm nét, NR theo look | chưa port |

**v0.4c16** dựng v0.4c15 trên file firmware mà server cập nhật của OM đang phát (SHA-256 `691a8a8e…`; v0.4c15 trở về
trước dựng trên `f0c25dd8…`). File này nạp Section 1 ít hơn 2 KiB lúc khởi động, khiến mã 65:24 / 21:9 không được nạp,
nên v0.4c16 thêm một chỉnh sửa để nạp lại. **v0.4c17** = v0.4c16 cộng một bản sửa Color Creator: look trên thẻ nạp sau
khi đã mở trình chỉnh giờ hiện đúng màu của nó, không phải màu của look có sẵn. Cả hai đạt mọi bước kiểm giả lập [E];
chưa bản nào chạy trên máy.

**v0.4c24** = v0.4c17 cộng halation, trang Halo của Color Creator và watchdog 30 giây. Halo bắt đầu ở **Off**: khi đó các
job chụp trên giả lập giống bản gốc, nên máy chụp như v0.4c17 cho tới khi bật Halo, và nếu halation có lỗi thì đặt Halo
về Off là xong. Lúc khởi động nó chỉ thêm watchdog 30 giây và một vùng nạp 100 KB mà bản dò sp1 đã dùng an toàn trên máy
(không có gì khác trong file 3.7 hiện tại dùng vùng nhớ đó). Seal với 21 bước kiểm; chưa nạp lên máy. Lần đầu nên nạp
file khôi phục gốc một lần (bước 0 trong hướng dẫn), rồi mới nạp v0.4c24.

**v0.4c25t** = v0.4c24 cộng nhớ look (sid 965). **v0.4c26t** = v0.4c25t cộng WB shift theo look, và trình chỉnh giờ tắt
look trước khi đổi look, để không tấm chụp nào ghép trạng thái của look này với look khác. Cả hai là bản thử trên máy,
seal với mọi bước kiểm của bản trước cộng harness riêng của nó.

## Tham gia thử

Các bản dưới đây đã qua mọi bước kiểm trên giả lập nhưng **chưa chạy trên máy thật**. Người thử nạp và báo lại kết quả
sẽ quyết định những gì vào bản phát hành đầu tiên. Đi **từng bước một**: chỉ nạp bản tiếp theo khi bản trước đã chạy tốt
trên máy bạn.

| Bước | Bản | Thêm gì | Kiểm gì (hướng dẫn từng bước) |
|---|---|---|---|
| 0 | `restore` (file 3.7 gốc của OM) | không gì cả: bắt đầu sạch | máy khởi động và chụp như trước |
| 1 | **v0.4c24** | halation (trang Halo, mặc định Off), watchdog 30 giây, trên nền look / XPan / 21:9 / video 9 giờ / focus stacking | [thu-may-halation.md](docs/OMD-EM1-II/thu-may-halation.md) |
| 2 | **v0.4c25t** | look Color Creator được nhớ sau khi tắt máy | [thu-may-nho-look.md](docs/OMD-EM1-II/thu-may-nho-look.md) |
| 3 | **v0.4c26t** | áp WB shift của từng look màu (năm look có sẵn đổi màu: Nostalgic, Gold 200, Kodachrome64, Portra 400, CineStill800) | [thu-may-look-wb.md](docs/OMD-EM1-II/thu-may-look-wb.md) |

**Báo kết quả** từng bước trong [Issues](https://github.com/xtruong88/caduceus-em1ii/issues): tên bản, bạn đã làm gì,
kết quả ra sao (chạy tốt / có gì lạ / treo), và các ảnh JPEG mà hướng dẫn yêu cầu. Báo treo máy hoặc không khởi động
được là có ích nhất: ghi rõ thao tác cuối cùng bạn đã bấm.

## Cài đặt

Cần có: E-M1 Mark II firmware **3.7** (Setup › Firmware), **pin đầy**, thẻ SD ở **khe 1**, và **Python 3** trên máy
tính (Windows: tải ở [python.org](https://www.python.org/downloads/), nhớ tick "Add python.exe to PATH"). Không cần
trình biên dịch hay công cụ nào khác.

1. **Cập nhật lên firmware gốc 3.7 trước** nếu máy đang ở bản cũ hơn (dùng OM Workspace, xem hướng dẫn ở trên).
2. **Tải repo này:** `git clone https://github.com/xtruong88/caduceus-em1ii`, hoặc bấm **Code › Download ZIP** (hoặc
   "Source code (zip)" trong [Releases](https://github.com/xtruong88/caduceus-em1ii/releases)) rồi giải nén.
3. **Dựng file cập nhật** trong thư mục đó (Windows: mở PowerShell trong thư mục; macOS / Linux: dùng `python3` thay cho
   `py`). Công cụ tự tải file 3.7 gốc từ server của OM, kiểm mã hash, áp bản bạn chọn, rồi ghi ra các file cho thẻ và
   một file khôi phục gốc:

   ```powershell
   py caduceus.py build --camera em1mk2 --release v0.4c24 --out out/em1mk2-thu-may/4-v0.4c24
   py caduceus.py verify out/em1mk2-thu-may/4-v0.4c24
   ```

   Ở các bước sau dùng `--release v0.4c25t --out out/em1mk2-thu-may/5-v0.4c25t` và
   `--release v0.4c26t --out out/em1mk2-thu-may/6-v0.4c26t`: các hướng dẫn thử dùng đúng tên thư mục này.

   `verify` phải kết thúc bằng `All good.`. Nếu đã có sẵn file của OM (`OLY_E_125_3700_0000_0000.BIN`), thêm
   `--stock <đường dẫn tới file>` vào lệnh `build`.
4. **Chép vào thẻ SD:** `DCOLYMP/E1259999.BIN` và (không bắt buộc, để dùng look trên thẻ) `EM1MOD/LOOKS.BIN`. Giữ
   `restore/E1259999.BIN` cẩn thận trên máy tính.
5. **Nạp:** thẻ ở khe 1, giữ nút **OK** rồi bật máy. Đèn sáng liên tục khi đang ghi và nhấp nháy (~2 lần/giây) khi
   xong. Không tắt máy hay mở nắp pin khi đang ghi.
6. **Chụp:** đặt picture mode là **Color Creator**. Sau khi bật máy, nhấn nửa cò một lần (để nạp look từ thẻ), rồi mở
   Color Creator để chọn và chỉnh look.

**Quay về firmware gốc:** nạp `restore/E1259999.BIN` theo cùng cách (đó là file của OM, không sửa gì).

**Vì sao không có sẵn file `.BIN` để tải?** Giấy phép của OM cấm phân phối lại firmware của họ, nên các bản phát hành
chỉ chứa danh sách chỉnh sửa và file thẻ của Caduceus. Công cụ áp chúng vào bản firmware của OM mà nó tải về giúp bạn.

## Cách dùng

- **Trình chỉnh Color Creator:** tên look và một dòng trạng thái hiện ở dưới cùng. INFO để chuyển trang (look, Chroma,
  Highlights / Shadows, Strength); xoay núm để đổi giá trị.
- **Mã trên dòng trạng thái:** `C1.n` đã nạp look từ thẻ (n = số lần thử), `C0.n` đang thử, `CF.8` không có
  `LOOKS.BIN`, `CF.1` file hỏng; `K<hex>` = mã look đang dùng (`+` khi đã áp); ` Exx` = một lần ghi setting bị từ chối.
- **Tự làm look:** chạy Control Panel trong repo này (`webapp/`), chọn máy **E-M1 II** rồi xuất `LOOKS.BIN` vào thư mục
  `EM1MOD/` trên thẻ. Pack và mã chia sẻ giống hệt E-P7. (Panel E-P7 trên web chưa có E-M1 II cho tới khi phần xuất
  được gộp vào upstream.)
- **Tỉ lệ ảnh:** Shooting Menu 1 › Image Aspect, hoặc ô tỉ lệ trên Super Control Panel. 65:24 chụp 5184x1920, 21:9 chụp
  5184x2224.
- **Halation:** trong trình chỉnh Color Creator, bấm INFO tới trang **Halo**, Trái / Phải để chọn Off / Low / Med / High
  (giữ qua khi tắt máy). Áp cho ảnh JPEG màu thông thường (không áp cho Monotone, Art Filter, Art Effect hay các chế độ
  chụp đặc biệt). Cảnh đêm có đèn sẽ lưu lâu hơn vài giây.

## An toàn

- **Không ai chịu trách nhiệm cho bất kỳ hư hỏng nào.** Bạn tự chịu rủi ro khi nạp.
- Chỉ hỗ trợ E-M1 Mark II firmware **3.7**. Công cụ từ chối mọi file gốc khác.
- Mọi patch đều chạy trên giả lập CPU của máy trước khi một bản được đưa lên máy (quy tắc trong
  [AGENTS.md](AGENTS.md)). Giả lập không bao gồm driver thẻ SD thật, bước chép flash lúc khởi động, màu ảnh hay những
  gì màn hình vẽ: những điều đó chỉ được chứng minh khi thử trên máy, và bảng Tình trạng ghi rõ.
- Pin đầy và quá trình ghi không bị gián đoạn là bắt buộc. Ghi hỏng có thể làm máy không khởi động được.
- **Thẻ không có thư mục `EM1MOD`** = chỉ còn look có sẵn, tuỳ chọn tỉ lệ ảnh, giới hạn quay dài hơn và focus stacking.
  Nếu có gì bất thường, bỏ `EM1MOD` trước; nếu vẫn không được, nạp file khôi phục.

## Cách hoạt động

- **Repo này không chứa firmware của OM.** Công cụ tải file chính thức của OM và kiểm mã hash.
- Các patch (`patches/omdem1mk2/`) là những đoạn assembly MN103 nhỏ và chỉnh sửa dữ liệu. Mỗi script build kiểm từng
  byte gốc mà nó thay, và chỉ đặt mã vào những section mà máy thật sự nạp (`tools/omdem1mk2_check_loaded.py`).
- `tools/omdem1mk2_make_release_edits.py <VERSION>` build lại mọi patch, chạy kiểm vùng nạp và kiểm opcode, rồi seal
  bản phát hành vào `releases/em1mk2/<VERSION>/`.
- Các harness giả lập (`tools/omdem1mk2_emu_*.py`) chạy chính mã của máy từ firmware đã giải mã, bản patch so với bản
  gốc: trình nạp thẻ, ô Super Control Panel, hiển thị AF, quy tắc ràng buộc, kiểm giá trị setting, WB theo look.
- Trạng thái lúc chạy nằm trong một khối heap (`patches/omdem1mk2/p_layout.inc`), không bao giờ nằm trong image
  firmware hay bảng RAM gốc.
- Bố cục firmware và bằng chứng: [docs/OMD-EM1-II/](docs/OMD-EM1-II/), [docs/PORT_EM1MK2.md](docs/PORT_EM1MK2.md).

## Cho nhà phát triển

Công cụ build cần Linux (hoặc WSL / container Linux trên Windows):

```bash
git clone --recurse-submodules https://github.com/xtruong88/caduceus-em1ii
cd caduceus-em1ii
tools/setup_toolchain.sh   # GNU binutils cho mn10300 (assembler / linker)
python3 external/oly_fw_analysis/tools/build_mn103_emulator.py --archive <file binutils-gdb, xem docs/tooling/EMULATOR.md của nó>
python3 external/oly_fw_analysis/tools/om_firmware_catalog.py --model-id 1250 --model-name "E-M1 Mark II" \
  --installed 00001000 --download --out cache/catalog     # file 3.7 của OM; chép vào stock_firmware/
python3 external/oly_fw_analysis/tools/oly_container.py stock_firmware/OLY_E_125_3700_0000_0000.BIN \
  --code-base 0x60021020 --out em1mk2/extracted
python3 patches/omdem1mk2/color_creator_wheel/build.py   # chỉnh sửa Color Creator (edits.json)
EM1_CC_HALO=1 python3 patches/omdem1mk2/color_creator_wheel/build.py   # như trên, có trang Halo (edits_halo.json)
python3 patches/omdem1mk2/halation/build.py               # chỉnh sửa halation (mức lấy từ trang Halo)
python3 tools/omdem1mk2_catalog_release.py --stock stock_firmware/OLY_E_125_3700_0000_0000.BIN --version v0.4c24
                                           # seal trên file catalog của OM; chạy check_loaded, audit và mọi emu_* trước
python3 -m unittest tools/test_caduceus_releases.py
```

Trước khi port hay patch, đọc [docs/FIRMWARE_GUIDE.md](docs/FIRMWARE_GUIDE.md) và [AGENTS.md](AGENTS.md): giữ đúng định
dạng look và mã chia sẻ chung.

## Ghi công

- **[cakelesscoder/caduceus-ep7](https://github.com/cakelesscoder/caduceus-ep7):** chính Caduceus (E-P7), định dạng look,
  Control Panel, đường đi của engine màu và bộ công cụ build / an toàn mà bản port này dựa vào.
- [androidfanman/caduceus-om3](https://github.com/androidfanman/caduceus-om3): bản port cho OM-3, tài liệu tham khảo khi
  port sang máy khác.
- [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis): nghiên cứu firmware và bộ giả lập MN103 (dùng
  làm submodule).
- Bản mod firmware HSL cho PEN-F của u/fischgurke, nơi dự án Caduceus bắt đầu; LightSnowDev, Altsoph/mx3 (diễn đàn
  CHDK), các thread Olympus trên DVXuser và Personal View, và iKenndac với các nghiên cứu firmware Olympus trước đó.

## Giấy phép

Mã patch, công cụ và tài liệu phát hành theo [Apache License 2.0](LICENSE). Firmware của OM không được đưa vào hay phân
phối lại: công cụ tải nó từ server của OM ngay trên máy bạn. Submodule `external/oly_fw_analysis` giữ giấy phép riêng.
Xem [NOTICE](NOTICE).

Không liên kết với OM Digital Solutions. "Olympus", "OM-D" và tên các loại phim là thương hiệu của chủ sở hữu tương ứng.
