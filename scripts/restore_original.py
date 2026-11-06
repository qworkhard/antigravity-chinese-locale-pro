#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Antigravity Restore Script
一键无损恢复 Google Antigravity 官方原版英文状态
"""

import os
import sys
import shutil

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def find_antigravity_resources():
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        p = os.path.join(local_app_data, "Programs", "antigravity", "resources")
        if os.path.exists(p) and os.path.exists(os.path.join(p, "app.asar")):
            return p
    mac_path = "/Applications/Antigravity.app/Contents/Resources"
    if os.path.exists(mac_path) and os.path.exists(os.path.join(mac_path, "app.asar")):
        return mac_path
    linux_path = "/opt/Antigravity/resources"
    if os.path.exists(linux_path) and os.path.exists(os.path.join(linux_path, "app.asar")):
        return linux_path
    return None

def main():
    print("=" * 60)
    print("  Antigravity Official Restore Tool")
    print("  Google Antigravity 官方原版一键无损还原工具")
    print("=" * 60)

    resources_dir = find_antigravity_resources()
    if not resources_dir:
        print("[!] Antigravity installation not detected in standard path.")
        user_in = input("Please input the 'resources' folder path of Antigravity: ").strip()
        if os.path.exists(user_in) and os.path.exists(os.path.join(user_in, "app.asar")):
            resources_dir = user_in
        else:
            print("[Error] Invalid path or app.asar not found.")
            sys.exit(1)

    target_asar = os.path.join(resources_dir, "app.asar")
    backup_asar = os.path.join(resources_dir, "app.asar.bak")
    target_unpacked = target_asar + ".unpacked"
    backup_unpacked = backup_asar + ".unpacked"

    if not os.path.exists(backup_asar):
        print(f"[Error] Backup file not found at: {backup_asar}")
        print("未检测到备份文件 app.asar.bak，无法自动恢复。")
        sys.exit(1)

    print(f"[*] Restoring pristine app.asar from: {backup_asar} ...")
    shutil.copy2(backup_asar, target_asar)
    print("[OK] app.asar restored successfully.")

    if os.path.exists(backup_unpacked):
        print(f"[*] Restoring pristine app.asar.unpacked ...")
        if os.path.exists(target_unpacked):
            shutil.rmtree(target_unpacked)
        shutil.copytree(backup_unpacked, target_unpacked)
        print("[OK] app.asar.unpacked restored successfully.")

    print("\n" + "=" * 60)
    print("  Antigravity has been 100% restored to official pristine status!")
    print("  Antigravity 客户端已完整恢复为官方纯净原版！")
    print("  请重启客户端使还原生效。")
    print("=" * 60)

if __name__ == "__main__":
    main()
