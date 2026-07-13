# 私人小说浏览系统 — 数据库原型说明

> 数据库类型：SQLite3  
> ORM：Flask-SQLAlchemy  
> 编码：UTF-8

---

## 目录

1. [总览](#1-总览)
2. [ER 关系图](#2-er-关系图)
3. [表结构说明](#3-表结构说明)
   - 3.1 user（用户表）
   - 3.2 category（小说分类表）
   - 3.3 novel（小说表）
   - 3.4 chapter（章节表）
   - 3.5 chapter_rule（章节拆分规则表）
   - 3.6 reading_progress（阅读进度表）
   - 3.7 bookmark（书签表）
   - 3.8 tag（标签表）
   - 3.9 novel_tags（小说-标签关联表）
   - 3.10 favorite（收藏表）
   - 3.11 rating（评分表）
4. [索引设计](#4-索引设计)
5. [初始化数据](#5-初始化数据)
6. [典型查询场景](#6-典型查询场景)

---

## 1. 总览

系统共包含 **11 张数据表** + **1 张多对多关联表**，围绕"小说阅读"核心业务展开：

| 表名 | 中文名 | 说明 |
|------|--------|------|
| `user` | 用户表 | 单用户账号，存储登录凭证 |
| `category` | 分类表 | 小说分类（如：玄幻、科幻） |
| `novel` | 小说表 | 小说基本信息（标题、作者、分类等） |
| `chapter` | 章节表 | 每章标题与正文内容 |
| `chapter_rule` | 章节拆分规则表 | TXT 导入时的章节标题正则规则（全局规则） |
| `novel_chapter_rule` | 小说章节规则表 | 每本书独立的章节拆分规则（长期保存） |
| `reading_progress` | 阅读进度表 | 记录每本书读到第几章、滚动位置 |
| `bookmark` | 书签表 | 章节内书签，含位置信息 |
| `tag` | 标签表 | 可自由定义的标签 |
| `novel_tags` | 小说-标签关联表 | 多对多关联，一本小说可多个标签 |
| `favorite` | 收藏表 | 用户收藏的小说 |
| `rating` | 评分表 | 用户对小说的 1-5 星评分与评价 |

---

## 2. ER 关系图

```
user ─────< reading_progress
  │              │
  │              └──> novel <── category
  │                       ∧
  │                       │
  ├──< bookmark >─────────┘
  │                       │
  ├──< favorite >─────────┘
  │                       │
  └──< rating >───────────┘
                          │
                          ∨
                       chapter
                          │
                          ∨
                    chapter_rule  (用于导入时拆分章节)
                          │
                          ∨
                       tag ─── novel_tags ─── novel  (多对多)
```

**关系说明：**
- 1 个用户 → 多条阅读进度（每本书一条）
- 1 个用户 → 多个书签
- 1 个用户 → 多个收藏
- 1 个用户 → 多条评分
- 1 个分类 → 多本小说
- 1 本小说 → 多个章节
- 1 本小说 ↔ 多个标签（通过 novel_tags 多对多）
- 1 条章节规则 → 可用于多本小说的导入（使用时选定）

---

## 3. 表结构说明

### 3.1 user（用户表）

单用户系统，存储登录账号与密码哈希。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户 ID |
| `username` | VARCHAR(80) | UNIQUE NOT NULL | 用户名 |
| `password_hash` | VARCHAR(255) | NOT NULL | 密码哈希（werkzeug security 生成） |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 3.2 category（小说分类表）

小说一级分类，如"玄幻""科幻""都市"等。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 分类 ID |
| `name` | VARCHAR(100) | UNIQUE NOT NULL | 分类名称 |
| `description` | TEXT | NULL | 分类描述 |
| `sort_order` | INTEGER | DEFAULT 0 | 排序权重（数值越小越靠前） |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 3.3 novel（小说表）

小说主表，存储每本小说的基本元信息。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 小说 ID |
| `title` | VARCHAR(255) | NOT NULL | 小说标题（导入时默认取文件名不含扩展名） |
| `author` | VARCHAR(255) | NULL | 作者（可为空） |
| `description` | TEXT | NULL | 简介/描述 |
| `category_id` | INTEGER | FOREIGN KEY → category.id, NULL | 所属分类 ID，删除分类时置 NULL |
| `cover` | VARCHAR(500) | NULL | 封面图片路径（预留） |
| `word_count` | INTEGER | DEFAULT 0 | 总字数（所有章节字数之和） |
| `chapter_count` | INTEGER | DEFAULT 0 | 章节总数 |
| `is_favorite` | - | - | 不存字段，通过 favorite 表动态查询 |
| `avg_rating` | - | - | 不存字段，通过 rating 表动态计算 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 导入时间 |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 最后更新时间 |

**索引：** `idx_novel_category_id`、`idx_novel_title`

---

### 3.4 chapter（章节表）

存储每本小说的所有章节内容。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 章节 ID |
| `novel_id` | INTEGER | FOREIGN KEY → novel.id, NOT NULL, ON DELETE CASCADE | 所属小说 ID，删除小说时级联删除 |
| `title` | VARCHAR(255) | NOT NULL | 章节标题 |
| `content` | TEXT | NOT NULL | 章节正文内容 |
| `order` | INTEGER | NOT NULL | 章节序号（从 1 开始；序章为 0） |
| `word_count` | INTEGER | DEFAULT 0 | 本章字数 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 最后修改时间 |

**索引：** `idx_chapter_novel_id`、`idx_chapter_novel_order`（复合索引，novel_id + order）

---

### 3.5 chapter_rule（章节拆分规则表）

TXT 导入时用于匹配章节标题的正则规则库。可启用/禁用，可自定义新增。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 规则 ID |
| `name` | VARCHAR(100) | UNIQUE NOT NULL | 规则名称（如"中文数字章节"） |
| `pattern` | VARCHAR(500) | NOT NULL | 正则表达式（如 `^第\d+章.*$`） |
| `category` | VARCHAR(50) | NULL | 规则分类（中文序号/特殊章节/分隔符/英文序号/特殊符号/纯数字/分节阅读/卷部篇） |
| `description` | VARCHAR(500) | NULL | 规则说明 |
| `enabled` | BOOLEAN | DEFAULT TRUE | 是否启用（启用的规则才出现在导入下拉框） |
| `is_default` | BOOLEAN | DEFAULT FALSE | 是否为内置默认规则（用于"恢复默认"功能） |
| `sort_order` | INTEGER | DEFAULT 0 | 排序权重 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**内置 8 大类默认规则（is_default = TRUE）：**

| 分类 | 名称 | 正则 | 示例 |
|------|------|------|------|
| 中文序号 | 中文数字章节 | `^第[零一二三四五六七八九十百千万\d]+章.*$` | 第一章、第1章 |
| 特殊章节 | 特殊章节 | `^(序章\|楔子\|终章\|后记\|尾声\|番外\|前言\|正文).*$` | 序章、番外一 |
| 分隔符章节 | 分隔符章节 | `^[、.,_—\-,,::].*$` | 、第一章 |
| 英文序号 | 英文章节 | `^(Chapter\|Section\|Part\|Episode\|No\.)\s*\d+.*$` | Chapter 1 |
| 特殊符号 | 特殊符号章节 | `^[【】〔〕〖〗「」『』〈〉［］《》（）===].*$` | 【第一章】 |
| 纯数字 | 纯数字章节 | `^\d+\.?\s+.*$` | 1. xxx |
| 分节阅读 | 分节阅读 | `^(分[页节章段]阅读\|第\d+[页节]).*$` | 分节阅读一 |
| 卷/部/篇 | 卷部篇回 | `^第?[零一二三四五六七八九十百千万\d]+[卷部篇回场话集].*$` | 第一卷、第1回 |

---

### 3.5.1 novel_chapter_rule（小说章节规则表）

每本小说独立的章节拆分规则，长期保存。在导入过程中可添加自定义规则（只对本书有效）。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 规则 ID |
| `novel_id` | INTEGER | FOREIGN KEY → novel.id, UNIQUE NOT NULL, ON DELETE CASCADE | 关联的小说 ID（一对一） |
| `pattern` | VARCHAR(500) | NOT NULL | 正则表达式（如 `^第\d+章.*$`） |
| `description` | VARCHAR(500) | NULL | 规则说明 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 最后修改时间 |

**唯一约束：** `novel_id` 唯一，即每本书只能有一条独立规则

**索引：** `idx_novel_chapter_rule_novel_id`

**与 chapter_rule 的区别：**
- `chapter_rule`：全局规则，可复用于多本书
- `novel_chapter_rule`：每本书独立规则，只对本书有效，长期保存

---

### 3.6 reading_progress（阅读进度表）

记录每本书的阅读位置，下次打开时自动定位。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 进度 ID |
| `user_id` | INTEGER | FOREIGN KEY → user.id, NOT NULL | 用户 ID |
| `novel_id` | INTEGER | FOREIGN KEY → novel.id, NOT NULL, ON DELETE CASCADE | 小说 ID |
| `chapter_id` | INTEGER | FOREIGN KEY → chapter.id, NULL, ON DELETE SET NULL | 当前读到的章节 ID |
| `scroll_position` | INTEGER | DEFAULT 0 | 滚动位置（像素或百分比，前端记录） |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 最后阅读时间 |

**唯一约束：** `(user_id, novel_id)` 唯一，即每用户每本书只有一条进度记录

**索引：** `idx_progress_user_novel`

---

### 3.7 bookmark（书签表）

用户在章节中添加的书签，可跳转到指定位置。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 书签 ID |
| `user_id` | INTEGER | FOREIGN KEY → user.id, NOT NULL | 用户 ID |
| `novel_id` | INTEGER | FOREIGN KEY → novel.id, NOT NULL, ON DELETE CASCADE | 小说 ID |
| `chapter_id` | INTEGER | FOREIGN KEY → chapter.id, NOT NULL, ON DELETE CASCADE | 章节 ID |
| `title` | VARCHAR(255) | NOT NULL | 书签名称（默认为章节标题，可自定义） |
| `position` | INTEGER | DEFAULT 0 | 书签位置（滚动像素） |
| `sort_order` | INTEGER | DEFAULT 0 | 排序 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_bookmark_user_novel`

---

### 3.8 tag（标签表）

小说标签，多对多关联。每本小说可打多个标签。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 标签 ID |
| `name` | VARCHAR(50) | UNIQUE NOT NULL | 标签名称（如"爽文""治愈""烧脑"） |
| `color` | VARCHAR(20) | DEFAULT '#1E9FFF' | 标签颜色（十六进制，用于前端展示） |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 3.9 novel_tags（小说-标签关联表）

多对多关联表，连接 novel 与 tag。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `novel_id` | INTEGER | FOREIGN KEY → novel.id, ON DELETE CASCADE, PRIMARY KEY | 小说 ID |
| `tag_id` | INTEGER | FOREIGN KEY → tag.id, ON DELETE CASCADE, PRIMARY KEY | 标签 ID |

**主键：** 复合主键 `(novel_id, tag_id)`

---

### 3.10 favorite（收藏表）

用户收藏的小说列表。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 收藏 ID |
| `user_id` | INTEGER | FOREIGN KEY → user.id, NOT NULL | 用户 ID |
| `novel_id` | INTEGER | FOREIGN KEY → novel.id, NOT NULL, ON DELETE CASCADE | 小说 ID |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 收藏时间 |

**唯一约束：** `(user_id, novel_id)` 唯一，防止重复收藏

**索引：** `idx_favorite_user_id`、`idx_favorite_novel_id`

---

### 3.11 rating（评分表）

用户对小说的评分与简短评价。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 评分 ID |
| `user_id` | INTEGER | FOREIGN KEY → user.id, NOT NULL | 用户 ID |
| `novel_id` | INTEGER | FOREIGN KEY → novel.id, NOT NULL, ON DELETE CASCADE | 小说 ID |
| `score` | INTEGER | NOT NULL, CHECK (score BETWEEN 1 AND 5) | 评分（1-5 星） |
| `comment` | TEXT | NULL | 评价文字（可选） |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 评分时间 |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 最后修改时间 |

**唯一约束：** `(user_id, novel_id)` 唯一，每用户每本书只能有一条评分

**索引：** `idx_rating_novel_id`

---

## 4. 索引设计

| 索引名 | 所在表 | 字段 | 类型 | 用途 |
|--------|--------|------|------|------|
| `idx_novel_category_id` | novel | category_id | 普通索引 | 按分类筛选小说 |
| `idx_novel_title` | novel | title | 普通索引 | 按标题搜索 |
| `idx_chapter_novel_order` | chapter | novel_id, order | 复合索引 | 按小说查询章节并排序 |
| `idx_progress_user_novel` | reading_progress | user_id, novel_id | 唯一索引 | 查询某本书的阅读进度 |
| `idx_bookmark_user_novel` | bookmark | user_id, novel_id | 普通索引 | 查询某本书的书签 |
| `idx_favorite_user_id` | favorite | user_id | 普通索引 | 查询用户的收藏列表 |
| `idx_rating_novel_id` | rating | novel_id | 普通索引 | 计算某本书的平均评分 |
| `idx_chapter_rule_enabled` | chapter_rule | enabled | 普通索引 | 快速筛选启用的规则 |

---

## 5. 初始化数据

系统首次启动时，自动初始化以下数据：

### 5.1 默认用户
- 用户名：`admin`
- 密码：`admin123`（首次登录后建议修改）

### 5.2 内置章节拆分规则
| 名称 | 正则 | 说明 |
|------|------|------|
| 中文章节 | `^第[一二三四五六七八九十百千零\d]{1,8}[章节回卷].*$` | 匹配"第一章 xxx"等 |
| 中文回目 | `^第.{1,8}回.*$` | 匹配"第一回 xxx"等 |
| 英文章节 | `^Chapter\s+\d+.*$` | 匹配"Chapter 1 xxx"等 |

### 5.3 示例分类（可选）
- 玄幻
- 科幻
- 都市
- 历史

---

## 6. 典型查询场景

### 6.1 获取小说列表（带分类、标签筛选、评分、收藏状态）

```sql
SELECT 
  n.*,
  c.name AS category_name,
  (SELECT AVG(score) FROM rating WHERE novel_id = n.id) AS avg_rating,
  (SELECT COUNT(*) FROM rating WHERE novel_id = n.id) AS rating_count,
  EXISTS(SELECT 1 FROM favorite WHERE novel_id = n.id AND user_id = :user_id) AS is_favorite
FROM novel n
LEFT JOIN category c ON n.category_id = c.id
WHERE n.category_id = :category_id  -- 按分类筛选（可选）
  AND n.id IN (                     -- 按标签筛选（可选）
    SELECT nt.novel_id FROM novel_tags nt WHERE nt.tag_id = :tag_id
  )
ORDER BY n.updated_at DESC;
```

### 6.2 获取小说章节列表

```sql
SELECT id, title, word_count, `order`
FROM chapter
WHERE novel_id = :novel_id
ORDER BY `order` ASC;
```

### 6.3 全文搜索章节内容

```sql
SELECT 
  c.id, 
  c.title, 
  n.title AS novel_title,
  SUBSTR(c.content, MAX(1, INSTR(c.content, :keyword) - 20), 100) AS snippet
FROM chapter c
JOIN novel n ON c.novel_id = n.id
WHERE c.content LIKE '%' || :keyword || '%'
ORDER BY n.title, c.`order`
LIMIT 100;
```

### 6.4 计算小说平均评分

```sql
SELECT 
  AVG(score) AS avg_score,
  COUNT(*) AS rating_count
FROM rating
WHERE novel_id = :novel_id;
```

### 6.5 获取收藏列表（带最近阅读进度）

```sql
SELECT 
  n.id, 
  n.title, 
  n.author,
  rp.chapter_id,
  ch.title AS current_chapter,
  f.created_at AS favorited_at
FROM favorite f
JOIN novel n ON f.novel_id = n.id
LEFT JOIN reading_progress rp ON rp.novel_id = n.id AND rp.user_id = f.user_id
LEFT JOIN chapter ch ON rp.chapter_id = ch.id
WHERE f.user_id = :user_id
ORDER BY f.created_at DESC;
```

### 6.6 导入时获取启用的章节拆分规则

```sql
SELECT id, name, pattern, description
FROM chapter_rule
WHERE enabled = TRUE
ORDER BY sort_order ASC, id ASC;
```

---

## 7. 级联删除规则

| 操作 | 级联行为 |
|------|----------|
| 删除小说 | 级联删除章节、阅读进度、书签、收藏、评分、标签关联 |
| 删除分类 | 关联小说的 category_id 置为 NULL |
| 删除标签 | 级联删除 novel_tags 关联记录（不删除小说） |
| 删除用户 | 级联删除其所有进度、书签、收藏、评分 |
| 删除章节规则 | 无外键关联，仅删除自身 |

---

*文档版本：v1.0*  
*生成时间：2026-07-13*
