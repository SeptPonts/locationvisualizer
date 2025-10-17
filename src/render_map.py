#!/usr/bin/env python3
"""
地图模板渲染工具

从 .env 读取浏览器端 AK，渲染 map_template.html 生成最终的 map.html
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 配置
load_dotenv()


def render_map_template():
    """从模板生成最终的 map.html"""
    # 获取配置
    browser_ak = os.getenv("BAIDU_BROWSER_AK", "")

    if not browser_ak or browser_ak == "YOUR_BROWSER_AK_HERE":
        print("错误: 请先在 .env 中配置 BAIDU_BROWSER_AK")
        print("申请地址: https://lbsyun.baidu.com/apiconsole/key")
        sys.exit(1)

    # 读取模板
    template_path = Path("web/map_template.html")
    if not template_path.exists():
        print(f"错误: 找不到模板文件 {template_path}")
        sys.exit(1)

    print(f"读取模板: {template_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 替换占位符
    rendered = template.replace("{{BROWSER_AK}}", browser_ak)

    # 写入输出文件
    output_path = Path("web/map.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"✓ 生成成功: {output_path}")
    print(f"  使用的 BROWSER_AK: {browser_ak[:20]}...")


def main():
    """主函数"""
    try:
        render_map_template()
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
