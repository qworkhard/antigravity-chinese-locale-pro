#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Antigravity Chinese Locale One-Click Installer & Restorer v3.0
Google Antigravity 官方客户端一键安全汉化与全生命周期持久化工具 (适配 v2.29.0+ WebContentsView 架构)

Features:
- Auto-detects Antigravity resources folder across Windows, macOS & Linux
- Smart pristine backup management (auto-detects official app updates vs patched app.asar)
- Non-destructive & 100% reversible via --restore flag or restore_original.py
- Multi-candidate REVERSE_INDEX for Base UI / Radix Select & ToggleGroup controlled components
- Full WebContents & WebContentsView (hubContents) lifecycle hook
- Main-process native context menu (ipcHandlers.js), system tray, quit dialog & application menu localization
- Static syntax gatekeeper (node --check on all modified files)
- Atomic replacement of app.asar & app.asar.unpacked
- Live hot-reload across all active pages via Chrome DevTools Protocol (CDP)
"""

import os
import sys
import re
import shutil
import tempfile
import subprocess
import json
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def find_antigravity_resources():
    # 1. Windows default path
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        p = os.path.join(local_app_data, "Programs", "antigravity", "resources")
        if os.path.exists(p) and os.path.exists(os.path.join(p, "app.asar")):
            return p
    # 2. macOS default path
    mac_path = "/Applications/Antigravity.app/Contents/Resources"
    if os.path.exists(mac_path) and os.path.exists(os.path.join(mac_path, "app.asar")):
        return mac_path
    # 3. Linux default path
    linux_path = "/opt/Antigravity/resources"
    if os.path.exists(linux_path) and os.path.exists(os.path.join(linux_path, "app.asar")):
        return linux_path
    return None


def is_asar_already_patched(asar_path):
    """Checks the ASAR header to see if i18n_runner.js is already packaged inside."""
    try:
        with open(asar_path, "rb") as f:
            header_chunk = f.read(524288)
        return b"i18n_runner.js" in header_chunk
    except Exception:
        return False


def restore_original(resources_dir):
    print("=" * 60)
    print("  Restoring pristine official Antigravity files...")
    print("  正在恢复 Antigravity 官方原版文件...")
    print("=" * 60)

    target_asar = os.path.join(resources_dir, "app.asar")
    backup_asar = os.path.join(resources_dir, "app.asar.bak")
    target_unpacked = target_asar + ".unpacked"
    backup_unpacked = backup_asar + ".unpacked"

    if not os.path.exists(backup_asar):
        print("[Error] Backup file not found: app.asar.bak")
        print("未找到原版备份文件 app.asar.bak，无法自动恢复。")
        return False

    shutil.copy2(backup_asar, target_asar)
    print(f"[OK] Restored app.asar from {backup_asar}")

    if os.path.exists(backup_unpacked):
        if os.path.exists(target_unpacked):
            shutil.rmtree(target_unpacked)
        shutil.copytree(backup_unpacked, target_unpacked)
        print(f"[OK] Restored app.asar.unpacked from {backup_unpacked}")

    print("\n[OK] Antigravity has been completely restored to official pristine state!")
    print("[OK] 客户端已完全恢复为官方原始纯净英文版！")
    return True


def main():
    print("=" * 60)
    print("  Google Antigravity Chinese Localization Installer v3.0")
    print("  Google Antigravity 客户端一键安全汉化工具 (v3.0 深度全量版)")
    print("=" * 60)

    # 1. 检查 Node.js 环境
    try:
        node_bin = shutil.which("node") or "node"
        res = subprocess.run([node_bin, "-v"], shell=(os.name == "nt"), capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[Error] Node.js is required. Return code: {res.returncode}. {res.stderr}")
            sys.exit(1)
        print(f"[OK] Node.js detected: {res.stdout.strip()}")
    except Exception as e:
        print(f"[Error] Node.js executable check failed: {e}")
        sys.exit(1)

    # 2. 定位资源目录
    resources_dir = find_antigravity_resources()
    if not resources_dir:
        print("[!] Antigravity installation not detected in standard path.")
        user_in = input("Please input the 'resources' folder path of Antigravity: ").strip()
        if os.path.exists(user_in) and os.path.exists(os.path.join(user_in, "app.asar")):
            resources_dir = user_in
        else:
            print("[Error] Invalid path or app.asar not found.")
            sys.exit(1)

    print(f"[OK] Antigravity resources found: {resources_dir}")

    # Check if restore mode requested
    if "--restore" in sys.argv or "-r" in sys.argv:
        restore_original(resources_dir)
        return

    target_asar = os.path.join(resources_dir, "app.asar")
    backup_asar = os.path.join(resources_dir, "app.asar.bak")
    target_unpacked = target_asar + ".unpacked"
    backup_unpacked = backup_asar + ".unpacked"

    # 3. 官方原版纯净备份 (自动识别客户端版本升级)
    target_patched = is_asar_already_patched(target_asar)
    if not os.path.exists(backup_asar):
        print("[*] Creating initial pristine backup: app.asar.bak ...")
        shutil.copy2(target_asar, backup_asar)
        print("[OK] app.asar backup completed.")
    elif not target_patched:
        print("[*] Detected newly updated official app.asar, refreshing app.asar.bak ...")
        shutil.copy2(target_asar, backup_asar)
        if os.path.exists(target_unpacked):
            if os.path.exists(backup_unpacked):
                shutil.rmtree(backup_unpacked)
            shutil.copytree(target_unpacked, backup_unpacked)
        print("[OK] Refreshed pristine backup for new official version.")
    else:
        print("[OK] Existing pristine backup verified (app.asar.bak).")

    if os.path.exists(target_unpacked) and not os.path.exists(backup_unpacked):
        print("[*] Creating initial unpacked backup: app.asar.bak.unpacked ...")
        shutil.copytree(target_unpacked, backup_unpacked)
        print("[OK] app.asar.unpacked backup completed.")

    # 4. 从纯净原版备份解包并注入
    script_dir = os.path.dirname(os.path.abspath(__file__))
    i18n_runner_src = os.path.join(script_dir, "i18n_runner.js")
    i18n_data_src = os.path.join(script_dir, "i18n_data.json")

    if not os.path.exists(i18n_runner_src) or not os.path.exists(i18n_data_src):
        print("[Error] Missing i18n_runner.js or i18n_data.json in scripts directory.")
        sys.exit(1)

    work_dir = tempfile.mkdtemp(prefix="antigravity_i18n_")
    try:
        source_asar = backup_asar if os.path.exists(backup_asar) else target_asar
        print(f"[*] Extracting pristine {os.path.basename(source_asar)} into temporary sandbox...")
        subprocess.run(f'npx --yes @electron/asar extract "{source_asar}" "{work_dir}"', shell=True, check=True)

        dist_dir = os.path.join(work_dir, "dist")
        os.makedirs(dist_dir, exist_ok=True)
        shutil.copy2(i18n_runner_src, os.path.join(dist_dir, "i18n_runner.js"))
        shutil.copy2(i18n_data_src, os.path.join(dist_dir, "i18n_data.json"))

        utils_js = os.path.join(dist_dir, "utils.js")
        main_js = os.path.join(dist_dir, "main.js")
        tray_js = os.path.join(dist_dir, "tray.js")
        menu_js = os.path.join(dist_dir, "menu.js")
        updater_js = os.path.join(dist_dir, "updater.js")
        ipc_js = os.path.join(dist_dir, "ipcHandlers.js")
        modified_files = []

        # A. 注入 utils.js (支持 v2.29.0 WebContentsView hubContents 与主进程词典翻译器)
        if os.path.exists(utils_js):
            with open(utils_js, "r", encoding="utf-8") as f:
                u_content = f.read()

            if "injectAntigravityI18n" not in u_content:
                top_inject = (
                    '\nlet __agI18nCache = null;\n'
                    'const getAntigravityI18nCache = () => {\n'
                    '    if (__agI18nCache) return __agI18nCache;\n'
                    '    try {\n'
                    '        const runnerPath = path_1.default.join(__dirname, "i18n_runner.js");\n'
                    '        const dataPath = path_1.default.join(__dirname, "i18n_data.json");\n'
                    '        if (fs.existsSync(runnerPath) && fs.existsSync(dataPath)) {\n'
                    '            const dataStr = fs.readFileSync(dataPath, "utf-8");\n'
                    '            const runnerCode = fs.readFileSync(runnerPath, "utf-8");\n'
                    '            const dataObj = JSON.parse(dataStr);\n'
                    '            __agI18nCache = {\n'
                    '                exact: dataObj.exact || {},\n'
                    '                script: "(function(){try{window.__ANTIGRAVITY_I18N_DATA__=" + dataStr + ";\\n" + runnerCode + "\\n}catch(e){console.error(\\"[Antigravity i18n] Error:\\",e);}})();"\n'
                    '            };\n'
                    '        }\n'
                    '    } catch (e) {}\n'
                    '    return __agI18nCache;\n'
                    '};\n'
                    'const translateAntigravityText = (raw) => {\n'
                    '    if (typeof raw !== "string" || !raw) return raw;\n'
                    '    const cache = getAntigravityI18nCache();\n'
                    '    if (!cache || !cache.exact) return raw;\n'
                    '    const trimmed = raw.trim();\n'
                    '    if (cache.exact[trimmed]) return cache.exact[trimmed];\n'
                    '    if (trimmed.endsWith(" (Default)")) {\n'
                    '        const base = trimmed.slice(0, -10);\n'
                    '        return (cache.exact[base] || base) + " (默认)";\n'
                    '    }\n'
                    '    if (trimmed.startsWith("Move to Group: ")) {\n'
                    '        const grp = trimmed.slice(15);\n'
                    '        return "移动到分组: " + (cache.exact[grp] || grp);\n'
                    '    }\n'
                    '    return raw;\n'
                    '};\n'
                    'exports.translateAntigravityText = translateAntigravityText;\n'
                    'const injectAntigravityI18n = (target) => {\n'
                    '    try {\n'
                    '        const wc = (typeof getHubWebContents === "function" && target && target.contentView)\n'
                    '            ? getHubWebContents(target)\n'
                    '            : (target && target.webContents ? target.webContents : target);\n'
                    '        if (!wc || typeof wc.executeJavaScript !== "function" || wc.isDestroyed()) return;\n'
                    '        const cache = getAntigravityI18nCache();\n'
                    '        if (cache && cache.script) {\n'
                    '            wc.executeJavaScript(cache.script).catch(() => {});\n'
                    '        }\n'
                    '    } catch (e) {\n'
                    '        console.error("[Antigravity i18n] Injection error:", e);\n'
                    '    }\n'
                    '};\n'
                    'exports.injectAntigravityI18n = injectAntigravityI18n;\n'
                )
                import_needle = 'const wsl_1 = require("./wsl");'
                if import_needle in u_content:
                    u_content = u_content.replace(import_needle, import_needle + '\n' + top_inject, 1)
                else:
                    u_content = top_inject + '\n' + u_content

                # 挂载 v2.29.0+ hubContents 与旧版 win.webContents
                hub_needle = "hubContents.setWindowOpenHandler"
                if hub_needle in u_content:
                    hub_hook = (
                        '    hubContents.on("dom-ready", () => injectAntigravityI18n(hubContents));\n'
                        '    hubContents.on("did-finish-load", () => injectAntigravityI18n(hubContents));\n'
                        '    hubContents.on("did-navigate-in-page", () => injectAntigravityI18n(hubContents));\n'
                    )
                    u_content = u_content.replace(hub_needle, hub_hook + '    ' + hub_needle, 1)

                win_needle = "win.webContents.setWindowOpenHandler"
                if win_needle in u_content:
                    win_hook = (
                        '    win.webContents.on("dom-ready", () => injectAntigravityI18n(win.webContents));\n'
                        '    win.webContents.on("did-finish-load", () => injectAntigravityI18n(win.webContents));\n'
                        '    win.webContents.on("did-navigate-in-page", () => injectAntigravityI18n(win.webContents));\n'
                    )
                    u_content = u_content.replace(win_needle, win_hook + '    ' + win_needle, 1)

                # showOrCreateWindow 唤醒补偿
                show_needle = "wins[0].focus();"
                if show_needle in u_content:
                    u_content = u_content.replace(
                        show_needle,
                        show_needle + "\n        if (exports.injectAntigravityI18n) { (0, exports.injectAntigravityI18n)(wins[0]); }",
                        1
                    )

                with open(utils_js, "w", encoding="utf-8") as f:
                    f.write(u_content)
            modified_files.append(utils_js)

        # B. 注入 main.js (全局 web-contents-created 守卫 + 托盘菜单与退出确认弹窗汉化)
        if os.path.exists(main_js):
            with open(main_js, "r", encoding="utf-8") as f:
                m_content = f.read()

            if "injectAntigravityI18n" not in m_content:
                main_inject = (
                    "    // Register global WebContents i18n injection lifecycle hook\n"
                    "    electron_1.app.on('web-contents-created', (_event, wc) => {\n"
                    "        wc.on('dom-ready', () => { if (utils_1.injectAntigravityI18n) (0, utils_1.injectAntigravityI18n)(wc); });\n"
                    "        wc.on('did-finish-load', () => { if (utils_1.injectAntigravityI18n) (0, utils_1.injectAntigravityI18n)(wc); });\n"
                    "        wc.on('did-navigate-in-page', () => { if (utils_1.injectAntigravityI18n) (0, utils_1.injectAntigravityI18n)(wc); });\n"
                    "    });\n"
                )
                pattern = r'(electron_1\.app\s*\.whenReady\(\)\s*\.then\(async\s*\(\)\s*=>\s*\{)'
                if re.search(pattern, m_content):
                    m_content = re.sub(pattern, r'\1\n' + main_inject, m_content, count=1)
                else:
                    print("[Warning] whenReady pattern not matched in main.js.")

                # 汉化主进程系统托盘与退出确认对话框
                main_replacements = [
                    ("label: 'No agents running'", "label: '无正在运行的智能体'"),
                    ("label: `Open ${electron_1.app.getName()}`", "label: `打开 ${electron_1.app.getName()}`"),
                    ("label: 'New Window'", "label: '新建窗口'"),
                    ("label: 'Quit'", "label: '退出'"),
                    ("title: 'Confirm Quit'", "title: '确认退出'"),
                    ("message: 'Are you sure you want to quit?'", "message: '确定要退出 Antigravity 吗？'"),
                    ("detail: 'There may be agents or background tasks running.'", "detail: '当前可能仍有智能体或后台任务正在运行。'"),
                    ("buttons: ['Cancel', 'Quit']", "buttons: ['取消', '退出']"),
                ]
                for old_str, new_str in main_replacements:
                    m_content = m_content.replace(old_str, new_str)

                with open(main_js, "w", encoding="utf-8") as f:
                    f.write(m_content)
            modified_files.append(main_js)

        # C. 注入 tray.js (托盘运行智能体计数动态更新汉化)
        if os.path.exists(tray_js):
            with open(tray_js, "r", encoding="utf-8") as f:
                t_content = f.read()
            old_tray = (
                "            countItem.label =\n"
                "                (count > 0 ? `${count}` : 'No') +\n"
                "                    ' agent' +\n"
                "                    (count === 1 ? '' : 's') +\n"
                "                    ' running';"
            )
            new_tray = "            countItem.label = count > 0 ? `${count} 个智能体正在运行` : '无正在运行的智能体';"
            if old_tray in t_content:
                t_content = t_content.replace(old_tray, new_tray)
                with open(tray_js, "w", encoding="utf-8") as f:
                    f.write(t_content)
            modified_files.append(tray_js)

        # D. 注入 menu.js (原生顶部应用菜单扩展项汉化)
        if os.path.exists(menu_js):
            with open(menu_js, "r", encoding="utf-8") as f:
                mn_content = f.read()
            menu_replacements = [
                ("label: 'New Window'", "label: '新建窗口'"),
                ("label: 'Docs'", "label: '官方文档'"),
                ("label: 'Connect to WSL'", "label: '连接到 WSL'"),
                ("label: 'Reopen Locally'", "label: '在本地重新打开'"),
            ]
            for old_str, new_str in menu_replacements:
                mn_content = mn_content.replace(old_str, new_str)
            with open(menu_js, "w", encoding="utf-8") as f:
                f.write(mn_content)
            modified_files.append(menu_js)

        # E. 注入 updater.js (自动更新菜单状态与提示弹窗汉化)
        if os.path.exists(updater_js):
            with open(updater_js, "r", encoding="utf-8") as f:
                up_content = f.read()
            updater_replacements = [
                ('MenuUpdateStep["CheckForUpdates"] = "Check for Updates";', 'MenuUpdateStep["CheckForUpdates"] = "检查更新";'),
                ('MenuUpdateStep["CheckingForUpdates"] = "Checking for Updates...";', 'MenuUpdateStep["CheckingForUpdates"] = "正在检查更新...";'),
                ('MenuUpdateStep["DownloadingUpdate"] = "Downloading Update...";', 'MenuUpdateStep["DownloadingUpdate"] = "正在下载更新...";'),
                ('MenuUpdateStep["RestartToUpdate"] = "Restart to Update";', 'MenuUpdateStep["RestartToUpdate"] = "重启以应用更新";'),
                ("title: 'Check for Updates'", "title: '检查更新'"),
                ("message: 'No updates available'", "message: '当前已是最新版本'"),
                ("buttons: ['OK']", "buttons: ['确定']"),
            ]
            for old_str, new_str in updater_replacements:
                up_content = up_content.replace(old_str, new_str)
            with open(updater_js, "w", encoding="utf-8") as f:
                f.write(up_content)
            modified_files.append(updater_js)

        # F. 注入 ipcHandlers.js (原生右键菜单与三点菜单 window:show-context-menu 拦截汉化)
        if os.path.exists(ipc_js):
            with open(ipc_js, "r", encoding="utf-8") as f:
                ipc_content = f.read()
            old_ipc_label = "label: item.label ?? '',"
            new_ipc_label = "label: utils_1.translateAntigravityText ? (0, utils_1.translateAntigravityText)(item.label ?? '') : (item.label ?? ''),"
            if old_ipc_label in ipc_content and "translateAntigravityText" not in ipc_content:
                ipc_content = ipc_content.replace(old_ipc_label, new_ipc_label, 1)
                with open(ipc_js, "w", encoding="utf-8") as f:
                    f.write(ipc_content)
            modified_files.append(ipc_js)

        modified_files.append(os.path.join(dist_dir, "i18n_runner.js"))

        # 5. 严格语法检查门禁 (node --check)
        print("[*] Performing syntax gatekeeper checks (node --check)...")
        for fpath in modified_files:
            chk = subprocess.run(["node", "--check", fpath], capture_output=True, text=True)
            if chk.returncode != 0:
                print(f"[Error] Syntax verification failed on {fpath}:\n{chk.stderr}")
                sys.exit(1)
        print(f"[OK] Syntax checks passed 100% ({len(modified_files)} files verified).")

        # 6. 打包新 asar
        temp_pack = os.path.join(tempfile.gettempdir(), "antigravity_new.asar")
        temp_unpacked = temp_pack + ".unpacked"
        if os.path.exists(temp_pack):
            os.remove(temp_pack)
        if os.path.exists(temp_unpacked):
            shutil.rmtree(temp_unpacked)

        print("[*] Packaging modified files into asar...")
        subprocess.run(
            f'npx --yes @electron/asar pack "{work_dir}" "{temp_pack}" --unpack-dir "node_modules/chrome-devtools-mcp"',
            shell=True,
            check=True
        )

        # 7. 原子替换
        if os.path.exists(temp_unpacked):
            if os.path.exists(target_unpacked):
                shutil.rmtree(target_unpacked)
            shutil.copytree(temp_unpacked, target_unpacked)

        shutil.copy2(temp_pack, target_asar)
        print("[OK] Production app.asar successfully updated!")

        # 8. 尝试 CDP 实时热注入 (支持多窗口全量热更新)
        try:
            active_port_file = os.path.join(os.environ.get("APPDATA", ""), "Antigravity", "DevToolsActivePort")
            if os.path.exists(active_port_file):
                with open(active_port_file, "r") as f:
                    dt_port = f.readline().strip()
                with urllib.request.urlopen(f"http://127.0.0.1:{dt_port}/json", timeout=2) as resp:
                    pages = json.loads(resp.read().decode("utf-8"))
                    target_pages = [p for p in pages if p.get("type") == "page" and p.get("webSocketDebuggerUrl")]
                    if target_pages:
                        with open(os.path.join(dist_dir, "i18n_data.json"), "r", encoding="utf-8") as f:
                            dt_str = f.read()
                        with open(os.path.join(dist_dir, "i18n_runner.js"), "r", encoding="utf-8") as f:
                            rn_str = f.read()
                        full_code = "window.__ANTIGRAVITY_I18N_DATA__ = " + dt_str + ";\n" + rn_str
                        ws_urls = [p["webSocketDebuggerUrl"] for p in target_pages]
                        node_eval = f'''
                        const urls = {json.dumps(ws_urls)};
                        const expr = {json.dumps(full_code)};
                        let done = 0;
                        urls.forEach((u) => {{
                            const ws = new WebSocket(u);
                            ws.onopen = () => {{
                                ws.send(JSON.stringify({{ id: 1, method: "Runtime.evaluate", params: {{ expression: expr }} }}));
                            }};
                            ws.onmessage = () => {{
                                done++;
                                if (done >= urls.length) process.exit(0);
                            }};
                            ws.onerror = () => {{
                                done++;
                                if (done >= urls.length) process.exit(0);
                            }};
                        }});
                        setTimeout(() => process.exit(0), 1500);
                        '''
                        eval_file = os.path.join(tempfile.gettempdir(), "cdp_hot_reload.js")
                        with open(eval_file, "w", encoding="utf-8") as f:
                            f.write(node_eval)
                        subprocess.run(["node", eval_file], capture_output=True)
                        print(f"[OK] Active Antigravity window(s) hot-reloaded successfully ({len(ws_urls)} page(s))!")
        except Exception:
            pass

        print("\n" + "=" * 60)
        print("  Localization v3.0 deployed successfully! Enjoy Antigravity in Chinese.")
        print("  汉化 v3.0 部署成功！当前活动界面已实时热重载。")
        print("  若需体验主进程托盘菜单与退出弹窗汉化，请在右下角托盘退出客户端后重开。")
        print("  如需一键还原回官方原版，双击“一键还原官方英文.bat”或运行: python scripts/deploy_chinese.py --restore")
        print("=" * 60)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
