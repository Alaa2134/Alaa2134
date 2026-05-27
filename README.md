# منصة ريلز القرآن التلقائية 🕌

منصة تولّد ريلز قرآن يومياً وتنشرها أوتوماتيك على إنستجرام، بدون أي تدخل
يدوي، باستخدام **Instagram Graph API الرسمي** و **GitHub Actions** المجاني.

## إزاي بتشتغل؟

```
اختيار آية ← جلب نصها + صوت التلاوة ← رسم النص بالعربي ←
دمج (خلفية + نص + صوت) بـ ffmpeg ← رفع الفيديو كـ GitHub Release ←
النشر على إنستجرام عبر Graph API ← تحديث حالة الآيات المنشورة
```

- **المحتوى**: نص الآية وصوت التلاوة من [Al Quran Cloud API](https://alquran.cloud/api).
- **الفيديو**: مقاس 1080×1920 (9:16)، نص الآية بالعربي بخط أميري مع تشكيل
  واتجاه صحيح، فوق خلفية فيديو طبيعة (لو موجودة) أو تدرج لوني هادئ.
- **الاستضافة**: الفيديو بيترفع كـ GitHub Release asset عشان يبقى ليه رابط
  عام يقدر إنستجرام يحمّل منه (Graph API بيطلب رابط عام).
- **الجدولة**: GitHub Actions كل يوم الساعة 06:00 UTC.

## الإعداد (مرة واحدة)

### 1) حساب إنستجرام و Graph API
1. حوّل حسابك على إنستجرام إلى **Business** أو **Creator** واربطه بصفحة فيسبوك.
2. اعمل تطبيق على [Meta for Developers](https://developers.facebook.com/) وفعّل
   منتج **Instagram Graph API**.
3. احصل على:
   - **`IG_USER_ID`**: معرّف حساب إنستجرام (Instagram Business Account ID).
   - **`IG_ACCESS_TOKEN`**: توكن وصول طويل الأمد (long-lived) بصلاحيات
     `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`.

> التوكن طويل الأمد بيدوم ~60 يوم؛ جدّده دورياً أو استخدم System User token
> اللي ما بينتهيش.

### 2) إعداد الـ Secrets في GitHub
من **Settings → Secrets and variables → Actions**:

**Secrets** (سرية):
| الاسم | القيمة |
|------|--------|
| `IG_USER_ID` | معرّف حساب إنستجرام |
| `IG_ACCESS_TOKEN` | التوكن طويل الأمد |

> `GITHUB_TOKEN` بيتوفّر تلقائياً من GitHub Actions — مش محتاج تضيفه.

**Variables** (اختيارية للتحكم):
| الاسم | الافتراضي | الوصف |
|------|-----------|-------|
| `AUDIO_EDITION` | `ar.alafasy` | القارئ (مثلاً `ar.husary`, `ar.minshawi`) |
| `SELECTION_MODE` | `sequential` | `sequential` بالترتيب أو `random` عشوائي |
| `CAPTION_HASHTAGS` | هاشتاجات قرآن | الهاشتاجات في الكابشن |

### 3) فعّل الجدولة
ادمج هذا الفرع في الفرع الافتراضي (`main`)، لأن جدولة `schedule` في GitHub
Actions بتشتغل فقط من الفرع الافتراضي.

## التحكم الكامل

- **تشغيل يدوي فوري**: من تبويب **Actions → Daily Quran Reel → Run workflow**،
  وتقدر تحدد آية معينة (`reference`) أو تشغّل `dry_run` (توليد بدون نشر).
- **تغيير القارئ / الهاشتاجات / وضع الاختيار**: من الـ Variables بدون تعديل كود.
- **مواعيد النشر**: عدّل `cron` في `.github/workflows/daily.yml`.
- **قائمة الآيات**: عدّل `data/verses.json` (مراجع `سورة:آية`).
- **الخلفيات**: ضع فيديوهات 9:16 في `assets/backgrounds/` (اختياري).

## تجربة محلية

```bash
pip install -r requirements.txt
sudo apt-get install -y ffmpeg fonts-hosny-amiri   # أو أي خط عربي

# توليد فيديو بدون نشر:
DRY_RUN=true VERSE_REFERENCE=2:255 python main.py
# الناتج في مجلد output/
```

للنشر محلياً، اضبط متغيرات البيئة في ملف `.env` (انظر `.env.example`).

## هيكل المشروع

```
main.py                      # المنسّق الرئيسي للـ pipeline
src/
  config.py                  # الإعدادات من متغيرات البيئة
  quran.py                   # جلب نص الآية + صوت التلاوة
  render.py                  # رسم النص العربي + الخلفية (Pillow)
  video.py                   # دمج الفيديو (ffmpeg)
  publisher.py               # رفع GitHub Release + نشر Instagram Graph API
  state.py                   # اختيار الآية + تتبّع المنشور
  caption.py                 # بناء الكابشن
data/verses.json             # قائمة الآيات المنسّقة
data/state.json              # حالة النشر (تتحدّث تلقائياً)
assets/backgrounds/          # فيديوهات الخلفية (اختياري)
.github/workflows/daily.yml  # الجدولة اليومية
```

## ملاحظات

- استخدمنا الـ API الرسمي عشان الحساب يفضل آمن ومتوافق مع شروط إنستجرام.
- اتأكد إن المحتوى (الخلفيات، التلاوات) عندك حق نشره.
