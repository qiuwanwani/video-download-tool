from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import json
import os
import httpx
from typing import Dict, Any, List

# 导入抖音解析模块
from douyin_parser import is_douyin_url, parse_douyin_video

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 解析视频信息
@app.get("/api/parse")
async def parse_video(url: str = Query(..., description="视频URL")):
    try:
        # 如果是抖音链接，使用专用解析模块
        if is_douyin_url(url):
            print(f"检测到抖音链接，使用专用解析模块: {url}")
            return await parse_douyin_video(url)
        
        # 其他平台使用yt-dlp
        print(f"使用yt-dlp解析: {url}")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 提取可用的格式
            formats = []
            for fmt in info.get('formats', []):
                if fmt.get('ext') in ['mp4', 'webm', 'm4a', 'mp3']:
                    formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'resolution': fmt.get('resolution', 'audio only'),
                        'filesize': fmt.get('filesize', 0),
                        'format_note': fmt.get('format_note', ''),
                    })
            
            # 提取字幕信息
            subtitles = []
            if 'subtitles' in info:
                for lang, subs in info['subtitles'].items():
                    for sub in subs:
                        subtitles.append({
                            'language': lang,
                            'url': sub.get('url'),
                            'ext': sub.get('ext'),
                        })
            
            return {
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'description': info.get('description'),
                'formats': formats,
                'subtitles': subtitles,
            }
    except Exception as e:
        print(f"解析视频失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"解析视频失败: {str(e)}")


# 生成视频直链
@app.get("/api/get-direct-link")
async def get_direct_link(
    url: str = Query(..., description="视频URL"),
    format_id: str = Query(..., description="格式ID")
):
    try:
        # 如果是抖音链接，使用专用解析模块
        if is_douyin_url(url):
            print(f"检测到抖音链接，获取直链: {url}")
            douyin_data = await parse_douyin_video(url)
            return {
                'direct_link': douyin_data.get('direct_url', ''),
                'ext': 'mp4',
                'filesize': 0,
            }
        
        # 其他平台使用yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 找到指定格式的视频
            selected_format = None
            for fmt in info.get('formats', []):
                if fmt.get('format_id') == format_id:
                    selected_format = fmt
                    break
            
            if not selected_format:
                raise HTTPException(status_code=400, detail="指定的格式ID不存在")
            
            return {
                'direct_link': selected_format.get('url'),
                'ext': selected_format.get('ext'),
                'filesize': selected_format.get('filesize'),
            }
    except Exception as e:
        print(f"获取直链失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"获取直链失败: {str(e)}")


# 下载视频
@app.get("/api/download")
async def download_video(
    url: str = Query(..., description="视频URL"),
    format_id: str = Query(..., description="格式ID")
):
    try:
        # 如果是抖音链接，使用专用解析模块
        if is_douyin_url(url):
            print(f"检测到抖音链接，准备下载: {url}")
            douyin_data = await parse_douyin_video(url)
            return {
                'title': douyin_data.get('title', '未知标题'),
                'direct_link': douyin_data.get('direct_url', ''),
                'ext': 'mp4',
                'filesize': 0,
                'format_id': format_id,
            }
        
        # 其他平台使用yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 找到指定格式的视频
            selected_format = None
            for fmt in info.get('formats', []):
                if fmt.get('format_id') == format_id:
                    selected_format = fmt
                    break
            
            if not selected_format:
                raise HTTPException(status_code=400, detail="指定的格式ID不存在")
            
            return {
                'title': info.get('title'),
                'direct_link': selected_format.get('url'),
                'ext': selected_format.get('ext'),
                'filesize': selected_format.get('filesize'),
                'format_id': format_id,
            }
    except Exception as e:
        print(f"下载失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"下载失败: {str(e)}")


# 图片代理接口
@app.get("/api/proxy-image")
async def proxy_image(
    url: str = Query(..., description="图片URL")
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            # 提取Content-Type
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            from fastapi.responses import Response
            return Response(content=response.content, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片代理失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
