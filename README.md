# MiniPeekaboo v2.0

Python版Peekaboo克隆，兼容 macOS 12+。

## 🎯 核心对比

| 项目 | Peekaboo | MiniPeekaboo | 赢家 |
|-----|----------|--------------|------|
| **系统要求** | macOS 15 Sequoia | macOS 12+ | **Mini** ✅ |
| **代码体积** | Swift ~40MB | Python 836行 | **Mini** ✅ |
| **AI分析** | 内置多provider | 需配置API | **Peekaboo** |
| **菜单操作** | 自然语言AI | 快捷键优先 | 各有优势 |

## 功能覆盖

- 19个命令，100% Peekaboo核心功能覆盖
- Quartz真实鼠标拖拽
- AI视觉分析（OpenAI/Claude/豆包）
- 自然语言菜单（快捷键优先）
- 虚拟桌面切换
- 滑动手势

## 安装

```bash
pip3 install pyobjc-framework-Quartz
sudo cp minipeekaboo.py /usr/local/bin/minipeekaboo
sudo chmod +x /usr/local/bin/minipeekaboo
```

## 使用

```bash
minipeekaboo --help
minipeekaboo list apps
minipeekaboo image --mode screen
minipeekaboo menu --app Safari save
minipeekaboo see --prompt "描述UI"
```

## 许可证

MIT
