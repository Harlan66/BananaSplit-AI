<<<<<<< HEAD
# BananaSplit-AI
专为 Nano Banana Pro 用户设计的 AI 九宫格分镜智能切分与超分工具。基于 Real-ESRGAN 本地模型，一键实现分镜图无损放大、自动命名与批量打包。  English: An AI-powered 9-grid storyboard splitter and upscaler designed for Nano Banana Pro. Effortlessly enhance and slice your AI-generated grids with local Real-ESRGAN models.
=======
# 🍌 BananaSplit-AI

[简体中文](./README.md) | [English](./README_EN.md)

**BananaSplit-AI** 是一款专为 AI 创作者（特别是 **Nano Banana Pro** 用户）设计的智能分镜处理工具。

它可以一键将 AI 生成的九宫格分镜图进行**智能切割**，并利用 **Real-ESRGAN** 本地模型进行**画面超分（画质增强）**，最后自动重命名并打包输出。

---

## ✨ 核心功能

- ✂️ **智能切分**：自动将 3x3 九宫格原图裁切为 9 张独立图片。
- 🚀 **AI 超分**：内置 Real-ESRGAN 模型，支持 4 倍无损放大，让模糊的分镜瞬间清晰。
- 📏 **分辨率可控**：支持自定义输出大小（1080p, 2K, 4K 或原比例），平衡画质与体积。
- 💻 **全本地运行**：无需 API Key，隐私安全，充分利用您的 GPU（支持 RTX 40 系列显卡）。
- 📦 **自动打包**：按照 `任务名_序列_位置` 自动命名并生成 ZIP 压缩包。
- 🎨 **友好界面**：基于 Streamlit 的现代化 Web 操作界面。

---

## 🛠️ 安装指南

### 1. 克隆仓库
```bash
git clone https://github.com/Harlan66/BananaSplit-AI.git
cd BananaSplit-AI
```

### 2. 环境准备
推荐使用 Python 3.10+。

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装 PyTorch (推荐使用 CUDA 版本以获得 GPU 加速)
# 请根据您的显卡访问 https://pytorch.org/ 获取安装命令，例如：
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

---

## 🚀 使用方法

### 启动 Web 界面 (推荐)
```bash
streamlit run app.py
```
启动后，在浏览器中：
1. 在侧边栏设置 **任务名称** 和 **目标分辨率**。
2. 拖拽上传您的 **九宫格分镜图**。
3. 点击 **开始处理**。
4. 处理完成后点击 **下载 ZIP**。

---

## 📂 项目结构
- `app.py`: Web 界面启动程序
- `src/`: 核心逻辑组件（切分、超分模型、打包）
- `inputs/`: 默认输入目录
- `outputs/`: 默认输出目录
- `models/`: 存放模型权重文件（首次运行自动下载）

---

## 🤝 贡献与反馈
欢迎提交 Issue 或 Pull Request 来完善这个项目！

## 📄 开源协议
基于 [MIT License](./LICENSE) 开源。
>>>>>>> 5c2fa3a (Initial commit: BananaSplit-AI for Nano Banana Pro storyboards)
