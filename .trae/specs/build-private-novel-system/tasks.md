# Tasks

- [ ] Task 1: 初始化项目骨架与依赖
  - [ ] SubTask 1.1: 创建 `requirements.txt`（Flask、Flask-Admin、Flask-SQLAlchemy、chardet 等）
  - [ ] SubTask 1.2: 创建 `app/__init__.py` Flask 应用工厂，配置 SQLite3 数据库与密钥
  - [ ] SubTask 1.3: 创建 `config.py` 配置文件（SECRET_KEY、数据库路径、上传目录）
  - [ ] SubTask 1.4: 创建 `run.py` 启动入口
  - [ ] SubTask 1.5: 准备 Layui 静态资源目录与基础模板 `templates/base.html`

- [ ] Task 2: 设计数据模型 (`app/models.py`)
  - [ ] SubTask 2.1: `User` 模型（id、username、password_hash）
  - [ ] SubTask 2.2: `Category` 模型（id、name、description）
  - [ ] SubTask 2.3: `Novel` 模型（id、title、author、description、category_id、created_at、updated_at）
  - [ ] SubTask 2.4: `Chapter` 模型（id、novel_id、title、content、order、word_count）
  - [ ] SubTask 2.5: `ReadingProgress` 模型（id、user_id、novel_id、chapter_id、scroll_position、updated_at）
  - [ ] SubTask 2.6: `Bookmark` 模型（id、user_id、chapter_id、title、position、created_at）
  - [ ] SubTask 2.7: `ChapterRule` 模型（id、name、pattern、description、enabled、is_default）
  - [ ] SubTask 2.8: `Tag` 模型（id、name、color） + `novel_tags` 多对多关联表
  - [ ] SubTask 2.9: `Favorite` 模型（id、user_id、novel_id、created_at）
  - [ ] SubTask 2.10: `Rating` 模型（id、user_id、novel_id、score、comment、created_at、updated_at）

- [ ] Task 3: 实现登录鉴权模块 (`app/auth.py`)
  - [ ] SubTask 3.1: `/login` GET 渲染登录页 / POST 校验用户名密码并创建 session
  - [ ] SubTask 3.2: `/logout` 清除 session 并重定向到 `/login`
  - [ ] SubTask 3.3: `login_required` 装饰器，未登录重定向到 `/login`
  - [ ] SubTask 3.4: 根路径 `/` 重定向到 `/login` 或 `/dashboard`（根据登录状态）
  - [ ] SubTask 3.5: 命令行初始化默认用户脚本/函数（首次启动自动创建账号）

- [ ] Task 4: 实现 TXT 导入模块 (`app/importer.py`)
  - [ ] SubTask 4.1: 使用 chardet 自动检测文件编码并读取文本
  - [ ] SubTask 4.2: 从 `ChapterRule` 表加载规则正则，提供默认 fallback
  - [ ] SubTask 4.3: 支持"自定义正则"输入框覆盖所选规则
  - [ ] SubTask 4.4: 按章节拆分并写入 `Novel` 与 `Chapter` 记录，第一章前的引言归入"序章"
  - [ ] SubTask 4.5: `/novels/import` GET 渲染上传页（含规则下拉框 + 自定义正则输入框）/ POST 接收文件、rule_id 或 custom_pattern 并调用导入逻辑

- [ ] Task 5: 实现 TXT 目录规则管理模块 (`app/rules.py`)
  - [ ] SubTask 5.1: 首次启动初始化内置默认规则（`第.{1,8}章`、`第.{1,8}回`、`Chapter\s+\d+`，is_default=True，enabled=True）
  - [ ] SubTask 5.2: `/rules` GET 渲染规则列表页（名称、正则、描述、启用状态、操作按钮）
  - [ ] SubTask 5.3: `/rules/create` POST 新增规则
  - [ ] SubTask 5.4: `/rules/<id>/edit` POST 编辑规则
  - [ ] SubTask 5.5: `/rules/<id>/toggle` POST 启用/禁用切换
  - [ ] SubTask 5.6: `/rules/<id>/delete` POST 删除规则
  - [ ] SubTask 5.7: `/rules/restore-defaults` POST 恢复缺失的内置默认规则

- [ ] Task 6: 实现小说分类管理模块
  - [ ] SubTask 6.1: `/categories` GET 渲染分类列表页
  - [ ] SubTask 6.2: `/categories/create` POST 创建分类
  - [ ] SubTask 6.3: `/categories/<id>/edit` POST 编辑分类
  - [ ] SubTask 6.4: `/categories/<id>/delete` POST 删除分类（关联小说 category_id 置空）

- [ ] Task 7: 实现小说标签模块
  - [ ] SubTask 7.1: `/tags` GET 渲染标签管理列表页（名称、颜色、关联小说数、操作按钮）
  - [ ] SubTask 7.2: `/tags/create` POST 新增标签（名称 + 颜色）
  - [ ] SubTask 7.3: `/tags/<id>/edit` POST 编辑标签
  - [ ] SubTask 7.4: `/tags/<id>/delete` POST 删除标签（清除关联，不删除小说）
  - [ ] SubTask 7.5: 小说详情页支持勾选/取消勾选标签，`/novels/<id>/tags` POST 更新关联
  - [ ] SubTask 7.6: 小说列表页支持按标签筛选（`/novels?tag_id=xxx`）

- [ ] Task 8: 实现小说收藏模块
  - [ ] SubTask 8.1: `/favorites` GET 渲染收藏列表页
  - [ ] SubTask 8.2: `/novels/<id>/favorite` POST 收藏小说
  - [ ] SubTask 8.3: `/novels/<id>/unfavorite` POST 取消收藏
  - [ ] SubTask 8.4: 小说详情页显示收藏状态，支持一键切换

- [ ] Task 9: 实现小说评分模块
  - [ ] SubTask 9.1: `/novels/<id>/rate` POST 提交/更新评分（score 1-5，可选 comment）
  - [ ] SubTask 9.2: 小说详情页显示平均评分、评分人数、当前用户评分
  - [ ] SubTask 9.3: 小说列表页显示每本书的平均星级

- [ ] Task 10: 实现小说列表与详情模块
  - [ ] SubTask 10.1: `/novels` GET 渲染小说列表页（支持按分类/标签筛选，显示评分与收藏状态）
  - [ ] SubTask 10.2: `/novels/<id>` GET 渲染小说详情页（标签、章节目录、阅读进度、评分、收藏按钮、操作按钮）
  - [ ] SubTask 10.3: `/novels/<id>/delete` POST 删除小说及其章节、进度、书签、收藏、评分、标签关联

- [ ] Task 11: 实现小说阅读模块
  - [ ] SubTask 11.1: `/novels/<id>/read/<chapter_id>` GET 渲染阅读页（章节正文 + 上下章 + 书签按钮）
  - [ ] SubTask 11.2: 上/下一章切换，更新阅读进度
  - [ ] SubTask 11.3: `/api/progress` POST 保存阅读进度（chapter_id + scroll_position）
  - [ ] SubTask 11.4: `/api/bookmark` POST 添加书签，`/api/bookmark/<id>/delete` 删除书签
  - [ ] SubTask 11.5: 书签列表与跳转

- [ ] Task 12: 实现在线内容修改模块
  - [ ] SubTask 12.1: `/novels/<id>/chapter/<chapter_id>/edit` GET 渲染编辑页
  - [ ] SubTask 12.2: `/novels/<id>/chapter/<chapter_id>/edit` POST 保存标题与正文修改

- [ ] Task 13: 实现小说导出模块
  - [ ] SubTask 13.1: `/novels/<id>/export` GET 返回 `<小说标题>.txt` 文件流（章节按序拼接，空行分隔）

- [ ] Task 14: 实现全站全文搜索模块
  - [ ] SubTask 14.1: `/search` GET 接收 `q` 参数，对 `Chapter.content` 做 LIKE 查询
  - [ ] SubTask 14.2: 渲染搜索结果页（小说标题、章节标题、匹配摘要、跳转链接）

- [ ] Task 15: 集成 Flask-Admin 后台
  - [ ] SubTask 15.1: 在 `app/__init__.py` 中初始化 Admin（template_mode='bootstrap4'）
  - [ ] SubTask 15.2: 为 Category、Novel、Chapter、ReadingProgress、Bookmark、User、ChapterRule、Tag、Favorite、Rating 注册 ModelView
  - [ ] SubTask 15.3: 为 Admin 视图增加 `is_accessible` 鉴权，未登录重定向到 `/login`

- [ ] Task 16: 完善响应式 UI 模板
  - [ ] SubTask 16.1: `templates/base.html` 引入 Layui，使用 Layui 响应式栅格布局
  - [ ] SubTask 16.2: 登录页、列表页、详情页、阅读页、编辑页、搜索页、规则管理页、标签管理页、收藏列表页均适配手机（<992px）
  - [ ] SubTask 16.3: 阅读页字体大小、按钮在手机下可正常操作

- [ ] Task 17: 验证与测试
  - [ ] SubTask 17.1: 启动应用并验证首页跳转到登录页
  - [ ] SubTask 17.2: 验证登录、登出流程
  - [ ] SubTask 17.3: 验证规则列表页、新增/编辑/启用禁用/删除/恢复默认规则
  - [ ] SubTask 17.4: 验证导入一本含章节的 TXT 小说（使用规则与自定义正则两种方式）并查看章节列表
  - [ ] SubTask 17.5: 验证标签管理（新增、编辑、删除）与小说标签关联（添加、移除、按标签筛选）
  - [ ] SubTask 17.6: 验证收藏功能（收藏、取消收藏、收藏列表）
  - [ ] SubTask 17.7: 验证评分功能（首次评分、修改评分、平均评分显示）
  - [ ] SubTask 17.8: 验证阅读、进度记录、书签功能
  - [ ] SubTask 17.9: 验证在线编辑章节并查看生效
  - [ ] SubTask 17.10: 验证导出 TXT 文件
  - [ ] SubTask 17.11: 验证全文搜索结果
  - [ ] SubTask 17.12: 验证 Flask-Admin 后台需登录可访问
  - [ ] SubTask 17.13: 验证手机视口下页面布局正常

# Task Dependencies
- Task 2 依赖 Task 1
- Task 3 依赖 Task 1、Task 2
- Task 4 依赖 Task 1、Task 2、Task 5（导入需规则可选）
- Task 5 依赖 Task 1、Task 2、Task 3
- Task 6 依赖 Task 1、Task 2、Task 3
- Task 7 依赖 Task 1、Task 2、Task 3
- Task 8 依赖 Task 2、Task 3、Task 10
- Task 9 依赖 Task 2、Task 3、Task 10
- Task 10 依赖 Task 2、Task 3、Task 6、Task 7
- Task 11 依赖 Task 2、Task 3、Task 10
- Task 12 依赖 Task 2、Task 3、Task 10
- Task 13 依赖 Task 2、Task 3、Task 10
- Task 14 依赖 Task 2、Task 3、Task 10
- Task 15 依赖 Task 1、Task 2、Task 3
- Task 16 依赖 Task 1（可与 Task 3-14 并行进行模板开发）
- Task 17 依赖 Task 1-16 全部完成
