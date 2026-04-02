"""
抖音视频解析模块 - 无需登录态
核心原理：
1. 通过分享链接获取video_id
2. 调用 iesdouyin.com 的公开API
3. 将 playwm (watermark) 替换成 play 获取无水印视频
"""

import httpx
import re
from typing import Dict, Any, Optional


class DouyinParser:
    """抖音视频解析器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/'
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
        """获取短链重定向后的完整URL"""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=self.headers)
                return str(response.url)
            except Exception as e:
                print(f"获取重定向URL失败: {e}")
                return url
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """从URL中提取视频ID (aweme_id)"""
        # 匹配 /video/1234567890 格式
        patterns = [
            r'/video/(\d+)',
            r'video_id=(\d+)',
            r'aweme_id=(\d+)',
            r'/share/video/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """通过公开API获取视频信息"""
        # 使用抖音公开API - 尝试多个API端点
        api_urls = [
            f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}",
            f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}",
        ]
        
        last_error = None
        
        for api_url in api_urls:
            try:
                print(f"尝试API: {api_url}")
                async with httpx.AsyncClient() as client:
                    response = await client.get(api_url, headers=self.headers, timeout=10.0)
                    print(f"API响应状态: {response.status_code}")
                    print(f"API响应内容前200字符: {response.text[:200]}")
                    
                    # 检查响应是否为JSON
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' not in content_type:
                        print(f"警告: 响应不是JSON格式，Content-Type: {content_type}")
                    
                    data = response.json()
                    
                    # 处理不同API的响应格式
                    if 'item_list' in data:
                        # iesdouyin API格式
                        if data.get('status_code') != 0:
                            raise Exception(f"API返回错误: {data.get('status_msg', '未知错误')}")
                        
                        item_list = data.get('item_list', [])
                        if not item_list:
                            raise Exception("未找到视频信息")
                        
                        item = item_list[0]
                    elif 'aweme_detail' in data:
                        # douyin.com API格式
                        item = data['aweme_detail']
                    else:
                        raise Exception(f"未知的API响应格式: {list(data.keys())}")
                    
                    # 提取视频信息
                    video_info = item.get('video', {})
                    author_info = item.get('author', {})
                    
                    # 获取视频播放地址 (有水印)
                    play_url_wm = video_info.get('play_addr', {}).get('url_list', [''])[0] if video_info.get('play_addr') else ''
                    
                    # 获取无水印视频地址
                    # 方法1: 替换 playwm 为 play
                    play_url = play_url_wm.replace('playwm', 'play') if 'playwm' in play_url_wm else play_url_wm
                    
                    # 方法2: 从 render 接口获取
                    if not play_url or 'playwm' in play_url:
                        render_data = video_info.get('render_data', {})
                        if render_data:
                            render_url = render_data.get('url_list', [''])[0]
                            if render_url:
                                play_url = render_url
                    
                    return {
                        'aweme_id': video_id,
                        'title': item.get('desc', '未知标题'),
                        'cover': video_info.get('cover', {}).get('url_list', [''])[0] if video_info.get('cover') else '',
                        'duration': video_info.get('duration', 0) // 1000 if video_info.get('duration') else 0,  # 毫秒转秒
                        'author': author_info.get('nickname', '未知作者') if author_info else '未知作者',
                        'author_id': author_info.get('unique_id', '') if author_info else '',
                        'author_avatar': author_info.get('avatar_thumb', {}).get('url_list', [''])[0] if author_info and author_info.get('avatar_thumb') else '',
                        'play_url': play_url,  # 无水印视频地址
                        'play_url_wm': play_url_wm,  # 有水印视频地址
                        'create_time': item.get('create_time', 0),
                        'digg_count': item.get('statistics', {}).get('digg_count', 0) if item.get('statistics') else 0,
                        'comment_count': item.get('statistics', {}).get('comment_count', 0) if item.get('statistics') else 0,
                        'share_count': item.get('statistics', {}).get('share_count', 0) if item.get('statistics') else 0,
                    }
                    
            except Exception as e:
                print(f"API {api_url} 失败: {str(e)}")
                last_error = e
                continue
        
        # 如果所有API都失败了
        raise last_error if last_error else Exception("所有API端点都失败了")
    
    async def parse(self, url: str) -> Dict[str, Any]:
        """解析抖音视频"""
        # 1. 处理短链，获取完整URL
        full_url = await self.get_redirect_url(url)
        print(f"完整URL: {full_url}")
        
        # 2. 提取视频ID
        video_id = self.extract_video_id(full_url)
        if not video_id:
            raise Exception("无法提取视频ID，请检查链接是否正确")
        
        print(f"视频ID: {video_id}")
        
        # 3. 获取视频信息
        video_info = await self.get_video_info(video_id)
        
        return video_info


# 兼容旧接口的函数
async def parse_douyin_video(url: str) -> Dict[str, Any]:
    """解析抖音视频（兼容函数）"""
    parser = DouyinParser()
    video_info = await parser.parse(url)
    
    # 转换为统一的返回格式
    formats = []
    if video_info.get('play_url'):
        formats.append({
            'format_id': '0',
            'ext': 'mp4',
            'resolution': '高清无水印',
            'filesize': 0,
            'format_note': '无水印视频',
        })
    
    return {
        'title': video_info.get('title', '未知标题'),
        'thumbnail': video_info.get('cover', ''),
        'duration': video_info.get('duration', 0),
        'uploader': video_info.get('author', '未知作者'),
        'upload_date': '',
        'view_count': 0,
        'like_count': video_info.get('digg_count', 0),
        'description': '',
        'formats': formats,
        'subtitles': [],
        'direct_url': video_info.get('play_url', ''),  # 无水印视频直链
        'raw_info': video_info,  # 原始信息
    }


def is_douyin_url(url: str) -> bool:
    """检查是否为抖音链接"""
    parser = DouyinParser()
    return parser.is_douyin_url(url)
