# 私人小说浏览系统开发计划

> 基于 spec.md 和 database_prototype.md 生成的完整开发计划  
> 项目：Flask + SQLite3 + Layui 单用户小说浏览系统

---

## 1. 项目概述

### 1.1 目标
开发一个自托管的私人小说浏览系统，支持 TXT 小说导入、章节拆分、阅读进度记录、书签、收藏、评分、全文搜索等功能，适配电脑和手机，提供白天/黑夜主题切换。

### 1.2 技术栈
- **后端**：Flask 2.x + Flask-SQLAlchemy + Flask-Admin
- **数据库**：SQLite3
- **前端**：Layui 2.x（响应式栅格布局）
- **编码检测**：chardet（支持 GBK/GB2312/UTF-8 自动识别）

### 1.3 核心特性
- 单用户登录鉴权（所有功能需登录）
- TXT 导入 4 步向导（上传转码 → 选择规则 → 预览章节 → 确认保存）
- 8 大类章节拆分规则（中文序号、特殊章节、分隔符、英文序号、特殊符号、纯数字、分节阅读、卷部篇）
- 小说标签、收藏、评分（多对多关系）
- 阅读进度记录 + 书签功能
- 在线编辑章节 + 导出 TXT + 全文搜索
- Flask-Admin 后台管理
- 响应式布局（电脑 + 手机）
- 白天/黑夜主题切换（localStorage 持久化）

---

## 2. 当前状态分析

### 2.1 已完成文档
- ✅ [spec.md](file:///workspace/.trae/specs/build-private-novel-system/spec.md) - 完整需求规格
- ✅ [database_prototype.md](file:///workspace/database_prototype.md) - 数据库原型设计
- ✅ [tasks.md](file:///workspace/.trae/specs/build-private-novel-system/tasks.md) - 任务清单（18 个 Task）
- ✅ [checklist.md](file:///workspace/.trae/specs/build-private-novel-system/checklist.md) - 验证检查清单
- ✅ [README.md](file:///workspace/README.md) - 项目说明文档

### 2.2 项目状态
- 📄 规格文档完成，已提交到远程仓库
- 📄 数据模型设计完成（11 张表 + 1 张关联表）
- 📄 任务分解完成（143 个子任务）
- ❌ 代码实现尚未开始（工作区为空）

### 2.3 依赖关系图
```
Task 1（项目骨架） ──> Task 2（数据模型） ──> Task 3（登录鉴权）
    │
    └─> Task 16（UI模板）可并行
    │
    └─> Task 5（章节规则） ──> Task 4（TXT导入）
    │
    └─> Task 6（分类管理）
    │
    └─> Task 7（标签管理）
    │
    └─> Task 15（Flask-Admin）
    │
Task 10（小说列表/详情） ──> Task 8（收藏）
                       ──> Task 9（评分）
                       ──> Task 11（阅读）
                       ──> Task 12（编辑）
                       ──> Task 13（导出）
                       ──> Task 14（搜索）
    │
Task 17（主题切换） ──> Task 18（验证测试）
```

---

## 3. 实施计划（18 个 Task）

### Phase 1：基础设施（Task 1-3）

#### Task 1: 初始化项目骨架与依赖
**目标**：创建 Flask 应用框架、配置文件、依赖声明

**文件清单**：
- `requirements.txt` — Flask、Flask-Admin、Flask-SQLAlchemy、chardet
- `config.py` — SECRET_KEY、数据库路径、上传目录、最大文件大小
- `run.py` — 启动入口（开发模式 + 生产模式）
- `app/__init__.py` — Flask 应用工厂（配置数据库、注册蓝图）
- `templates/base.html` — Layui 基础模板（引入静态资源、定义布局结构）
- `static/` — 静态资源目录结构（css、js、layui）

**关键决策**：
- 使用 Flask 应用工厂模式（`create_app()`）
- SQLite 数据库路径：`instance/novel.db`（相对路径）
- 上传临时目录：`uploads/temp/`
- Layui 通过 CDN 引入（避免本地文件过大）

**验证标准**：
- ✅ `python run.py` 能正常启动
- ✅ 访问 `http://localhost:5000` 返回 404（路由尚未注册）

---

#### Task 2: 设计数据模型
**目标**：定义 11 张数据表 + 1 张关联表

**文件**：`app/models.py`

**模型清单**（基于 database_prototype.md）：

| 模型 | 表名 | 核心字段 |
|------|------|----------|
| User | user | id、username、password_hash、created_at |
| Category | category | id、name、description、sort_order |
| Novel | novel | id、title、author、category_id、word_count、chapter_count |
| Chapter | chapter | id、novel_id、title、content、order、word_count |
| ChapterRule | chapter_rule | id、name、pattern、category、enabled、is_default |
| ReadingProgress | reading_progress | id、user_id、novel_id、chapter_id、scroll_position |
| Bookmark | bookmark | id、user_id、novel_id、chapter_id、title、position |
| Tag | tag | id、name、color |
| novel_tags | novel_tags | novel_id、tag_id（复合主键） |
| Favorite | favorite | id、user_id、novel_id |
| Rating | rating | id、user_id、novel_id、score、comment |

**关键实现**：
- 使用 `db.Table` 定义 `novel_tags` 关联表
- `Novel.tags` 使用 `secondary='novel_tags'` 建立多对多关系
- `ChapterRule.category` 字段存储规则分类（中文序号/特殊章节等）
- 所有外键设置级联删除规则（见 database_prototype.md 第 7 节）

**验证标准**：
- ✅ 所有模型继承 `db.Model`
- ✅ 关系定义正确（一对多、多对多）
- ✅ 索引定义完整（见 database_prototype.md 第 4 节）

---

#### Task 3: 实现登录鉴权模块
**目标**：单用户登录、登出、会话管理

**文件**：`app/auth.py` + `templates/login.html`

**路由设计**：
- `/` GET → 重定向到 `/login` 或 `/dashboard`（根据登录状态）
- `/login` GET/POST → 渲染登录页 / 校验凭证并创建 session
- `/logout` GET → 清除 session 并重定向到 `/login`

**核心逻辑**：
- `login_required` 装饰器：检查 `session.get('user_id')`
- 密码哈希：使用 `werkzeug.security.generate_password_hash` / `check_password_hash`
- 首次启动初始化：命令行脚本或 `before_first_request` 创建默认用户（admin/admin123）

**验证标准**：
- ✅ 未登录访问 `/dashboard` 重定向到 `/login`
- ✅ 正确凭证登录成功，创建 session
- ✅ 错误凭证显示提示信息

---

### Phase 2：核心功能（Task 4-7）

#### Task 4: 实现 TXT 导入模块（4 步向导）
**目标**：上传 TXT → 选择规则 → 预览章节 → 确认保存

**文件**：`app/importer.py` + `templates/import/*.html`

**4 步流程**：

**Step 1：上传转码**
- 路由：`/novels/import` GET/POST
- 使用 `chardet.detect()` 检测编码
- 转换为 UTF-8，保存临时文件（`uploads/temp/<session_id>.txt`）
- 标题默认取文件名（不含扩展名）

**Step 2：选择规则**
- 路由：`/novels/import/step2` GET/POST
- 从 `ChapterRule` 表查询 `enabled=True` 的规则
- 提供下拉框 + 自定义正则输入框
- 执行章节拆分，生成章节列表（保存到 session）

**Step 3：预览章节**
- 路由：`/novels/import/step3` GET/POST
- 显示章节标题、字数、内容预览片段
- 支持删除章节并重新生成列表

**Step 4：确认保存**
- 路由：`/novels/import/step4` GET/POST
- 填写元信息（标题、作者、分类）
- 创建 `Novel` + `Chapter` 记录
- 计算总字数、章节数量

**关键实现**：
- 章节拆分逻辑：按正则匹配章节标题行，第一章前内容归入"序章"（order=0）
- Session 存储：`session['import_data']` = `{file_path, chapters, metadata}`
- 临时文件清理：导入成功后删除临时文件

---

#### Task 5: 实现章节拆分规则管理模块
**目标**：8 大类默认规则 + 自定义规则管理

**文件**：`app/rules.py` + `templates/rules/*.html`

**内置规则初始化**（首次启动）：

| 分类 | 名称 | 正则 |
|------|------|------|
| 中文序号 | 中文数字章节 | `^第[零一二三四五六七八九十百千万\d]+章.*$` |
| 特殊章节 | 特殊章节 | `^(序章|楔子|终章|后记|尾声|番外|前言|正文).*$` |
| 分隔符 | 分隔符章节 | `^[、.,_—\-,,::].*$` |
| 英文序号 | 英文章节 | `^(Chapter|Section|Part|Episode|No\.)\s*\d+.*$` |
| 特殊符号 | 特殊符号章节 | `^[【】〔〕〖〗「」『』〈〉［］《》（）===].*$` |
| 纯数字 | 纯数字章节 | `^\d+\.?\s+.*$` |
| 分节阅读 | 分节阅读 | `^(分[页节章段]阅读|第\d+[页节]).*$` |
| 卷部篇 | 卷部篇回 | `^第?[零一二三四五六七八九十百千万\d]+[卷部篇回场话集].*$` |

**路由设计**：
- `/rules` GET → 规则列表页
- `/rules/create` POST → 新增规则
- `/rules/<id>/edit` POST → 编辑规则
- `/rules/<id>/toggle` POST → 启用/禁用切换
- `/rules/<id>/delete` POST → 删除规则
- `/rules/restore-defaults` POST → 恢复缺失的默认规则

---

#### Task 6: 实现小说分类管理模块
**目标**：分类 CRUD

**文件**：`app/categories.py` + `templates/categories/*.html`

**路由设计**：
- `/categories` GET → 分类列表页
- `/categories/create` POST → 创建分类
- `/categories/<id>/edit` POST → 编辑分类
- `/categories/<id>/delete` POST → 删除分类（关联小说 category_id 置空）

---

#### Task 7: 实现小说标签模块
**目标**：标签管理 + 小说-标签多对多关联

**文件**：`app/tags.py` + `templates/tags/*.html`

**路由设计**：
- `/tags` GET → 标签列表页
- `/tags/create` POST → 新增标签（名称 + 颜色）
- `/tags/<id>/edit` POST → 编辑标签
- `/tags/<id>/delete` POST → 删除标签（清除关联）
- `/novels/<id>/tags` POST → 更新小说标签关联

**前端实现**：
- 小说详情页使用多选框勾选/取消勾选标签
- 小说列表页点击标签筛选（`/novels?tag_id=xxx`）

---

### Phase 3：小说核心模块（Task 8-14）

#### Task 8: 实现小说收藏模块
**文件**：`app/favorites.py`
- `/favorites` GET → 收藏列表页
- `/novels/<id>/favorite` POST → 收藏
- `/novels/<id>/unfavorite` POST → 取消收藏

#### Task 9: 实现小说评分模块
**文件**：`app/ratings.py`
- `/novels/<id>/rate` POST → 提交评分（score 1-5 + comment）
- 计算平均评分：`Rating.query.filter_by(novel_id=xxx).with_entities(func.avg(Rating.score))`

#### Task 10: 实现小说列表与详情模块
**文件**：`app/novels.py` + `templates/novels/*.html`
- `/novels` GET → 小说列表（支持分类/标签筛选）
- `/novels/<id>` GET → 小说详情页（标签、章节目录、评分、收藏状态）
- `/novels/<id>/delete` POST → 删除小说（级联删除章节、进度、书签、收藏、评分）

#### Task 11: 实现小说阅读模块
**文件**：`app/reading.py` + `templates/reading.html`
- `/novels/<id>/read/<chapter_id>` GET → 阅读页
- `/api/progress` POST → 保存阅读进度
- `/api/bookmark` POST → 添加书签
- 上一章/下一章切换逻辑

#### Task 12: 实现在线内容修改模块
**文件**：`app/editing.py`
- `/novels/<id>/chapter/<chapter_id>/edit` GET/POST → 编辑章节

#### Task 13: 实现小说导出模块
**文件**：`app/export.py`
- `/novels/<id>/export` GET → 导出 TXT 文件流

#### Task 14: 实现全站全文搜索模块
**文件**：`app/search.py`
- `/search?q=keyword` GET → 搜索结果页
- 使用 LIKE 查询：`Chapter.content.like('%keyword%')`

---

### Phase 4：后台与 UI（Task 15-17）

#### Task 15: 集成 Flask-Admin 后台
**文件**：`app/__init__.py` 修改
- 初始化 Admin：`admin = Admin(app, template_mode='bootstrap4')`
- 注册 ModelView：User、Category、Novel、Chapter、ChapterRule、Tag、Favorite、Rating
- 自定义 `is_accessible` 方法：未登录重定向到 `/login`

#### Task 16: 完善响应式 UI 模板
**目标**：适配电脑（≥992px）与手机（<992px）

**关键页面**：
- `templates/base.html` — Layui 响应式栅格布局
- `templates/login.html` — 登录页（主题切换按钮）
- `templates/novels/list.html` — 小说列表
- `templates/novels/detail.html` — 小说详情
- `templates/reading.html` — 阅读页（字体大小适配）

**响应式策略**：
- 使用 Layui 的 `layui-col-md*`（电脑）和 `layui-col-sm*`（手机）
- 阅读页在手机下使用 18px 字体，按钮放大

#### Task 17: 实现主题切换功能
**目标**：白天/黑夜配色，localStorage 持久化

**文件**：
- `static/css/theme.css` — 定义 `.theme-light` 和 `.theme-dark` 样式
- `static/js/theme.js` — 切换逻辑（读取/保存 localStorage、切换 body class）
- `templates/base.html` — 右上角添加主题切换按钮（月亮/太阳图标）
- `templates/login.html` — 独立添加切换按钮（未登录可用）

**实现要点**：
- 默认白天主题
- 切换时更新 `body` class（`theme-light` / `theme-dark`)
- localStorage 存储：`localStorage.setItem('theme', 'dark')`

---

### Phase 5：验证与测试（Task 18）

#### Task 18: 验证与测试
**目标**：全面验证功能点

**验证清单**（基于 checklist.md）：
- ✅ 登录鉴权：首页跳转登录页、登录/登出流程
- ✅ 分类管理：创建、编辑、删除
- ✅ 标签管理：创建、编辑、删除、小说关联
- ✅ 章节规则：8 大类默认规则、新增/编辑/删除/恢复默认
- ✅ TXT 导入 4 步：上传转码、选择规则、预览删除、确认保存
- ✅ 收藏功能：收藏、取消收藏、收藏列表
- ✅ 评分功能：首次评分、修改评分、平均评分显示
- ✅ 阅读功能：进度记录、书签、章节切换
- ✅ 在线编辑：修改章节标题与正文
- ✅ 导出 TXT：文件下载、章节拼接
- ✅ 全文搜索：搜索结果、跳转链接
- ✅ Flask-Admin：后台需登录可访问
- ✅ 响应式布局：电脑 + 手机视口正常
- ✅ 主题切换：未登录可切换、刷新保持主题

---

## 4. 实施策略

### 4.1 并行开发建议
- **Phase 1（Task 1-3）**：串行执行，建立基础架构
- **Phase 2（Task 4-7）**：Task 4 依赖 Task 5，其余可并行
- **Phase 3（Task 8-14）**：依赖 Task 10，其余可并行
- **Phase 4（Task 15-17）**：Task 15、16、17 可并行
- **Phase 5（Task 18）**：所有 Task 完成后执行

### 4.2 技术实现原则
- **最小改动原则**：只实现 spec.md 要求的功能，不添加额外特性
- **复用原则**：优先使用 Flask-Admin 内置功能（后台管理）
- **样式分离**：主题切换使用 CSS class 切换，不修改 Layui 核心样式
- **安全优先**：密码哈希存储、文件上传限制、编码检测

### 4.3 代码规范
- 使用 Flask 蓝图组织模块（`app/novels.py`、`app/rules.py` 等）
- 所有路由使用 `login_required` 装饰器（除 `/login`、静态资源）
- 模板继承 `base.html`，使用 Jinja2 模板语法
- 数据库查询使用 SQLAlchemy ORM（避免原生 SQL）

---

## 5. 风险与决策

### 5.1 关键决策
1. **章节数量统计**：不存储到数据库，实时查询 `Chapter.query.filter_by(novel_id=xxx).count()`
2. **平均评分**：不存储到 Novel 表，实时计算 `func.avg(Rating.score)`
3. **主题切换**：不使用 Flask session，使用 localStorage（前端持久化）
4. **临时文件清理**：导入成功后删除临时文件，避免磁盘占用

### 5.2 潜在风险
1. **大文件上传**：需设置 `MAX_CONTENT_LENGTH = 50MB`（Layui 限制）
2. **编码检测失败**：chardet 可能误判，提供手动选择编码选项（后续可扩展）
3. **正则性能**：大文件章节拆分可能慢，考虑缓存拆分结果（session 存储）
4. **全文搜索性能**：LIKE 查询可能慢，后续可考虑 SQLite FTS5 或 Elasticsearch（当前阶段不实现）

---

## 6. 文件清单

### 6.1 后端文件（app/*.py）
```
app/
├── __init__.py          # Flask 应用工厂 + Flask-Admin 初始化
├── models.py            # 11 个数据模型
├── auth.py              # 登录鉴权
├── importer.py          # TXT 导入 4 步向导
├── rules.py             # 章节拆分规则管理
├── categories.py        # 分类管理
├── tags.py              # 标签管理
├── favorites.py         # 收藏管理
├── ratings.py           # 评分管理
├── novels.py            # 小说列表与详情
├── reading.py           # 阅读模块
├── editing.py           # 在线编辑
├── export.py            # 导出模块
└── search.py            # 全文搜索
```

### 6.2 前端文件（templates/*.html）
```
templates/
├── base.html            # 基础模板（Layui 响应式布局 + 主题切换按钮）
├── login.html           # 登录页（主题切换按钮）
├── dashboard.html       # 仪表盘
├── novels/
│   ├── list.html        # 小说列表页
│   ├── detail.html      # 小说详情页
│   ├── import_step1.html # 导入 Step 1
│   ├── import_step2.html # 导入 Step 2
│   ├── import_step3.html # 导入 Step 3
│   └── import_step4.html # 导入 Step 4
├── rules/
│   ├── list.html        # 规则列表页
│   ├── edit.html        # 规则编辑页
├── categories/
│   ├── list.html        # 分类列表页
├── tags/
│   ├── list.html        # 标签列表页
├── favorites/
│   ├── list.html        # 收藏列表页
├── reading/
│   ├── read.html        # 阅读页
│   ├── edit.html        # 章节编辑页
├── search/
│   ├── result.html      # 搜索结果页
```

### 6.3 静态文件（static/*）
```
static/
├── css/
│   ├── theme.css        # 主题样式（白天/黑夜）
│   └── custom.css       # 自定义样式覆盖
├── js/
│   ├── theme.js         # 主题切换逻辑
│   └── common.js        # 公共 JS 函数
└── layui/               # Layui 框架（本地或 CDN）
```

---

## 7. 下一步行动

### 7.1 立即开始
1. 执行 Task 1：创建项目骨架（`requirements.txt`、`config.py`、`run.py`、`app/__init__.py`）
2. 执行 Task 2：定义数据模型（`app/models.py`）
3. 执行 Task 3：实现登录鉴权（`app/auth.py`）

### 7.2 并行推进
- Task 16（UI模板）可与 Task 1-3 并行开发
- Task 17（主题切换）可与 Task 15（Flask-Admin）并行

### 7.3 验证节点
- Phase 1 完成后验证：登录鉴权正常
- Phase 2 完成后验证：TXT 导入流程完整
- Phase 3 完成后验证：小说管理功能完整
- Phase 5 完成后验证：全部 checklist 项通过

---

## 8. 参考文档

- [spec.md](file:///workspace/.trae/specs/build-private-novel-system/spec.md) — 完整需求规格
- [database_prototype.md](file:///workspace/database_prototype.md) — 数据库原型设计
- [tasks.md](file:///workspace/.trae/specs/build-private-novel-system/tasks.md) — 任务清单
- [checklist.md](file:///workspace/.trae/specs/build-private-novel-system/checklist.md) — 验证清单
- [README.md](file:///workspace/README.md) — 项目说明

---

*计划生成时间：2026-07-13*