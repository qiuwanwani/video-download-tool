# 视频下载工具 - 项目总结

## 项目概述

一个支持多平台视频解析和下载的Web应用，采用前后端分离架构，支持抖音、B站、YouTube等1800+网站。

## 技术栈

### 前端
- **框架**: Vue 3 + Vite
- **样式**: Tailwind CSS
- **HTTP客户端**: Axios
- **图标**: SVG图标（无emoji）
- **主题**: 支持亮色/暗色模式切换

### 后端
- **框架**: FastAPI
- **视频解析**: yt-dlp + 自定义解析器
- **HTTP客户端**: httpx
- **B站专用**: injahow API
- **抖音专用**: 移动端页面解析

## 核心功能

### 1. 视频解析
- **抖音**: 通过分享链接解析，无需Cookie
- **B站**: 双源解析（yt-dlp + injahow）
- **其他平台**: yt-dlp支持1800+网站

### 2. 格式选择
- 显示视频分辨率、格式、文件大小
- 标注音视频类型（仅音频/仅视频/音视频合并）
- 支持多种清晰度选择

### 3. 视频播放
- 点击缩略图小窗播放
- 支持最高清晰度播放
- B站使用injahow源播放

### 4. 视频下载
- 支持多种格式下载
- 下载历史记录
- 文件大小预估

### 5. 主题切换
- 亮色/暗色模式
- 所有UI元素支持主题切换
- 本地存储主题偏好

## B站双源解析策略

### 解析源
1. **injahow API**: 返回音视频合并的MP4格式
2. **yt-dlp**: 返回DASH格式（音视频分离）

### 格式筛选
- injahow只保留1080P（不含1080P60）
- yt-dlp保留所有可用格式

### 排序规则
1. 纯音频（排在最前）
2. 纯视频
3. 音视频合并（排在最后）
   - injahow的源排在同类型最后

### 播放策略
- 默认选择格式列表最后一个（injahow的1080P）
- 使用injahow的播放源

## 项目结构

```
video-download-tool/
├── backend/
│   ├── main.py              # FastAPI主入口
│   ├── douyin_parser.py     # 抖音专用解析器
│   └── requirements.txt     # Python依赖
├── frontend/
│   ├── src/
│   │   ├── App.vue          # 主组件
│   │   ├── icons/           # SVG图标组件
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
├── .gitignore
├── LICENSE                  # MIT协议
├── README.md                # 项目说明
└── PROJECT_SUMMARY.md       # 项目总结（本文档）
```

## API接口

### 解析视频
```
GET /api/parse?url={video_url}
```

### 获取直链
```
GET /api/get-direct-link?url={video_url}&format_id={format_id}
```

### 下载视频
```
GET /api/download?url={video_url}&format_id={format_id}
```

### 代理图片
```
GET /api/proxy-image?url={image_url}
```

### 代理视频
```
GET /api/proxy-video?url={video_url}
```

## 运行方式

### 后端
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 技术亮点

1. **双源解析**: B站同时支持yt-dlp和injahow，提高解析成功率
2. **智能排序**: 格式按类型和来源智能排序，优先推荐最佳格式
3. **代理优化**: 图片和视频通过后端代理，解决跨域问题
4. **主题适配**: 完整的亮色/暗色主题支持
5. **无Cookie解析**: 抖音和B站都无需用户提供Cookie

## 待优化项

1. 文件大小获取不稳定（依赖服务器返回Content-Length）
2. 部分视频格式可能存在兼容性问题
3. 下载大文件时可能需要分片下载
4. 可以考虑添加下载队列管理

## 许可证

MIT License

## 作者

TX

## 更新时间

2026-04-03
