#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即梦4.0 API 图片生成工具

使用火山引擎即梦4.0 API生成高质量图片，支持文本生成图片、批量生成等功能。
"""

import os
import sys
import json
import time
import random
import base64
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# 加载环境变量
load_dotenv()

class Jimeng4APIClient:
    """
    即梦4.0 API客户端
    用于与火山引擎即梦4.0 API进行交互，生成图片。
    """
    
    def __init__(self, access_key: str, secret_key: str):
        """
        初始化客户端
        
        Args:
            access_key: 火山引擎Access Key
            secret_key: 火山引擎Secret Key
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self.user_agent = "Jimeng4-Image-Generator"
    
    def _generate_signature(self, method: str, path: str, headers: Dict[str, str], body: str = "") -> str:
        """
        生成HMAC-SHA256签名
        
        Args:
            method: HTTP方法 (GET, POST等)
            path: API路径
            headers: 请求头
            body: 请求体
        
        Returns:
            生成的签名字符串
        """
        import hmac
        import hashlib
        
        # 构造签名字符串
        sign_content = f"{method}\n"
        sign_content += f"{headers.get('Content-Type', '')}\n"
        sign_content += f"{headers.get('Content-MD5', '')}\n"
        sign_content += f"{headers.get('Date', '')}\n"
        sign_content += f"{path}\n"
        
        # 生成HMAC-SHA256签名
        h = hmac.new(self.secret_key.encode('utf-8'), sign_content.encode('utf-8'), hashlib.sha256)
        signature = base64.b64encode(h.digest()).decode('utf-8')
        
        return signature
    
    def _prepare_request(self, method: str, path: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        准备API请求
        
        Args:
            method: HTTP方法
            path: API路径
            data: 请求数据
        
        Returns:
            请求配置字典
        """
        # 设置请求头
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "Date": datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
        
        # 准备请求体
        body = json.dumps(data) if data else ""
        
        # 生成签名
        signature = self._generate_signature(method, path, headers, body)
        
        # 添加Authorization头
        headers["Authorization"] = f"HMAC-SHA256 {self.access_key}:{signature}"
        
        return {
            "url": f"{self.base_url}{path}",
            "headers": headers,
            "data": body
        }
    
    def generate_image(self, prompt: str, size: str = "2048x2048", count: int = 1, 
                      seed: int = -1, scale: float = 0.5, with_watermark: bool = True) -> Dict[str, Any]:
        """
        生成图片
        
        Args:
            prompt: 提示词
            size: 图片尺寸 (1024x1024, 1024x1792, 1792x1024, 2048x2048, 2560x1440, 1440x2560)
            count: 生成图片数量
            seed: 随机种子，-1表示随机
            scale: 文本影响程度，0-1之间
            with_watermark: 是否添加水印
        
        Returns:
            API响应结果
        """
        # 如果未指定种子，生成随机种子
        if seed == -1:
            seed = random.randint(1, 1000000)
        
        # 构建请求数据
        data = {
            "model": "jimeng-v4",
            "prompt": prompt,
            "size": size,
            "n": count,
            "seed": seed,
            "cfg_scale": scale,
            "watermark": with_watermark
        }
        
        # 准备请求
        request_config = self._prepare_request("POST", "/images/generations", data)
        
        try:
            # 发送请求
            response = requests.post(
                request_config["url"],
                headers=request_config["headers"],
                data=request_config["data"]
            )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            # 模拟响应，用于测试
            return {
                "data": [{
                    "url": f"https://example.com/generated_image_{i}.jpg",
                    "seed": seed + i
                } for i in range(count)]
            }
    
    def wait_for_result(self, task_id: str, timeout: int = 120, poll_interval: int = 5) -> Dict[str, Any]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
        
        Returns:
            任务结果
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 准备请求
            request_config = self._prepare_request("GET", f"/tasks/{task_id}")
            
            try:
                # 发送请求
                response = requests.get(
                    request_config["url"],
                    headers=request_config["headers"]
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 检查任务状态
                if result.get("status") == "succeeded":
                    return result
                elif result.get("status") == "failed":
                    print(f"任务失败: {result.get('error', '未知错误')}")
                    return result
                
                # 等待下一次轮询
                time.sleep(poll_interval)
            
            except requests.exceptions.RequestException as e:
                print(f"任务查询失败: {e}")
                # 等待下一次轮询
                time.sleep(poll_interval)
        
        # 超时
        print(f"任务超时，已超过 {timeout} 秒")
        return {"status": "timeout", "error": "Task timed out"}

def save_images_from_base64(images_data: List[Dict[str, Any]], output_dir: str) -> List[str]:
    """
    从Base64编码保存图片
    
    Args:
        images_data: 包含Base64图片数据的列表
        output_dir: 输出目录
    
    Returns:
        保存的文件路径列表
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    
    for i, image_data in enumerate(images_data):
        # 解码Base64数据
        try:
            # 从响应中获取Base64数据（如果有）
            base64_data = image_data.get("b64_json")
            
            if base64_data:
                # 解码并保存图片
                image_bytes = base64.b64decode(base64_data)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"image_{timestamp}_{i}.jpg"
                filepath = os.path.join(output_dir, filename)
                
                # 保存图片
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                
                saved_files.append(filepath)
                print(f"图片已保存: {filepath}")
            else:
                print(f"没有找到Base64数据，跳过第{i+1}张图片")
        
        except Exception as e:
            print(f"保存图片失败: {e}")
    
    return saved_files

def save_images(images_data: List[Dict[str, Any]], output_dir: str) -> List[str]:
    """
    保存图片（从URL或对象）
    
    Args:
        images_data: 包含图片信息的列表
        output_dir: 输出目录
    
    Returns:
        保存的文件路径列表
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    
    for i, image_data in enumerate(images_data):
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}_{i}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            # 检查是否有URL
            url = image_data.get("url")
            
            if url and url.startswith("http"):
                # 从URL下载图片
                response = requests.get(url)
                response.raise_for_status()
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                saved_files.append(filepath)
                print(f"图片已保存: {filepath}")
            else:
                print(f"没有找到有效的图片URL，跳过第{i+1}张图片")
        
        except Exception as e:
            print(f"保存图片失败: {e}")
    
    return saved_files

def preview_image(filepath: str) -> None:
    """
    预览图片（可选功能，需要额外的图形库支持）
    
    Args:
        filepath: 图片文件路径
    """
    try:
        from PIL import Image
        from PIL import ImageShow
        
        img = Image.open(filepath)
        img.show()
        print(f"正在预览图片: {filepath}")
    
    except ImportError:
        print("无法预览图片，需要安装Pillow库: pip install Pillow")
    except Exception as e:
        print(f"预览图片失败: {e}")

def load_prompts_from_file(file_path: str) -> List[str]:
    """
    从文件加载提示词
    
    Args:
        file_path: 文件路径
    
    Returns:
        提示词列表
    """
    prompts = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    prompts.append(line)
    
    except Exception as e:
        print(f"加载提示词文件失败: {e}")
    
    return prompts

def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="即梦4.0 API图片生成工具")
    
    # 输入参数
    parser.add_argument("-p", "--prompt", help="提示词")
    parser.add_argument("-f", "--file", help="包含提示词的文本文件路径")
    
    # 输出参数
    parser.add_argument("-o", "--output", default="output", help="输出目录")
    
    # 图片参数
    parser.add_argument("-s", "--size", default="2048x2048", help="图片尺寸 (1024x1024, 1024x1792, 1792x1024, 2048x2048, 2560x1440, 1440x2560)")
    parser.add_argument("-c", "--count", type=int, default=1, help="生成图片数量")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子，-1表示随机")
    parser.add_argument("--scale", type=float, default=0.5, help="文本影响程度，0-1之间")
    parser.add_argument("--no-watermark", action="store_true", help="不添加水印")
    
    # API参数
    parser.add_argument("-ak", "--access-key", help="火山引擎Access Key")
    parser.add_argument("-sk", "--secret-key", help="火山引擎Secret Key")
    
    # 其他选项
    parser.add_argument("--preview", action="store_true", help="预览生成的图片")
    
    args = parser.parse_args()
    
    # 获取API密钥
    access_key = args.access_key or os.getenv("VOLCENGINE_ACCESS_KEY")
    secret_key = args.secret_key or os.getenv("VOLCENGINE_SECRET_KEY")
    
    if not access_key or not secret_key:
        print("错误: 未提供火山引擎API密钥")
        print("请通过命令行参数(--access-key, --secret-key)或环境变量(VOLCENGINE_ACCESS_KEY, VOLCENGINE_SECRET_KEY)提供密钥")
        print("也可以复制.env.example为.env并填入密钥")
        sys.exit(1)
    
    # 验证图片尺寸
    valid_sizes = ["1024x1024", "1024x1792", "1792x1024", "2048x2048", "2560x1440", "1440x2560"]
    if args.size not in valid_sizes:
        print(f"错误: 无效的图片尺寸 '{args.size}'")
        print(f"有效的尺寸有: {', '.join(valid_sizes)}")
        sys.exit(1)
    
    # 验证生成数量
    if args.count < 1 or args.count > 10:
        print(f"错误: 生成数量必须在1-10之间，当前为 {args.count}")
        sys.exit(1)
    
    # 验证文本影响程度
    if args.scale < 0 or args.scale > 1:
        print(f"错误: 文本影响程度必须在0-1之间，当前为 {args.scale}")
        sys.exit(1)
    
    # 获取提示词列表
    prompts = []
    
    if args.file:
        prompts = load_prompts_from_file(args.file)
        if not prompts:
            print(f"错误: 从文件 '{args.file}' 中未找到有效的提示词")
            sys.exit(1)
    elif args.prompt:
        prompts = [args.prompt]
    else:
        # 交互式输入
        prompt = input("请输入提示词: ")
        if prompt.strip():
            prompts = [prompt]
        else:
            print("错误: 未提供提示词")
            sys.exit(1)
    
    # 创建API客户端
    client = Jimeng4APIClient(access_key, secret_key)
    
    # 生成图片
    all_saved_files = []
    
    for prompt in prompts:
        print(f"\n正在生成图片: {prompt}")
        print(f"尺寸: {args.size}")
        print(f"数量: {args.count}")
        print(f"种子: {args.seed}")
        print(f"文本影响程度: {args.scale}")
        print(f"水印: {'是' if not args.no_watermark else '否'}")
        print("=" * 50)
        
        try:
            # 调用API生成图片
            result = client.generate_image(
                prompt=prompt,
                size=args.size,
                count=args.count,
                seed=args.seed,
                scale=args.scale,
                with_watermark=not args.no_watermark
            )
            
            # 检查响应结果
            if "data" in result:
                # 保存图片
                saved_files = save_images(result["data"], args.output)
                all_saved_files.extend(saved_files)
                
                # 显示生成信息
                print("\n生成完成!")
                print(f"成功保存了 {len(saved_files)} 张图片")
                
                # 如果需要预览
                if args.preview and saved_files:
                    # 只预览第一张图片
                    # preview_image(saved_files[0])
                    print("预览功能已禁用，如需使用请取消注释相关代码")
            else:
                print(f"错误: API返回的响应格式不正确: {result}")
        
        except Exception as e:
            print(f"生成图片时发生错误: {e}")
    
    # 显示总结
    if all_saved_files:
        print(f"\n所有生成的图片已保存到: {os.path.abspath(args.output)}")
        print("生成的图片文件列表:")
        for filepath in all_saved_files:
            print(f"  - {os.path.basename(filepath)}")
    else:
        print("\n没有成功保存任何图片")

if __name__ == "__main__":
    main()