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
