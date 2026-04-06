from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import json
import os
import httpx
from typing import Dict, Any, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入抖音解析模块
from douyin_parser import is_douyin_url, parse_douyin_video
import re

# 从环境变量读取AI配置
AI_API_URL = os.getenv('AI_API_URL', '')
AI_MODEL = os.getenv('AI_MODEL', '')
AI_API_KEY = os.getenv('AI_API_KEY', '')

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
            
            # 只保留 1080P (80)，排除 1080P60 (116) 等其他高帧率格式
            high_quality_only = [q for q in accept_quality if q == 80]
            if not high_quality_only:
                # 如果没有 1080P，保留最高清晰度
                high_quality_only = [max(accept_quality)] if accept_quality else [64]
            
            print(f"injahow 支持的清晰度: {accept_quality}, 筛选后: {high_quality_only}")
            
            # 构建格式列表
            formats = []
            direct_urls = {}
            proxy_urls = {}
            
            for i, quality in enumerate(high_quality_only):
                quality_info = quality_map.get(quality, {'resolution': f'{quality}p', 'label': f'清晰度 {quality}'})
                
                # 获取该清晰度的视频地址
                url_response = await client.get(api_url, params={'bv': bvid, 'otype': 'url', 'q': quality}, timeout=30.0)
                url_response.raise_for_status()
                video_url = url_response.text.strip()
                
                # 尝试获取文件大小
                filesize = 0
                try:
                    # B站视频需要特定的 headers
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.bilibili.com/',
                    }
                    # 使用 stream 模式获取 content-length
                    async with client.stream('GET', video_url, headers=headers, timeout=10.0, follow_redirects=True) as response:
                        if 'content-length' in response.headers:
                            filesize = int(response.headers['content-length'])
                            print(f"[{quality_info['label']}] 获取到文件大小: {filesize} bytes ({filesize / 1024 / 1024:.2f} MB)")
                        else:
                            print(f"[{quality_info['label']}] 响应中没有 content-length")
                except Exception as e:
                    print(f"获取文件大小失败: {str(e)}")
                
                # 构建代理地址
                from urllib.parse import quote
                proxy_url = f"http://localhost:8000/api/proxy-video?url={quote(video_url, safe='')}"
                
                format_id = str(i)
                formats.append({
                    'format_id': format_id,
                    'ext': 'mp4',
                    'resolution': quality_info['resolution'],
                    'filesize': filesize,
                    'format_note': quality_info['label'],
                    'media_type': 'merged',
                    'vcodec': None,
                    'acodec': None,
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
        
        # B站链接使用双源解析
        if is_bilibili_url(url):
            print(f"检测到B站链接，使用双源解析: {url}")
            
            all_formats = []
            all_proxy_urls = {}
            all_direct_urls = {}
            
            # 使用 injahow 解析
            try:
                injahow_data = await parse_bilibili_with_injahow(url)
                for fmt in injahow_data.get('formats', []):
                    all_formats.append(fmt)
                all_proxy_urls.update(injahow_data.get('proxy_urls', {}))
                all_direct_urls.update(injahow_data.get('direct_urls', {}))
                
                base_info = {
                    'title': injahow_data.get('title'),
                    'thumbnail': injahow_data.get('thumbnail'),
                    'duration': injahow_data.get('duration'),
                    'uploader': injahow_data.get('uploader'),
                    'upload_date': injahow_data.get('upload_date'),
                    'view_count': injahow_data.get('view_count'),
                    'like_count': injahow_data.get('like_count'),
                    'description': injahow_data.get('description'),
                }
            except Exception as e:
                print(f"injahow 解析失败: {str(e)}")
                base_info = {}
            
            # 使用 yt-dlp 解析
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    for fmt in info.get('formats', []):
                        if fmt.get('ext') in ['mp4', 'webm', 'm4a', 'mp3', 'flv']:
                            vcodec = fmt.get('vcodec', 'none')
                            acodec = fmt.get('acodec', 'none')
                            
                            if vcodec == 'none' and acodec != 'none':
                                media_type = 'audio'
                                resolution = '音频'
                            elif vcodec != 'none' and acodec == 'none':
                                media_type = 'video'
                                resolution = fmt.get('resolution', 'unknown')
                            else:
                                media_type = 'merged'
                                resolution = fmt.get('resolution', 'unknown')
                            
                            filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
                            
                            format_note = fmt.get('format_note', '')
                            if not format_note and vcodec != 'none':
                                if 'avc' in vcodec.lower():
                                    format_note = 'H.264'
                                elif 'hev' in vcodec.lower() or 'h265' in vcodec.lower():
                                    format_note = 'H.265'
                                elif 'vp9' in vcodec.lower():
                                    format_note = 'VP9'
                                elif 'av01' in vcodec.lower():
                                    format_note = 'AV1'
                            
                            all_formats.append({
                                'format_id': fmt.get('format_id'),
                                'ext': fmt.get('ext'),
                                'resolution': resolution,
                                'filesize': filesize,
                                'format_note': format_note,
                                'vcodec': vcodec if vcodec != 'none' else None,
                                'acodec': acodec if acodec != 'none' else None,
                                'media_type': media_type,
                            })
                            
                            # 构建代理URL
                            video_url = fmt.get('url', '')
                            from urllib.parse import quote
                            all_proxy_urls[fmt.get('format_id')] = f"http://localhost:8000/api/proxy-video?url={quote(video_url, safe='')}"
                            all_direct_urls[fmt.get('format_id')] = video_url
                    
                    if not base_info:
                        base_info = {
                            'title': info.get('title'),
                            'thumbnail': info.get('thumbnail'),
                            'duration': info.get('duration'),
                            'uploader': info.get('uploader'),
                            'upload_date': info.get('upload_date'),
                            'view_count': info.get('view_count'),
                            'like_count': info.get('like_count'),
                            'description': info.get('description'),
                        }
            except Exception as e:
                print(f"yt-dlp 解析失败: {str(e)}")
            
            # 排序格式：纯音频 -> 纯视频 -> 音视频合并（injahow 的源排在最后）
            def sort_key(f):
                # 类型排序：音频(2) -> 视频(1) -> 合并(0)，反转后就是 音频 -> 视频 -> 合并
                type_order = {'audio': 0, 'video': 1, 'merged': 2}
                
                # 在同类型中，injahow 的源排在最后（通过检查 format_id 是否为纯数字）
                is_injahow = f.get('format_id', '').isdigit()
                source_order = 1 if is_injahow else 0
                
                res = f['resolution']
                if res == '音频':
                    res_num = 0
                elif 'x' in res:
                    res_num = int(res.split('x')[1])
                else:
                    res_num = 0
                return (type_order.get(f['media_type'], 3), -res_num, source_order)
            
            all_formats.sort(key=sort_key)
            
            return {
                **base_info,
                'formats': all_formats,
                'proxy_urls': all_proxy_urls,
                'direct_urls': all_direct_urls,
                'subtitles': [],
            }
        
        # 其他平台使用yt-dlp
        print(f"使用yt-dlp解析: {url}")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 提取可用的格式（不去重，显示所有）
            formats = []
            for fmt in info.get('formats', []):
                if fmt.get('ext') in ['mp4', 'webm', 'm4a', 'mp3', 'flv']:
                    vcodec = fmt.get('vcodec', 'none')
                    acodec = fmt.get('acodec', 'none')
                    
                    # 判断音视频类型
                    if vcodec == 'none' and acodec != 'none':
                        media_type = 'audio'
                        resolution = '音频'
                    elif vcodec != 'none' and acodec == 'none':
                        media_type = 'video'
                        resolution = fmt.get('resolution', 'unknown')
                    else:
                        media_type = 'merged'
                        resolution = fmt.get('resolution', 'unknown')
                    
                    # 获取文件大小
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
                    
                    # 生成格式说明
                    format_note = fmt.get('format_note', '')
                    if not format_note and vcodec != 'none':
                        # 根据编码生成说明
                        if 'avc' in vcodec.lower():
                            format_note = 'H.264'
                        elif 'hev' in vcodec.lower() or 'h265' in vcodec.lower():
                            format_note = 'H.265'
                        elif 'vp9' in vcodec.lower():
                            format_note = 'VP9'
                        elif 'av01' in vcodec.lower():
                            format_note = 'AV1'
                    
                    formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'resolution': resolution,
                        'filesize': filesize,
                        'format_note': format_note,
                        'vcodec': vcodec if vcodec != 'none' else None,
                        'acodec': acodec if acodec != 'none' else None,
                        'media_type': media_type,
                    })
            
            # 排序：合并的 > 纯视频 > 纯音频，同类型按分辨率从高到低
            def sort_key(f):
                type_order = {'merged': 0, 'video': 1, 'audio': 2}
                res = f['resolution']
                if res == '音频':
                    res_num = 0
                elif 'x' in res:
                    res_num = int(res.split('x')[1])
                else:
                    res_num = 0
                return (type_order.get(f['media_type'], 3), -res_num)
            
            formats.sort(key=sort_key)
            
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
    format_id: str = Query(..., description="格式ID"),
    source: str = Query("auto", description="解析源: auto, injahow, ytdlp")
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
        
        # B站链接支持多解析源
        if is_bilibili_url(url):
            print(f"检测到B站链接，获取直链，解析源: {source}, URL: {url}")
            
            # 如果指定了 injahow 源，或者自动模式下优先使用 injahow
            if source == "injahow" or source == "auto":
                try:
                    bilibili_data = await parse_bilibili_with_injahow(url)
                    # 根据 format_id 获取对应的清晰度 URL
                    proxy_urls = bilibili_data.get('proxy_urls', {})
                    direct_link = proxy_urls.get(format_id, bilibili_data.get('direct_url', ''))
                    return {
                        'direct_link': direct_link,
                        'ext': 'mp4',
                        'filesize': 0,
                    }
                except Exception as e:
                    print(f"injahow 获取直链失败，回退到 yt-dlp: {str(e)}")
                    if source == "injahow":
                        raise
            
            # 使用 yt-dlp 获取直链
            print(f"使用 yt-dlp 获取B站直链: {url}")
        
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
        
        # B站链接使用 injahow 接口
        if is_bilibili_url(url):
            print(f"检测到B站链接，准备下载: {url}, format_id: {format_id}")
            bilibili_data = await parse_bilibili_with_injahow(url)
            # 根据 format_id 获取对应的清晰度 URL
            direct_urls = bilibili_data.get('direct_urls', {})
            direct_link = direct_urls.get(format_id, bilibili_data.get('direct_url', ''))
            # 获取格式信息
            formats = bilibili_data.get('formats', [])
            selected_format = next((f for f in formats if f['format_id'] == format_id), None)
            format_note = selected_format['format_note'] if selected_format else '未知清晰度'
            return {
                'title': f"{bilibili_data.get('title', '未知标题')}_{format_note}",
                'direct_link': direct_link,
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"下载失败: {str(e)}")


# 图片代理接口
@app.get("/api/proxy-image")
async def proxy_image(
    url: str = Query(..., description="图片URL")
):
    try:
        # 根据URL设置不同的headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        # B站图片需要Referer
        if 'bilibili.com' in url or 'hdslb.com' in url:
            headers['Referer'] = 'https://www.bilibili.com/'
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=10.0)
            response.raise_for_status()
            
            # 提取Content-Type
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            from fastapi.responses import Response
            return Response(content=response.content, media_type=content_type)
    except Exception as e:
        print(f"图片代理失败: {str(e)}, URL: {url}")
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


# B站热门视频接口
@app.get("/api/bilibili/hot")
async def get_bilibili_hot():
    """获取B站热门视频列表"""
    try:
        async with httpx.AsyncClient() as client:
            # 使用B站官方热门API
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
            
            # 获取热门视频列表
            response = await client.get(
                'https://api.bilibili.com/x/web-interface/popular',
                headers=headers,
                params={'ps': 12},  # 获取12个视频
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 0:
                raise Exception(f"B站API返回错误: {data.get('message', '未知错误')}")
            
            videos = data.get('data', {}).get('list', [])
            
            # 格式化视频数据
            formatted_videos = []
            for video in videos:
                formatted_videos.append({
                    'bvid': video.get('bvid'),
                    'title': video.get('title'),
                    'pic': video.get('pic', ''),
                    'link': f"https://www.bilibili.com/video/{video.get('bvid')}",
                    'owner': {
                        'name': video.get('owner', {}).get('name', '未知UP主')
                    },
                    'stat': {
                        'view': video.get('stat', {}).get('view', 0),
                        'like': video.get('stat', {}).get('like', 0)
                    }
                })
            
            return {'videos': formatted_videos}
            
    except Exception as e:
        print(f"获取B站热门视频失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"获取B站热门视频失败: {str(e)}")


# 字幕获取接口 - 双方案实现
@app.post("/api/bilibili/subtitles")
async def get_bilibili_subtitles(request: dict):
    """
    获取B站视频字幕
    方案1: 使用B站官方API获取字幕
    方案2: 使用yt-dlp提取字幕
    """
    url = request.get('url', '')
    if not url:
        raise HTTPException(status_code=400, detail="请提供视频URL")
    
    # 方案1: 使用B站官方API获取字幕
    try:
        subtitles = await get_bilibili_subtitles_from_api(url)
        if subtitles and len(subtitles) > 0:
            return {'subtitles': subtitles, 'source': 'api'}
    except Exception as e:
        print(f"方案1(B站API)获取字幕失败: {str(e)}")
    
    # 方案2: 使用yt-dlp提取字幕
    try:
        subtitles = await get_bilibili_subtitles_from_ytdlp(url)
        if subtitles and len(subtitles) > 0:
            return {'subtitles': subtitles, 'source': 'ytdlp'}
    except Exception as e:
        print(f"方案2(yt-dlp)获取字幕失败: {str(e)}")
    
    # 如果两种方案都失败，返回空字幕
    return {'subtitles': [], 'source': 'none', 'message': '无法获取字幕，该视频可能没有字幕'}


async def get_bilibili_subtitles_from_api(url: str) -> list:
    """方案1: 使用B站 dm/view API 获取字幕"""
    async with httpx.AsyncClient() as client:
        # 获取视频BV号
        bvid = extract_bvid_from_url(url)
        if not bvid:
            raise Exception("无法提取BV号")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'https://www.bilibili.com/video/{bvid}'
        }
        
        # 获取视频详情和cid
        video_info_response = await client.get(
            f'https://api.bilibili.com/x/web-interface/view',
            params={'bvid': bvid},
            headers=headers,
            timeout=10.0
        )
        video_info_response.raise_for_status()
        video_info = video_info_response.json()
        
        if video_info.get('code') != 0:
            raise Exception(f"获取视频信息失败: {video_info.get('message', '未知错误')}")
        
        cid = video_info['data']['cid']
        aid = video_info['data']['aid']
        
        # 使用 dm/view API 获取字幕列表（这个API不需要登录）
        dm_response = await client.get(
            f'https://api.bilibili.com/x/v2/dm/view',
            params={'aid': aid, 'oid': cid, 'type': 1},
            headers=headers,
            timeout=10.0
        )
        dm_response.raise_for_status()
        dm_data = dm_response.json()
        
        if dm_data.get('code') != 0:
            raise Exception(f"获取字幕列表失败: {dm_data.get('message', '未知错误')}")
        
        # 获取字幕URL
        subtitles_list = dm_data['data'].get('subtitle', {}).get('subtitles', [])
        if not subtitles_list:
            raise Exception("该视频没有字幕")
        
        # 优先选择中文人工字幕，其次是中文AI字幕
        best_subtitle = subtitles_list[0]
        for sub in subtitles_list:
            lang = sub.get('lan', '')
            if lang in ['zh', 'zh-Hans', 'zh-CN']:
                best_subtitle = sub
                break
        
        subtitle_url = best_subtitle.get('subtitle_url', '')
        if not subtitle_url:
            raise Exception("字幕URL为空")
        
        # 添加https协议头
        if subtitle_url.startswith('//'):
            subtitle_url = 'https:' + subtitle_url
        if subtitle_url.startswith('http://'):
            subtitle_url = 'https://' + subtitle_url[7:]
        
        # 下载字幕内容
        subtitle_content_response = await client.get(subtitle_url, headers=headers, timeout=10.0)
        subtitle_content_response.raise_for_status()
        subtitle_content = subtitle_content_response.json()
        
        # 解析字幕
        subtitles = []
        for item in subtitle_content.get('body', []):
            content = item.get('content', '').strip()
            if content:
                subtitles.append({
                    'time': format_time(item.get('from', 0)),
                    'text': content
                })
        
        return subtitles


async def get_bilibili_subtitles_from_ytdlp(url: str) -> list:
    """方案2: 使用yt-dlp提取字幕"""
    import yt_dlp
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['zh-CN', 'zh', 'en'],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # 检查是否有字幕
        subtitles = info.get('subtitles', {})
        automatic_captions = info.get('automatic_captions', {})
        
        # 优先使用人工字幕
        subtitle_data = None
        for lang in ['zh-CN', 'zh', 'en']:
            if lang in subtitles and subtitles[lang]:
                subtitle_data = subtitles[lang][0]
                break
        
        # 如果没有人工字幕，使用自动字幕
        if not subtitle_data:
            for lang in ['zh-CN', 'zh', 'en']:
                if lang in automatic_captions and automatic_captions[lang]:
                    subtitle_data = automatic_captions[lang][0]
                    break
        
        if not subtitle_data:
            raise Exception("没有找到字幕")
        
        # 下载字幕内容
        subtitle_url = subtitle_data.get('url', '')
        if not subtitle_url:
            raise Exception("字幕URL为空")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(subtitle_url, timeout=10.0)
            response.raise_for_status()
            
            # 解析SRT或JSON格式字幕
            content = response.text
            subtitles = parse_subtitle_content(content)
            
            return subtitles


def extract_bvid_from_url(url: str) -> str:
    """从URL中提取BV号"""
    import re
    patterns = [
        r'BV([a-zA-Z0-9]+)',
        r'bvid=([a-zA-Z0-9]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            bvid = match.group(1)
            if not bvid.startswith('BV'):
                bvid = 'BV' + bvid
            return bvid
    return ''


def format_time(seconds: float) -> str:
    """将秒数格式化为时间字符串 MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def parse_subtitle_content(content: str) -> list:
    """解析字幕内容，支持SRT和JSON格式"""
    subtitles = []
    
    # 尝试解析JSON格式
    try:
        data = json.loads(content)
        if isinstance(data, dict) and 'body' in data:
            for item in data['body']:
                subtitles.append({
                    'time': format_time(item.get('from', 0)),
                    'text': item.get('content', '')
                })
            return subtitles
    except:
        pass
    
    # 解析SRT格式
    import re
    pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        start_time = match[0]
        text = match[2].strip().replace('\n', ' ')
        # 转换为MM:SS格式
        time_parts = start_time.split(':')
        minutes = int(time_parts[1])
        secs = int(time_parts[2].split(',')[0])
        subtitles.append({
            'time': f"{minutes:02d}:{secs:02d}",
            'text': text
        })
    
    return subtitles


@app.post("/api/bilibili/ai/summary")
async def generate_ai_summary(request: dict):
    """
    使用AI大模型生成视频总结摘要
    """
    url = request.get('url', '')
    if not url:
        raise HTTPException(status_code=400, detail="请提供视频URL")
    
    # 检查AI配置
    if not AI_API_KEY:
        return {
            'summary': 'AI服务未配置，请联系管理员设置AI_API_KEY环境变量。',
            'source': 'error'
        }
    
    try:
        # 1. 获取视频字幕
        subtitles = await get_bilibili_subtitles_from_api(url)
        
        if not subtitles or len(subtitles) == 0:
            # 尝试使用yt-dlp获取字幕
            subtitles = await get_bilibili_subtitles_from_ytdlp(url)
        
        if not subtitles or len(subtitles) == 0:
            return {
                'summary': '该视频没有字幕，无法生成摘要。',
                'source': 'none'
            }
        
        # 2. 构建字幕文本（根据实际字幕内容）
        subtitle_lines = []
        for sub in subtitles[:200]:  # 限制前200条字幕
            time_str = sub.get('time', '00:00')
            text_str = sub.get('text', '').strip()
            if text_str:
                subtitle_lines.append(f"[{time_str}] {text_str}")
        
        subtitle_text = "\n".join(subtitle_lines)
        
        # 3. 调用AI大模型生成摘要
        async with httpx.AsyncClient() as client:
            # 根据实际字幕内容构建提示词
            prompt = f"""请根据以下视频字幕内容，生成一个简洁的视频总结摘要（200-300字）。

【视频字幕内容】
{subtitle_text}

【分析要求】
请基于上述字幕内容，总结以下要点：
1. 视频主题和核心内容（根据字幕中提到的主题）
2. 主要观点或关键信息（从字幕中提取的重要观点）
3. 适合什么观众观看（根据内容判断目标受众）

【输出要求】
- 直接输出摘要内容，不要输出思考过程
- 语言简洁明了，用中文回答
- 字数控制在200-300字

请生成摘要："""

            headers = {
                'Authorization': f'Bearer {AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': AI_MODEL,
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的视频内容分析助手。请直接输出最终答案，不要输出思考过程。'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 800
            }
            
            response = await client.post(
                AI_API_URL,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取AI生成的摘要
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                message = choice.get('message', {})
                
                # 优先使用 content，如果没有则使用 reasoning_content
                if 'content' in message and message['content']:
                    summary = message['content']
                elif 'reasoning_content' in message and message['reasoning_content']:
                    summary = message['reasoning_content']
                else:
                    summary = f"AI响应格式异常: {json.dumps(message, ensure_ascii=False)[:200]}"
                
                # 清理思考过程，提取最终答案
                # 如果包含"摘要："或"最终摘要："，提取后面的内容
                import re
                patterns = [
                    r'(?:最终)?摘要[：:]\s*([\s\S]+)$',
                    r'(?:视频)?总结[：:]\s*([\s\S]+)$',
                ]
                for pattern in patterns:
                    match = re.search(pattern, summary)
                    if match:
                        summary = match.group(1).strip()
                        break
                
                # 如果内容太长，截取前1000字符
                if len(summary) > 1000:
                    summary = summary[:997] + "..."
            else:
                summary = f"AI响应格式异常: {json.dumps(result, ensure_ascii=False)[:200]}"
            
            return {
                'summary': summary,
                'source': 'ai',
                'subtitle_count': len(subtitles)
            }
            
    except Exception as e:
        print(f"AI生成摘要失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 返回友好的错误信息
        return {
            'summary': f'生成摘要时出错: {str(e)}',
            'source': 'error'
        }


@app.post("/api/bilibili/ai/mindmap")
async def generate_ai_mindmap(request: dict):
    """
    使用AI大模型生成视频思维导图
    """
    url = request.get('url', '')
    if not url:
        raise HTTPException(status_code=400, detail="请提供视频URL")
    
    # 检查AI配置
    if not AI_API_KEY:
        return {
            'mindmap': 'AI服务未配置，请联系管理员设置AI_API_KEY环境变量。',
            'source': 'error'
        }
    
    try:
        # 1. 获取视频字幕
        subtitles = await get_bilibili_subtitles_from_api(url)
        
        if not subtitles or len(subtitles) == 0:
            subtitles = await get_bilibili_subtitles_from_ytdlp(url)
        
        if not subtitles or len(subtitles) == 0:
            return {
                'mindmap': '',
                'source': 'none',
                'message': '该视频没有字幕，无法生成思维导图。'
            }
        
        # 2. 构建字幕文本
        subtitle_lines = []
        for sub in subtitles[:300]:  # 限制前300条字幕
            time_str = sub.get('time', '00:00')
            text_str = sub.get('text', '').strip()
            if text_str:
                subtitle_lines.append(f"[{time_str}] {text_str}")
        
        subtitle_text = "\n".join(subtitle_lines)
        
        # 3. 调用AI大模型生成思维导图
        async with httpx.AsyncClient() as client:
            prompt = f"""请根据以下视频字幕内容，生成一个详细的思维导图（使用Markdown列表格式）。

【视频字幕内容】
{subtitle_text}

【思维导图要求】
请基于上述字幕内容，生成一个层次清晰的思维导图，使用Markdown列表格式（使用 - 和缩进）：

1. 第一行必须是中心主题（视频的核心主题，用一句话概括）
2. 第二行开始是主要分支（至少3-5个主要章节或要点）
3. 每个主要分支下要有2-4个子分支（详细内容）

【输出格式要求】
必须严格按照以下格式输出：
- 中心主题（一句话概括视频内容）
  - 主要分支1（如：项目背景/核心功能）
    - 子分支1.1（详细说明）
    - 子分支1.2（详细说明）
  - 主要分支2（如：技术实现/应用场景）
    - 子分支2.1（详细说明）
    - 子分支2.2（详细说明）
  - 主要分支3（如：优势特点/未来规划）
    - 子分支3.1（详细说明）
    - 子分支3.2（详细说明）

【重要提示】
- 必须包含至少3个主要分支
- 每个主要分支下必须包含至少2个子分支
- 内容要详细，不能过于简略
- 直接输出思维导图内容，不要输出思考过程

请生成详细的思维导图："""

            headers = {
                'Authorization': f'Bearer {AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': AI_MODEL,
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的思维导图生成助手。请直接输出Markdown格式的思维导图，不要输出思考过程。'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 1500
            }
            
            response = await client.post(
                AI_API_URL,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取AI生成的思维导图
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                message = choice.get('message', {})
                
                if 'content' in message and message['content']:
                    mindmap = message['content']
                elif 'reasoning_content' in message and message['reasoning_content']:
                    mindmap = message['reasoning_content']
                else:
                    mindmap = f"AI响应格式异常"
                
                # 清理思考过程，提取Markdown列表
                import re
                # 查找Markdown列表格式的内容（匹配整个列表）
                lines = mindmap.split('\n')
                list_lines = []
                in_list = False
                
                for line in lines:
                    # 检查是否是列表项（以 - 开头，前面可以有空格）
                    if re.match(r'^(\s*)-\s+', line):
                        list_lines.append(line)
                        in_list = True
                    elif in_list and line.strip() == '':
                        # 列表结束
                        break
                    elif in_list:
                        # 列表中的其他内容（如空行）也保留
                        list_lines.append(line)
                
                if list_lines:
                    mindmap = '\n'.join(list_lines).strip()
                
                # 如果内容太长，截取前2000字符
                if len(mindmap) > 2000:
                    mindmap = mindmap[:1997] + "..."
            else:
                mindmap = "AI响应格式异常"
            
            return {
                'mindmap': mindmap,
                'source': 'ai',
                'subtitle_count': len(subtitles)
            }
            
    except Exception as e:
        print(f"AI生成思维导图失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'mindmap': f'生成思维导图时出错: {str(e)}',
            'source': 'error'
        }


@app.post("/api/bilibili/ai/qa")
async def ai_qa(request: dict):
    """
    AI智能问答 - 基于视频字幕回答用户问题
    """
    url = request.get('url', '')
    question = request.get('question', '')
    
    if not url:
        raise HTTPException(status_code=400, detail="请提供视频URL")
    
    if not question:
        raise HTTPException(status_code=400, detail="请输入问题")
    
    # 检查AI配置
    if not AI_API_KEY:
        return {
            'answer': 'AI服务未配置，请联系管理员设置AI_API_KEY环境变量。',
            'source': 'error'
        }
    
    try:
        # 1. 获取视频字幕
        subtitles = await get_bilibili_subtitles_from_api(url)
        
        if not subtitles or len(subtitles) == 0:
            subtitles = await get_bilibili_subtitles_from_ytdlp(url)
        
        if not subtitles or len(subtitles) == 0:
            return {
                'answer': '该视频没有字幕，无法进行AI问答。',
                'source': 'none'
            }
        
        # 2. 构建字幕文本
        subtitle_lines = []
        for sub in subtitles[:300]:  # 限制前300条字幕
            time_str = sub.get('time', '00:00')
            text_str = sub.get('text', '').strip()
            if text_str:
                subtitle_lines.append(f"[{time_str}] {text_str}")
        
        subtitle_text = "\n".join(subtitle_lines)
        
        # 3. 调用AI大模型回答问题
        async with httpx.AsyncClient() as client:
            prompt = f"""你是一个专业的视频内容分析助手。请根据提供的视频字幕内容，回答用户的问题。

## 视频字幕内容
```
{subtitle_text}
```

## 用户问题
{question}

## 判断与回答规则

**第一步：判断问题类型**
- 如果问题是关于视频内容、主题、讲解的知识点、人物、事件等 → 基于字幕回答
- 如果问题是闲聊、问候、与视频无关的问题（如"你好""今天天气""你会什么"）→ 简短回复并引导

**第二步：回答要求**

**情况A：视频相关问题**
1. 严格基于字幕内容回答，不添加外部信息
2. 开门见山，先给核心答案
3. 可适当引用字幕原话
4. 字幕中无相关信息时，明确说明
5. 控制在150字以内

**情况B：非视频相关问题（闲聊/无关）**
1. 简短友好回复（不超过30字）
2. 提示用户："我可以帮你分析视频内容，试着问关于这个视频的问题吧~"

请直接输出答案："""

            headers = {
                'Authorization': f'Bearer {AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': AI_MODEL,
                'messages': [
                    {'role': 'system', 'content': '你是视频内容分析专家。你的任务是基于视频字幕准确回答用户问题。只使用字幕中的信息，不添加外部知识。回答要直接、准确、简洁。'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 1000
            }
            
            response = await client.post(
                AI_API_URL,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取AI回答
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                message = choice.get('message', {})
                
                if 'content' in message and message['content']:
                    answer = message['content'].strip()
                elif 'reasoning_content' in message and message['reasoning_content']:
                    answer = message['reasoning_content'].strip()
                else:
                    answer = "AI响应格式异常"
            else:
                answer = "AI响应格式异常"
            
            return {
                'answer': answer,
                'source': 'ai',
                'subtitle_count': len(subtitles)
            }
            
    except Exception as e:
        print(f"AI问答失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'answer': f'回答问题时出错: {str(e)}',
            'source': 'error'
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
