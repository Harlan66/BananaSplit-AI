# 🍌 BananaSplit-AI

[简体中文](./README.md) | [English](./README_EN.md)

**BananaSplit-AI** is an intelligent storyboard processing tool designed specifically for AI creators (especially users of **Nano Banana Pro**).

It provides a one-click solution to **intelligently split** AI-generated 9-grid storyboards and perform **AI Upscaling (Super-resolution)** using local **Real-ESRGAN** models, finally renaming and packaging all images automatically.

---

## ✨ Key Features

- ✂️ **Smart Splitting**: Automatically crops a 3x3 grid into 9 individual images.
- 🚀 **AI Upscaling**: Built-in Real-ESRGAN models support 4x lossless enlargement, turning blurry storyboards into high-definition art.
- 📏 **Resolution Control**: Customize output sizes (1080p, 2K, 4K, or Full AI x4) to balance quality and file weight.
- 💻 **Fully Local**: No API Key required, privacy-safe, and fully utilizes your Local GPU (supports RTX 40-series).
- 📦 **Auto Packaging**: Automatically names files as `TaskName_Seq_GridIndex` and generates a ZIP archive.
- 🎨 **User-friendly UI**: Modern Web interface built with Streamlit.

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/Harlan66/BananaSplit-AI.git
cd BananaSplit-AI
```

### 2. Requirements
Python 3.10+ is recommended.

```bash
# Install basic dependencies
pip install -r requirements.txt

# Install PyTorch (CUDA version recommended for GPU acceleration)
# Visit https://pytorch.org/ to get the command for your system:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

---

## 🚀 How to Use

### Start Web UI (Recommended)
```bash
streamlit run app.py
```
After launching:
1. Set the **Task Name** and **Target Resolution** in the sidebar.
2. Drag and drop your **9-grid storyboard images**.
3. Click **Start Processing**.
4. Click **Download ZIP** once finished.

---

## 📂 Project Structure
- `app.py`: Main Web UI entry point.
- `src/`: Core logic modules (Splitter, Upscaler, Packager).
- `inputs/`: Default input directory.
- `outputs/`: Default output directory.
- `models/`: Weights storage (Automatically downloads on first run).

---

## 🤝 Contributing
Issues and Pull Requests are welcome!

## 📄 License
Released under the [MIT License](./LICENSE).
