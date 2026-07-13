# 私人小说浏览系统 - 测试报告（20260713）

> 基于 TDD 原则的测试报告
> 日期：2026-07-13
> 测试框架：pytest
> Python 版本：3.14.4

---

## 1. 测试概览

| 指标 | 数值 |
|------|------|
| 总测试数 | 58 |
| 通过数 | 36 |
| 失败数 | 22 |
| 通过率 | 62.1% |

---

## 2. 测试结果明细

### 2.1 数据模型测试（test_models.py）- 全部通过 ✅

| 测试类 | 测试方法 | 状态 |
|--------|----------|------|
| TestUserModel | test_user_creation | ✅ 通过 |
| TestUserModel | test_user_password_hash | ✅ 通过 |
| TestUserModel | test_user_password_check | ✅ 通过 |
| TestCategoryModel | test_category_creation | ✅ 通过 |
| TestCategoryModel | test_category_default_sort_order | ✅ 通过 |
| TestNovelModel | test_novel_creation | ✅ 通过 |
| TestNovelModel | test_novel_user_rating_default | ✅ 通过 |
| TestNovelModel | test_novel_author_optional | ✅ 通过 |
| TestChapterModel | test_chapter_creation | ✅ 通过 |
| TestChapterModel | test_chapter_order | ✅ 通过 |
| TestChapterRuleModel | test_rule_creation | ✅ 通过 |
| TestChapterRuleModel | test_rule_enabled_default | ✅ 通过 |
| TestNovelChapterRuleModel | test_novel_rule_creation | ✅ 通过 |
| TestNovelChapterRuleModel | test_novel_rule_novel_relation | ✅ 通过 |
| TestTagModel | test_tag_creation | ✅ 通过 |
| TestTagModel | test_tag_color_default | ✅ 通过 |
| TestFavoriteModel | test_favorite_creation | ✅ 通过 |
| TestRatingModel | test_rating_creation | ✅ 通过 |
| TestRatingModel | test_rating_score_range | ✅ 通过 |
| TestReadingProgressModel | test_progress_creation | ✅ 通过 |
| TestBookmarkModel | test_bookmark_creation | ✅ 通过 |

### 2.2 登录鉴权测试（test_auth.py）- 部分通过

| 测试类 | 测试方法 | 状态 | 原因 |
|--------|----------|------|------|
| TestAuthLogin | test_login_success | ✅ 通过 | |
| TestAuthLogin | test_login_failure_wrong_password | ❌ 失败 | 模板路径问题 |
| TestAuthLogin | test_login_failure_empty_username | ❌ 失败 | 模板路径问题 |
| TestAuthLogin | test_logout | ❌ 失败 | 模板路径问题 |
| TestAuthPermission | test_unauthenticated_access_redirect | ❌ 失败 | 路由不存在 |
| TestAuthPermission | test_unauthenticated_access_novels_redirect | ❌ 失败 | 路由重定向问题 |
| TestAuthPermission | test_authenticated_access_allowed | ❌ 失败 | 路由不存在 |

### 2.3 分类管理测试（test_categories.py）- 全部通过 ✅

| 测试类 | 测试方法 | 状态 |
|--------|----------|------|
| TestCategoriesCRUD | test_create_category | ✅ 通过 |
| TestCategoriesCRUD | test_read_category | ✅ 通过 |
| TestCategoriesCRUD | test_update_category | ✅ 通过 |
| TestCategoriesCRUD | test_delete_category | ✅ 通过 |

### 2.4 标签管理测试（test_tags.py）- 部分通过

| 测试类 | 测试方法 | 状态 | 原因 |
|--------|----------|------|------|
| TestTagsCRUD | test_create_tag | ✅ 通过 | |
| TestTagsCRUD | test_read_tags | ✅ 通过 | |
| TestTagsCRUD | test_update_tag | ❌ 失败 | DetachedInstanceError |
| TestTagsCRUD | test_delete_tag | ❌ 失败 | DetachedInstanceError |
| TestNovelTagsRelation | test_novel_add_tags | ❌ 失败 | DetachedInstanceError |
| TestNovelTagsRelation | test_novel_remove_tags | ❌ 失败 | DetachedInstanceError |
| TestNovelTagsRelation | test_novel_multiple_tags | ✅ 通过 | |

### 2.5 章节规则测试（test_rules.py）- 部分通过

| 测试类 | 测试方法 | 状态 | 原因 |
|--------|----------|------|------|
| TestChapterRulesCRUD | test_create_rule | ✅ 通过 | |
| TestChapterRulesCRUD | test_read_rules | ✅ 通过 | |
| TestChapterRulesCRUD | test_update_rule | ❌ 失败 | DetachedInstanceError |
| TestChapterRulesCRUD | test_toggle_rule | ❌ 失败 | DetachedInstanceError |
| TestChapterRulesCRUD | test_delete_rule | ❌ 失败 | DetachedInstanceError |
| TestDefaultRules | test_default_rules_count | ✅ 通过 | |
| TestDefaultRules | test_default_rules_categories | ❌ 失败 | 分类不匹配 |
| TestNovelChapterRules | test_create_novel_rule | ❌ 失败 | DetachedInstanceError |
| TestNovelChapterRules | test_read_novel_rule | ❌ 失败 | DetachedInstanceError |
| TestNovelChapterRules | test_update_novel_rule | ❌ 失败 | DetachedInstanceError |
| TestNovelChapterRules | test_delete_novel_rule | ❌ 失败 | DetachedInstanceError |

### 2.6 评分功能测试（test_ratings.py）- 部分通过

| 测试类 | 测试方法 | 状态 | 原因 |
|--------|----------|------|------|
| TestRatingsCRUD | test_create_rating | ❌ 失败 | DetachedInstanceError |
| TestRatingsCRUD | test_update_rating | ❌ 失败 | DetachedInstanceError |
| TestRatingsCRUD | test_delete_rating | ❌ 失败 | DetachedInstanceError |
| TestAverageRatingCalculation | test_calculate_average_rating_single | ✅ 通过 | |
| TestAverageRatingCalculation | test_calculate_average_rating_multiple | ✅ 通过 | |
| TestAverageRatingCalculation | test_calculate_average_rating_rounding | ✅ 通过 | |
| TestAverageRatingCalculation | test_update_user_rating_after_rate | ✅ 通过 | |
| TestAverageRatingCalculation | test_user_rating_default_zero | ❌ 失败 | 瞬态对象 |

---

## 3. 失败原因分析

### 3.1 DetachedInstanceError（15 个测试）
**原因**：测试中在 `app.app_context()` 外部使用了数据库对象，导致 SQLAlchemy 对象脱离了 session。

**解决方案**：在测试中保存对象 ID，后续操作使用 ID 而不是对象引用。

### 3.2 模板路径问题（3 个测试）
**原因**：`auth/login.html` 模板路径可能不匹配。

**解决方案**：检查模板文件路径和引用路径是否一致。

### 3.3 路由问题（3 个测试）
**原因**：部分路由（如 `/dashboard`）未实现。

**解决方案**：添加缺失的路由和视图函数。

### 3.4 规则分类不匹配（1 个测试）
**原因**：测试期望的分类与实际默认规则分类不一致。

**解决方案**：更新测试期望或添加缺失的规则分类。

---

## 4. 通过测试覆盖的功能

### 4.1 数据模型层
- 用户模型：创建、密码哈希、密码校验
- 分类模型：创建、默认排序
- 小说模型：创建、默认评分、作者可选
- 章节模型：创建、排序
- 章节规则模型：创建、默认启用
- 书籍规则模型：创建、关联
- 标签模型：创建、默认颜色
- 收藏模型：创建
- 评分模型：创建、评分范围
- 阅读进度模型：创建
- 书签模型：创建

### 4.2 业务逻辑层
- 分类管理：CRUD 操作
- 标签管理：创建、读取
- 规则管理：创建、读取、默认规则初始化
- 评分计算：平均分计算、四舍五入、更新小说评分

---

## 5. 测试执行命令

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行模型测试
pytest tests/unit/test_models.py -v

# 生成覆盖率报告
pytest tests/unit/ --cov=app --cov-report=html
```

---

## 6. 结论

- **核心数据模型测试全部通过**（21/21），验证了所有数据库模型的正确性
- **分类管理测试全部通过**（4/4），验证了分类 CRUD 操作
- **评分计算逻辑测试通过**（4/5），验证了平均分计算和四舍五入功能
- **失败测试主要集中在**：集成测试中的 DetachedInstanceError，需要优化测试代码结构

---

*测试报告生成时间：2026-07-13*
*测试运行时间：10.15 秒*
*警告数：12（主要为 SQLAlchemy 2.0 兼容性警告）*