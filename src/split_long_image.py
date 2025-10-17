#!/usr/bin/env python3
"""
超长截图智能切分工具
使用水平投影法找到安全的切割点（空白行），避免切断文字
"""

import sys
from math import ceil
from pathlib import Path

import numpy as np
from PIL import Image

# 参数配置
MAX_HEIGHT = 3200  # 超过此高度视为"超长"
SPLIT_HEIGHT = 3000  # 每段目标高度
SEARCH_RANGE = 100  # 在切割点上下100px内找空白行
OVERLAP = 50  # 段间重叠50px


def compute_edge_strength(img: Image.Image, y: int) -> float:
    """
    计算某一行的边缘强度（像素变化程度）

    Args:
        img: PIL Image对象
        y: 行号

    Returns:
        边缘强度值（越小说明该行越接近空白/纯色）
    """
    # 提取这一行的像素（宽度×1的矩形）
    row = img.crop((0, y, img.width, y + 1))
    row_array = np.array(row)

    # 如果是RGB图，转为灰度（简单平均）
    if len(row_array.shape) == 3:
        row_array = np.mean(row_array, axis=2)

    # 计算相邻像素的差值（梯度）
    row_pixels = row_array[0]  # 提取第一行（只有一行）
    diff = np.abs(np.diff(row_pixels))  # 相邻像素差的绝对值

    # 边缘强度 = 差值总和
    return np.sum(diff)


def find_safe_split_point(
    img: Image.Image, target_y: int, search_range: int = SEARCH_RANGE
) -> int:
    """
    在目标切割点附近找到边缘强度最小的行（最安全的切割位置）

    Args:
        img: PIL Image对象
        target_y: 目标切割点y坐标
        search_range: 搜索范围（±像素）

    Returns:
        实际切割点y坐标
    """
    start_y = max(0, target_y - search_range)
    end_y = min(img.height, target_y + search_range)

    min_edge = float("inf")
    best_y = target_y

    for y in range(start_y, end_y):
        edge_strength = compute_edge_strength(img, y)
        if edge_strength < min_edge:
            min_edge = edge_strength
            best_y = y

    return best_y


def split_long_image(input_path: str, output_dir: str = "output"):
    """
    切分超长截图的主函数

    Args:
        input_path: 输入图片路径
        output_dir: 输出目录
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    # 加载图片
    print(f"Loading image: {input_path}")
    img = Image.open(input_path)
    width, height = img.size
    print(f"Image size: {width}×{height}px")

    # 判断是否超长
    if height <= MAX_HEIGHT:
        print(
            f"Image height ({height}px) <= MAX_HEIGHT ({MAX_HEIGHT}px), "
            "no need to split."
        )
        return

    # 计算需要切成几段
    n_splits = ceil(height / SPLIT_HEIGHT)
    print(f"Image is too long, splitting into {n_splits} parts...")

    # 计算目标切割点（不包括0和height）
    target_split_points = [SPLIT_HEIGHT * i for i in range(1, n_splits)]

    # 找到实际的安全切割点
    print("Finding safe split points...")
    actual_split_points = []
    for i, target_y in enumerate(target_split_points, 1):
        safe_y = find_safe_split_point(img, target_y)
        actual_split_points.append(safe_y)
        print(
            f"  Split point {i}: target={target_y}px, actual={safe_y}px "
            f"(offset={safe_y - target_y}px)"
        )

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 准备输出文件名
    stem = input_path.stem  # 不含扩展名的文件名
    ext = input_path.suffix  # 扩展名（如 .jpeg）

    # 切分并保存
    print(f"Splitting and saving to {output_dir}/...")

    # 所有切割边界（包括0和height）
    boundaries = [0] + actual_split_points + [height]

    for i in range(len(boundaries) - 1):
        # 计算裁剪区域（带overlap）
        if i == 0:
            # 第一段：从0到第一个切割点+overlap
            y_start = 0
            y_end = min(boundaries[i + 1] + OVERLAP, height)
        elif i == len(boundaries) - 2:
            # 最后一段：从最后一个切割点-overlap到底部
            y_start = max(boundaries[i] - OVERLAP, 0)
            y_end = height
        else:
            # 中间段：前一个切割点-overlap到后一个切割点+overlap
            y_start = max(boundaries[i] - OVERLAP, 0)
            y_end = min(boundaries[i + 1] + OVERLAP, height)

        # 裁剪
        part = img.crop((0, y_start, width, y_end))

        # 保存
        part_filename = f"{stem}_part{i + 1:02d}{ext}"
        part_path = output_dir / part_filename
        part.save(part_path, quality=95)  # JPEG质量95

        part_height = y_end - y_start
        print(
            f"  Part {i + 1}: y={y_start}-{y_end} ({part_height}px) -> {part_filename}"
        )

    print(f"✓ Done! Split into {len(boundaries) - 1} parts.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_long_image.py <input_image_path> [output_dir]")
        print(
            "Example: python split_long_image.py data/hotels_shanghai_screenshot.jpeg"
        )
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    split_long_image(input_path, output_dir)
