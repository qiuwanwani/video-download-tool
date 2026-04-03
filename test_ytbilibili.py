#!/usr/bin/env python3
"""
测试 yt-dlp 解析 B站视频的格式信息
"""

import yt_dlp
import json

# B站测试视频
url = "https://www.bilibili.com/video/BV1urPMzwEwY/"

print(f"测试视频: {url}")
print("="*80)

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)
    
    print(f"\n视频标题: {info.get('title')}")
    print(f"UP主: {info.get('uploader')}")
    print(f"时长: {info.get('duration')} 秒")
    print(f"\n{'='*80}")
    print("可用格式列表:")
    print(f"{'='*80}\n")
    
    # 按分辨率分组
    formats_by_res = {}
    audio_formats = []
    
    for fmt in info.get('formats', []):
        format_id = fmt.get('format_id', '')
        resolution = fmt.get('resolution', 'unknown')
        ext = fmt.get('ext', '')
        vcodec = fmt.get('vcodec', 'none')
        acodec = fmt.get('acodec', 'none')
        filesize = fmt.get('filesize', 0) or fmt.get('filesize_approx', 0)
        format_note = fmt.get('format_note', '')
        
        # 判断是否为纯音频
        if vcodec == 'none' and acodec != 'none':
            audio_formats.append({
                'format_id': format_id,
                'ext': ext,
                'acodec': acodec,
                'filesize': filesize,
                'format_note': format_note
            })
        else:
            # 视频或音视频合并
            if resolution not in formats_by_res:
                formats_by_res[resolution] = []
            formats_by_res[resolution].append({
                'format_id': format_id,
                'ext': ext,
                'vcodec': vcodec,
                'acodec': acodec,
                'filesize': filesize,
                'format_note': format_note,
                'has_audio': acodec != 'none'
            })
    
    # 打印音视频合并的格式
    print("[音视频合并格式] (vcodec + acodec)\n")
    for res in sorted(formats_by_res.keys(), key=lambda x: int(x.replace('p', '').split('x')[0]) if 'x' in x else 0, reverse=True):
        formats = formats_by_res[res]
        print(f"分辨率: {res}")
        for fmt in formats:
            audio_status = "[有音频]" if fmt['has_audio'] else "[无音频]"
            print(f"  - ID: {fmt['format_id']}, 格式: {fmt['ext']}, {audio_status}")
            print(f"    编码: vcodec={fmt['vcodec']}, acodec={fmt['acodec']}")
            print(f"    大小: {fmt['filesize'] / 1024 / 1024:.2f} MB" if fmt['filesize'] else "    大小: 未知")
            print(f"    备注: {fmt['format_note']}")
        print()
    
    # 打印纯音频格式
    if audio_formats:
        print(f"\n{'='*80}")
        print("[纯音频格式]\n")
        for fmt in audio_formats:
            print(f"  - ID: {fmt['format_id']}, 格式: {fmt['ext']}, 编码: {fmt['acodec']}")
            print(f"    大小: {fmt['filesize'] / 1024 / 1024:.2f} MB" if fmt['filesize'] else "    大小: 未知")
            print(f"    备注: {fmt['format_note']}")
            print()
    
    # 打印最佳音视频合并格式
    print(f"\n{'='*80}")
    print("[推荐: 音视频合并的最佳格式]\n")
    merged_formats = []
    for res, formats in formats_by_res.items():
        for fmt in formats:
            if fmt['has_audio']:
                merged_formats.append(fmt)
    
    # 按分辨率排序
    merged_formats.sort(key=lambda x: x['filesize'] or 0, reverse=True)
    
    for i, fmt in enumerate(merged_formats[:5], 1):
        print(f"{i}. ID: {fmt['format_id']}")
        print(f"   分辨率: {fmt.get('resolution', 'unknown')}")
        print(f"   格式: {fmt['ext']}")
        print(f"   大小: {fmt['filesize'] / 1024 / 1024:.2f} MB" if fmt['filesize'] else "   大小: 未知")
        print(f"   备注: {fmt['format_note']}")
        print()

print("\n" + "="*80)
print("测试完成!")
print("="*80)
