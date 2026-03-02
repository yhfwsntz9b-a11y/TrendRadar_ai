import requests
from bs4 import BeautifulSoup
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time

# ================= 配置区域 (必填) =================
# 你的QQ邮箱
SENDER_QQ = "827368026@qq.com"  

# 刚刚生成的16位授权码 (不是QQ密码!)
AUTH_CODE = "qyhvtlrklrptbeia"  

# 接收邮件的邮箱 (可以发给自己，也可以发给别人)
RECEIVER_EMAIL = "827368026@qq.com" 

# ================= 数据源抓取函数 =================

def get_github_trending():
    """抓取 GitHub Python 领域今日热门项目"""
    print("[1/3] 正在抓取 GitHub Trending...")
    url = "https://github.com/trending/python?since=daily"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        repos = soup.find_all('article', class_='Box-row')[:5] # 取前5个热门
        
        results = []
        for repo in repos:
            name = repo.h2.a.get('href').strip()
            desc_tag = repo.p
            desc = desc_tag.get_text().strip() if desc_tag else "无描述"
            link = f"https://github.com{name}"
            results.append(f"<b>{name}</b><br/>描述: {desc}<br/>链接: <a href='{link}'>{link}</a>")
        return results
    except Exception as e:
        print(f"GitHub 抓取失败: {e}")
        return ["GitHub 抓取失败，请检查网络连接"]

def get_hf_trending():
    """抓取 Hugging Face 热门模型"""
    print("[2/3] 正在抓取 Hugging Face 热门模型...")
    url = "https://huggingface.co/api/models?sort=trending&limit=5"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        results = []
        for item in data:
            model_id = item.get('modelId', 'Unknown')
            tag = item.get('pipeline_tag', 'unknown')
            link = f"https://huggingface.co/{model_id}"
            results.append(f"模型: <a href='{link}'>{model_id}</a> (任务类型: {tag})")
        return results
    except Exception as e:
        print(f"Hugging Face 抓取失败: {e}")
        return ["Hugging Face 抓取失败"]

def get_arxiv_cs_cl():
    """抓取 ArXiv CL (NLP/LLM) 最新论文"""
    print("[3/3] 正在抓取 ArXiv 论文...")
    # cs.CL: 计算与语言 (NLP/LLM)，cs.CV: 计算机视觉
    feed_url = "http://export.arxiv.org/api/query?search_query=cat:cs.CL&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending"
    try:
        feed = feedparser.parse(feed_url)
        results = []
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            summary = entry.summary.replace('\n', ' ')[:80] + "..."
            results.append(f"论文: <a href='{link}'>{title}</a><br/>摘要: {summary}")
        return results
    except Exception as e:
        print(f"ArXiv 抓取失败: {e}")
        return ["ArXiv 抓取失败"]

# ================= 邮件发送功能 (QQ邮箱版) =================

def send_qq_email(subject, html_content):
    print("正在准备发送邮件...")
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = SENDER_QQ
    message['To'] = RECEIVER_EMAIL
    
    # 将内容包装为 HTML 格式，这样点击链接更方便
    full_html = f"""
    <html>
    <body>
    <h2>今日 AI 前沿速递</h2>
    <p>工程师你好，以下是今天 AI 领域最火的开源项目、模型和论文：</p>
    
    <h3>🔥 GitHub Trending (Python/AI)</h3>
    <ul>
        {''.join([f'<li>{item}</li>' for item in html_content["github"]])}
    </ul>
    
    <h3>🤗 Hugging Face 热门模型</h3>
    <ul>
        {''.join([f'<li>{item}</li>' for item in html_content["hf"]])}
    </ul>
    
    <h3>📄 ArXiv 最新论文 (NLP/LLM)</h3>
    <ul>
        {''.join([f'<li>{item}</li>' for item in html_content["arxiv"]])}
    </ul>
    
    <br/>
    <p>--- 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M")} ---</p>
    </body>
    </html>
    """
    
    part = MIMEText(full_html, 'html', 'utf-8')
    message.attach(part)
    
    try:
        # QQ邮箱使用 SSL 加密，端口 465
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(SENDER_QQ, AUTH_CODE)
            server.sendmail(SENDER_QQ, RECEIVER_EMAIL, message.as_string())
            print("✅ 邮件发送成功！请检查收件箱。")
    except smtplib.SMTPAuthenticationError:
        print("❌ 登录失败：请检查邮箱地址和授权码是否正确！(注意：密码处需填写授权码)")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

# ================= 主逻辑 =================

def generate_report():
    # 1. 抓取数据
    github_data = get_github_trending()
    hf_data = get_hf_trending()
    arxiv_data = get_arxiv_cs_cl()
    
    content = {
        "github": github_data,
        "hf": hf_data,
        "arxiv": arxiv_data
    }
    
    # 2. 发送邮件
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"【AI日报】{today} - GitHub热门与前沿论文"
    send_qq_email(subject, content)

if __name__ == "__main__":
    generate_report()
