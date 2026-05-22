# راهنمای فعال‌سازی ماژول بای‌پس تحریم/فیلترینگ تلگرام (Relay Bypass)

این ماژول برای سرورهایی که در ایران مستقر هستند و **دسترسی به اینترنت جهانی (یا تلگرام) ندارند** طراحی شده است. از تکنیک **Domain Fronting** از طریق سرورهای قدرتمند گوگل (Google Apps Script) و کلادفلر (Cloudflare Workers) استفاده می‌شود تا درخواست‌های تلگرام شما بدون فیلترینگ و با امنیت کامل رد شوند.

---

## 🛠 مراحل راه‌اندازی و فعال‌سازی

### مرحله ۱: استقرار Cloudflare Worker (مقصد نهایی)
1. وارد داشبورد کلادفلر خود ([dash.cloudflare.com](https://dash.cloudflare.com)) شوید.
2. از منوی سمت چپ به بخش **Workers & Pages** رفته و روی دکمه **Create Application** و سپس **Create Worker** کلیک کنید.
3. نامی برای ورکر خود انتخاب کنید (مثلاً `telegram-relay`) و روی **Deploy** کلیک کنید.
4. روی **Edit Code** کلیک کنید، تمام کدهای پیش‌فرض را پاک کرده و محتوای فایل **[`worker.js`](file:///f:/platibot/relay/worker.js)** را در آن قرار دهید.
5. دکمه **Save and deploy** (بالا سمت راست) را بزنید.
6. به صفحه اصلی تنظیمات ورکر خود برگردید. وارد تب **Settings** شده و بخش **Variables** را انتخاب کنید.
7. در بخش **Environment Variables** روی **Add variable** کلیک کنید:
   - **Name:** `RELAY_TOKEN`
   - **Value:** یک کلید امنیتی و طولانی به دلخواه خود وارد کنید (مثلاً `MySecretToken9876!`). این کلید مانع سوءاستفاده دیگران از سرور شما می‌شود.
8. روی **Save and deploy** کلیک کنید.
9. آدرس ورکر خود را کپی کنید (به عنوان مثال: `https://telegram-relay.yourname.workers.dev`).

---

### مرحله ۲: استقرار Google Apps Script (بای‌پس فیلترینگ)
1. وارد سایت [script.google.com](https://script.google.com) شوید (با حساب گوگل خود).
2. روی دکمه **New Project** کلیک کنید.
3. کدهای پیش‌فرض را پاک کرده و محتوای فایل **[`gas.js`](file:///f:/platibot/relay/gas.js)** را پیست کنید.
4. در خطوط بالایی کد:
   - مقدار `RELAY_TOKEN` را **دقیقاً** همان کلید امنیتی که در مرحله قبل برای کلادفلر تعریف کردید قرار دهید.
   - مقدار `CFW_URL` را برابر با **آدرس ورکر کلادفلر خود** که در مرحله اول کپی کردید بگذارید.
5. از بالا سمت راست روی دکمه **Deploy** و سپس **New deployment** کلیک کنید.
6. روی آیکون چرخ‌دنده کلیک کرده و نوع آن را **Web App** انتخاب کنید.
7. تنظیمات را به شکل زیر قرار دهید:
   - **Description:** `Telegram Relay Web App`
   - **Execute as:** `Me (your-email@gmail.com)`
   - **Who has access:** `Anyone` (بسیار مهم: این گزینه برای دسترسی پروکسی به گوگل بدون نیاز به لاگین الزامی است. امنیت تماماً توسط توکن اختصاصی شما تضمین می‌شود).
8. روی دکمه **Deploy** کلیک کنید.
9. گوگل از شما دسترسی می‌خواهد؛ روی **Authorize Access** کلیک کنید. ایمیل خود را انتخاب کرده، دکمه **Advanced** را بزنید و روی **Go to Untitled project (unsafe)** کلیک کرده و دسترسی‌ها را تایید کنید.
10. پس از اتمام استقرار، گوگل به شما یک **Web App URL** می‌دهد (مثلاً `https://script.google.com/macros/s/XXXXXX/exec`). این آدرس را کپی کنید.

---

### مرحله ۳: تنظیم سرور ایران و ربات
حالا کافیست فایل‌های ماژول را در سرور ایران یا خارج قرار دهید و متغیرهای محیطی را در فایل `.env` خود ست کنید:

```ini
# فعال‌سازی پروکسی بای‌پس تلگرام (روی سرور خارج false و روی سرور ایران true کنید)
USE_PROXY_RELAY=true

# آدرسی که از وب‌اپ گوگل در مرحله ۲ کپی کردید
GAS_URL=https://script.google.com/macros/s/XXXXXX/exec

# همان توکن امنیتی مشترک بین داکر، گوگل و کلادفلر
RELAY_TOKEN=MySecretToken9876!

# آدرس اتصال به پروکسی محلی (در حالت پیش‌فرض برای داکر ست شده است)
LOCAL_PROXY_URL=http://telegram-proxy:8080

# فعال‌سازی پروفایل پروکسی در داکر کامپوز (بسیار مهم)
# - روی سرور ایران این خط را فعال کنید تا کانتینر پروکسی هم بالا بیاید
# - روی سرور خارج این خط را کامنت کنید تا کانتینر پروکسی اصلاً اجرا نشود و منابع بیهوده مصرف نشوند
COMPOSE_PROFILES=proxy
```

---

## 📦 نحوه استفاده از این ماژول در پروژه‌های پایتونی دیگر
این ماژول کاملاً مستقل طراحی شده است. برای استفاده در هر ربات تلگرامی دیگر (با فریم‌ورک‌های مختلف مثل `aiogram` یا `python-telegram-bot`):

1. پوشه `relay/` را به طور کامل در کنار فایل اصلی پروژه خود کپی کنید.
2. فایل `relay/local_proxy.py` را به عنوان یک پروسه مجزا (مثلاً با PM2، دستور Background یا سرویس داکر جدید) روی پورت دلخواه (مثلاً `8080`) اجرا کنید:
   ```bash
   # نصب کتابخانه aiohttp در صورت نیاز
   pip install aiohttp
   
   # اجرای پروکسی محلی
   export GAS_URL="آدرس گوگل اسکریپت شما"
   export RELAY_TOKEN="توکن شما"
   export PROXY_PORT=8080
   python relay/local_proxy.py
   ```
3. در ربات پایتونی خود، آدرس API تلگرام را به پروکسی محلی تغییر دهید. 
   مثال در **aiogram 3**:
   ```python
   from aiogram import Bot
   from aiogram.client.session.aiohttp import AiohttpSession
   from aiogram.client.telegram import TelegramAPIServer

   # تنظیم سرور API به پروکسی محلی
   local_server = TelegramAPIServer(
       base="http://localhost:8080/bot{token}/{method}",
       file="http://localhost:8080/file/bot{token}/{path}"
   )
   session = AiohttpSession(api=local_server)
   bot = Bot(token="BOT_TOKEN", session=session)
   ```

با این کار، ربات شما بدون اینکه بداند ترافیک از فیلتر رد می‌شود، تمام درخواست‌های خود را به پروکسی محلی می‌فرستد و پاسخ را به صورت کاملاً عادی و سریع دریافت می‌کند!
