#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
執行 LINE 財金早報發送
直接執行此檔案即可發送早報到 LINE
"""
import subprocess
import sys
import os

script_path = r"C:\Users\AD83734\OneDrive - 和泰汽車-經銷商\桌面\Claude-workspace\send_line.py"

if not os.path.exists(script_path):
    print(f"❌ 找不到 send_line.py")
    input("按 Enter 鍵關閉...")
    sys.exit(1)

print("⏳ 正在發送 LINE 財金早報...\n")

try:
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8')

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print("\n✅ 發送成功！")
    else:
        print(f"\n⚠️ 發送可能出錯（代碼：{result.returncode}）")

except Exception as e:
    print(f"❌ 執行出錯：{e}")

input("\n按 Enter 鍵關閉...")
