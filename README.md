# 视频下载工具

一个现代化的视频下载工具，支持 1800+ 网站，包括抖音、B站等。

## 功能特性

- 🚀 支持 1800+ 网站视频下载
- 📱 抖音专用解析，无需 Cookie
- 🎬 B站视频解析支持
- 🎨 现代化 UI 设计
- 📹 视频预览播放
- 📊 多种清晰度选择
- 📝 下载历史记录

## 技术栈

### 前端
- Vue 3 + Vite
- Tailwind CSS
- Axios

### 后端
- FastAPI
- yt-dlp
- httpx

## 快速开始

### 前端
```bash
cd frontend
npm install
npm run dev
```

### 后端
```bash
cd backend
pip install -r requirements.txt
python main.py
```

## 使用说明

1. 启动前端服务（默认 http://localhost:5173）
2. 启动后端服务（默认 http://localhost:8000）
3. 在输入框中粘贴视频链接
4. 点击"解析视频"
5. 选择清晰度并下载

## 支持平台

- 抖音（无需 Cookie）
- B站（哔哩哔哩）
- YouTube
- 其他 1800+ 网站

## 许可证

MIT License
