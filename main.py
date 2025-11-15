import json
import os
import time
import argparse
from datetime import datetime

import requests
from PIL import Image


# === 读取 TOKEN ===
def load_token():
    token_file = "./token.txt"
    if not os.path.exists(token_file):
        raise FileNotFoundError("❌ 未找到 token.txt，请在脚本目录下创建并填入 TOKEN。")
    with open(token_file, "r", encoding="utf-8") as f:
        token = f.read().strip()
    if not token:
        raise ValueError("❌ token.txt 为空，请填入有效 TOKEN。")
    return token

# === 配置区 ===
API_LIST = "https://api.talesofai.cn/v1/artifact/list"
API_SIGN = "https://api.talesofai.cn/v1/checkin/manual"
API_URL = "https://api.talesofai.cn/v1/assignment/complete-assignment-action"
UUID = "5aa750e5-d63b-410d-9565-fc7b7381eb31"  # 要完成的任务UUID

SAVE_DIR_STAR = "./pic"
SAVE_DIR_NOSTAR = "./pic_nostar"
LOG_FILE = "./nieta_auto.log"


# === 日志函数 ===
def log(msg: str):
    t = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    text = f"{t} {msg}"
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

os.makedirs(SAVE_DIR_STAR, exist_ok=True)
os.makedirs(SAVE_DIR_NOSTAR, exist_ok=True)


# === 自动签到 ===
def auto_sign(token):
    log("开始自动签到...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "x-platform": "nieta-app/web",
        "x-nieta-app-version": "5.18.21",
        "x-token": token,
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://app.nieta.art",
        "referer": "https://app.nieta.art/",
    }
    try:
        r = requests.post(API_SIGN, headers=headers, json=None, timeout=15)
        res = r.json()
        if r.status_code == 200:
            log(f"✅ 签到成功：{res}")
        else:
            log(f"⚠️ 签到失败：HTTP {r.status_code} - {res}")
    except Exception as e:
        log(f"❌ 签到异常：{e}")


def complete_assignment(token: str, uuid: str):
    headers = {
        "x-token": token,
        "x-platform": "nieta-app/web",
        "x-nieta-app-version": "5.18.21",
        "content-type": "application/json",
        "origin": "https://app.nieta.art",
        "referer": "https://app.nieta.art/",
        "user-agent": "Mozilla/5.0",
    }

    payload = {"uuid": uuid}

    log(f"开始上报任务完成：{uuid}")
    try:
        r = requests.put(API_URL, headers=headers, json=payload, timeout=15)
        try:
            res = r.json()
        except json.JSONDecodeError:
            res = r.text

        if r.status_code == 200:
            log(f"✅ 请求成功：{res}")
        else:
            log(f"⚠️ 请求失败：HTTP {r.status_code} - {res}")
    except Exception as e:
        log(f"❌ 请求异常：{e}")


# === webp→png 无损转换 ===
def webp_to_png(file_path: str):
    """立即转换 webp -> png 并删除原文件"""
    try:
        png_path = file_path[:-5] + ".png"
        with Image.open(file_path) as img:
            img.save(png_path, "PNG", lossless=True)
        os.remove(file_path)
        log(f"🖼️ 已转换并删除 webp：{os.path.basename(png_path)}")
    except Exception as e:
        log(f"⚠️ 转换失败：{file_path} - {e}")


# === 下载作品 ===
def download_artifacts(token):
    log("开始拉取作品列表...")
    total_downloaded = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "x-platform": "nieta-app/web",
        "x-nieta-app-version": "5.18.21",
        "x-token": token,
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://app.nieta.art",
        "referer": "https://app.nieta.art/",
    }

    try:
        params = {"page": 1, "page_size": 9999999}
        r = requests.get(API_LIST, headers=headers, params=params, timeout=60)
        if r.status_code != 200:
            log(f"⚠️ 请求失败：HTTP {r.status_code}")
            return

        res = r.json()
        data = res.get("list", [])
        if not data:
            log("📘 未获取到作品。")
            return

        total_count = len(data)
        log(f"\n📄 共 {total_count} 个作品：")

        # 输出作品概览（带计数）
        for i, item in enumerate(data, start=1):
            title = item.get("name") or item.get("prompt") or "未命名"
            uuid = item.get("uuid", "unknown")
            starred = "⭐" if item.get("is_starred", False) else "  "
            log(f"({i}/{total_count}) {starred} {uuid} | {title}")

        # 下载逻辑
        for i, item in enumerate(data, start=1):
            url = item.get("url")
            if not url or item.get("status") != "SUCCESS":
                continue

            is_starred = item.get("is_starred", False)
            folder = SAVE_DIR_STAR if is_starred else SAVE_DIR_NOSTAR
            os.makedirs(folder, exist_ok=True)

            uuid = item.get("uuid", str(time.time()))
            filename_webp = os.path.join(folder, f"{uuid}.webp")
            filename_png = filename_webp[:-5] + ".png"

            if os.path.exists(filename_png):
                log(f"⏩ ({i}/{total_count}) 跳过已存在：{filename_png}")
                continue

            try:
                img = requests.get(url, timeout=25)
                with open(filename_webp, "wb") as f:
                    f.write(img.content)
                log(f"✅ ({i}/{total_count}) 下载完成：{filename_webp}")
                webp_to_png(filename_webp)
                total_downloaded += 1
                time.sleep(0.5)
            except Exception as e:
                log(f"❌ ({i}/{total_count}) 下载失败：{url}，原因：{e}")

    except Exception as e:
        log(f"❌ 获取列表异常：{e}")

    log(f"\n🎉 全部完成，共下载并转换 {total_downloaded} 个文件。")


# === 主程序 ===
if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="NieTa 自动化脚本")
    parser.add_argument("--token", type=str, help="API Token")
    parser.add_argument("--no-sign", action="store_true", help="跳过签到")
    parser.add_argument("--no-task", action="store_true", help="跳过完成任务")
    parser.add_argument("--no-download", action="store_true", help="跳过下载")
    args = parser.parse_args()

    # 获取 token：优先从命令行参数，其次从文件
    TOKEN = None
    if args.token:
        TOKEN = args.token.strip()
        log(f"✅ 从命令行参数获取 TOKEN: {TOKEN[:10]}...")
    else:
        try:
            TOKEN = load_token()
            log(f"✅ 从文件获取 TOKEN: {TOKEN[:10]}...")
        except (FileNotFoundError, ValueError) as e:
            log(str(e))
            exit(1)

    log("=" * 60)
    
    # 根据参数决定执行哪些步骤
    if not args.no_sign:
        auto_sign(TOKEN)
        log("=" * 60)
    else:
        log("⏭️ 跳过签到")
        log("=" * 60)
    
    if not args.no_task:
        complete_assignment(TOKEN, UUID)
        log("=" * 60)
    else:
        log("⏭️ 跳过完成任务")
        log("=" * 60)
    
    if not args.no_download:
        download_artifacts(TOKEN)
        log("=" * 60)
    else:
        log("⏭️ 跳过下载")
        log("=" * 60)
        
    log("🎊 所有选定操作完成")