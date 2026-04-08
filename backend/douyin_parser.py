"""
抖音视频解析模块 - 使用分享短链方案
通过抖音分享短链获取视频信息
"""

import httpx
import re
import json
from typing import Dict, Any, Optional


class DouyinParser:
    """抖音视频解析器"""
    
    def __init__(self):
        # 微信内置浏览器headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.38(0x18002629) NetType/WIFI Language/zh_CN',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def is_douyin_url(self, url: str) -> bool:
        """检查是否为抖音链接"""
        douyin_patterns = [
            r'douyin\.com',
            r'v\.douyin\.com',
            r'iesdouyin\.com'
        ]
        return any(re.search(pattern, url) for pattern in douyin_patterns)
    
    async def get_redirect_url(self, url: str) -> str:
        """处理短链，获取完整URL"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, follow_redirects=True, timeout=10.0)
            return str(response.url)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """从URL中提取视频ID"""
        patterns = [
            r'video/([0-9]+)',
            r'v\.douyin\.com/([a-zA-Z0-9]+)',
            r'aweme_id=([0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_video_info_from_web(self, video_id: str) -> Dict[str, Any]:
        """通过网页获取视频信息"""
        # 构建分享页面URL - 使用移动端分享页面
        share_url = f"https://www.iesdouyin.com/share/video/{video_id}"
        
        try:
            print(f"访问分享页面: {share_url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(share_url, headers=self.headers, timeout=10.0)
                print(f"页面响应状态: {response.status_code}")
                
                html_content = response.text
                print(f"页面内容长度: {len(html_content)}")
                
                # 尝试从页面中提取视频信息
                # 方法1: 匹配 <script id="RENDER_DATA" type="application/json">...</script>
                pattern = r'<script id="RENDER_DATA" type="application/json">(.*?)</script>'
                match = re.search(pattern, html_content, re.DOTALL)
                
                if match:
                    try:
                        json_str = match.group(1)
                        # URL解码
                        import urllib.parse
                        json_str = urllib.parse.unquote(json_str)
                        data = json.loads(json_str)
                        
                        # 提取视频信息
                        app = data.get('app', {})
                        video_info = app.get('videoInfo', {})
                        
                        if video_info:
                            return video_info
                    except Exception as e:
                        print(f"解析RENDER_DATA失败: {str(e)}")
                
                # 方法2: 匹配 window._SSR_HYDRATED_DATA
                pattern = r'window\._SSR_HYDRATED_DATA\s*=\s*(\{.*?\});'
                match = re.search(pattern, html_content, re.DOTALL)
                
                if match:
                    try:
                        json_str = match.group(1)
                        data = json.loads(json_str)
                        
                        aweme = data.get('aweme', {})
                        if aweme:
                            return aweme
                    except Exception as e:
                        print(f"解析SSR数据失败: {str(e)}")
                
                # 方法3: 匹配 window.__INITIAL_STATE__
                pattern = r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});'
                match = re.search(pattern, html_content, re.DOTALL)
                
                if match:
                    try:
                        json_str = match.group(1)
                        data = json.loads(json_str)
                        
                        aweme = data.get('aweme', {})
                        if aweme:
                            return aweme
                    except Exception as e:
                        print(f"解析INITIAL_STATE失败: {str(e)}")
                
                # 方法4: 匹配 window._ROUTER_DATA (新版抖音页面)
                # 使用更健壮的方法提取JSON
                start_marker = 'window._ROUTER_DATA = '
                start_idx = html_content.find(start_marker)
                
                if start_idx != -1:
                    try:
                        # 从start_marker之后开始提取JSON
                        json_start = start_idx + len(start_marker)
                        
                        # 找到JSON的结束位置（匹配最后一个}）
                        # 使用栈来匹配括号
                        brace_count = 0
                        json_end = json_start
                        in_string = False
                        escape_next = False
                        
                        for i, char in enumerate(html_content[json_start:]):
                            if escape_next:
                                escape_next = False
                                continue
                            
                            if char == '\\':
                                escape_next = True
                                continue
                            
                            if char == '"' and not in_string:
                                in_string = True
                            elif char == '"' and in_string:
                                in_string = False
                            elif not in_string:
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = json_start + i + 1
                                        break
                        
                        json_str = html_content[json_start:json_end]
                        print(f"提取的JSON长度: {len(json_str)}")
                        
                        data = json.loads(json_str)
                        
                        # 提取视频信息
                        loader_data = data.get('loaderData', {})
                        video_page = loader_data.get('video_(id)/page', {})
                        video_info_res = video_page.get('videoInfoRes', {})
                        item_list = video_info_res.get('item_list', [])
                        
                        if item_list and len(item_list) > 0:
                            print(f"从ROUTER_DATA成功提取视频信息")
                            return item_list[0]
                    except Exception as e:
                        print(f"解析ROUTER_DATA失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                # 方法4: 直接搜索视频地址
                pattern = r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)'
                matches = re.findall(pattern, html_content)
                
                if matches:
                    # 找到视频地址，构建基本信息
                    video_url = matches[0]
                    # 尝试提取标题
                    title_match = re.search(r'<title>(.*?)</title>', html_content)
                    title = title_match.group(1) if title_match else '未知标题'
                    
                    return {
                        'desc': title,
                        'video': {
                            'play_addr': {
                                'url_list': [video_url]
                            },
                            'cover': {
                                'url_list': []
                            }
                        },
                        'author': {
                            'nickname': '未知作者'
                        }
                    }
                
                # 保存页面内容以便调试
                with open('douyin_page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("页面内容已保存到 douyin_page_debug.html")
                
                raise Exception("无法从页面中提取视频信息")
                
        except httpx.TimeoutException as e:
            print(f"网页请求超时: {str(e)}")
            raise Exception("请求超时，请稍后重试")
        except httpx.ConnectError as e:
            print(f"网络连接错误: {str(e)}")
            raise Exception("网络连接失败，请检查网络")
        except Exception as e:
            print(f"网页请求失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"获取视频信息失败: {str(e)}")
    
    async def parse(self, url: str) -> Dict[str, Any]:
        """解析抖音视频"""
        print(f"解析抖音视频: {url}")
        
        # 1. 处理短链，获取完整URL
        full_url = await self.get_redirect_url(url)
        print(f"完整URL: {full_url}")
        
        # 2. 提取视频ID
        video_id = self.extract_video_id(full_url)
        if not video_id:
            raise Exception("无法提取视频ID")
        print(f"视频ID: {video_id}")
        
        # 3. 使用网页获取视频信息
        video_info = await self.get_video_info_from_web(video_id)
        
        # 4. 提取视频详情
        title = video_info.get('desc', '未知标题')
        author_info = video_info.get('author', {})
        author = author_info.get('nickname', '未知作者') if author_info else '未知作者'
        
        video_data = video_info.get('video', {})
        cover = video_data.get('cover', {}).get('url_list', [''])[0] if video_data.get('cover') else ''
        duration = video_data.get('duration', 0) // 1000 if video_data.get('duration') else 0
        
        # 5. 提取视频播放地址
        play_addr = video_data.get('play_addr', {})
        uri = play_addr.get('uri', '')
        
        if not uri:
            raise Exception("无法提取视频URI")
        
        # 6. 构建多清晰度格式列表
        # 抖音支持的多清晰度
        quality_options = [
            {'ratio': '360p', 'resolution': '360p', 'label': '流畅 360P'},
            {'ratio': '480p', 'resolution': '480p', 'label': '标清 480P'},
            {'ratio': '540p', 'resolution': '540p', 'label': '高清 540P'},
            {'ratio': '720p', 'resolution': '720p', 'label': '超清 720P'},
            {'ratio': '1080p', 'resolution': '1080p', 'label': '蓝光 1080P'},
        ]
        
        formats = []
        direct_urls = {}
        
        for i, quality in enumerate(quality_options):
            # 构造无水印播放地址
            play_url = f"https://www.douyin.com/aweme/v1/play/?video_id={uri}&ratio={quality['ratio']}"
            
            format_info = {
                'format_id': str(i),
                'ext': 'mp4',
                'resolution': quality['resolution'],
                'filesize': 0,
                'format_note': quality['label'],
            }
            formats.append(format_info)
            direct_urls[str(i)] = play_url
            
            if i == 0:
                # 第一个作为默认 direct_url
                default_direct_url = play_url
        
        print(f"构建 {len(formats)} 个清晰度选项")
        for fmt in formats:
            print(f"  - {fmt['format_note']}")
        
        # 构建代理播放地址（避免前端播放时403）
        from urllib.parse import quote
        proxy_urls = {}
        for fmt_id, video_url in direct_urls.items():
            proxy_urls[fmt_id] = f"/api/proxy-video?url={quote(video_url, safe='')}"
        
        return {
            'title': title,
            'thumbnail': cover,
            'duration': duration,
            'uploader': author,
            'upload_date': None,
            'view_count': 0,
            'like_count': 0,
            'description': title,
            'formats': formats,
            'subtitles': [],
            'direct_url': proxy_urls.get('0', ''),
            'direct_urls': direct_urls,
            'proxy_urls': proxy_urls,
        }


# 兼容旧接口的函数
async def parse_douyin_video(url: str) -> Dict[str, Any]:
    """解析抖音视频（兼容函数）"""
    parser = DouyinParser()
    return await parser.parse(url)


def is_douyin_url(url: str) -> bool:
    """检查是否为抖音链接"""
    parser = DouyinParser()
    return parser.is_douyin_url(url)
