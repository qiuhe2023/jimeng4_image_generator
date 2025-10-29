# 即梦4.0 API 图片生成工具

一个简单易用的Python工具，用于调用即梦4.0 API生成高质量图片。

## 功能特点

- 🚀 支持文本生成图片
- 📁 批量生成功能，支持多组提示词
- 🎨 多种尺寸选择，最高支持4K分辨率
- 💾 自动保存生成的图片
- 🔧 丰富的参数配置（种子、水印、文本影响程度等）
- 🔐 支持火山引擎API的HMAC-SHA256签名认证
- 🌐 提供Flask网页界面，方便直观操作

## 安装指南

### 前置要求

- Python 3.7+
- 火山引擎账号及Access Key/Secret Key（可从[火山引擎](https://www.volcengine.com/)获取）

### 安装步骤

1. 克隆或下载本项目
```bash
git clone https://github.com/qiuhe2023/jimeng4_image_generator.git
cd jimeng4_image_generator
```

2. 安装依赖包
```bash
pip install -r requirements.txt
```

3. 配置API密钥
   - 复制`.env.example`文件为`.env`
   - 编辑`.env`文件，填入您的火山引擎Access Key和Secret Key
```bash
cp .env.example .env
nano .env
```

## 使用说明

### 命令行使用

```bash
# 使用单个提示词生成图片
python main.py --prompt "A beautiful landscape with mountains and lake at sunset"

# 指定尺寸生成图片
python main.py --prompt "A futuristic city skyline" --size 2560x1440

# 生成多张图片
python main.py --prompt "A cute cat" --count 3

# 不添加水印
python main.py --prompt "A portrait of a knight" --no-watermark
```

### 批量生成

```bash
# 从文件加载提示词批量生成
python main.py --file example_prompts.txt

# 指定输出目录
python main.py --file example_prompts.txt --output my_artworks
```

### 高级用法

```bash
# 指定随机种子（可复现结果）
python main.py --prompt "A sushi platter" --seed 12345

# 调整文本影响程度
python main.py --prompt "A dragon flying over a castle" --scale 0.8

# 通过命令行参数指定密钥
python main.py --prompt "A cozy cabin" --access-key YOUR_ACCESS_KEY --secret-key YOUR_SECRET_KEY
```

### 命令行参数说明

| 参数 | 缩写 | 说明 | 默认值 |
|------|------|------|--------|
| `--prompt` | `-p` | 图片生成提示词 | 无 |
| `--file` | `-f` | 包含提示词的文本文件路径 | 无 |
| `--size` | `-s` | 图片尺寸，如'2048x2048' | `2048x2048` |
| `--count` | `-c` | 生成图片数量 | `1` |
| `--output` | `-o` | 输出目录 | `output` |
| `--access-key` | `-ak` | 火山引擎Access Key | 从环境变量获取 |
| `--secret-key` | `-sk` | 火山引擎Secret Key | 从环境变量获取 |
| `--no-watermark` | 无 | 不添加水印 | `False` |
| `--seed` | 无 | 随机种子，-1表示随机 | `-1` |
| `--scale` | 无 | 文本影响程度，0-1之间 | `0.5` |

## 网页界面使用

本项目提供了一个基于Flask的网页界面，方便用户通过浏览器操作：

1. 启动Web服务
```bash
python app.py
```

2. 访问网页
   - 本地地址: http://127.0.0.1:5001
   - 网络地址: http://您的IP地址:5001

3. 在网页界面中，您可以：
   - 输入提示词
   - 选择图片尺寸
   - 设置生成数量
   - 调整其他参数
   - 查看生成历史和结果预览

## 项目结构

```
jimeng4_image_generator/
├── app.py              # Flask Web服务
├── main.py             # 核心功能实现
├── requirements.txt    # 项目依赖
├── .env.example        # 环境变量示例
├── example_prompts.txt # 示例提示词
├── templates/          # 网页模板
│   └── index.html      # 主页面
└── static/             # 静态资源
    ├── style.css       # 样式文件
    └── script.js       # JavaScript交互
```

## 注意事项

1. API密钥安全：请妥善保管您的Access Key和Secret Key，不要泄露给他人
2. 生成限制：免费额度可能有限，请合理使用
3. 提示词技巧：
   - 尽量详细描述您想要的图像
   - 可以指定艺术风格、色彩、构图等
   - 中英文均可，建议不超过300个汉字

## 许可证

MIT License