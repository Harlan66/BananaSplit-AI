# 🍌 BananaSplit-AI

[简体中文](./README.md) | [English](./README_EN.md)

**BananaSplit-AI** 是一款专为 AI 创作者（特别是 **Nano Banana Pro** 用户）设计的智能分镜处理工具。

它可以一键将 AI 生成的九宫格分镜图进行**智能切割**，并提供双引擎**画面超分（画质增强）**，最后自动重命名并打包输出。

---

## ✨ 核心功能

- **🚀 双 AI 引擎**：
    - **Real-ESRGAN (默认)**：速度快，兼容性好，适合快速修复。
    - **SeedVR2-GGUF (新!)**：基于扩散模型，拥有强大的**细节重绘**能力，画质极佳。
- **✂️ 智能切分**：自动将 3x3 九宫格原图裁切为 9 张独立图片。
- **🎨 画质可控**：支持自定义输出分辨率 (1080p/2K/4K) 和 AI 幻想程度 (Input Noise)。
- **🧠 显存优化**：支持 3B/7B 大模型，内置 BlockSwap 和 CPU Offload 技术，**8G 显存也能跑大模型**。
- **💻 全本地运行**：无需 API Key，隐私安全。
- **📦 自动打包**：按照 `任务名_序列_位置` 自动命名并生成 ZIP 压缩包。

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

### 3. (可选) 配置 SeedVR2 引擎
如果您需要使用画质更好的 SeedVR2 引擎，请运行一键配置脚本：

```bash
# 推荐：下载 3B 模型 (平衡速度与画质, ~2GB)
python setup_seedvr2.py --model Q4_K_M

# 发烧友：下载 7B 模型 (画质天花板, ~4.5GB)
python setup_seedvr2.py --model 7B_Q4_K_M
```

---

## 🚀 使用方法

### 方式一：Web 界面 (推荐)
```bash
streamlit run app.py
```
启动后，在浏览器中：
1. **侧边栏设置**：
    - 选择 **AI 引擎** (Real-ESRGAN 或 SeedVR2)。
    - 如果使用 SeedVR2，可调整 **GGUF 模型** 和 **AI 幻想程度** (建议 0.2 以增强细节)。
2. **上传图片**：拖拽九宫格分镜图。
3. **开始处理**：点击按钮，等待 AI 处理完成。
4. **从左侧下载**：处理完成后，侧边栏会出现 ZIP 下载按钮。

### 方式二：命令行 (批量处理)
```bash
# 使用默认引擎
python main.py

# 使用 SeedVR2 引擎 (需先运行 setup 脚本)
python main.py --engine seedvr2 --model seedvr2_ema_7b-Q4_K_M.gguf
```

---

## ⚖️ 引擎对比

| 特性 | Real-ESRGAN | SeedVR2-GGUF |
| :--- | :--- | :--- |
| **原理** | 该 GAN 网络修复 | 扩散模型 (Diffusion) 重绘 |
| **速度** | 极快 (<5s / 张) | 较慢 (30s - 2min / 张) |
| **显存** | 低 (<4GB) | 中/高 (6GB - 12GB+) |
| **画质** | 清晰但有涂抹感 | **细节丰富，纹理逼真** |
| **适用** | 快速预览、简单放大 | **最终成品、追求极致画质** |

---

## 📂 项目结构
- `app.py`: Web 界面启动程序
- `setup_seedvr2.py`: SeedVR2 一键配置脚本
- `src/`: 核心逻辑组件
    - `upscaler.py`: Real-ESRGAN 封装
    - `upscaler_seed.py`: SeedVR2 封装
- `seedvr2_engine/`: SeedVR2 官方引擎 (自动克隆)
- `models/`: 存放模型权重文件

---

## 🤝 贡献与反馈
欢迎提交 Issue 或 Pull Request 来完善这个项目！

## 📄 开源协议
基于 [MIT License](./LICENSE) 开源。
