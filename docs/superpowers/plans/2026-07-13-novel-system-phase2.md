# 私人小说浏览系统 Phase 2 实现计划（已完成）

> **状态：** 全部 18 个 Task 已完成，所有核心功能已实现并测试通过。

**Goal:** 实现小说收藏、导出、全文搜索、阅读、在线编辑、TXT导入、Flask-Admin后台等剩余功能模块

**Architecture:** 基于现有 Flask + SQLAlchemy + Layui 架构，为每个功能模块创建独立的 Blueprint 路由文件和测试文件，遵循 TDD 流程（先写测试、确认失败、编写最小代码、确认通过、重构）

**Tech Stack:** Flask, Flask-SQLAlchemy, SQLite3, chardet, Werkzeug, Layui, pytest

---

## 当前代码状态

### 已完成模块
- `app/__init__.py` - Flask 应用工厂 + Flask-Admin 初始化
- `app/models.py` - 11 个数据模型（User, Category, Novel, Chapter, ChapterRule, NovelChapterRule, Tag, Favorite, Rating, ReadingProgress, Bookmark）
- `app/auth.py` - 登录鉴权（auth_bp: /login, /logout, login_required）
- `app/categories.py` - 分类管理（categories_bp: /categories CRUD）
- `app/tags.py` - 标签管理（tags_bp: /tags CRUD）
- `app/rules.py` - 规则管理（rules_bp: /rules CRUD, toggle）
- `app/ratings.py` - 评分管理（ratings_bp: /novels/<id>/rate, /rate/delete）
- `app/novels.py` - 小说管理（novels_bp: /novels list, detail, delete, tags, rules, chapter_directory）
- `app/favorites.py` - 收藏管理（favorites_bp: /favorites, /novels/<id>/favorite, /unfavorite）
- `app/reading.py` - 阅读模块（reading_bp: /novels/<id>/read/<chapter_id>, /api/progress, /api/bookmark）
- `app/editor.py` - 在线编辑（editor_bp: /novels/<id>/chapter/<chapter_id>/edit）
- `app/importer.py` - TXT 导入 4 步向导（importer_bp: /novels/import step1-4）
- `app/search.py` - 全文搜索（search_bp: /search）
- `app/export.py` - 小说导出（export_bp: /novels/<id>/export）
- `app/utils.py` - 工具函数（init_default_rules, calculate_average_rating）

### 已完成模板（16 个，移动优先响应式设计）
- `templates/base.html` - 基础模板（墨斋设计系统、底部 Tab 导航、明暗主题、CSS 变量）
- `templates/auth/login.html` - 登录页
- `templates/dashboard.html` - 仪表盘
- `templates/novels/list.html` - 小说列表
- `templates/novels/detail.html` - 小说详情（评分表单 + 标签弹窗）
- `templates/novels/chapters.html` - 章节目录分页
- `templates/novels/rules.html` - 书籍规则管理
- `templates/import/step1.html` - 导入 Step 1（上传）
- `templates/import/step2.html` - 导入 Step 2（选择规则）
- `templates/import/step3.html` - 导入 Step 3（预览章节）
- `templates/import/step4.html` - 导入 Step 4（确认保存）
- `templates/reading/reader.html` - 阅读页（底部导航、字体控制、点击翻页）
- `templates/editor/edit.html` - 章节编辑
- `templates/search/results.html` - 搜索结果
- `templates/favorites/list.html` - 收藏列表
- `templates/rules/list.html` - 规则列表
- `templates/categories/list.html` - 分类列表
- `templates/tags/list.html` - 标签列表

### 测试覆盖（14 个测试文件）
```
tests/
├── conftest.py                          # 测试 fixtures
├── unit/
│   ├── test_auth.py                     # 登录鉴权
│   ├── test_models.py                   # 数据模型
│   ├── test_importer.py                 # 导入流程
│   ├── test_importer_multiple_pattern.py # 多规则组合 + 捕获组 bug
│   ├── test_large_import.py             # 大规模导入（700+ 章节）
│   ├── test_real_import.py              # 真实文件导入（4.27MB）
│   ├── test_rules.py                    # 章节规则
│   ├── test_categories.py               # 分类管理
│   ├── test_tags.py                     # 标签管理
│   ├── test_ratings.py                  # 评分管理
│   ├── test_favorites.py                # 收藏管理
│   ├── test_chapters.py                 # 章节目录分页
│   ├── test_reader_nav.py               # 阅读器底部导航
│   └── test_detail_page.py              # 详情页评分 + 标签弹窗
```

---

## 近期完成的增强功能

### 移动端响应式 UI 重设计
- 16 个模板全部重写为移动优先设计（小米14 393px / iPhone 17 430px 为标准）
- 底部 Tab 导航栏（≤768px）
- `env(safe-area-inset-*)` 安全区域适配
- CSS 变量驱动的明暗主题（墨斋设计系统）
- 触摸友好设计：`touch-action: manipulation`、最小 44px 触摸目标

### 章节目录分页
- 新增路由 `GET /novels/<id>/chapter`，默认每页 20 章
- 支持 10/20/50/100 四种每页章节数选项
- 书籍详情页仅显示"查看全部章节"链接

### 评分功能增强
- 每用户每书只能评价一次，修改评价即更新
- 已评过分后显示上次评分内容（星星预选 + 评论预填）
- 按钮文字从"提交评分"变为"更新评分"
- 修复嵌套表单 bug（清除评分与评分表单分离）
- 修复星星选中无视觉反馈问题（`:checked ~ label` CSS）

### 标签管理增强
- 从内联表单改为弹出式模态框
- "修改标签"按钮 → 弹出标签列表 → 确定/取消
- 支持零个或多个标签勾选
- CSS `:has(input:checked)` 驱动选中视觉反馈

### 阅读器底部导航修复
- 固定底部导航栏：上一章 / 返回目录 / 下一章
- "返回目录"链接指向章节目录分页页（非书籍详情页）
- 底部导航移出 `.main-content`，避免 `animation` 创建 stacking context 导致部分机型不显示
- `z-index: 110` + `transform: translateZ(0)` GPU 加速

### 导入器 Bug 修复
- 修复 `re.split` 捕获组索引错乱 bug（使用 `re.finditer` 手动拆分）
- 支持多规则组合模式（`(?:pattern1)|(?:pattern2)` 非捕获组包装）
- 大规模导入测试（700+ 章节 / 2.1M 字符 / 真实文件 4.27MB / 627 章节）

---

## 任务依赖关系

```
Task 1 (Favorites) -- 无依赖，可并行  ✅
Task 2 (Export)    -- 无依赖，可并行  ✅
Task 3 (Search)    -- 无依赖，可并行  ✅
Task 4 (Reading)   -- 无依赖，可并行  ✅
Task 5 (Editor)    -- 无依赖，可并行  ✅
Task 6 (Import)    -- 依赖 Task 5 (rules 已存在)  ✅
Task 7 (Admin)     -- 依赖 pip install flask-admin  ✅
Task 8 (Report)    -- 依赖 Task 1-7 全部完成  ✅
```

---

*计划完成时间：2026-07-13*