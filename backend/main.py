from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import json
import os
import httpx
from typing import Dict, Any, List

# 导入抖音解析模块
from douyin_parser import is_douyin_url, parse_douyin_video
import re

def is_bilibili_url(url: str) -> bool:
    """判断是否为B站链接"""
    return 'bilibili.com' in url or 'b23.tv' in url

async def parse_bilibili_with_injahow(url: str) -> Dict[str, Any]:
    """使用 injahow 接口解析 B站 视频"""
    print(f"使用 injahow 解析 B站: {url}")
    
    # 从URL中提取 BV 号
    bv_match = re.search(r'/video/(BV[a-zA-Z0-9]+)', url)
    if not bv_match:
        raise Exception("无法提取 BV 号")
    
    bvid = bv_match.group(1)
    api_url = "https://api.injahow.cn/bparse/"
    
    # 首先获取视频信息（使用 yt-dlp）
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # 清晰度映射
        quality_map = {
            16: {'resolution': '360p', 'label': '流畅 360P'},
            32: {'resolution': '480p', 'label': '清晰 480P'},
            64: {'resolution': '720p', 'label': '高清 720P'},
            80: {'resolution': '1080p', 'label': '超清 1080P'},
            112: {'resolution': '1080p+', 'label': '1080P高码率'},
            116: {'resolution': '1080p60', 'label': '1080P 60帧'},
            120: {'resolution': '4K', 'label': '4K 超清'},
        }
        
        # 获取支持的清晰度
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params={'bv': bvid, 'otype': 'json'}, timeout=30.0)
            response.raise_for_status()
            injahow_data = response.json()
            
            accept_quality = injahow_data.get('accept_quality', [64])
            
            # 构建格式列表
            formats = []
            direct_urls = {}
            proxy_urls = {}
            
            for i, quality in enumerate(accept_quality):
                quality_info = quality_map.get(quality, {'resolution': f'{quality}p', 'label': f'清晰度 {quality}'})
                
                # 获取该清晰度的视频地址
                url_response = await client.get(api_url, params={'bv': bvid, 'otype': 'url', 'q': quality}, timeout=30.0)
                url_response.raise_for_status()
                video_url = url_response.text.strip()
                
                # 构建代理地址
                from urllib.parse import quote
                proxy_url = f"http://localhost:8000/api/proxy-video?url={quote(video_url, safe='')}"
                
                format_id = str(i)
                formats.append({
                    'format_id': format_id,
                    'ext': 'mp4',
                    'resolution': quality_info['resolution'],
                    'filesize': 0,
                    'format_note': quality_info['label'],
                })
                direct_urls[format_id] = video_url
                proxy_urls[format_id] = proxy_url
        
        return {
            'title': info.get('title', '未知标题'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', '未知作者'),
            'upload_date': info.get('upload_date'),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'description': info.get('description', ''),
            'formats': formats,
            'subtitles': [],
            'direct_url': proxy_urls.get('0', ''),
            'direct_urls': direct_urls,
            'proxy_urls': proxy_urls,
        }

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
        
        # 暂时禁用 injahow 接口，使用 yt-dlp
        # if is_bilibili_url(url):
        #     print(f"检测到B站链接，使用 injahow 接口: {url}")
        #     return await parse_bilibili_with_injahow(url)
        
        # 其他平台使用yt-dlp
        print(f"使用yt-dlp解析: {url}")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 提取可用的格式，按分辨率去重
            formats = []
            seen_resolutions = set()
            for fmt in info.get('formats', []):
                if fmt.get('ext') in ['mp4', 'webm', 'm4a', 'mp3']:
                    resolution = fmt.get('resolution', 'audio only')
                    # 跳过重复的分辨率
                    if resolution in seen_resolutions:
                        continue
                    seen_resolutions.add(resolution)
                    formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'resolution': resolution,
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
            print(f"检测到抖音链接，获取直链: {url}, format_id: {format_id}")
            douyin_data = await parse_douyin_video(url)
            # 根据 format_id 获取对应的清晰度 URL
            proxy_urls = douyin_data.get('proxy_urls', {})
            direct_link = proxy_urls.get(format_id, douyin_data.get('direct_url', ''))
            return {
                'direct_link': direct_link,
                'ext': 'mp4',
                'filesize': 0,
            }
        
        # 暂时禁用 injahow 接口
        # if is_bilibili_url(url):
        #     print(f"检测到B站链接，获取直链: {url}, format_id: {format_id}")
        #     bilibili_data = await parse_bilibili_with_injahow(url)
        #     # 根据 format_id 获取对应的清晰度 URL
        #     proxy_urls = bilibili_data.get('proxy_urls', {})
        #     direct_link = proxy_urls.get(format_id, bilibili_data.get('direct_url', ''))
        #     return {
        #         'direct_link': direct_link,
        #         'ext': 'mp4',
        #         'filesize': 0,
        #     }
        
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
            
            # 对于其他平台，也需要代理播放地址避免403
            video_url = selected_format.get('url', '')
            from urllib.parse import quote
            proxy_url = f"http://localhost:8000/api/proxy-video?url={quote(video_url, safe='')}"
            
            return {
                'direct_link': proxy_url,
                'ext': selected_format.get('ext'),
                'filesize': selected_format.get('filesize'),
            }
    except Exception as e:
        print(f"获取直链失败: {str(e)}")
        import traceback
        traceback.print_exc()
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
            print(f"检测到抖音链接，准备下载: {url}, format_id: {format_id}")
            douyin_data = await parse_douyin_video(url)
            # 根据 format_id 获取对应的清晰度 URL
            direct_urls = douyin_data.get('direct_urls', {})
            direct_link = direct_urls.get(format_id, douyin_data.get('direct_url', ''))
            # 获取格式信息
            formats = douyin_data.get('formats', [])
            selected_format = next((f for f in formats if f['format_id'] == format_id), None)
            format_note = selected_format['format_note'] if selected_format else '未知清晰度'
            return {
                'title': f"{douyin_data.get('title', '未知标题')}_{format_note}",
                'direct_link': direct_link,
                'ext': 'mp4',
                'filesize': 0,
                'format_id': format_id,
            }
        
        # 暂时禁用 injahow 接口
        # if is_bilibili_url(url):
        #     print(f"检测到B站链接，准备下载: {url}, format_id: {format_id}")
        #     bilibili_data = await parse_bilibili_with_injahow(url)
        #     # 根据 format_id 获取对应的清晰度 URL
        #     direct_urls = bilibili_data.get('direct_urls', {})
        #     direct_link = direct_urls.get(format_id, bilibili_data.get('direct_url', ''))
        #     # 获取格式信息
        #     formats = bilibili_data.get('formats', [])
        #     selected_format = next((f for f in formats if f['format_id'] == format_id), None)
        #     format_note = selected_format['format_note'] if selected_format else '未知清晰度'
        #     return {
        #         'title': f"{bilibili_data.get('title', '未知标题')}_{format_note}",
        #         'direct_link': direct_link,
        #         'ext': 'mp4',
        #         'filesize': 0,
        #         'format_id': format_id,
        #     }
        
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
        import traceback
        traceback.print_exc()
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


# 视频下载代理接口
@app.get("/api/proxy-download")
async def proxy_download(
    url: str = Query(..., description="视频URL"),
    filename: str = Query(..., description="下载文件名")
):
    try:
        # 抖音视频下载需要特定的headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://www.douyin.com/',
        }
        
        from fastapi.responses import StreamingResponse
        from urllib.parse import quote
        import httpx
        
        # 对文件名进行URL编码，处理中文字符
        encoded_filename = quote(filename, safe='')
        
        # 使用流式传输，边下载边返回
        async def video_stream():
            async with httpx.AsyncClient(follow_redirects=True) as client:
                async with client.stream('GET', url, headers=headers, timeout=60.0) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        yield chunk
        
        # 使用StreamingResponse返回视频流
        return StreamingResponse(
            video_stream(),
            media_type='video/mp4',
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        print(f"视频代理下载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"视频下载失败: {str(e)}")


# 视频播放代理接口
@app.get("/api/proxy-video")
async def proxy_video(
    url: str = Query(..., description="视频URL")
):
    try:
        print(f"代理播放接收到的 URL: {url}")
        
        # 确保 URL 有协议
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        # 根据域名设置不同的 Referer
        if 'douyin.com' in url or 'douyinvod.com' in url:
            referer = 'https://www.douyin.com/'
        elif 'bilivideo.com' in url or 'bilibili.com' in url:
            referer = 'https://www.bilibili.com/'
        else:
            referer = 'https://www.example.com/'
        
        # 视频播放需要特定的headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Referer': referer,
        }
        
        from fastapi.responses import StreamingResponse
        import httpx
        
        # 使用流式传输
        async def video_stream():
            async with httpx.AsyncClient(follow_redirects=True) as client:
                async with client.stream('GET', url, headers=headers, timeout=60.0) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        yield chunk
        
        return StreamingResponse(
            video_stream(),
            media_type='video/mp4'
        )
    except Exception as e:
        print(f"视频代理播放失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"视频播放失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
