# flask-admin-sqlite-novel

私人小说浏览系统 — 基于 Flask + SQLite3 + Layui 的单用户小说阅读与管理平台

## 功能特性

- **登录鉴权**：首页为登录页面，所有功能需登录后访问
- **小说分类管理**：创建、编辑、删除分类，支持分类筛选
- **小说标签管理**：多对多标签关联，每本书可打多个标签，支持按标签筛选
- **小说收藏**：一键收藏/取消收藏，收藏列表页
- **小说评分**：1-5 星评分，支持评价文字，显示平均评分
- **TXT 导入（4 步向导）**：
  - Step 1：上传文件，自动检测编码（GBK/GB2312/UTF-8）并转换为 UTF-8
  - Step 2：选择章节拆分规则（8 大类默认规则）或自定义正则
  - Step 3：预览章节标题列表，支持删除章节并重新生成
  - Step 4：确认保存，标题默认取文件名（不含扩展名），作者可为空
- **章节拆分规则管理**：8 大类内置规则（中文序号、特殊章节、分隔符、英文序号、特殊符号、纯数字、分节阅读、卷/部/篇），支持自定义新增、编辑、启用/禁用
- **小说阅读**：完整阅读进度记录，上一章/下一章切换
- **书签功能**：添加、查看、删除书签，支持跳转
- **在线内容修改**：修改章节标题与正文，即时生效
- **小说导出**：导出为 TXT 文件，章节按序拼接
- **全站全文搜索**：搜索章节内容，显示匹配摘要与跳转链接
- **Flask-Admin 后台**：完整的数据模型管理界面
- **响应式设计**：适配电脑（≥992px）与手机（<992px）

## 技术栈

- **后端**：Flask 2.x + Flask-SQLAlchemy + Flask-Admin
- **数据库**：SQLite3
- **前端**：Layui 2.x
- **编码检测**：chardet

## 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装与运行

```bash
# 克隆项目
git clone <repository-url>
cd flask-admin-sqlite-novel

# 安装依赖
pip install -r requirements.txt

# 启动应用
python run.py
```

### 访问

- **前台**：http://localhost:5000
- **后台**：http://localhost:5000/admin

### 默认账号

- 用户名：`admin`
- 密码：`admin123`

> ⚠️ 首次登录后建议修改默认密码

## 项目结构

```
flask-admin-sqlite-novel/
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── models.py            # 数据模型定义
│   ├── auth.py              # 登录鉴权模块
│   ├── importer.py          # TXT 导入模块（4 步向导）
│   ├── rules.py             # 章节拆分规则管理
│   ├── categories.py        # 分类管理
│   ├── tags.py              # 标签管理
│   ├── favorites.py         # 收藏管理
│   ├── ratings.py           # 评分管理
│   ├── novels.py            # 小说列表与详情
│   ├── reading.py           # 阅读模块
│   ├── search.py            # 全文搜索
│   └── export.py            # 导出模块
├── templates/               # Layui 模板
│   ├── base.html            # 基础模板
│   ├── login.html           # 登录页
│   ├── dashboard.html       # 仪表盘
│   ├── novels/              # 小说相关页面
│   ├── rules/               # 规则管理页面
│   └── ...
├── static/                  # 静态资源（Layui）
├── config.py                # 配置文件
├── run.py                   # 启动入口
└── requirements.txt         # 依赖清单
```

## 数据模型

| 表名 | 说明 |
|------|------|
| `user` | 用户表 |
| `category` | 小说分类表 |
| `novel` | 小说表 |
| `chapter` | 章节表 |
| `chapter_rule` | 章节拆分规则表 |
| `reading_progress` | 阅读进度表 |
| `bookmark` | 书签表 |
| `tag` | 标签表 |
| `novel_tags` | 小说-标签关联表（多对多） |
| `favorite` | 收藏表 |
| `rating` | 评分表 |

详细的数据模型设计请参考 [database_prototype.md](database_prototype.md)

## 章节拆分规则（内置 8 大类）

| 分类 | 规则名称 | 正则示例 | 匹配示例 |
|------|----------|----------|----------|
| 中文序号 | 中文数字章节 | `^第[零一二三四五六七八九十百千万\d]+章.*$` | 第一章、第1章 |
| 特殊章节 | 特殊章节 | `^(序章\|楔子\|终章\|后记\|尾声\|番外\|前言\|正文).*$` | 序章、番外一 |
| 分隔符章节 | 分隔符章节 | `^[、.,_—\-,,::].*$` | 、第一章 |
| 英文序号 | 英文章节 | `^(Chapter\|Section\|Part\|Episode\|No\.)\s*\d+.*$` | Chapter 1 |
| 特殊符号 | 特殊符号章节 | `^[【】〔〕〖〗「」『』〈〉［］《》（）===].*$` | 【第一章】 |
| 纯数字 | 纯数字章节 | `^\d+\.?\s+.*$` | 1. xxx |
| 分节阅读 | 分节阅读 | `^(分[页节章段]阅读\|第\d+[页节]).*$` | 分节阅读一 |
| 卷/部/篇 | 卷部篇回 | `^第?[零一二三四五六七八九十百千万\d]+[卷部篇回场话集].*$` | 第一卷、第1回 |

## 路由列表

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页（未登录跳转到登录页） |
| `/login` | GET/POST | 登录页 |
| `/logout` | GET | 登出 |
| `/dashboard` | GET | 仪表盘 |
| `/novels` | GET | 小说列表页（支持分类/标签筛选） |
| `/novels/<id>` | GET | 小说详情页 |
| `/novels/<id>/delete` | POST | 删除小说 |
| `/novels/<id>/read/<chapter_id>` | GET | 阅读页 |
| `/novels/<id>/chapter/<chapter_id>/edit` | GET/POST | 编辑章节 |
| `/novels/<id>/export` | GET | 导出 TXT |
| `/novels/<id>/favorite` | POST | 收藏 |
| `/novels/<id>/unfavorite` | POST | 取消收藏 |
| `/novels/<id>/rate` | POST | 评分 |
| `/novels/<id>/tags` | POST | 更新标签 |
| `/novels/import` | GET/POST | 导入 Step 1：上传文件 |
| `/novels/import/step2` | GET/POST | 导入 Step 2：选择规则 |
| `/novels/import/step3` | GET/POST | 导入 Step 3：章节预览 |
| `/novels/import/step4` | GET/POST | 导入 Step 4：确认保存 |
| `/categories` | GET | 分类列表 |
| `/categories/create` | POST | 创建分类 |
| `/categories/<id>/edit` | POST | 编辑分类 |
| `/categories/<id>/delete` | POST | 删除分类 |
| `/tags` | GET | 标签列表 |
| `/tags/create` | POST | 创建标签 |
| `/tags/<id>/edit` | POST | 编辑标签 |
| `/tags/<id>/delete` | POST | 删除标签 |
| `/favorites` | GET | 收藏列表 |
| `/rules` | GET | 章节规则列表 |
| `/rules/create` | POST | 新增规则 |
| `/rules/<id>/edit` | POST | 编辑规则 |
| `/rules/<id>/toggle` | POST | 启用/禁用规则 |
| `/rules/<id>/delete` | POST | 删除规则 |
| `/rules/restore-defaults` | POST | 恢复默认规则 |
| `/search` | GET | 全文搜索 |
| `/admin` | GET | Flask-Admin 后台 |

## 配置说明

配置文件位于 `config.py`：

```python
SECRET_KEY = 'your-secret-key'          # Flask 密钥
SQLALCHEMY_DATABASE_URI = 'sqlite:///novel.db'  # 数据库路径
UPLOAD_FOLDER = 'uploads'               # 上传目录
MAX_CONTENT_LENGTH = 50 * 1024 * 1024   # 最大上传大小（50MB）
```

## 使用说明

### 导入小说

1. 点击侧边栏"导入小说"进入 Step 1
2. 上传 TXT 文件，系统自动检测编码并转换为 UTF-8
3. Step 2 选择章节拆分规则（或填入自定义正则）
4. Step 3 预览章节列表，可删除不需要的章节
5. Step 4 确认导入，标题默认为文件名（不含扩展名），作者可选填

### 阅读小说

1. 在小说列表页点击小说封面或标题进入详情页
2. 点击章节标题开始阅读
3. 阅读进度自动保存，下次打开自动定位到上次位置
4. 可添加书签标记重要位置

### 管理标签

1. 点击侧边栏"标签管理"进入标签列表
2. 创建标签时可设置颜色
3. 在小说详情页可勾选/取消勾选标签

## 开发说明

### 添加新功能

1. 在 `app/` 目录下创建新的模块文件
2. 在 `app/__init__.py` 中注册蓝图
3. 在 `templates/` 目录下创建对应模板
4. 在 `models.py` 中添加数据模型（如需）

### 数据库迁移

```bash
# 初始化迁移（首次）
flask db init

# 创建迁移
flask db migrate -m "description"

# 应用迁移
flask db upgrade
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request
