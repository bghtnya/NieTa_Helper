import os
import time
import requests
from datetime import datetime

# === 配置区 ===
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NjExNzk0OCwidXVpZCI6IjQ1YzhmNDQ0ZmFmYzRkODI5NDk3NDUzODg1N2M4ZjQ3IiwicGhvbmVfbnVtIjoiMTM3NjEzOTQzNDMiLCJleHBpcmVzX2F0IjoxNzkzMzQ4MTcyLCJpc19yZWdpc3RlciI6ZmFsc2UsInVzZXJfYWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTQxLjAuMC4wIFNhZmFyaS81MzcuMzYgRWRnLzE0MS4wLjAuMCIsInNhbHQiOiJkYWMyOTE4MzQyY2Q0ZWVkYWMyM2UyYzI4MzBjOGRjOCJ9.rXc6T4Rb6xHSMzQQ1VSvHgArTD7kGi9f3nbI10mMJeY"
API_LIST = "https://api.talesofai.cn/v1/artifact/list"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "x-token": TOKEN,
}
SAVE_DIR_STAR = "./pic"
SAVE_DIR_NOSTAR = "./pic_nostar"
LOG_FILE = "./nieta_auto.log"

# === 基础函数 ===
def log(msg: str):
    t = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    text = f"{t} {msg}"
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

os.makedirs(SAVE_DIR_STAR, exist_ok=True)
os.makedirs(SAVE_DIR_NOSTAR, exist_ok=True)

# === 签到 ===
def auto_sign():
    """自动签到"""
    log("开始自动签到...")
    try:
        r = requests.post("https://api.talesofai.cn/v1/user/sign_in", headers=HEADERS, timeout=15)
        res = r.json()
        print(res)
        if r.status_code == 200:
            if res.get("msg") == "ok":
                log(f"✅ 签到成功 返回：{res}")
            else:
                log(f"⚠️ 签到返回：{res}")
        else:
            log(f"❌ 签到返回：{res}")
    except Exception as e:
        log(f"❌ 签到异常：{e}")

# === 下载函数 ===
def download_artifacts():
    """分页下载所有 artifact 图片"""
    log("开始拉取 artifact 列表...")
    page = 1
    total_downloaded = 0

    while True:
        try:
            params = {"page": page, "page_size": 50}
            r = requests.get(API_LIST, headers=HEADERS, params=params, timeout=20)
            if r.status_code != 200:
                log(f"⚠️ 第 {page} 页请求失败：HTTP {r.status_code}")
                break

            res = r.json()
            data = res.get("list", [])
            if not data:
                log(f"📘 第 {page} 页为空，停止翻页")
                break

            log(f"📄 第 {page} 页，共 {len(data)} 个作品")

            for item in data:
                url = item.get("url")
                if not url or item.get("status") != "SUCCESS":
                    continue

                is_starred = item.get("is_starred", False)
                folder = SAVE_DIR_STAR if is_starred else SAVE_DIR_NOSTAR
                os.makedirs(folder, exist_ok=True)

                filename = os.path.join(folder, f"{item.get('uuid')}.webp")
                if os.path.exists(filename):
                    log(f"⏩ 跳过已存在文件：{filename}")
                    continue

                try:
                    img = requests.get(url, timeout=25)
                    with open(filename, "wb") as f:
                        f.write(img.content)
                    total_downloaded += 1
                    log(f"✅ 下载完成：{filename}")
                    time.sleep(0.5)
                except Exception as e:
                    log(f"❌ 下载失败：{url}，原因：{e}")

            page += 1
            time.sleep(1)

        except Exception as e:
            log(f"❌ 第 {page} 页获取异常：{e}")
            break

    log(f"🎉 全部完成，共下载 {total_downloaded} 个文件")

# === 主程序 ===
if __name__ == "__main__":
    log("=" * 50)
    auto_sign()
    download_artifacts()
    log("=" * 50)
