# Location Visualizer

百度地图酒店批量展示工具。使用百度 Place API v3.0 批量将"酒店名+城市"转换为坐标，并在地图上可视化展示。

## 功能特性

- ✅ 使用百度 Place API v3.0 **行政区划区域检索**接口
- ✅ 支持批量处理 CSV 格式的酒店数据
- ✅ 自动过滤不符合条件的数据并记录失败原因
- ✅ 前端地图自动调整视野，让所有酒店都可见
- ✅ 点击 Marker 显示详细信息（地址、电话、评分等）
- ✅ 配置统一从 .env 读取，安全便捷

## 目录结构

```
location_visualizer/
├── src/
│   ├── geocode.py          # 地理编码脚本
│   └── render_map.py       # 地图模板渲染脚本
├── data/
│   └── hotels_sample.csv   # 示例数据（10 个酒店）
├── output/                  # 生成结果（gitignore）
│   └── hotels.json         # 坐标数据
├── web/
│   ├── map_template.html   # HTML 模板
│   └── map.html            # 生成的最终 HTML（gitignore）
├── .env                    # 配置文件（gitignore）
├── .env.example            # 配置示例
├── pyproject.toml          # 依赖管理
├── Makefile                # 命令快捷方式
└── README.md
```

## 快速开始

### 1. 申请百度地图 AK

访问 [百度地图开放平台](https://lbsyun.baidu.com/apiconsole/key) 申请两个 AK：

- **服务端 AK**：用于 Python 脚本调用 API，配置 **IP 白名单**
- **浏览器端 AK**：用于前端地图显示，配置 **Referer 白名单**

### 2. 配置 .env

复制 `.env.example` 为 `.env`，填写你的 AK：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# 百度地图 API
BAIDU_SERVER_AK='你的服务端AK'
BAIDU_BROWSER_AK='你的浏览器端AK'
BAIDU_PLACE_API_BASE='https://api.map.baidu.com/place/v3'
REQUEST_DELAY='0.1'
REQUEST_TIMEOUT='10'
```

### 3. 安装依赖

```bash
make install
```

或手动安装：

```bash
uv sync
```

### 4. 准备数据

创建你的 CSV 文件，格式如下（参考 `data/hotels_sample.csv`）：

```csv
name,city
北京国贸大酒店,北京
上海和平饭店,上海
```

### 5. 运行工具

#### 步骤 1：批量地理编码

```bash
make geocode
```

这会读取 `data/hotels_sample.csv`，调用百度 API，生成 `output/hotels.json`。

#### 步骤 2：渲染地图

```bash
make render-map
```

这会从 `.env` 读取 `BAIDU_BROWSER_AK`，生成 `web/map.html`。

#### 步骤 3：启动本地服务器

```bash
make serve
```

然后在浏览器打开 `http://localhost:8000/web/map.html`。

## 使用自定义数据

如果你有自己的酒店列表：

```bash
uv run python src/geocode.py <你的CSV文件> output/hotels.json
make render-map
make serve
```

## API 说明

### geocode.py

批量地理编码工具，将"酒店名+城市"转换为坐标。

**使用方法：**

```bash
python src/geocode.py <输入CSV> [输出JSON]
```

**输入格式（CSV）：**

| name | city |
|------|------|
| 酒店名称 | 城市名 |

**输出格式（JSON）：**

```json
[
  {
    "uid": "xxx",
    "name": "北京国贸大酒店",
    "city": "北京",
    "province": "北京市",
    "area": "朝阳区",
    "address": "建国门外大街1号",
    "lng": 116.46,
    "lat": 39.91,
    "telephone": "010-xxxx",
    "detail_info": {}
  }
]
```

### render_map.py

从 `.env` 读取浏览器端 AK，渲染地图模板。

**使用方法：**

```bash
python src/render_map.py
```

自动生成 `web/map.html`。

## 注意事项

### 安全配置

- ❌ **绝对不能**把 `.env` 提交到 Git 仓库
- ❌ **绝对不能**用一个 AK 同时做前端和后端
- ✅ 服务端 AK 配置 IP 白名单或 SN 签名
- ✅ 浏览器端 AK 配置 Referer 白名单

### API 限制

- 百度地图有 **QPS（每秒请求数）限制**
- 脚本内置了 `REQUEST_DELAY=0.1`（每次请求间隔 0.1 秒）
- 如果数据量很大，考虑购买配额或使用异步队列

### 坐标系

- 百度 Place API 默认返回 **bd09ll**（百度经纬度）
- 百度地图 JS API 也使用 **bd09ll**
- 直接使用，不需要坐标转换

### 错误处理

- 如果 API 返回错误，脚本会直接抛异常（不悄悄返回 None）
- CSV 中数据不完整的行会被跳过并打印警告
- 所有失败记录会在最后汇总显示

## Linus 式代码审查

**【品味评分】** 🟢 好品味

**【核心洞察】**

- 数据流：`.env → geocode.py → hotels.json → map.html → 浏览器`，单向流动
- 配置集中化：消除 `config.py`，统一用 `.env`
- 模板渲染：用最简单的字符串替换，不引入 Jinja2 等重量级工具

**【复杂度】**

- `geocode.py`: ~200 行（包含完整错误处理）
- `render_map.py`: ~60 行（简单模板替换）
- 总计: ~260 行，符合"简单到无法加 bug"标准

**【零特殊情况】**

- 缺少 `.env` 配置 → 直接抛异常
- API 调用失败 → 记录并继续
- 所有错误统一处理，不需要大量 `if/else`

## 许可证

本项目代码基于 MIT 许可证开源。百度地图 API 使用需遵守百度地图开放平台服务条款。

## 相关链接

- [百度地图开放平台](https://lbsyun.baidu.com/)
- [Place API v3 文档](https://lbsyun.baidu.com/faq/api?title=webapi/guide/webservice-placeapi/district)
- [百度地图 JavaScript API 文档](https://mapopen-pub-jsapi.bj.bcebos.com/jsapi/reference/jsapi_reference_3_0.html)
