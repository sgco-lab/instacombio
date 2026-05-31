"""
ابزار استخراج اطلاعات کامنت‌گذاران اینستاگرام - نسخه نهایی با سشن فایرفاکس
"""

from flask import Flask, render_template_string, request, jsonify
import instaloader
import re
import time
import os
import pickle
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# HTML قالب با رابط کاربری ساده و حرفه‌ای
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>استخراج اطلاعات کامنت‌گذاران اینستاگرام</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Tahoma', 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .content { padding: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-weight: bold; margin-bottom: 8px; color: #333; }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 40px;
            border-radius: 50px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .output {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .log-area {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 10px;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        .results {
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        .alert {
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .alert-warning { background: #fff3cd; border: 1px solid #ffc107; color: #856404; }
        .alert-success { background: #d4edda; border: 1px solid #28a745; color: #155724; }
        .alert-info { background: #d1ecf1; border: 1px solid #17a2b8; color: #0c5460; }
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin: 5px;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-info { background: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕵️ ابزار استخراج اطلاعات اینستاگرام</h1>
            <p>استخراج کامنت‌ها، بیوگرافی، شماره تماس و ایمیل</p>
        </div>
        
        <div class="content">
            <div class="alert alert-warning">
                ⚠️ <strong>توجه مهم:</strong> از یک اکانت تستی اینستاگرام استفاده کنید.
            </div>
            
            <div id="statusAlert"></div>
            
            <form id="scrapeForm">
                <div class="form-group">
                    <label>🔗 لینک پست اینستاگرام:</label>
                    <input type="text" id="postUrl" placeholder="https://www.instagram.com/p/..." required>
                </div>
                
                <div class="form-group">
                    <label>👤 نام کاربری اینستاگرام:</label>
                    <input type="text" id="username" placeholder="your_username" required>
                </div>
                
                <div class="form-group">
                    <label>📊 تعداد کامنت برای استخراج:</label>
                    <input type="number" id="maxComments" value="50" min="1" max="500">
                </div>
                
                <button type="submit" id="submitBtn">🚀 شروع استخراج</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 10px;">در حال استخراج اطلاعات... لطفاً صبر کنید</p>
                <small>این عملیات ممکن است چند دقیقه طول بکشد</small>
            </div>
            
            <div class="output" id="output">
                <h3>📝 وضعیت اجرا:</h3>
                <div class="log-area" id="logArea"></div>
                
                <div class="results" id="resultsArea" style="display:none;">
                    <h3>📊 نتایج استخراج:</h3>
                    <div id="resultsContent"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('scrapeForm');
        const submitBtn = document.getElementById('submitBtn');
        const loading = document.getElementById('loading');
        const output = document.getElementById('output');
        const logArea = document.getElementById('logArea');
        const resultsArea = document.getElementById('resultsArea');
        const resultsContent = document.getElementById('resultsContent');
        const statusAlert = document.getElementById('statusAlert');
        
        function showAlert(message, type) {
            statusAlert.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            setTimeout(() => {
                statusAlert.innerHTML = '';
            }, 5000);
        }
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const postUrl = document.getElementById('postUrl').value;
            const username = document.getElementById('username').value;
            const maxComments = document.getElementById('maxComments').value;
            
            output.style.display = 'block';
            resultsArea.style.display = 'none';
            logArea.innerHTML = '';
            loading.style.display = 'block';
            submitBtn.disabled = true;
            
            try {
                const response = await fetch('/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        post_url: postUrl,
                        username: username,
                        max_comments: parseInt(maxComments)
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    logArea.innerHTML = data.logs.join('\\n');
                    
                    if (data.results && data.results.length > 0) {
                        resultsArea.style.display = 'block';
                        let html = '<div style="margin-bottom: 15px;">';
                        html += '<p><strong>✅ تعداد کل کاربران:</strong> ' + data.results.length + '</p>';
                        html += '<p><strong>📞 کاربران دارای شماره تماس:</strong> ' + data.users_with_phone_count + '</p>';
                        html += '</div><div style="max-height: 400px; overflow-y: auto;">';
                        
                        data.results.forEach(user => {
                            html += '<div style="border:1px solid #e0e0e0; padding:10px; margin-bottom:10px; border-radius:10px;">';
                            html += '<strong>🆔 @' + user.username + '</strong><br>';
                            html += '<strong>👤 نام:</strong> ' + (user.full_name || '-') + '<br>';
                            if (user.phone_numbers && user.phone_numbers.length > 0) {
                                html += '<span class="badge badge-success">📞 ' + user.phone_numbers.join(', ') + '</span><br>';
                            }
                            if (user.emails && user.emails.length > 0) {
                                html += '<span class="badge badge-info">📧 ' + user.emails.join(', ') + '</span><br>';
                            }
                            if (user.biography) {
                                html += '<small><strong>📝 بیوگرافی:</strong> ' + user.biography.substring(0, 150) + '</small><br>';
                            }
                            html += '</div>';
                        });
                        html += '</div>';
                        resultsContent.innerHTML = html;
                    }
                    showAlert('✅ استخراج با موفقیت انجام شد!', 'success');
                } else {
                    logArea.innerHTML = data.logs.join('\\n') + '\\n\\n❌ خطا: ' + data.error;
                    showAlert('❌ خطا: ' + data.error, 'warning');
                }
            } catch (error) {
                logArea.innerHTML = '❌ خطا در ارتباط با سرور: ' + error.message;
                showAlert('❌ خطا در ارتباط با سرور', 'warning');
            } finally {
                loading.style.display = 'none';
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
'''

def extract_phone_numbers(text):
    """استخراج شماره تماس از متن بیوگرافی"""
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

def extract_emails(text):
    """استخراج ایمیل از متن بیوگرافی"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(email_pattern, text)))

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.json
        post_url = data.get('post_url')
        username = data.get('username')
        max_comments = data.get('max_comments', 50)
        
        logs = []
        def log_message(msg):
            logs.append(msg)
            print(msg)
        
        log_message("🔑 در حال بارگذاری سشن ذخیره‌شده از فایرفاکس...")
        
        # ساخت شیء Instaloader
        L = instaloader.Instaloader(
            max_connection_attempts=3,
            request_timeout=60,
            sleep_on_rate_limit=True
        )
        
        # مسیر فایل سشن
        session_filename = f"valid_session_{username}.pkl"
        
        # بررسی وجود فایل سشن
        if not os.path.exists(session_filename):
            log_message(f"❌ خطا: فایل سشن '{session_filename}' یافت نشد!")
            log_message("لطفاً ابتدا فایل سشن معتبر را در پوشه پروژه قرار دهید.")
            return jsonify({
                'success': False, 
                'logs': logs, 
                'error': f'فایل سشن {session_filename} یافت نشد. لطفاً ابتدا سشن را از فایرفاکس استخراج کنید.'
            })
        
        # بارگذاری کوکی‌ها از فایل pickle
        try:
            with open(session_filename, 'rb') as f:
                cookies = pickle.load(f)
                L.context._session.cookies.update(cookies)
            log_message("✅ فایل سشن با موفقیت بارگذاری شد.")
        except Exception as e:
            log_message(f"❌ خطا در بارگذاری فایل سشن: {e}")
            return jsonify({'success': False, 'logs': logs, 'error': f'خطا در بارگذاری سشن: {e}'})
        
        # بررسی اعتبار سشن
        log_message("🔄 در حال بررسی اعتبار سشن...")
        try:
            username_check = L.test_login()
            if username_check:
                log_message(f"✅ سشن برای کاربر '{username_check}' معتبر است.")
            else:
                log_message("❌ سشن معتبر نیست یا منقضی شده است.")
                log_message("لطفاً دوباره فایل get_firefox_session.py را اجرا کنید.")
                return jsonify({
                    'success': False, 
                    'logs': logs, 
                    'error': 'سشن معتبر نیست یا منقضی شده است. لطفاً سشن جدید بگیرید.'
                })
        except Exception as e:
            log_message(f"⚠️ خطا در بررسی اعتبار سشن: {e}")
            log_message("ادامه می‌دهیم...")
        
        # دریافت پست
        log_message(f"📱 در حال دریافت پست...")
        try:
            post = instaloader.Post.from_url(L.context, post_url)
            log_message(f"📊 تعداد کل کامنت‌های این پست: {post.comments}")
        except Exception as e:
            log_message(f"❌ خطا در دریافت پست: {e}")
            return jsonify({'success': False, 'logs': logs, 'error': f'خطا در دریافت پست: {e}'})
        
        # استخراج کامنت‌ها
        results = []
        count = 0
        
        for comment in post.get_comments():
            if count >= max_comments:
                break
            
            count += 1
            commenter = comment.owner
            log_message(f"🔍 [{count}/{max_comments}] در حال بررسی @{commenter.username}")
            
            try:
                profile = instaloader.Profile.from_username(L.context, commenter.username)
                bio = profile.biography if profile.biography else ""
                
                phones = extract_phone_numbers(bio)
                emails = extract_emails(bio)
                
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
                    log_message(f"   📞 شماره تماس: {', '.join(phones)}")
                if emails:
                    log_message(f"   📧 ایمیل: {', '.join(emails)}")
                
            except Exception as e:
                log_message(f"   ⚠️ خطا در دریافت اطلاعات {commenter.username}: {e}")
            
            time.sleep(1.5)
        
        log_message(f"\n✅ استخراج کامل شد!")
        log_message(f"📊 تعداد کل: {len(results)} کاربر")
        log_message(f"📞 کاربران دارای شماره: {sum(1 for r in results if r['phone_numbers'])}")
        
        return jsonify({
            'success': True,
            'logs': logs,
            'results': results,
            'users_with_phone_count': sum(1 for r in results if r['phone_numbers'])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'logs': logs if 'logs' in locals() else [],
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
