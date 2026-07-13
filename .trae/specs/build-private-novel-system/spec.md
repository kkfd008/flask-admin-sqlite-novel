# 私人小说浏览系统 Spec

## Why
用户需要一个自托管的私人小说浏览系统，能够在电脑和手机上随时阅读自己导入的 TXT 小说。系统需提供完整的小说管理生命周期：分类、导入、阅读、修改、导出、搜索，且仅限本人登录访问，保护隐私。

## What Changes
- 新建 Flask + Flask-Admin + SQLite3 + Layui 单用户小说浏览系统
- **登录鉴权模块**：首页即登录页，未登录用户无法访问任何功能；登录后可访问全部功能
- **小说分类设置模块**：支持分类的增删改查，分类可关联多本小说
- **TXT 小说导入模块**：上传 TXT 文件，按章节标题正则匹配自动分章保存
- **小说阅读模块**：分章节阅读，自动/手动记录阅读进度，支持书签增删与跳转
- **小说在线内容修改模块**：支持在线编辑章节标题与正文内容
- **小说导出模块**：支持将整本小说导出为 TXT 文件下载
- **全站小说内容搜索**：跨小说/章节的全文搜索，结果定位到章节
- **响应式布局**：基于 Layui 实现电脑与手机自适应
- **Flask-Admin 管理后台**：提供数据模型的后台管理能力

## Impact
- Affected specs: 全新项目，无既有 spec 受影响
- Affected code:
  - `app.py` / `app/__init__.py` Flask 应用入口与工厂
  - `models.py` / `app/models.py` SQLAlchemy/SQLite3 数据模型
  - `auth.py` / `app/auth.py` 登录鉴权
  - `routes.py` / `app/routes.py` 业务路由
  - `importer.py` / `app/importer.py` TXT 解析导入
  - `templates/` Layui 模板
  - `static/` 静态资源
  - `requirements.txt` 依赖声明

## ADDED Requirements

### Requirement: 登录鉴权
系统 SHALL 提供单用户登录功能，根路径 `/` 重定向到登录页；除 `/login` 与静态资源外的所有路由 SHALL 要求登录后访问。

#### Scenario: 未登录访问受保护页面
- **WHEN** 用户未登录访问 `/dashboard`
- **THEN** 系统重定向到 `/login` 并提示需要登录

#### Scenario: 登录成功
- **WHEN** 用户在 `/login` 输入正确用户名和密码
- **THEN** 创建会话，重定向到 `/dashboard`，并显示登录成功

#### Scenario: 登录失败
- **WHEN** 用户输入错误凭证
- **THEN** 返回登录页并提示用户名或密码错误

### Requirement: 小说分类管理
系统 SHALL 提供小说分类的创建、查看、编辑、删除功能；分类 SHALL 支持名称和可选描述。

#### Scenario: 创建分类
- **WHEN** 用户在分类管理页提交分类名称"玄幻"
- **THEN** 系统保存分类并显示在分类列表中

#### Scenario: 删除分类
- **WHEN** 用户删除一个分类
- **THEN** 该分类被删除；关联小说的分类字段置为空，不删除小说

### Requirement: TXT 小说导入
系统 SHALL 支持上传 TXT 文件（支持 GBK/GB2312/UTF-8 自动检测编码），按章节标题正则匹配拆分章节并保存；默认章节正则匹配 `第.{1,8}章`、`第.{1,8}回`、`Chapter\s+\d+` 等常见模式，并允许用户自定义正则。

#### Scenario: 默认规则导入
- **WHEN** 用户上传一个含 `第一章 xxx` 章节标题的 UTF-8 TXT 文件
- **THEN** 系统按章节标题拆分，每章保存为独立 Chapter 记录，第一章之前的引言归入"序章"

#### Scenario: 自定义规则导入
- **WHEN** 用户上传 TXT 并填入自定义正则 `^\d+\.`
- **THEN** 系统按自定义正则拆分章节

#### Scenario: 编码自动识别
- **WHEN** 用户上传 GBK 编码的 TXT 文件
- **THEN** 系统自动检测并以正确编码读取内容，无乱码

### Requirement: 小说阅读
系统 SHALL 提供分章节阅读页面，显示章节正文；SHALL 自动记录阅读进度（最后阅读的章节 + 滚动位置）；SHALL 支持上一章/下一章切换；SHALL 支持书签的添加、查看、跳转、删除。

#### Scenario: 记录阅读进度
- **WHEN** 用户阅读某章节并滚动或切换章节
- **THEN** 系统更新该小说的阅读进度，下次打开时定位到上次位置

#### Scenario: 添加书签
- **WHEN** 用户在阅读页点击"添加书签"
- **THEN** 系统保存书签（章节 + 位置 + 时间），可在书签列表查看与跳转

#### Scenario: 章节切换
- **WHEN** 用户点击"下一章"
- **THEN** 系统跳转到当前章节的下一章并自动记录进度

### Requirement: 在线内容修改
系统 SHALL 提供章节在线编辑页面，可修改章节标题与正文；保存后立即生效。

#### Scenario: 修改章节标题
- **WHEN** 用户在编辑页将章节标题改为新名称并保存
- **THEN** 系统更新章节标题，阅读页显示新标题

#### Scenario: 修改章节正文
- **WHEN** 用户修改正文内容并保存
- **THEN** 系统更新章节正文，阅读页显示新内容

### Requirement: 小说导出
系统 SHALL 支持将整本小说导出为单个 TXT 文件下载，章节之间用空行分隔。

#### Scenario: 导出小说
- **WHEN** 用户在小说详情页点击"导出 TXT"
- **THEN** 浏览器下载 `<小说标题>.txt`，内容为各章节按顺序拼接

### Requirement: 全站全文搜索
系统 SHALL 提供跨所有小说章节的全文搜索功能，输入关键词返回匹配的章节列表，点击结果可跳转到对应章节。

#### Scenario: 搜索关键词
- **WHEN** 用户在搜索框输入"剑"
- **THEN** 系统返回所有包含"剑"的章节列表，显示小说标题、章节标题、匹配片段摘要

### Requirement: 响应式布局
系统 SHALL 基于 Layui 实现响应式 UI，在电脑（≥992px）与手机（<992px）下均可正常浏览与操作。

#### Scenario: 手机访问阅读页
- **WHEN** 用户在手机浏览器打开阅读页
- **THEN** 页面自适应屏幕宽度，字体与按钮可正常操作

### Requirement: Flask-Admin 后台
系统 SHALL 通过 Flask-Admin 提供数据模型（Category、Novel、Chapter、ReadingProgress、Bookmark、User）的后台增删改查界面，且后台同样需要登录鉴权。

#### Scenario: 访问后台
- **WHEN** 已登录用户访问 `/admin`
- **THEN** 显示 Flask-Admin 管理界面，可对模型进行管理

## MODIFIED Requirements
（全新项目，无既有需求被修改）

## REMOVED Requirements
（全新项目，无既有需求被移除）
