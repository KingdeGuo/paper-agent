#!/usr/bin/env python3
"""
智能文献管理系统 - 安装脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """运行shell命令"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"错误: {e}")
        print(f"输出: {e.stderr}")
        return None

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 9):
        print("错误: 需要Python 3.9或更高版本")
        sys.exit(1)
    print(f"✓ Python版本: {sys.version}")

def install_python_dependencies():
    """安装Python依赖"""
    print("正在安装Python依赖...")
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("错误: requirements.txt文件不存在")
        sys.exit(1)
    
    result = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    if result is None:
        print("错误: 安装Python依赖失败")
        sys.exit(1)
    print("✓ Python依赖安装完成")

def create_directories():
    """创建必要的目录"""
    directories = [
        "data/pdfs",
        "data/vector_db",
        "logs"
    ]
    
    for directory in directories:
        path = Path(__file__).parent / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def check_frontend():
    """检查前端环境"""
    print("检查前端环境...")
    
    # 检查Node.js
    node_result = run_command("node --version")
    if node_result is None:
        print("警告: Node.js未安装，前端将无法运行")
        return False
    
    print(f"✓ Node.js版本: {node_result.strip()}")
    
    # 检查npm
    npm_result = run_command("npm --version")
    if npm_result is None:
        print("警告: npm未安装，前端将无法运行")
        return False
    
    print(f"✓ npm版本: {npm_result.strip()}")
    return True

def install_frontend_dependencies():
    """安装前端依赖"""
    frontend_dir = Path(__file__).parent / "frontend"
    if not frontend_dir.exists():
        print("警告: 前端目录不存在")
        return
    
    print("正在安装前端依赖...")
    result = run_command("npm install", cwd=str(frontend_dir))
    if result is None:
        print("警告: 安装前端依赖失败")
    else:
        print("✓ 前端依赖安装完成")

def main():
    """主函数"""
    print("=" * 50)
    print("智能文献管理系统 - 安装脚本")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 安装Python依赖
    install_python_dependencies()
    
    # 创建目录
    create_directories()
    
    # 检查前端环境
    frontend_available = check_frontend()
    
    if frontend_available:
        install_frontend_dependencies()
    
    print("\n" + "=" * 50)
    print("安装完成！")
    print("=" * 50)
    
    print("\n下一步:")
    print("1. 启动后端: cd backend && python main.py")
    if frontend_available:
        print("2. 启动前端: cd frontend && npm start")
    print("\nAPI文档: http://localhost:8000/docs")
    print("前端应用: http://localhost:3000")

if __name__ == "__main__":
    main()
