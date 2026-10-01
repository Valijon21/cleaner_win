# CleanGuard — Audit, reja va tuzatishlar hisoboti

**Sana:** 2026-10-01
**Ko'lam:** `cleanguard/` (Python 3.8+ / PyQt5 / Win32 ctypes / SQLite), testlar, sozlamalar oqimi
**Natija:** 25 ta tasdiqlangan muammo **tuzatildi**, yana 10 tasi keyingi bosqich rejasiga kiritildi (5-bo'lim), 18 ta yangi regressiya testi qo'shildi.
**Testlar:** `177 passed` (avval 141 ta edi)

> Har bir topilma kodni o'qib va (imkon bo'lgan joyda) real Windows'da ishga tushirib tasdiqlangan.
> Mavjud `AUDIT_REPORT.md` dan mustaqil tarzda tekshirildi.

---

## 1. Qisqa xulosa

Arxitektura yaxshi o'ylangan (Scanner → RiskEngine → Planner → Executor → SafetyEngine darvozasi),
lekin **amalda bir nechta yo'l bu darvozani chetlab o'tgan** va Windows API chaqiruvlarida xavfsizlik
tekshiruvlarini sindiradigan xatolar bor edi. Eng xavflilari:

1. Uninstaller "qoldiqlar" oynasi butun papkalarni `shutil.rmtree` bilan **butunlay** o'chirardi,
   nom bo'yicha **substring** moslashtirish bilan (`"git"` → `"Digital…"`), hammasi oldindan belgilangan holda.
2. Rejalashtirilgan Auto-Care va Smart Care foydalanuvchining **Savatini (Recycle Bin) so'ramasdan bo'shatardi**.
3. Smart Care reestr bosqichida **har safar qulardi** (`ValueError`), UI esa abadiy "bloklangan" holda qolardi.
4. `GetFileAttributesW` noto'g'ri `restype` tufayli mavjud bo'lmagan fayllar "junction" va "system" deb hisoblanardi.
5. Sozlamalardagi "minimal fayl yoshi", "PyInstaller qoidasi", "tasdiqlash", "ishga tushganda skanerlash"
   **hech qayerda ishlatilmas edi** — UI "soxta" edi.

---

## 2. Topilgan muammolar va holati

### P0 — Ma'lumot yo'qotish / qulash (barchasi tuzatildi)

| # | Muammo | Joy | Holat |
|---|--------|-----|-------|
| 1 | Qoldiqlar: substring moslashtirish, oldindan belgilangan, `shutil.rmtree(ignore_errors=True)` bilan butunlay o'chirish | `windows/uninstaller.py`, `ui/uninstaller_page.py` | ✅ Aniq kalit moslashtirish (`leftover_match_key`), umumiy vendor papkalari ro'yxati, junction'lar tashlanadi, hech narsa oldindan belgilanmaydi, Savatga ko'chiriladi |
| 2 | `self.safety_engine.is_protected_path` — bunday metod yo'q edi → `AttributeError` | `ui/uninstaller_page.py`, `ui/duplicates_page.py` | ✅ `SafetyEngine.is_protected_path()` qo'shildi |
| 3 | Dublikatlar: guruhdagi **barcha** nusxani o'chirish mumkin edi; `os.remove` bilan butunlay | `ui/duplicates_page.py` | ✅ Har guruhda kamida 1 nusxa majburiy; Savat orqali |
| 4 | Katta fayllar: `os.remove` to'g'ridan-to'g'ri, xavfsizlik tekshiruvisiz | `ui/large_files_page.py`, `core/scanner/large_files.py` | ✅ Yagona xavfsiz yo'l + Savat + "Savatga sig'masa ogohlantir" (`FOF_WANTNUKEWARNING`) |
| 5 | Auto-Care / Smart Care Savatni va shaxsiy tarixni so'ramasdan tozalaydi | `windows/scheduler.py`, `services/smart_care_service.py` | ✅ `CleanupPlanner.select_unattended()` — `recycle_bin` va `privacy_traces` chiqarib tashlanadi |
| 6 | Smart Care: `cleaned, _ = clean_issues(...)` 3 ta qiymat qaytaradi → `ValueError`; `error` signali ulanmagan → UI qotib qoladi | `services/smart_care_service.py`, `ui/dashboard_page.py` | ✅ Tuzatildi + xato handler + **tasdiqlash oynasi** |
| 7 | `RECYCLE_BIN` strategiyasi muvaffaqiyatsiz bo'lsa **jimgina butunlay o'chirishga** o'tardi | `core/cleaner/strategy.py` | ✅ Endi xato qaytaradi, fayl joyida qoladi |
| 8 | `"$Recycle.Bin"` bilan **tugaydigan istalgan yo'l** xavfsizlik darvozasini chetlab, `SHEmptyRecycleBin` chaqirardi | `core/cleaner/executor.py` | ✅ Faqat aniq `X:\$Recycle.Bin` + `recycle_bin` kategoriyasi |
| 9 | Reestr: zaxira yaratilmasa ham tozalash davom etardi | `windows/registry_cleaner.py` | ✅ Zaxirasiz reestrga tegilmaydi |

### P0 — Windows API (ctypes) xatolari (tuzatildi)

| # | Muammo | Ta'siri | Holat |
|---|--------|---------|-------|
| 10 | `GetFileAttributesW` `restype` = `c_int` → `0xFFFFFFFF` o'rniga `-1` | Mavjud bo'lmagan yo'l = "junction", "system file", "directory" | ✅ `WinDLL(use_last_error=True)` + to'liq prototiplar |
| 11 | `CreateFileW` HANDLE 32-bitga qisqartirilgan; `GetLastError()` ishonchsiz | Fayl qulfini noto'g'ri aniqlash | ✅ `HANDLE` restype, `ctypes.get_last_error()` |
| 12 | `SHFILEOPSTRUCTW.fAnyOperationsAborted` `c_bool` (1 bayt) — Win32 `BOOL` 4 bayt | Offset 34 o'rniga 36: bekor qilingan amal "muvaffaqiyatli" ko'rinardi | ✅ `c_int` |
| 13 | `GetTickCount64` `c_int` → ~24.8 kun uptime'dan keyin to'lib ketadi | PyInstaller "boot time" xavfsizlik qatlami buziladi | ✅ `c_uint64` |

### P1 — Mantiq / ishonchlilik (tuzatildi)

| # | Muammo | Holat |
|---|--------|-------|
| 14 | `PathGuard`: `normalize_path()` `realpath` qiladi, junction tekshiruvi esa **nishon**da bajarilardi (u hech qachon junction emas). `..` tekshiruvi har doim `True` edi (o'lik kod) | ✅ Literal yo'l tekshiriladi, o'lik kod olib tashlandi |
| 15 | Sozlamalar ishlatilmas edi: `min_file_age_hours`, `smart_pyinstaller_cleanup`, `pyinstaller_min_age_hours`, `scan_threads`, `confirm_before_cleanup`, `auto_scan_on_startup` | ✅ Hammasi ulandi, o'zgarishlar **jonli** qo'llanadi |
| 16 | Sozlamalarda yangi istisno papka qo'shilsa, ishlab turgan `SafetyEngine` uni **qayta ishga tushirishgacha bilmasdi** | ✅ `ConfigManager.revision` + registry avto-reload |
| 17 | `config.json` atomik bo'lmagan yozuv: qulash vaqtida fayl buzilsa **barcha sozlamalar jimgina tiklanardi** | ✅ temp fayl + `fsync` + `os.replace` |
| 18 | Restore point UI oqimida (30+ s muzlash), admin bo'lmasa ham PowerShell kutardi, `END_SYSTEM_CHANGE` chaqirilmasdi | ✅ Worker oqimida, admin tekshiruvi, BEGIN/END juftligi, PowerShell escaping |
| 19 | `CleanupWorker.error` ulanmagan → xato bo'lsa tozalash sahifasi abadiy aylanadi; `scan_id` uzatilmasdi | ✅ |
| 20 | Tarix: `scan_id` FK — skan yozilmagan bo'lsa tozalash auditi **yo'qolardi**; Smart Care tarixga yozilmasdi; indekslar yo'q | ✅ NULL'ga tushadi, `executemany`, schema v2 indekslari |
| 21 | `is_system_critical_path()` har chaqiruvda yangi registry quradi (dublikat skanida har papka uchun) | ✅ Umumiy keshlangan registry |
| 22 | "Qaytariladigan hajm"ga BLOCKED elementlar ham qo'shilardi | ✅ |
| 23 | `os.walk` Python < 3.12'da junction'larga kiradi (katta fayl / dublikat skanida ikki marta sanash, sikl) | ✅ Junction'lar kesiladi |
| 24 | Dublikat skanerini bekor qilish ishlamas edi (bayroq skanerga uzatilmagan) | ✅ `CancellationToken` |
| 25 | `log_viewer_dialog.py`: `get_logger` import qilinmagan → eksport xatosida `NameError` | ✅ |

Qo'shimcha: `uninstaller.launch_uninstall` registrdagi buyruqni `shell=True` bilan (cmd.exe orqali) ishga tushirardi —
endi `shell=False` + `expandvars`. Musiqa papkasi himoyalangan papkalarga qo'shildi. Yangi matnlar uz/en/ru'ga qo'shildi.

---

## 3. Arxitektura o'zgarishi: yagona "foydalanuvchi ma'lumotini o'chirish" yo'li

Avval 4 xil joyda (`duplicates_page`, `large_files_page`, `large_files.py`, `uninstaller_page`) o'z
o'chirish kodi bor edi. Endi hammasi bitta funksiya orqali o'tadi:

```
UI (dublikat / katta fayl / qoldiq)
        │
        ▼
core/cleaner/user_data.py :: recycle_user_items()
        │  SafetyEngine.verify_user_data_target()  ← mavjudlik, himoyalangan yo'l, junction
        ▼
windows/recycle_bin.py :: move_to_recycle_bin(warn_if_permanent=True)   ← har doim qaytariladigan
```

Keraksiz fayllar (temp/kesh) esa avvalgidek `CleanupPlanner → CleanupExecutor → verify_cleanup_target` orqali o'tadi.

---

## 4. Tekshirish

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

- `159 passed` — `tests/test_audit_fixes.py` har bir tuzatishni qotiradi (junction, ctypes struktura offseti,
  Savat fallback'i, unattended filtr, Smart Care, jonli sozlamalar, atomik config, FK, qoldiq moslashtirish).
- Real Windows 11'da qo'lda tekshirildi: qulflangan fayl aniqlanadi, mavjud bo'lmagan yo'l junction emas,
  haqiqiy junction rad etiladi.
- Qilinmagan: GUI'ni qo'lda bosib ko'rish va haqiqiy Savatga ko'chirish (testlarda mock qilingan).

---

## 5. Ikkinchi bosqich (bajarildi)

| Vazifa | Natija |
|--------|--------|
| O'chirishda skaner chegarasini qayta tekshirish | `ScanItem.allowed_roots` → `verify_cleanup_target`. Real skanda 1794 ta SAFE elementning hammasiga chegara biriktirildi; 400 ta tekshirilganidan birortasi ham noto'g'ri rad etilmadi |
| Bitta nusxa himoyasi | `app/single_instance.py` (`QLockFile` + `QLocalServer`): ikkinchi ishga tushirish mavjud oynani ochadi; Auto-Care GUI ishlayotganda o'tkazib yuboriladi; admin sifatida qayta ishga tushirishda 8 s kutadi |
| `QThread.terminate()` o'rniga kooperativ to'xtatish | Barcha worker'lar `cancel()` + `requestInterruption()` + umumiy kutish muddati bilan to'xtatiladi; Tozalash/Smart Care/DISM ishlayotganda dasturni yopishga ruxsat berilmaydi (thread ishlab turganda o'chirilib qulashining oldi olindi) |
| Yashirin xato | Yopishda katta fayllar worker'i noto'g'ri atribut nomi (`_scan_worker`) tufayli umuman to'xtatilmas edi |
| `.exe` build | `scripts/build.py` → `dist/CleanGuard.exe` (39.8 MB). Ishga tushirildi; ikkinchi nusxa birinchisini faollashtirib, kod 0 bilan chiqdi |

## 6. Uchinchi bosqich (bajarildi)

| Vazifa | Natija |
|--------|--------|
| Lokalizatsiya | ~120 ta qattiq yozilgan matn `tr()` ga o'tkazildi (UI va Windows servis xabarlari); tweaks/bloatware katalogi `display_name`/`display_description` orqali jonli tarjima qilinadi; avvaldan **hech bir tilda bo'lmagan** 31 ta kalit qo'shildi. Jami 559 kalit, uz/en/ru to'plamlari va `{placeholder}` lari bir xil |
| i18n nazorati | `tests/test_translations_complete.py`: koddagi har bir `tr("kalit")` 3 tilda mavjudligi va placeholder mosligi CI'da tekshiriladi |
| Kod sifati | `ruff.toml` + CI'da `ruff check .`; 62 ta topilma tuzatildi (ishlatilmagan import, bo'sh f-string, keraksiz o'zgaruvchi) |
| O'lik kod | `ignored_paths` config kaliti olib tashlandi, DB jadvali v3 migratsiyasida o'chiriladi |
| DB migratsiyalari | `schema.py`: o'zgarmas v1 bazasi + raqamlangan `MIGRATIONS`; har biri alohida tranzaksiyada, xato bo'lsa to'liq orqaga qaytariladi. Testlar: yangi baza, eski v1 bazani ma'lumot bilan yangilash, idempotentlik, atomik rollback |
| Qoldiqlar | Dastur hali o'rnatilgan bo'lsa (uninstall bekor qilingan/tugamagan), qoldiq qidirish rad etiladi (`is_app_installed`) |
| MuiCache | Tarmoq (UNC) va hozir ulanmagan disklardagi yo'llar endi "o'chirilgan ilova" deb belgilanmaydi |
| `.reg` zaxira | `format_reg_value`: SZ, EXPAND_SZ, MULTI_SZ, DWORD, QWORD, BINARY, default qiymat va boshqa turlar regedit formatida; qator oxiridagi ikki karra CR (CR CR LF) xatosi tuzatildi. Haqiqiy `reg import` bilan qaytarib tiklash testi barcha turlarda o'tdi |
| Qo'shimcha topilma | Sozlamalardagi "Auto-Care sinovi" haqiqiy tozalashni **tasdiqsiz va UI oqimida** bajarardi — endi tasdiq so'raydi, fon oqimida ishlaydi va ishlayotganda dasturni yopish bloklanadi |
| Testlar o'zbek tiliga bog'liq edi | `conftest.py` har test uchun tilni belgilaydi (foydalanuvchining haqiqiy `config.json` iga yozmasdan) |

**Testlar:** `177 passed`. Dastur uz/en/ru tillarida ochilib, barcha 16 sahifa xatosiz aylanib chiqildi.

## 7. Qolgan ishlar (kod tashqarisida)

| Vazifa | Izoh |
|--------|------|
| GUI'ni qo'lda sinash | Skan → tozalash, dublikat/katta fayl/qoldiq (Savatga tushishi), Smart Care, admin rejimi |
| Inno Setup o'rnatuvchisini toza kompyuterda sinash | `installer/cleanguard_setup.iss` |
| Kod imzolash (code signing) | Imzosiz tozalovchi dasturlarni SmartScreen/antiviruslar bloklaydi |
| Diagnostika oynasi (log viewer) va crash dialog | Dasturchi uchun mo'ljallangan, hozircha faqat inglizcha |
