#!/usr/bin/env python3
"""
百度地图酒店批量地理编码工具

使用百度 Place API v3.0 行政区划区域检索接口
将"酒店名+城市"批量转换为坐标数据
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# 加载 .env 配置
load_dotenv()


def get_config(key: str, default: str = "") -> str:
    """从环境变量获取配置，如果不存在则返回默认值"""
    return os.getenv(key, default)


def validate_config():
    """验证配置是否有效"""
    ak = get_config("BAIDU_SERVER_AK")
    if not ak or ak == "YOUR_SERVER_AK_HERE":
        raise RuntimeError(
            "请先在 .env 中配置 BAIDU_SERVER_AK\n"
            "申请地址: https://lbsyun.baidu.com/apiconsole/key"
        )


def search_hotel(name: str, city: str) -> dict:
    """
    使用百度 Place API v3 检索酒店坐标

    Args:
        name: 酒店名称
        city: 城市名称

    Returns:
        dict: 包含 uid/name/lng/lat/address 等字段，失败抛异常
    """
    api_base = get_config("BAIDU_PLACE_API_BASE", "https://api.map.baidu.com/place/v3")
    url = f"{api_base}/region"

    params = {
        "query": name,
        "region": city,
        "region_limit": "true",  # 严格限制在城市内
        "filter": "industry_type:hotel",  # 强化酒店召回
        "scope": 1,  # 基础信息
        "page_size": 1,  # 只取 Top1 结果
        "output": "json",
        "ak": get_config("BAIDU_SERVER_AK"),
    }

    timeout = float(get_config("REQUEST_TIMEOUT", "10"))

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        # 检查 API 状态码
        if data.get("status") != 0:
            msg = data.get("message", "未知错误")
            raise RuntimeError(f"百度 API 错误 (status={data.get('status')}): {msg}")

        # 检查是否有结果
        results = data.get("results")
        if not results:
            raise ValueError(f"找不到酒店: {name} @ {city}")

        # 提取第一个结果
        poi = results[0]
        location = poi.get("location", {})

        return {
            "uid": poi.get("uid"),
            "name": poi.get("name", name),
            "city": city,
            "province": poi.get("province", ""),
            "area": poi.get("area", ""),
            "address": poi.get("address", ""),
            "lng": location.get("lng"),
            "lat": location.get("lat"),
            "telephone": poi.get("telephone", ""),
            "detail_info": poi.get("detail_info", {}),
        }

    except requests.RequestException as e:
        raise RuntimeError(f"网络请求失败: {e}")


def process_csv(input_file: str, output_file: str):
    """
    批量处理 CSV 文件中的酒店数据

    Args:
        input_file: 输入 CSV 文件路径，需要包含 name 和 city 列
        output_file: 输出 JSON 文件路径
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"找不到输入文件: {input_file}")

    # 读取 CSV
    print(f"读取 CSV 文件: {input_file}")
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV 文件为空")

    print(f"共读取 {len(rows)} 条酒店记录\n")

    # 批量处理
    results = []
    failed = []
    delay = float(get_config("REQUEST_DELAY", "0.1"))

    for i, row in enumerate(rows, 1):
        name = row.get("name", "").strip()
        city = row.get("city", "").strip()

        # 验证必填字段
        if not name or not city:
            warning = f"第{i}行数据不完整，跳过: name='{name}', city='{city}'"
            print(f"⚠️  {warning}")
            failed.append(
                {"row": i, "reason": "数据不完整", "name": name, "city": city}
            )
            continue

        # 调用 API
        print(f"[{i}/{len(rows)}] 检索: {name} ({city})...", end=" ")

        try:
            result = search_hotel(name, city)
            results.append(result)
            print(f"✓ {result['lng']:.6f}, {result['lat']:.6f}")

            # 限流，避免 QPS 超限
            time.sleep(delay)

        except Exception as e:
            print(f"✗ {e}")
            failed.append({"row": i, "reason": str(e), "name": name, "city": city})
            time.sleep(delay)

    # 输出 JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 统计结果
    print(f"\n{'=' * 60}")
    print("处理完成!")
    print(f"成功: {len(results)} 条")
    print(f"失败: {len(failed)} 条")
    print(f"输出文件: {output_file}")

    if failed:
        print("\n失败记录:")
        for item in failed:
            row = item["row"]
            name = item["name"]
            city = item["city"]
            reason = item["reason"]
            print(f"  第{row}行: {name} ({city}) - {reason}")

    return results, failed


def main():
    """主函数"""
    # 验证配置
    try:
        validate_config()
    except RuntimeError as e:
        print(f"配置错误: {e}")
        sys.exit(1)

    # 处理参数
    if len(sys.argv) < 2:
        print("用法: python geocode.py <输入 CSV 文件> [输出 JSON 文件]")
        print("示例: python geocode.py data/hotels.csv output/hotels.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output/hotels.json"

    # 执行批处理
    try:
        process_csv(input_file, output_file)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
