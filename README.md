# Emdash 1.2.7 简体中文本地汉化

此仓库保存 Linux x86_64 AppImage 版 Emdash 的简体中文词库、版本绑定补丁、构建与恢复工具。当前已实测版本为 1.2.7；构建工具同时保留 1.2.5 和 1.2.6 的版本记录。仓库仅包含汉化工具和补丁，不包含 Emdash 原始或汉化后的安装包。中文 AppImage 与按版本保存的原始安装包独立存放。启动入口指向更新程序使用的固定文件名 `emdash-x86_64.AppImage`，避免更新删除带版本号的汉化包后造成入口断链。应用标识与用户数据目录保持原有规则。

## 使用前提

此工具用于已有的 Linux AppImage 安装，默认路径使用当前用户的主目录；它不是完整的 Emdash 安装器。所有命令均在仓库根目录执行。

- 准备未经修改且 SHA-256 与 `tools/build.py` 中记录一致的原始 AppImage，并按版本单独保存。默认源文件为 `~/.local/share/emdash-app/Emdash-1.2.7.AppImage`；其他位置可用 `--source /absolute/path/to/original.AppImage` 指定。
- 安装脚本要求 `~/.local/bin/emdash` 已是指向该原包或同目录 `emdash-x86_64.AppImage` 的符号链接。未知入口、未知版本和校验不符时会停止。
- 需要 Python 3.11 或更高版本、支持 `node:test` 与内置 `fetch` 的 Node.js（建议 20 或更高版本）、`unsquashfs`、`mksquashfs`。当前脚本使用 Debian/Ubuntu 的 `/usr/share/nodejs/acorn`；界面验证还使用 `/usr/share/nodejs/ws`。
- 先构建，再运行安装脚本。构建生成的 `verification/build.json` 和安装生成的 `verification/installation.json` 是本机状态，请保留以便恢复；它们不会通过 Git 同步。

## 安装位置

- 原始安装包：`~/.local/share/emdash-app/Emdash-1.2.7.AppImage`
- 中文安装包：`~/.local/share/emdash-app/emdash-x86_64.AppImage`
- 启动入口：`~/.local/bin/emdash`
- 桌面菜单：沿用已有 `emdash.desktop`，无需建立新快捷方式。

正常从应用菜单或终端执行 `emdash` 即可。已经运行的旧进程需要完全退出后重新打开。

## 汉化内容及边界

涵盖项目、任务、聊天控制、文件浏览与差异、Git 操作、设置、命令面板、自动化、代理、MCP、SSH、浏览器控制及主菜单等界面文案，包括可访问性标签、动态提示与退出确认。模板名称与说明为中文。

词库有1,936 条翻译，使用语法树选择界面表达式，共替换约 2,600 处文字，另包含少量经过精确匹配的显示逻辑补丁。不会通过全局英文字符串替换处理程序。标识符、状态键、快捷键、命令、路径、cron 表达式及传给代理的提示词保持原内容。现有项目名、浏览器配置名称、对话、用户输入、代码、代理输出、第三方网页及外部服务错误不会自动翻译。

这是针对经校验的 **1.2.7** 安装包的本地补丁，不是上游官方语言包。应用更新可能覆盖汉化，新版本需要重新检查和适配。部分第三方组件或运行时返回的文字仍可能为英文；没有对所有代理、远程服务和异常分支逐一执行实测。

## 恢复原版

在仓库根目录操作，先完全退出 Emdash，然后运行：

```bash
python3 tools/install.py --restore
```

重新打开 Emdash 即使用原始安装包。恢复只切换启动符号链接，不删除用户数据或中文安装包。脚本优先读取实际安装记录中的原包路径、版本和校验值，恢复到实际安装对应的原版；即使随后构建过其他输出，也能恢复实际安装对应的原版；如启动入口被其他软件或你手动改动，会停止并提示，避免覆盖其他入口。

重新启用当前构建的中文版：

```bash
python3 tools/install.py
```

## 维护与重建

- `translations/zh-CN.json`：唯一的通用翻译词库。
- `translations/scoped.json`、`translations/scoped-1.2.7.json`：带预期匹配次数的精确补丁，用于动态状态、设置搜索和默认模板等。
- `tools/translate.cjs`：仅修改明确选择的字面显示值，保留条件判断与插值。
- `tools/asar.py`：保留链接、unpacked 元数据并重算 ASAR 偏移和校验值。
- `tools/build.py`：校验原包、使用独立临时目录构建，逐文件验证后生成 AppImage。
- `tools/install.py`：发布到固定文件名、安装入口修复和按版本恢复。
- `verification/build.json`：构建版本、源文件与产物校验值及修改清单。
- `verification/installation.json`：实际安装记录。
- `verification/ui-checks.json`：界面实测结果。

本机依赖：Python 3、Node.js、`unsquashfs`、`mksquashfs`；语法解析器使用本机 `/usr/share/nodejs/acorn`。界面验证使用本机 `/usr/share/nodejs/ws`。

构建到一个**尚不存在**的路径：

```bash
python3 tools/build.py \
  --output "$HOME/.local/share/emdash-app/Emdash-1.2.7-zh-CN-rebuilt.AppImage"
```

构建不会自动安装。完全退出 Emdash 后运行安装命令，工具会核对原版备份、当前安装记录和候选包，将中文包复制到更新程序的固定文件名，再修复启动入口。遇到未知版本或未知校验值会停止，不会覆盖。

当前 1.2.7 原包 SHA-256：

```text
595bb9be13f2d29e858e78a16ea8dc91cbc1db33d9c592b94ea7808e0e396594
```

构建工具按审核过的 SHA-256 选择版本与界面文件；保留 1.2.5 和 1.2.6 的既有适配记录。遇到未审核的版本或不同来源的安装包会拒绝修改，不会尝试盲目套用。

## 验证

```bash
# 在仓库根目录执行
node --test tests/*.test.cjs
python3 -m unittest discover -s tests -p 'test_*.py'
```

已验证实际 AppImage 启动、`zh-CN` 页面语言、8 个设置分类、中文设置搜索、系统托盘设置搜索、命令面板搜索及自动化页面显示。这些历史验证使用本地测试环境；截图与机器相关记录保存在本地 `verification/`，不上传到仓库。测试使用独立用户数据目录；没有启动付费代理任务，也没有执行推送、合并或删除项目等操作。

`tools/verify-ui.cjs` 仅用于连接调试端口 19325 的独立测试实例，不用于日常启动。正常安装不开放此调试端口。

## 1.2.7 更新适配

补充下载进度、错误详情、代理偏好、新会话和对话界面等 18 条词库文案。新版使用独立的 22 项精确补丁，保留更新检查失败与已是最新版本的状态区别，并适配工作区类型与状态的显示名称。1.2.5 / 1.2.6 继续使用原补丁文件。上一版验证记录在本地保存在 `verification/1.2.6/`，原始安装包按版本保留；固定启动入口与对应版本恢复流程不变。
