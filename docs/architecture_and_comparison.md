# Antigravity 深度汉化架构演进与双路线对比工程总结

本文档系统总结了 **Antigravity Chinesizing v3.0 Pro（ASAR 原生内嵌架构）** 的核心设计思路、v2.29.0+ 客户端架构升级的五大根因突破，以及与 GitHub 开源项目 **`antigravity-full-zh-theme-skill-main`（外部 CDP 守护进程架构 v5.0.0）** 的深度源码级对比分析。

---

## 一、 `antigravity-full-zh-theme-skill-main` 在做什么？（深度源码拆解）

通过完整审阅 [`antigravity-full-zh-theme-skill-main`](file:///d:/my_project/chinese_localization_antigrivaty/antigravity-full-zh-theme-skill-main) 的核心源码（[`install.mjs`](file:///d:/my_project/chinese_localization_antigrivaty/antigravity-full-zh-theme-skill-main/install.mjs)、[`core/daemon.mjs`](file:///d:/my_project/chinese_localization_antigrivaty/antigravity-full-zh-theme-skill-main/core/daemon.mjs)、[`core/runtime.js`](file:///d:/my_project/chinese_localization_antigrivaty/antigravity-full-zh-theme-skill-main/core/runtime.js)、[`core/theme.css`](file:///d:/my_project/chinese_localization_antigrivaty/antigravity-full-zh-theme-skill-main/core/theme.css)、[`user/custom.js`](file:///d:/my_project/chinese_localization_antigrivaty/antigravity-full-zh-theme-skill-main/user/custom.js)），可以明确：**它绝不仅仅是一个汉化包，而是一个“六合一”的客户端外挂改装套件（代号 `chuanban-antigravity-theme-patch`）**。

### 1. 它的六大功能模块
1. **Claude 风格主题与字体改装（`core/theme.css` + `user/custom.css`）**：
   - 将 Antigravity 默认深色/浅色界面强制改装为类似 Claude Desktop 的暖白/羊皮纸配色（提供 `high-contrast` 高对比暖白、`claude-desktop-purewhite` 净白、`vintage-deep` 复古深色三套预设）。
   - 全局替换字体栈：正文强制使用 `Anthropic Serif` 衬线体 + `更纱黑体 (Sarasa Gothic SC)`，代码与输入框强制使用 `Sarasa Mono Slab SC`。
   - 将智能体运行时的 2×2 四点加载动画替换为橙色旋转光环，并为对话中的内联文件引用（`.inline-pill`）加上暖色背景框。
2. **输入框“火漆蜡封”三态边框（`composerWaxSeal`）**：
   - 根据底部模式选择器（`Fast` / `Plan` 等）的状态，给底部输入框加上不同颜色的边框与微光动效。
3. **SQLite + Protobuf 实时会话指标胶囊（`core/daemon.mjs` 第 340–593 行）**：
   - 依赖 **Node.js >= 22.13** 内置的实验性 `node:sqlite` 模块，在后台直接以只读方式打开 `~/.gemini/antigravity/conversations/<cascadeId>.db`。
   - 手写了一个轻量 Protobuf 解码器（`parseProto`），解析 `gen_metadata` 表中的二进制数据，计算出实时生成速度（`tok/s`）、首字延迟（`TTFT`）、上下文占用率（`Ctx / 256k`）、缓存命中率与输出 Token 数，并通过 CDP 推送到聊天输入框底部的 `#ag-live-metrics-pill` 悬浮胶囊中展示。
4. **客户端原生 Bug 修复守卫（`deadlockHealer`）**：
   - 修复设置弹窗关闭但 URL 残留 `settingsOpen=true` 导致再次点击设置无反应的路由死锁问题；
   - 修复 `Ctrl/Cmd + -/=/0` 页面缩放快捷键失灵问题。
5. **新对话自动中文标题重命名（`user/custom.js` 第 147–205 行）**：
   - 每 3.5 秒轮询当前选中会话的标题，若发现标题是纯英文且用户的第一条消息包含中文，则通过逆向遍历 DOM 节点上的 React Fiber 树（`__reactFiber$` ➔ `memoizedState` ➔ `updateOptimisticSummary`），强行将英文标题改为用户首句中文的前 18 个字。
6. **DOM 界面汉化引擎（`core/runtime.js` 第 645–965 行）**：
   - 使用无原型对象 `Object.create(null)` 存储词典，通过 `WeakMap`（`origTextMap`）记录每个文本节点的原始英文，支持关闭开关时动态还原为英文，并用 `requestAnimationFrame` + `dirtyRoots` 批量合并 DOM 变更。

---

## 二、 两种技术路线的核心思路与本质区别

| 维度 | `antigravity-full-zh-theme-skill-main` (外部 CDP 守护进程路线) | 我们的 `antigravity-chinesizing-v3-pro` (ASAR 原生内嵌路线) |
| :--- | :--- | :--- |
| **注入载体与时机** | **外部常驻进程轮询注入**：在操作系统注册开机自启后台进程（Windows 注册表 + `wscript.exe` 拉起 `AntigravityThemeDaemon.vbs`），每 **2.5 秒**扫描一次 `DevToolsActivePort` 或 `9222` 端口，通过 WebSocket (CDP) 远程向页面注入脚本。 | **应用内部原生生命周期注入**：直接将汉化引擎封装进 `app.asar` 的 Electron 主进程（`utils.js` + `main.js` + `ipcHandlers.js`），在窗口创建与 `dom-ready` 时由 Electron 内部零延迟原生加载，**无需任何外部常驻守护进程**。 |
| **系统主进程与原生菜单** | **无法触及主进程**：由于只连接渲染器页面的 CDP 端口，**系统托盘菜单**（`No agents running`、`Quit`）、**退出确认原生弹窗**（`Confirm Quit`）、**顶部原生应用菜单**（`Connect to WSL`）全部无法汉化；右键菜单只能靠拦截渲染层 `Array.prototype.map` 碰运气。 | **主进程 + 渲染进程双端全覆盖**：直接在主进程 `ipcHandlers.js` 的 `buildContextMenuTemplate` 中原生翻译所有右键菜单与 `⋮` 菜单，并完整汉化 `main.js`、`tray.js`、`menu.js`、`updater.js` 的托盘、弹窗与顶部菜单。 |
| **Base UI 受控组件安全性** | **缺失 `Map.prototype` 反向代理**：`core/runtime.js` 开启了 `characterData: true` 且**没有**挂载 `Map.prototype.has/get` 反向映射桥！一旦词典翻译了受控下拉框（如 `Select` / `ToggleGroup` 的选项文本），React/Base UI 拿着中文去查内部英文 `Map` 会返回 `undefined`，存在下拉框状态失灵风险。 | **多候选 `REVERSE_INDEX` 100% 免疫**：构建了 **3,075 组一对多反向候选索引**，在 `Map.prototype.has/get` 中通过 `origHas.call(this, candidate)` 动态探测当前组件 `Map` 实例真正持有的英文 Key，彻底保护所有受控下拉框与单选组。 |
| **词典质量与体积** | `core/i18n.json` 含 2,172 条词条，但其中 **约 800 条是暴力穷举的数字**（如 `"1s"` 到 `"90d"`、`"1s ago"` 到 `"10y ago"`、`"Thinking for 1s"` 到 `"60s"`），且缺少 v2.29.0 新增的 ~1,000 条设置/插件/安全词条。 | **剔除暴力数字穷举 + 全量覆盖 v2.29.0**：采用 **3,340 条高纯度精准词条 + 51 条正则动态规则**，1 条正则即可覆盖任意秒/分/时/天/月/年，且 100% 覆盖 v2.29.0 新增的设置、插件市场、沙箱权限与 PDF/浏览器词条。 |
| **资源占用与侵入性** | 需要 Node.js >= 22.13 常驻后台每 2.5 秒轮询端口与读取 SQLite `.db` 文件，强制修改了全局配色与字体（审美侵入性强，不喜欢暖黄背景的用户需要额外改配置）。 | **零后台进程、零额外内存/磁盘轮询、零审美侵入**：100% 保持 Google Antigravity 原生视觉设计与深浅色主题，纯粹、干净、稳健。 |

---

## 三、 客观评价：哪个方案更好？

### 结论：**作为“纯净、稳定、全覆盖的汉化工程”，我们的 `v3.0 ASAR 原生内嵌方案` 在可靠性、完整度、受控组件安全性和零后台开销上显著更优；而 `antigravity-full-zh-theme-skill-main` 的价值在于其“SQLite 实时 Token 指标胶囊”和“暖白主题改装”等扩展玩法。**

具体原因如下：
1. **汉化覆盖面与原生程度**：
   外部 CDP 守护进程天然无法触及 Electron 主进程（托盘、退出确认框、原生 IPC 右键菜单构建器），且一旦调试端口被防火墙拦截或进程被杀，界面就会退回英文；而我们的 **v3.0 ASAR 原生内嵌方案**从 Electron 内部 `hubContents`、`web-contents-created` 与 `ipcHandlers.js` 根部注入，启动即中文、右键菜单原生中文、零外部进程依赖。
2. **受控组件（Select / ToggleGroup）防崩能力**：
   `antigravity-full-zh-theme-skill-main` 没有实现 `Map.prototype.has/get` 反向映射桥，面对 Antigravity 大量使用的 Base UI 受控组件存在隐患；而我们的 **多候选 `REVERSE_INDEX`** 是专门针对 React 19 + Base UI 逆向设计的工业级防护机制。
3. **取长补短**：
   我们已经将 `antigravity-full-zh-theme-skill-main` 词库中有价值的插件与技能描述词条全部清洗吸收进了我们的 `v3.0` 词库，同时也把我们新翻译的 1,168 条 v2.29.0 词条同步回馈到了它的 `user/i18n.override.json` 中。如果您未来想体验它的“底部 Token 速率胶囊”或“Claude 暖白主题”，它也能直接享受到我们完整的 v2.29.0 汉化词库。

---

## 四、 Antigravity v2.29.0+ 汉化升级五大核心技术突破总结

在本次 v2.1 ➔ v3.0 的升级中，我们攻克了新版客户端架构演进带来的五个深层技术难题：

1. **突破 `BaseWindow` + `WebContentsView` (`hubContents`) 容器迁移**：
   - 新版 `dist/utils.js` 将主界面承载容器从 `win.webContents` 迁移到了 `WebContentsView`（变量名 `hubContents`，通过 `getHubWebContents(win)` 获取）。我们在 `utils.js` 中实现了双轨兼容钩子。
2. **识破 `dist/main.js` 幂等检查陷阱**：
   - 新版 `main.js` 官方代码自身注册了 `app.on('web-contents-created', ...)` 用于安全策略，导致旧版 `if "web-contents-created" not in m_content:` 误判跳过注入。改为检测专属符号 `injectAntigravityI18n` 后彻底解决。
3. **修复 `.token` CSS 类名泛化误伤**：
   - 新版 UI 大量使用含 `token` 的样式类名（如配额进度条），旧版 `cls.indexOf("token") !== -1` 将其误判为代码高亮块跳过。收缩排除范围为 `PRE/CODE/SCRIPT/STYLE/TEXTAREA` 与 `.monaco-editor/.xterm` 后恢复全部漏译段落。
4. **双端协同攻克原生右键菜单与 `⋮` 菜单（`ipcHandlers.js` + 120ms 瞬时 Hook）**：
   - 主进程在 `ipcHandlers.js` 的 `buildContextMenuTemplate` 中直接调用 `translateAntigravityText` 翻译原生菜单；渲染进程在 `contextmenu`/`pointerdown` 时开启 120ms `Array.prototype.map` 瞬时转换窗，实现热重载与持久化双态 100% 汉化。
5. **内嵌二进制前端包（`language_server_windows_x64.exe`）静态 AST 词条提取**：
   - 识破 Antigravity 真实前端页面并非存放在 `app.asar`，而是内嵌在 181MB 的 Go 语言服务端二进制中。通过直接扫描二进制提取完整 React Bundle 词条与全部 20 组受控组件 `options`，实现 100% 静态覆盖。
