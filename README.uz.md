# CleanGuard Professional — Windows Tizimini Tozalash, Tezlashtirish va Xavfsizlik Majmuasi

<div align="center">

![CleanGuard Logo](https://img.shields.io/badge/CleanGuard-Professional-0078D7?style=for-the-badge&logo=windows&logoColor=white)
![Platform](https://img.shields.io/badge/Platforma-Windows%207%20SP1%20%7C%208%20%7C%208.1%20%7C%2010%20%7C%2011-0078D7?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Litsenziya](https://img.shields.io/badge/Litsenziya-MIT-green?style=for-the-badge)
![Arxitektura](https://img.shields.io/badge/Arxitektura-x86%20%7C%20x64%20%7C%20ARM64-lightgrey?style=for-the-badge)

**Yangi avlod, xavfsizlikka asoslangan professional Windows tozalash, tezlashtirish, maxfiylik va texnik xizmat ko'rsatish dasturi.**

[ 🇺🇿 O'zbekcha ](README.uz.md) &nbsp; | &nbsp; [ 🇷🇺 Русский ](README.ru.md) &nbsp; | &nbsp; [ 🇬🇧 English ](README.md)

</div>

---

## 🌟 Loyiha Haqida

**CleanGuard** — bu Windows operatsion tizimi uchun mo'ljallangan, korporativ darajadagi xavfsizlik kafolatlariga ega bo'lgan ochiq kodli tizim tozalash va optimallashtirish dasturi. Tizim fayllarini tavakkaliga o'chirib, Windows barqarorligiga xavf soluvchi an'anaviy tozalagichlardan farqli ravishda, CleanGuard **"Arxitektura darajasidagi xavfsizlik" (Safety-by-Architecture)** tamoyili asosida ishlaydi: har bir o'chirilishi kerak bo'lgan fayl va reestr yozuvi qat'iy tekshiruvdan, cheklovlar filtrlashidan o'tadi va faqat tizim xavfsizligiga ziyon yetkazmasligi tasdiqlangandagina o'chiriladi.

Dastur tarkibida **15 ta ixtisoslashtirilgan mustaqil modul** mavjud bo'lib, ular xotirani bo'shatish, dublikat fayllarni qidirish, gigant va katta fayllar tahlili, avtomatik zaxira nusxasi bilan reestrni xavfsiz tozalash, 1-bosishli Smart Care majmuasi, avto-yuklanishni sozlash, keraksiz ilovalar va telemetriyani o'chirish, Windows Update va WinSxS keshini tozalash (DISM), internet tezligini oshirish hamda kompyuter qurilmalari holatini real vaqtda monitoring qilishni ta'minlaydi.

---

## 🛡️ Asosiy Xavfsizlik Arxitekturasi

CleanGuard operatsion tizimning 100% barqaror va xavfsiz qolishini kafolatlash uchun bir qator qat'iy mexanizmlarni qo'llaydi:

1. **PathGuard Himoya Tizimi**:
   - `C:\Windows`, `System32`, `SysWOW64`, `WinSxS`, `Boot`, `Program Files` va boshqa muhim tizim papkalarini qat'iy bloklaydi.
   - Foydalanuvchining shaxsiy papkalariga (`Ish stoli`, `Hujjatlar`, `Rasmlar`, `Videolar`, `Musiqa`, `Yuklab olinganlar`) mutlaqo daxl qilmaydi.
   - Har bir fayl yo'lini kanoniklashtiradi (`GetFinalPathNameByHandleW`) va symlink, junction yoki hardlink orqali tizim fayllariga yo'naltirilgan yolg'on ssilkalarni aniqlab rad etadi.
2. **TOCTOU (Time-of-Check to Time-of-Use) Himoyasi**:
   - Faylni skanerlash va o'chirish vaqtlari oralig'ida uning holati yoki ruxsatnomalari o'zgarmaganligi to'g'ridan-to'g'ri o'chirishdan oldin qayta tekshiriladi. Agar zarracha shubha bo'lsa, jarayon to'xtatiladi.
3. **Avtomatik Tiklash va Qaytarish (Rollback)**:
   - **Tizimni Qayta Tiklash Nuqtasi (System Restore Point)**: Har qanday yirik tozalashdan avval Windows VSS xizmati orqali rasmiy tizim tiklash nuqtasini hosil qiladi.
   - **Reestr Rollback**: Reestr kalitlarini tozalashdan avval barcha o'zgarishlarning vaqt belgisi qo'yilgan `.reg` zaxira nusxasini avtomatik yaratadi va 1 ta tugma orqali ortga qaytarish imkonini beradi.
4. **3 Bosqichli Xavf Tasnifi Modeli**:
   - 🟢 `XAVFSIZ (SAFE)`: Dastur kesh fayllari, vaqtinchalik fayllar va 24 soatdan eski miniatyuralar.
   - 🟡 `KO'RIB CHIQISH (REVIEW)`: Tizim loglari, xato hisobotlari va brauzer ma'lumotlari (foydalanuvchi tasdig'i bilan).
   - 🔴 `BLOKLANGAN (BLOCKED)`: Tizim hayotiy fayllari, o'chirilishi qat'iyan man etilgan obyektlar.

---

## 🚀 15 Ta Asosiy Modul Tavsifi

```text
CleanGuard Majmuasi
├── 📊 01. Dashboard              ── Tizim holati, 1-Bosishli Smart Care va disk sig'imlari
├── 🧹 02. Chuqur Tozalash        ── Ko'p oqimli kesh va chiqindi fayllar skaneri
├── 🔍 03. Dublikatlar Qidiruvchi ── MD5/SHA256 xeshli ikki bosqichli dublikat skaneri
├── 🐘 04. Katta Fayllar Tahlili   ── 100MB+ va 1GB+ joy oluvchi fayllar va SafetyEngine
├── 🛡️ 05. Reestr Tozalash        ── Zaxira nusxa va 1 tugmali rollback bilan xavfsiz reestr
├── 📦 06. Dasturlarni O'chirish  ── Win32 va UWP dasturlarni to'liq qoldiqlari bilan o'chirish
├── 🚀 07. Avto-Yuklanish         ── Run, Startup va Task Scheduler dasturlarini boshqarish
├── ⚡ 08. Turbo RAM Booster      ── Working Set va Standby keshni tozalab RAMni bo'shatish
├── 🌐 09. Tarmoq Tezlatgich      ── DNS flush, Winsock reset, TCP tuning va DNS benchmark
├── 🛠️ 10. Tizim va WinSxS        ── Bloatware o'chirish, telemetriya bloklash va Windows Update (DISM)
├── 💻 11. Qurilmalar Monitori    ── Real vaqtda CPU, GPU, RAM, Disklarning to'liq ma'lumotlari
├── ⏰ 12. Avtomatik Xizmat       ── Windows vazifalar rejalashtiruvchisi (Task Scheduler)
├── 🔄 13. Tiklash Nuqtasi        ── Windows VSS tizim tiklash nuqtasini hosil qilish
├── 📜 14. Tarix va Audit         ── SQLite WAL bazasi va CSV/JSON hisobot eksporti
└── 🎨 15. Fluent Zamonaviy UI    ── High-DPI qorong'u interfeys va dinamik 3 tilli tizim
```

### 1. 📊 Asosiy Boshqaruv Paneli va 1-Bosishli Smart Care
- Kompyuterdagi barcha mahalliy disklarning (C:, D:, va h.k.) bandlik darajasini grafik shaklda ko'rsatadi.
- Tizimning umumiy xavfsizlik va tozalik reytingi, operativ xotira yuklamasi va markaziy skanerlash tugmasi.
- **⚡ 1-Bosishli Smart Care**: Yagona tugma bilan avtomatlashtirilgan to'liq texnik xizmat: Chiqindi fayllarni tozalash + Xavfsiz reestrni ta'mirlash + RAM keshini bo'shatish + DNS keshini tozalash + Windows Update keshini tozalash. Real vaqt jarayon indikatori va yakuniy hisobot modali bilan.

### 2. 🧹 Chuqur Tozalash Dvigateli (Deep Cleaner)
- Ko'p oqimli parallel skanerlash:
  - **Foydalanuvchi va Tizim Vaqtinchalik Fayllari**: `%TEMP%`, `Windows\Temp`.
  - **Ilova va DirectX Keshlar**: DirectX Shader Cache, D3DSCache, Delivery Optimization.
  - **Windows Miniatyura Keshlari**: `thumbcache_*.db` va piktogramma keshlar.
  - **Xatolar Hisobotlari va Tizim Damplari**: `MEMORY.DMP`, minidamplar, WER va CBS loglari.
  - **Veb Brauzerlar Keshi**: Chrome, Edge, Firefox, Brave, Opera (parollar, sessiyalar va cookie fayllariga tegilmaydi).
  - **Savatcha (Recycle Bin)**: Har bir disk bo'yicha savatcha hajmi tahlili.

### 3. 🔍 Dublikat Fayllarni Qidiruvchi (Duplicate Finder)
- Ikki bosqichli yuqori tezlikdagi tahlil:
  1. Dastlabki o'lcham va 4KB boshlang'ich baytlar xeshini solishtirish.
  2. To'liq MD5 va SHA256 kriptografik xeshlash orqali 100% aniqlik.
- Dublikatlarni guruhlab ko'rsatish va aqlli tanlash (eng eskisini qoldirish, eng yangisini qoldirish).
- PathGuard orqali tizim va dastur fayllari xatolik bilan o'chirilishining oldi olinadi.

### 4. 🐘 Katta Fayllar Tahlili (Large Files Finder)
- Disklardagi eng ko'p joy egallagan gigant fayllarni aniqlaydi (>100 MB, >500 MB, >1 GB, >5 GB).
- Fayllarni toifalar bo'yicha ajratadi:
  - 🎬 **Videolar** (`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`)
  - 🎵 **Audiolar** (`.mp3`, `.wav`, `.flac`, `.aac`)
  - 📦 **Arxivlar va ISO** (`.zip`, `.rar`, `.7z`, `.iso`, `.img`)
  - 💿 **Virtual Mashina Disklari** (`.vmdk`, `.vhd`, `.vhdx`)
  - 📄 **Hujjatlar va Zaxira Bazalar** (`.pdf`, `.docx`, `.bak`, `.sql`)
  - ⚙️ **O'rnatuvchi Dasturlar** (`.exe`, `.msi`, `.cab`)
- **SafetyEngine Himoyasi**: Tizim yadro fayllari (`pagefile.sys`, `swapfile.sys`, `hiberfil.sys`, `C:\Windows\*`) xatolik bilan o'chirilishining oldi qat'iy olingan.
- **"Explorerda Ko'rsatish"** (`explorer.exe /select`) va xavfsiz o'chirish imkoniyati.

### 5. 🛡️ Tizim Reestrini Xavfsiz Tozalovchi (Registry Cleaner)
- Noto'g'ri va eskirib qolgan reestr yozuvlarini tahlil qiladi:
  - Noto'g'ri CLSID va COM/ActiveX kalitlari.
  - Yo'qolgan ilovalarning buzilgan fayl assotsiatsiyalari.
  - Tizimdan o'chirilgan umumiy DLL kutubxona havolalari.
  - O'chirilgan dasturlarning reestrdagi qoldiqlari.
- **Nol Xavf Kafolati**: Tozalashdan oldin avtomatik ravishda `.reg` fayliga zaxira nusxa olinadi va bir bosishda qaytarish mumkin.

### 6. 📦 Dasturlarni O'chirish va Qoldiqlarni Yo'qotish (Uninstaller)
- Klassik Windows (Win32) dasturlari va zamonaviy UWP ilovalarini yagona ro'yxatda taqdim etadi.
- Standart va fon rejimida (silent) dasturlarni olib tashlashni qo'llab-quvvatlaydi.
- **Chuqur Qoldiqlarni Qidiruvchi**: Dastur o'chirilgandan so'ng `%AppData%`, `%LocalAppData%`, `Program Files` va Reestrdagi qoldiq axlatlarni avtomatik aniqlaydi va tozalaydi.

### 7. 🚀 Avto-Yuklanish Menejeri (Startup Manager)
- Windows ishga tushganda avtomatik yuklanadigan HKCU/HKLM `Run`, `RunOnce`, Startup papkalari va Task Scheduler vazifalarini to'liq ko'rsatadi.
- Har bir dasturning kompyuter yuklanishiga ta'sirini (Yuqori, O'rta, Past) tahlil qiladi.
- Dasturlarni o'chirish, yoqish yoki kechiktirib ishga tushirish imkoniyati.

### 8. ⚡ Turbo Tezlashtirish va RAM Optimizatsiyasi
- Win32 `EmptyWorkingSet` tizim API funksiyasi orqali ishlaydi.
- Ochiq turgan dasturlarni yopmasdan va ma'lumotlarni yo'qotmasdan operativ xotiradagi (RAM) bo'sh turgan zaxira keshini tozalaydi.

### 9. 🌐 Tarmoq va Internet Tezlatgich (Network Booster)
- **DNS Keshini Tozalash** (`ipconfig /flushdns`): Eski va noto'g'ri yo'naltirilgan IP keshlarini yangilaydi.
- **Winsock Katalogini Qayta Tiklash** (`netsh winsock reset`): Tarmoq protokollari xatolarini tuzatadi.
- **TCP/IP Stack Avtomatik Sozlash**: O'yinlar va internet ko'rishda ping (latency) va buferlanishni optimallashtiradi.
- **Jonli DNS Benchmark**: Dunyodagi eng tezkor xavfsiz DNS serverlar (Cloudflare `1.1.1.1`, Google `8.8.8.8`, OpenDNS `208.67.222.222`) tezligini o'lchab, millisekundlarda taqqoslaydi.

### 10. 🛠️ Windows Tizim Sozlamalari va WinSxS (Tweaks & Updates)
- **Windows Update Keshini Tozalash**: Eskirgan yangilanish fayllarini `SoftwareDistribution\Download` va `DeliveryOptimization` papkalaridan xavfsiz tozalaydi.
- **WinSxS Komponentlar Ombori (DISM)**: Rasmiy Microsoft `dism.exe /Online /Cleanup-Image /StartComponentCleanup` orqali eskirgan Windows paketlari va xizmat fayllarini siqib, 10–25+ GB gacha joy bo'shatadi.
- **Keraksiz Tizim Dasturlarini O'chirish (Bloatware)**: Windows bilan birga o'rnatiladigan ortiqcha UWP ilovalarni (Cortana, Bing News, Xbox telemetriyasi, Solitaire va b.) oson o'chiradi.
- **Telemetriya va Kuzatuvni Bloklash**: Microsoft DiagTrack va Connected User Experiences kabi josuslik xizmatlarini to'xtatadi.
- **Boshqaruv Paneli (Start Menu) Sozlash**: Windows menyusidagi Bing internet qidiruvini va reklamalarni olib tashlaydi.
- **O'yin Rejimi**: GPU yuklamasini va sichqoncha tezlanishini o'yinlar uchun moslashtiradi.

### 11. 💻 Qurilmalar Holati Monitoringi (Hardware Monitor)
- Real vaqtda barcha texnik qismlarni nazorat qiladi:
  - **Protsessor (CPU)**: Model, arxitektura, yadrolar soni va joriy yuklanish foizi.
  - **Xotira (RAM)**: Umumiy, band va bo'sh hajm, real vaqt grafigi.
  - **Videokarta (GPU)**: Model, drayver versiyasi, xotira hajmi.
  - **Qattiq Disklar**: Disk modellari, ularning turlari (SSD, NVMe, HDD), bo'sh va to'liq hajmi.
  - **Ona plata va BIOS**: Ishlab chiqaruvchi, model va BIOS versiyasi.
  - **Operatsion Tizim**: Windows nashri, yig'ma raqami (masalan, 22631) va arxitekturasi.

### 12. ⏰ Avtomatik Xizmat Rejalashtiruvchisi (Auto-Care)
- Windows Task Scheduler bilan integratsiya qilingan.
- Tozalashni belgilangan vaqtda (Har kuni, Haftada bir marta yoki Kompyuter bo'sh turganda) avtomatik bajaradi.
- Interfeyssiz fon rejimida (`--auto-clean`) xavfsiz tozalashni amalga oshiradi.

### 13. 🔄 Tizimni Qayta Tiklash Nuqtasi (System Restore Point)
- Windows VSS xizmati orqali har qanday xavfli tozalashdan avval rasmiy tiklash nuqtasini hosil qiladi.
- Foydalanuvchiga to'liq xotirjamlik va ishonchlilik kafolatini beradi.

### 14. 📜 Audit Tarixi va Hisobotlar
- Har bir tozalash tafsilotlari mahalliy SQLite ma'lumotlar bazasida **WAL (Write-Ahead Logging)** rejimida qayd etiladi.
- Umumiy tejalgan xotira hajmi va o'chirilgan fayllar statistikasi.
- Natijalarni **CSV** va **JSON** formatlarida hisobot sifatida eksport qilish imkoniyati.

### 15. 🎨 Fluent Zamonaviy UI va 3 Tilli Tizim
- Windows Fluent Design tamoyillari asosida yaratilgan zamonaviy quyuq (dark mode) interfeys.
- Dasturni qayta ishga tushirmasdan bir zumda tilni almashtirish imkoniyati:
  - 🇺🇿 **O'zbekcha** (Asosiy til)
  - 🇷🇺 **Русский**
  - 🇬🇧 **English**

---

## 💻 O'rnatish va Ishga Tushirish

### Minimal Talablar
- **Operatsion Tizim**: Windows 7 SP1, Windows 8, Windows 8.1, Windows 10 yoki Windows 11 (32-bit yoki 64-bit)
- **Python**: 3.8 yoki undan yuqori versiya
- **Huquqlar**: Barcha funksiyalar va reestrni boshqarish uchun Administrator huquqlari tavsiya etiladi.

### 1. Repozitoriyni Ko'chirib Olish va O'rnatish

```powershell
# Repozitoriyni klonlash
git clone https://github.com/Valijon21/cleaner_win.git
cd cleaner_win

# Virtual muhitni yaratish va faollashtirish
python -m venv .venv
.\.venv\Scripts\activate

# Kerakli kutubxonalarni o'rnatish
pip install -r requirements.txt
```

### 2. Dasturni Ishga Tushirish

```powershell
# To'liq grafik interfeysni ishga tushirish
python -m cleanguard.app.main
```

### 3. Fonsiz Avtomatik Rejim (Headless Auto-Clean)

CleanGuard dasturini grafik interfeys ochmasdan to'g'ridan-to'g'ri fonda xavfsiz tozalash uchun ishga tushirish:

```powershell
# Faqat xavfsiz (SAFE) toifadagi fayllarni fonda tozalash
python -m cleanguard.app.main --auto-clean
```

---

## 🧪 Avtomatlashtirilgan Sinovlar (Testing)

Loyihada xavfsizlik, xeshlar, reestrni qaytarish, 1-bosishli Smart Care, Windows Update DISM tozalash, katta fayllar tahlili va interfeys bo'yicha 28 ta keng qamrovli test to'plamlari (**132 ta muvaffaqiyatli test**) mavjud:

```powershell
# Sinov kutubxonalarini o'rnatish
pip install -r requirements-dev.txt

# Barcha 132 ta testlarni ishga tushirish
pytest -v tests/

# Alohida komponent testlarini ishga tushirish
pytest -v tests/test_smart_care.py
pytest -v tests/test_updates.py
pytest -v tests/test_large_files.py
pytest -v tests/test_safety_engine.py
pytest -v tests/test_registry_cleaner.py
pytest -v tests/test_network.py
```

---

## 📄 Litsenziya

Loyiha **MIT Litsenziyasi** asosida tarqatiladi. Batafsil ma'lumot uchun [`LICENSE`](LICENSE) fayliga qarang.

---

<div align="center">
  <sub>Windows operatsion tizimingizni tezkor, xavfsiz va toza saqlash uchun mehr bilan yaratildi.</sub>
</div>
