import json
import os
from datetime import datetime

import requests

# === 配置区 ===
API_URL = "https://api.talesofai.cn/v1/assignment/complete-assignment-action"
UUID = "5aa750e5-d63b-410d-9565-fc7b7381eb31"  # 要完成的任务UUID
TOKEN_FILE = "token.txt"
LOG_FILE = "nieta_assignment.log"


# === 基础函数 ===
def log(msg: str):
    """带时间戳的日志输出"""
    t = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    text = f"{t} {msg}"
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def load_token():
    """读取 token.txt"""
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"❌ 未找到 {TOKEN_FILE} 文件！请在同目录下创建，并写入 token。")
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token = f.read().strip()
    if not token:
        raise ValueError("❌ token.txt 为空！")
    return token


# === 主请求函数 ===
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


# === 主程序入口 ===
if __name__ == "__main__":
    log("=" * 60)
    token = load_token()
    complete_assignment(token, UUID)
    log("=" * 60)
