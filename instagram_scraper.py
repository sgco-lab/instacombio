"""
ابزار استخراج اطلاعات کامنت‌گذاران اینستاگرام - نسخه GUI ساده
"""
import instaloader
import re
import json
import time
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from threading import Thread

class InstagramApp:
    def __init__(self, root):
        self.root = root
        self.root.title("استخراج اطلاعات کامنت‌گذاران اینستاگرام")
        self.root.geometry("700x600")
        self.root.configure(bg='#f0f0f0')
        
        # متغیرها
        self.is_running = False
        
        # ساخت رابط کاربری
        self.setup_ui()
    
    def setup_ui(self):
        # عنوان
        title_label = tk.Label(self.root, text="🕵️ ابزار استخراج اطلاعات اینستاگرام", 
                               font=("Arial", 16, "bold"), bg='#f0f0f0', fg='#333')
        title_label.pack(pady=10)
        
        # فریم ورودی
        input_frame = tk.Frame(self.root, bg='#f0f0f0')
        input_frame.pack(pady=10, padx=20, fill='x')
        
        # لینک پست
        tk.Label(input_frame, text="🔗 لینک پست اینستاگرام:", bg='#f0f0f0', font=("Arial", 10)).pack(anchor='w')
        self.post_url_entry = tk.Entry(input_frame, width=70, font=("Arial", 10))
        self.post_url_entry.pack(fill='x', pady=5)
        
        # نام کاربری
        tk.Label(input_frame, text="👤 نام کاربری اینستاگرام خودتان:", bg='#f0f0f0', font=("Arial", 10)).pack(anchor='w')
        self.username_entry = tk.Entry(input_frame, width=70, font=("Arial", 10))
        self.username_entry.pack(fill='x', pady=5)
        
        # رمز عبور
        tk.Label(input_frame, text="🔐 رمز عبور:", bg='#f0f0f0', font=("Arial", 10)).pack(anchor='w')
        self.password_entry = tk.Entry(input_frame, width=70, show="*", font=("Arial", 10))
        self.password_entry.pack(fill='x', pady=5)
        
        # تعداد کامنت
        tk.Label(input_frame, text="📊 تعداد کامنت برای استخراج (پیش‌فرض 50):", bg='#f0f0f0', font=("Arial", 10)).pack(anchor='w')
        self.max_comments_entry = tk.Entry(input_frame, width=20, font=("Arial", 10))
        self.max_comments_entry.insert(0, "50")
        self.max_comments_entry.pack(anchor='w', pady=5)
        
        # دکمه شروع
        self.start_button = tk.Button(self.root, text="🚀 شروع استخراج", command=self.start_scraping,
                                       bg='#4CAF50', fg='white', font=("Arial", 12, "bold"),
                                       padx=20, pady=10)
        self.start_button.pack(pady=10)
        
        # منطقه نمایش خروجی
        output_frame = tk.Frame(self.root, bg='#f0f0f0')
        output_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        tk.Label(output_frame, text="📝 وضعیت اجرا:", bg='#f0f0f0', font=("Arial", 10, "bold")).pack(anchor='w')
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80, 
                                                       font=("Consolas", 9))
        self.output_text.pack(fill='both', expand=True)
        
        # هشدار
        warning_label = tk.Label(self.root, text="⚠️ توجه: از یک اکانت تستی استفاده کنید (نه اکانت اصلی)", 
                                 bg='#ffe0e0', fg='red', font=("Arial", 9))
        warning_label.pack(pady=5, fill='x')
    
    def log_message(self, message, color='black'):
        """اضافه کردن پیام به منطقه خروجی"""
        self.output_text.insert(tk.END, f"{message}\n", color)
        self.output_text.see(tk.END)
        self.root.update()
    
    def extract_phone_numbers(self, text):
        """استخراج شماره تماس از متن"""
        patterns = [
            r'0\d{9,10}',
            r'\+98\d{10}',
            r'0098\d{10}',
            r'09\d{9}'
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))
    
    def extract_emails(self, text):
        """استخراج ایمیل از متن"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return list(set(re.findall(email_pattern, text)))
    
    def scrape_comments(self, post_url, username, password, max_comments):
        """تابع اصلی استخراج"""
        try:
            self.log_message("🔑 در حال ورود به اینستاگرام...")
            L = instaloader.Instaloader(
                max_connection_attempts=3,
                request_timeout=30,
                sleep_on_rate_limit=True
            )
            
            L.login(username, password)
            self.log_message("✅ ورود موفقیت‌آمیز بود")
            
            self.log_message(f"📱 در حال دریافت پست...")
            post = instaloader.Post.from_url(L.context, post_url)
            self.log_message(f"📊 تعداد کل کامنت‌های این پست: {post.comments}")
            
            results = []
            count = 0
            
            for comment in post.get_comments():
                if count >= max_comments:
                    break
                
                count += 1
                commenter = comment.owner
                self.log_message(f"🔍 [{count}/{max_comments}] در حال بررسی @{commenter.username}")
                
                try:
                    profile = instaloader.Profile.from_username(L.context, commenter.username)
                    bio = profile.biography if profile.biography else ""
                    
                    phones = self.extract_phone_numbers(bio)
                    emails = self.extract_emails(bio)
                    
                    user_data = {
                        "username": commenter.username,
                        "full_name": profile.full_name,
                        "biography": bio,
                        "phone_numbers": phones,
                        "emails": emails,
                        "followers": profile.followers,
                        "is_private": profile.is_private
                    }
                    results.append(user_data)
                    
                    if phones:
                        self.log_message(f"   📞 شماره تماس: {', '.join(phones)}", 'green')
                    if emails:
                        self.log_message(f"   📧 ایمیل: {', '.join(emails)}", 'blue')
                    
                except Exception as e:
                    self.log_message(f"   ⚠️ خطا: {e}", 'orange')
                
                time.sleep(1.5)
            
            # ذخیره نتایج
            filename = f"instagram_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"\n✅ استخراج کامل شد!", 'green')
            self.log_message(f"📁 نتایج در فایل {filename} ذخیره شد", 'green')
            self.log_message(f"📊 تعداد کل: {len(results)} کاربر", 'green')
            self.log_message(f"📞 کاربران دارای شماره: {sum(1 for r in results if r['phone_numbers'])}", 'green')
            
            # نمایش خلاصه کاربران با شماره
            users_with_phone = [r for r in results if r['phone_numbers']]
            if users_with_phone:
                self.log_message(f"\n📋 لیست کاربران دارای شماره تماس:", 'blue')
                for user in users_with_phone:
                    self.log_message(f"   @{user['username']}: {', '.join(user['phone_numbers'])}", 'blue')
            
            messagebox.showinfo("پایان کار", f"استخراج با موفقیت انجام شد!\n{len(results)} کاربر پردازش شد.\nفایل خروجی: {filename}")
            
        except Exception as e:
            self.log_message(f"❌ خطا: {e}", 'red')
            messagebox.showerror("خطا", str(e))
        
        finally:
            self.is_running = False
            self.start_button.config(state='normal')
    
    def start_scraping(self):
        if self.is_running:
            return
        
        # گرفتن ورودی‌ها
        post_url = self.post_url_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        try:
            max_comments = int(self.max_comments_entry.get().strip())
        except ValueError:
            max_comments = 50
        
        # اعتبارسنجی
        if not post_url:
            messagebox.showerror("خطا", "لطفاً لینک پست را وارد کنید")
            return
        if not username or not password:
            messagebox.showerror("خطا", "لطفاً نام کاربری و رمز عبور را وارد کنید")
            return
        
        # پاک کردن خروجی قبلی
        self.output_text.delete(1.0, tk.END)
        
        self.is_running = True
        self.start_button.config(state='disabled')
        
        # اجرا در یک ترد جداگانه
        thread = Thread(target=self.scrape_comments, args=(post_url, username, password, max_comments))
        thread.daemon = True
        thread.start()

def main():
    root = tk.Tk()
    app = InstagramApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()