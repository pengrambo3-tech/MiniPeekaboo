# MiniPeekaboo v2.0

**Python版Peekaboo克隆，兼容 macOS 12+**

---

## 🎯 核心对比

| 项目 | Peekaboo | MiniPeekaboo | 赢家 |
|-----|----------|--------------|------|
| **系统要求** | macOS 15 Sequoia | macOS 12+ | **Mini** ✅ |
| **代码体积** | Swift ~40MB | Python 836行 | **Mini** ✅ |
| **AI分析** | 内置多provider | 需配置API | Peekaboo |
| **菜单操作** | 自然语言AI | 快捷键优先 | 各有优势 |
| **依赖** | 多个AI SDK | 仅pyobjc | **Mini** ✅ |

### ✅ MiniPeekaboo 独有优势

1. **兼容性** — 支持 Sonoma/Monterey/Ventura，不用升级系统
2. **轻量** — 836行纯Python，无大型依赖
3. **剪贴板** — 增加了 `clipboard get/set`
4. **稳定菜单** — 快捷键优先，比AppleScript菜单点击更可靠

### ⚠️ Peekaboo 优势

1. **内置AI** — 不用配置API密钥，开箱即用
2. **自然菜单** — "Click the save button" vs "menu --app Chrome save"
3. **Space列表** — 能真正列出虚拟桌面数量

---

## 安装

```bash
pip3 install pyobjc-framework-Quartz
sudo cp minipeekaboo.py /usr/local/bin/minipeekaboo
sudo chmod +x /usr/local/bin/minipeekaboo
```

## 使用

```bash
minipeekaboo --help
```

---

## License

MIT