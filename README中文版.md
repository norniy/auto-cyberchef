# AutoCyberChef 🔍

> 一个轻量级命令行工具，用于**自动识别和解码常见编码格式** —— 专为 CTF 竞赛、安全分析和数据处理场景设计。

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-84%20passed-brightgreen)]()
[![Lines of Code](https://img.shields.io/badge/Code-2000%2B%20lines-orange)]()

---

## ✨ 为什么要做这个工具？

做 CTF 或安全分析时，经常会遇到这样的字符串：

```
U0dWc2JIOD0=
```

它是 Base64？双层编码？Hex 里套了 ROT13？手动一层一层剥非常费时间。

AutoCyberChef 能**自动检测并逐层解码**，几秒钟给你答案：

```
$ python main.py auto U0dWc2JIOD0=

  Layer 1: [Base64]  →  SGVsbG8=
  Layer 2: [Base64]  →  Hello

Final result: Hello
```

---

## 🚀 快速开始

```bash
git clone https://github.com/norniy/auto-cyberchef.git
cd auto-cyberchef
pip install -r requirements.txt
python main.py shell
```

---

## 📦 安装方法

**环境要求：** Python 3.9 或更高版本，无需安装复杂依赖，核心功能全部使用 Python 标准库。

```bash
# 克隆仓库
git clone https://github.com/norniy/auto-cyberchef.git
cd auto-cyberchef

# 安装依赖（仅 pytest，用于运行测试）
pip install -r requirements.txt

# 验证安装
python main.py --version
```

---

## 🎮 功能列表

| 功能 | 说明 |
|---|---|
| **自动识别编码** | 识别 Base64、Hex、Binary、URL、ROT13、Morse、HTML、Caesar、Base32 共 9 种格式 |
| **自动多层解码** | 自动剥离最多 10 层嵌套编码 |
| **交互式 Shell** | 支持历史命令记录，↑↓ 方向键翻历史 |
| **批量文件解码** | 对文件每一行自动识别并解码 |
| **暴力解码模式** | 同时尝试所有解码器，汇总展示结果 |
| **置信度评分** | 对每种检测到的编码给出概率评分 |
| **JSON 输出** | 支持机器可读格式，方便与其他程序集成 |

---

## 📖 使用方法

### 交互式 Shell（推荐）

```bash
python main.py shell
```

```
autochef > decode SGVsbG8=
  Detected: Base64
  Result:   Hello

autochef > detect 48656c6c6f
  Possible encodings:
    - Hex
    - Base64

autochef > auto U0dWc2JIOD0=
  2 layer(s) found:
    Layer 1: [Base64]  →  SGVsbG8=
    Layer 2: [Base64]  →  Hello
  Final: Hello

autochef > brute "Uryyb Jbeyq"
    ✓ ROT13     Hello World
    ✓ Caesar    Hello World

autochef > history
autochef > exit
```

在 Unix/macOS 下支持 ↑/↓ 方向键翻历史命令。

---

### 命令行模式

#### `decode` — 解码字符串

```bash
# 自动检测编码并解码
python main.py decode SGVsbG8=

# 指定编码格式
python main.py decode 48656c6c6f -e hex
python main.py decode "Uryyb Jbeyq" -e rot13
python main.py decode ".... . .-.. .-.. ---" -e morse

# 输出 JSON 格式
python main.py decode SGVsbG8= --json
```

输出示例：
```
Detected encoding: Base64
Decoded result: Hello
```

---

#### `detect` — 识别编码类型

```bash
# 列出可能的编码
python main.py detect SGVsbG8=

# 显示置信度评分
python main.py detect SGVsbG8= --confidence
```

输出示例：
```
Possible encodings:
  - Base64

Encoding confidence scores:
  Base64        ████████████████████ 95.0%
```

---

#### `auto` — 多层自动解码

```bash
# 自动剥离所有编码层
python main.py auto U0dWc2JIOD0=

# 显示每层详细进度
python main.py auto U0dWc2JIOD0= --verbose

# 限制最大解码层数
python main.py auto U0dWc2JIOD0= --max-layers 5
```

输出示例：
```
Auto-decode: 2 layer(s) found

  Layer 1: [Base64]  →  SGVsbG8=
  Layer 2: [Base64]  →  Hello

Final result: Hello
```

---

#### `decode-file` — 批量解码文件

```bash
# 解码文件每一行
python main.py decode-file encoded.txt

# 结果保存到文件
python main.py decode-file encoded.txt -o decoded.txt

# 显示每行的解码层信息
python main.py decode-file encoded.txt --layers

# 强制指定编码格式
python main.py decode-file encoded.txt -e base64

# 输出 JSON 格式
python main.py decode-file encoded.txt --json
```

输入文件示例（`encoded.txt`）：
```
SGVsbG8=
48656c6c6f
.... . .-.. .-.. ---
```

输出：
```
Hello
Hello
HELLO

Processed 3 line(s): 3 decoded, 0 failed
```

---

#### `brute` — 暴力解码

```bash
# 尝试所有解码器
python main.py brute SGVsbG8=

# 同时显示失败的解码结果
python main.py brute SGVsbG8= --show-failures

# 展示全部 25 种凯撒位移
python main.py brute "Khoor" --caesar
```

---

#### `stats` — 文件编码统计

```bash
python main.py stats encoded.txt
```

输出示例：
```
File statistics: encoded.txt
  Total lines:   10
  Decoded lines: 9
  Failed lines:  1

Encoding breakdown:
  Base64         6
  Hex            3
```

---

## 🔤 支持的编码格式

| 编码格式 | 解码 | 编码 | 示例 |
|---|---|---|---|
| Base64 | ✅ | ✅ | `SGVsbG8=` |
| Base32 | ✅ | ✅ | `JBSWY3DP` |
| 十六进制 Hex | ✅ | ✅ | `48656c6c6f` |
| 二进制 Binary | ✅ | ✅ | `01001000 01100101...` |
| URL 编码 | ✅ | ✅ | `Hello%20World%21` |
| HTML 实体 | ✅ | ✅ | `&#72;&#101;&#108;...` |
| ROT13 | ✅ | ✅ | `Uryyb` |
| 摩尔斯电码 | ✅ | ✅ | `.... . .-.. .-.. ---` |
| 凯撒密码 | ✅ | ❌ | `Khoor`（位移 3） |

---

## 🏗️ 项目结构

```
auto-cyberchef/
│
├── autochef/
│   ├── __init__.py       # 包入口，对外暴露公开 API
│   ├── detector.py       # 编码识别（正则 + 启发式 + 置信度评分）
│   ├── decoder.py        # 各格式解码实现
│   ├── pipeline.py       # 多层自动解码编排
│   ├── file_handler.py   # 批量文件处理与 JSON 输出
│   └── utils.py          # 公共工具（熵值、可读性评分、字符串分析）
│
├── tests/
│   └── test_basic.py     # 84 个单元测试，覆盖所有模块
│
├── main.py               # CLI 入口（argparse + 交互式 Shell）
├── requirements.txt
└── README.md
```

---

## 🔌 作为 Python 库使用

AutoCyberChef 可以直接导入到你自己的脚本中：

```python
from autochef.detector import detect_encoding, get_encoding_confidence
from autochef.decoder import decode_base64, decode_hex, decode_by_name
from autochef.pipeline import auto_decode

# 检测编码
encodings = detect_encoding("SGVsbG8=")
print(encodings)  # ['Base64']

# 获取置信度评分
scores = get_encoding_confidence("SGVsbG8=")
print(scores)  # {'Base64': 0.95}

# 解码指定格式
result, success = decode_base64("SGVsbG8=")
print(result)  # Hello

# 按名称解码
result, success = decode_by_name("hex", "48656c6c6f")
print(result)  # Hello

# 多层自动解码
steps, final = auto_decode("U0dWc2JIOD0=")
print(final)  # Hello
for encoding, before, after in steps:
    print(f"{encoding}: {before} -> {after}")
```

---

## 🧪 运行测试

```bash
# 运行全部 84 个测试
python -m unittest tests.test_basic -v

# 运行指定测试类
python -m unittest tests.test_basic.TestPipeline -v

# 使用 pytest 运行（需安装）
pytest tests/ -v
```

---

## 🤝 参与贡献

欢迎任何形式的贡献！

- 🐛 **报告 Bug** — 提交 [Issue](https://github.com/norniy/auto-cyberchef/issues)
- ✨ **功能建议** — 提交标记 `enhancement` 的 Issue
- 🔧 **提交代码** — Fork 后发起 Pull Request

### 适合新手的任务

查看标记 [`good first issue`](https://github.com/norniy/auto-cyberchef/issues?q=label%3A%22good+first+issue%22) 的 Issue：

- 添加新的编码格式支持（Base58、XOR 等）
- 增加测试用例
- 修复文档错误

### 开发环境搭建

```bash
git clone https://github.com/norniy/auto-cyberchef.git
cd auto-cyberchef
pip install -r requirements.txt
python -m unittest tests.test_basic -v
```

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

## 🔗 相关项目

- [CyberChef](https://github.com/gchq/CyberChef) — 网页版"网络瑞士军刀"，本项目的灵感来源
- [Ciphey](https://github.com/Ciphey/Ciphey) — 基于 AI 的自动解密工具

AutoCyberChef 的定位：**无需浏览器，无需 ML 依赖**，Python 3.9+ 即可直接运行，适合集成进脚本和自动化流程。

---

<p align="center">
  为 CTF 选手、安全研究人员，以及所有花了太多时间手动解码字符串的人而做。
  <br>
  如果这个工具帮到了你，欢迎点个 ⭐
</p>
