# 🛡️ راهنمای پیکربندی و استحکام‌بخشی امنیتی (Security Guide)

این راهنما الزامات امنیتی را برای بهره‌برداری تجاری از سامانه فروش اشتراک VPN ارائه می‌دهد.

---

## ۱. هش رمزعبور و توکن‌های نشست (Session Tokens)
- تمامی کلمات عبور با الگوریتم **Bcrypt** همراه با نمک تصادفی (Salt) با ضریب امنیتی ۱۲ راند هش می‌شوند.
- توکن‌های ورود به پنل مدیریت بر پایه استاندارد **JWT (JSON Web Token)** با کلید رمزنگاری ۶۴ کاراکتری رندوم تولید و در کوکی امن با ویژگی‌های `HttpOnly` و `SameSite=Lax` نگهداری می‌شوند.

## ۲. محافظت در برابر حملات Brute-Force
- در اندپوینت ورود ادمین (`/api/auth/login`) سیستم محدودکننده نرخ درخواست (Rate Limiting) درون‌حافظه‌ای تعبیه شده است:
  - حداکثر ۵ تلاش ناموفق در ۵ دقیقه مجاز است؛ پس از آن IP مسدود موقت می‌شود.

## ۳. حفاظت از تراکنش‌های کیف پول و نژاد داده (Race Condition)
- عملیات کسر و افزایش موجودی با قفل اتمیک پایگاه‌داده (`with_for_update()`) انجام می‌شود.
- تا زمانی که ایجاد کلاینت در پنل 3X-UI با موفقیت تایید نشود، تراکنش قطعی نمی‌گردد و در صورت بروز خطا بلافاصله استرداد وجه (Auto Refund) انجام می‌شود.

## ۴. استقرار امن با HTTPS و Nginx
برای جلوگیری از سرقت سشن‌ها روی شبکه‌های اینترنت عمومی، توصیه می‌شود پنل را حتماً پشت گواهینامه معتبر SSL قرار دهید:
```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d panel.yourdomain.com
```

## ۵. امنیت فایروال سرور (UFW)
تنها پورت‌های ضروری را باز بگذارید:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8000/tcp    # Web Admin (یا فقط پشت Nginx)
sudo ufw enable
```
