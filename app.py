#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即梦4.0 API 图片生成工具 Web服务

基于Flask的Web界面，用于调用图片生成功能。
"""

import os
import sys
import json
import uuid
import shutil
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.urandom(24)
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 确保输出目录存在
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def generate_image(prompt: str, size: str = "2048x2048", count: int = 1,
                  seed: int = -1, scale: float = 0.5, with_watermark: bool = True) -> dict:
    """
    生成图片的函数
    
    Args:
        prompt: 提示词
        size: 图片尺寸
        count: 生成数量
        seed: 随机种子
        scale: 文本影响程度
        with_watermark: 是否添加水印
    
    Returns:
        包含生成状态和文件信息的字典
    """
    try:
        # 生成唯一ID用于本次生成任务
        task_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], f"{timestamp}_{task_id}")
        
        # 构建命令行参数
        cmd = [sys.executable, "main.py", 
               "--prompt", prompt, 
               "--size", size, 
               "--count", str(count),
               "--output", output_dir,
               "--scale", str(scale)]
        
        # 添加可选参数
        if seed != -1:
            cmd.extend(["--seed", str(seed)])
        
        if not with_watermark:
            cmd.append("--no-watermark")
        
        # 执行命令
        print(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待命令执行完成
        stdout, stderr = process.communicate()
        exit_code = process.returncode
        
        # 记录输出
        print(f"命令输出: {stdout}")
        if stderr:
            print(f"命令错误: {stderr}")
        
        # 检查是否成功
        if exit_code != 0:
            return {
                "success": False,
                "message": f"生成失败，错误码: {exit_code}",
                "error": stderr
            }
        
        # 获取生成的图片列表
        generated_images = []
        if os.path.exists(output_dir):
            for filename in sorted(os.listdir(output_dir)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # 构建相对路径，用于在网页中访问
                    relative_path = os.path.join(os.path.basename(output_dir), filename)
                    generated_images.append(relative_path)
        
        if not generated_images:
            return {
                "success": False,
                "message": "未找到生成的图片，请检查日志",
                "stdout": stdout,
                "stderr": stderr
            }
        
        return {
            "success": True,
            "message": "图片生成成功",
            "images": generated_images,
            "count": len(generated_images),
            "task_id": task_id,
            "timestamp": timestamp
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"生成过程中发生错误: {str(e)}"
        }

@app.route('/')
def index():
    """
    首页路由
    """
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """
    生成图片的API路由
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必要的参数
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "message": "缺少必要的提示词参数"
            }), 400
        
        # 提取参数
        prompt = data.get('prompt', '').strip()
        size = data.get('size', '2048x2048')
        count = int(data.get('count', 1))
        seed = int(data.get('seed', -1))
        scale = float(data.get('scale', 0.5))
        with_watermark = not data.get('no_watermark', False)
        
        # 验证参数
        if not prompt:
            return jsonify({
                "success": False,
                "message": "提示词不能为空"
            }), 400
        
        # 限制生成数量
        count = min(max(1, count), 10)
        
        # 限制提示词长度
        if len(prompt) > 500:
            return jsonify({
                "success": False,
                "message": "提示词长度不能超过500个字符"
            }), 400
        
        # 验证尺寸
        valid_sizes = ["1024x1024", "1024x1792", "1792x1024", "2048x2048", "2560x1440", "1440x2560"]
        if size not in valid_sizes:
            return jsonify({
                "success": False,
                "message": f"无效的图片尺寸，请选择: {', '.join(valid_sizes)}"
            }), 400
        
        # 验证scale
        scale = min(max(0, scale), 1)
        
        # 调用生成函数
        result = generate_image(
            prompt=prompt,
            size=size,
            count=count,
            seed=seed,
            scale=scale,
            with_watermark=with_watermark
        )
        
        # 返回结果
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"请求处理失败: {str(e)}"
        }), 500

@app.route('/output/<path:filename>')
def serve_image(filename):
    """
    提供生成的图片的路由
    """
    # 确保文件路径安全
    secure_path = secure_filename(filename)
    # 提取目录和文件名
    parts = filename.split('/')
    if len(parts) == 2:
        dir_name, file_name = parts
        return send_from_directory(os.path.join(app.config['OUTPUT_FOLDER'], dir_name), file_name)
    else:
        return "Invalid path", 404

@app.route('/output')
def list_outputs():
    """
    列出所有生成的图片的路由
    """
    try:
        output_list = []
        
        # 遍历输出目录
        if os.path.exists(app.config['OUTPUT_FOLDER']):
            for task_dir in sorted(os.listdir(app.config['OUTPUT_FOLDER']), reverse=True):
                task_path = os.path.join(app.config['OUTPUT_FOLDER'], task_dir)
                if os.path.isdir(task_path):
                    images = []
                    for filename in sorted(os.listdir(task_path)):
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                            images.append(os.path.join(task_dir, filename))
                    
                    if images:
                        # 提取时间戳和任务ID（如果有）
                        timestamp = task_dir.split('_')[0] if '_' in task_dir else "未知"
                        task_id = task_dir.split('_')[1] if '_' in task_dir else "未知"
                        
                        output_list.append({
                            "task_dir": task_dir,
                            "timestamp": timestamp,
                            "task_id": task_id,
                            "images": images,
                            "count": len(images),
                            "date": datetime.fromtimestamp(os.path.getctime(task_path)).strftime("%Y-%m-%d %H:%M:%S")
                        })
        
        # 限制返回的数量，避免数据过大
        output_list = output_list[:50]  # 只返回最近的50个任务
        
        return jsonify({
            "success": True,
            "total_tasks": len(output_list),
            "tasks": output_list
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取图片列表失败: {str(e)}"
        }), 500

def cleanup_old_outputs(max_age_days: int = 7):
    """
    清理旧的输出文件
    
    Args:
        max_age_days: 最大保留天数
    """
    try:
        import time
        
        max_age_seconds = max_age_days * 24 * 60 * 60
        current_time = time.time()
        
        if os.path.exists(app.config['OUTPUT_FOLDER']):
            for task_dir in os.listdir(app.config['OUTPUT_FOLDER']):
                task_path = os.path.join(app.config['OUTPUT_FOLDER'], task_dir)
                if os.path.isdir(task_path):
                    # 检查目录创建时间
                    dir_time = os.path.getctime(task_path)
                    if current_time - dir_time > max_age_seconds:
                        # 删除旧目录
                        shutil.rmtree(task_path)
                        print(f"已清理旧目录: {task_path}")
    
    except Exception as e:
        print(f"清理旧文件失败: {e}")

def check_dependencies():
    """
    检查依赖是否安装
    """
    try:
        import requests
        import dotenv
        import PIL
        print("所有依赖都已安装")
        return True
    except ImportError as e:
        missing_package = str(e).split("'"[1])
        print(f"缺少依赖: {missing_package}")
        print("请运行: pip install -r requirements.txt")
        return False

if __name__ == '__main__':
    # 检查依赖
    check_dependencies()
    
    # 启动前清理旧文件（可选）
    # cleanup_old_outputs()
    
    # 启动服务器
    print("启动Web服务...")
    print("访问地址: http://127.0.0.1:5001")
    print("按 Ctrl+C 停止服务")
    
    # 注意：在生产环境中，应该使用适当的WSGI服务器
    # 例如：gunicorn, uwsgi等
    app.run(host='0.0.0.0', port=5001, debug=False)