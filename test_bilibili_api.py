#!/usr/bin/env python3
"""
Bilibili-parse API 测试脚本
测试接口: https://api.injahow.cn/bparse/
"""

import requests
import json

BASE_URL = "https://api.injahow.cn/bparse/"


def test_api_with_params(params, description=""):
    """测试API并打印结果"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"参数: {params}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code == 200:
            # 尝试解析为JSON
            try:
                data = response.json()
                print(f"\n响应内容 (JSON):")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return data
            except:
                # 如果不是JSON，打印文本内容
                print(f"\n响应内容 (Text):")
                print(response.text[:1000])  # 只打印前1000字符
                return response.text
        else:
            print(f"请求失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"错误: {str(e)}")
        return None


def main():
    print("Bilibili-parse API 测试开始")
    print(f"基础URL: {BASE_URL}")
    
    # 测试1: 使用av号获取JSON格式
    test_api_with_params(
        {"av": "14661594", "p": "1", "q": "64", "otype": "json"},
        "使用av号获取视频信息 (JSON格式)"
    )
    
    # 测试2: 使用bv号获取JSON格式
    test_api_with_params(
        {"bv": "BV1xx411c7mD", "p": "1", "q": "80", "otype": "json"},
        "使用bv号获取视频信息 (高清1080P)"
    )
    
    # 测试3: 获取直接视频URL
    test_api_with_params(
        {"av": "14661594", "p": "2", "q": "32", "otype": "url"},
        "获取直接视频URL (第2集, 清晰480P)"
    )
    
    # 测试4: 使用mp4格式
    test_api_with_params(
        {"av": "14661594", "p": "1", "format": "mp4", "otype": "json"},
        "获取MP4格式视频"
    )
    
    # 测试5: 使用dash格式
    test_api_with_params(
        {"bv": "BV1xx411c7mD", "p": "1", "format": "dash", "otype": "json"},
        "获取DASH格式视频"
    )
    
    # 测试6: 番剧类型
    test_api_with_params(
        {"ep": "324928", "type": "bangumi", "otype": "json"},
        "获取番剧信息"
    )
    
    # 测试7: dplayer格式
    test_api_with_params(
        {"av": "14661594", "p": "1", "otype": "dplayer"},
        "获取DPlayer播放器配置"
    )
    
    # 测试8: 不同清晰度对比
    for q in [16, 32, 64, 80]:
        quality_name = {16: "360P", 32: "480P", 64: "720P", 80: "1080P"}.get(q, "未知")
        test_api_with_params(
            {"av": "14661594", "p": "1", "q": str(q), "otype": "json"},
            f"清晰度测试 - {quality_name} (q={q})"
        )
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
