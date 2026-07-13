# 私人小说浏览系统 Phase 2 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现小说收藏、导出、全文搜索、阅读、在线编辑、TXT导入、Flask-Admin后台等剩余功能模块

**Architecture:** 基于现有 Flask + SQLAlchemy + Layui 架构，为每个功能模块创建独立的 Blueprint 路由文件和测试文件，遵循 TDD 流程（先写测试、确认失败、编写最小代码、确认通过、重构）

**Tech Stack:** Flask, Flask-SQLAlchemy, SQLite3, chardet, Werkzeug, Layui, pytest

---

## 现有代码状态

**已完成模块：**
- `app/__init__.py` - Flask 应用工厂
- `app/models.py` - 11 个数据模型
- `app/auth.py` - 登录鉴权（auth_bp: /login, /logout, login_required）
- `app/categories.py` - 分类管理（categories_bp: /categories CRUD）
- `app/tags.py` - 标签管理（tags_bp: /tags CRUD）
- `app/rules.py` - 规则管理（rules_bp: /rules CRUD, toggle）
- `app/ratings.py` - 评分管理（ratings_bp: /novels/<id>/rate, /rate/delete）
- `app/novels.py` - 小说管理（novels_bp: /novels list, detail, delete, tags, rules）
- `app/utils.py` - 工具函数（init_default_rules, calculate_average_rating）
- `tests/` - 58 个测试用例，36 通过

**待实现模块：**
- 收藏模块（Task 8）
- 小说导出模块（Task 13）
- 全文搜索模块（Task 14）
- 阅读模块（Task 11）
- 在线编辑模块（Task 12）
- TXT 导入模块（Task 4）
- Flask-Admin 后台（Task 15）

---

### Task 1: 实现收藏模块（Favorites）

**Files:**
- Create: `app/favorites.py`
- Modify: `app/__init__.py` (register favorites_bp)
- Modify: `app/models.py` (already has Favorite model)
- Test: `tests/unit/test_favorites.py`

**功能说明：** 用户可在小说详情页收藏/取消收藏小说，收藏列表独立展示。

- [ ] **Step 1: 编写收藏功能测试**

```python
import pytest


class TestFavoritesCRUD:
    def test_favorite_novel(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/favorite', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Favorite
            fav = Favorite.query.filter_by(user_id=user.id, novel_id=novel.id).first()
            assert fav is not None

    def test_unfavorite_novel(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, Favorite
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            fav = Favorite(user_id=user.id, novel_id=novel.id)
            db.session.add(fav)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/unfavorite', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Favorite
            fav = Favorite.query.filter_by(user_id=user.id, novel_id=novel.id).first()
            assert fav is None

    def test_favorites_list(self, client, app):
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Favorite
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            novel2 = Novel(title='test novel 2')
            db.session.add_all([user, novel, novel2])
            db.session.commit()
            fav = Favorite(user_id=user.id, novel_id=novel.id)
            db.session.add(fav)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/favorites', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'test novel' in data
        assert 'test novel 2' not in data
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_favorites.py -v
```
Expected: FAIL with ImportError or routing error

- [ ] **Step 3: 创建收藏模块 `app/favorites.py`**

```python
from flask import Blueprint, render_template, redirect, url_for, request, session
from app.models import db, Favorite, Novel
from app.auth import login_required

favorites_bp = Blueprint('favorites', __name__, url_prefix='/favorites')


@favorites_bp.route('/')
@login_required
def list():
    user_id = session.get('user_id')
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    novels = [fav.novel for fav in favorites]
    return render_template('favorites/list.html', novels=novels)


@favorites_bp.route('/novels/<int:novel_id>/favorite', methods=['POST'])
@login_required
def favorite(novel_id):
    user_id = session.get('user_id')
    existing = Favorite.query.filter_by(user_id=user_id, novel_id=novel_id).first()
    if not existing:
        fav = Favorite(user_id=user_id, novel_id=novel_id)
        db.session.add(fav)
        db.session.commit()
    return redirect(url_for('novels.detail', id=novel_id))


@favorites_bp.route('/novels/<int:novel_id>/unfavorite', methods=['POST'])
@login_required
def unfavorite(novel_id):
    user_id = session.get('user_id')
    existing = Favorite.query.filter_by(user_id=user_id, novel_id=novel_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return redirect(url_for('novels.detail', id=novel_id))
```

- [ ] **Step 4: 注册 favorites_bp 到 `app/__init__.py`**

```python
# 在 app/__init__.py 中添加:
from app.favorites import favorites_bp
app.register_blueprint(favorites_bp)
```

- [ ] **Step 5: 创建收藏列表模板 `app/templates/favorites/list.html`**

```html
<!DOCTYPE html>
<html>
<head><title>Favorites</title></head>
<body>
<h1>Favorites</h1>
{% for novel in novels %}
<div>{{ novel.title }}</div>
{% endfor %}
</body>
</html>
```

- [ ] **Step 6: 运行测试验证通过**

```bash
pytest tests/unit/test_favorites.py -v
```
Expected: 3 PASS

- [ ] **Step 7: 提交**

```bash
git add tests/unit/test_favorites.py app/favorites.py app/__init__.py app/templates/favorites/list.html
git commit -m "feat: add favorites module (add/remove/list)"
```

---

### Task 2: 实现小说导出模块（Export）

**Files:**
- Create: `app/export.py`
- Modify: `app/__init__.py` (register export_bp)
- Test: `tests/unit/test_export.py`

**功能说明：** 将整本小说导出为 TXT 文件下载，章节按序拼接，空行分隔。

- [ ] **Step 1: 编写导出功能测试**

```python
import pytest


class TestExport:
    def test_export_novel(self, client, app):
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='test-export')
            db.session.add_all([user, novel])
            db.session.commit()
            ch1 = Chapter(novel_id=novel.id, title='Chapter 1', content='Content of chapter 1', order=1)
            ch2 = Chapter(novel_id=novel.id, title='Chapter 2', content='Content of chapter 2', order=2)
            db.session.add_all([ch1, ch2])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel_id}/export')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
        content = response.data.decode('utf-8')
        assert 'Chapter 1' in content
        assert 'Chapter 2' in content
        assert 'Content of chapter 1' in content
        assert 'Content of chapter 2' in content

    def test_export_novel_empty(self, client, app):
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='test-empty')
            db.session.add_all([user, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel_id}/export')
        assert response.status_code == 200
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_export.py -v
```
Expected: FAIL (404 or routing error)

- [ ] **Step 3: 创建导出模块 `app/export.py`**

```python
from flask import Blueprint, Response
from app.models import Novel, Chapter
from app.auth import login_required

export_bp = Blueprint('export', __name__)


@export_bp.route('/novels/<int:novel_id>/export')
@login_required
def export_novel(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    chapters = Chapter.query.filter_by(novel_id=novel_id).order_by(Chapter.order).all()
    
    lines = [novel.title, '']
    for ch in chapters:
        lines.append(ch.title)
        lines.append('')
        lines.append(ch.content)
        lines.append('')
    
    content = '\n'.join(lines)
    
    return Response(
        content,
        mimetype='text/plain; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{novel.title}.txt"'
        }
    )
```

- [ ] **Step 4: 注册 export_bp 到 `app/__init__.py`**

```python
from app.export import export_bp
app.register_blueprint(export_bp)
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/unit/test_export.py -v
```
Expected: 2 PASS

- [ ] **Step 6: 提交**

```bash
git add tests/unit/test_export.py app/export.py app/__init__.py
git commit -m "feat: add novel export module (TXT download)"
```

---

### Task 3: 实现全站全文搜索模块（Search）

**Files:**
- Create: `app/search.py`
- Modify: `app/__init__.py` (register search_bp)
- Test: `tests/unit/test_search.py`

**功能说明：** 跨所有小说章节的全文搜索，输入关键词返回匹配的章节列表。

- [ ] **Step 1: 编写搜索功能测试**

```python
import pytest


class TestSearch:
    def test_search_keyword(self, client, app):
        novel_id = None
        chapter_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='search-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='The sword of destiny', order=1)
            db.session.add(ch)
            db.session.commit()
            novel_id = novel.id
            chapter_id = ch.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/search?q=sword', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'search-test' in data
        assert 'Chapter 1' in data

    def test_search_no_results(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='search-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='hello world', order=1)
            db.session.add(ch)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/search?q=nonexistent', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'no result' in data.lower() or 'not found' in data.lower()

    def test_search_empty_query(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/search', follow_redirects=True)
        assert response.status_code == 200
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_search.py -v
```
Expected: FAIL

- [ ] **Step 3: 创建搜索模块 `app/search.py`**

```python
from flask import Blueprint, render_template, request
from app.models import Chapter, Novel
from app.auth import login_required

search_bp = Blueprint('search', __name__, url_prefix='/search')


@search_bp.route('')
@login_required
def search():
    q = request.args.get('q', '')
    results = []
    
    if q:
        chapters = Chapter.query.filter(Chapter.content.like(f'%{q}%')).all()
        for ch in chapters:
            novel = Novel.query.get(ch.novel_id)
            snippet_start = max(0, ch.content.find(q) - 20)
            snippet_end = min(len(ch.content), ch.content.find(q) + len(q) + 80)
            snippet = ch.content[snippet_start:snippet_end]
            results.append({
                'novel_title': novel.title,
                'novel_id': novel.id,
                'chapter_title': ch.title,
                'chapter_id': ch.id,
                'snippet': snippet
            })
    
    return render_template('search/results.html', results=results, query=q)
```

- [ ] **Step 4: 注册 search_bp 到 `app/__init__.py`**

```python
from app.search import search_bp
app.register_blueprint(search_bp)
```

- [ ] **Step 5: 创建搜索结果模板 `app/templates/search/results.html`**

```html
<!DOCTYPE html>
<html>
<head><title>Search Results</title></head>
<body>
<h1>Search: {{ query }}</h1>
{% if results %}
{% for r in results %}
<div>
  <strong>{{ r.novel_title }}</strong> - {{ r.chapter_title }}
  <p>{{ r.snippet }}</p>
</div>
{% endfor %}
{% else %}
<div>No results found</div>
{% endif %}
</body>
</html>
```

- [ ] **Step 6: 运行测试验证通过**

```bash
pytest tests/unit/test_search.py -v
```
Expected: 3 PASS

- [ ] **Step 7: 提交**

```bash
git add tests/unit/test_search.py app/search.py app/__init__.py app/templates/search/results.html
git commit -m "feat: add full-text search module"
```

---

### Task 4: 实现阅读模块（Reading）

**Files:**
- Create: `app/reading.py`
- Modify: `app/__init__.py` (register reading_bp)
- Test: `tests/unit/test_reading.py`

**功能说明：** 分章节阅读，自动记录进度，支持书签管理。

- [ ] **Step 1: 编写阅读功能测试**

```python
import pytest


class TestReading:
    def test_read_chapter(self, client, app):
        novel_id = None
        chapter_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='read-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='Reading content', order=1)
            db.session.add(ch)
            db.session.commit()
            novel_id = novel.id
            chapter_id = ch.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel_id}/read/{chapter_id}', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'Chapter 1' in data
        assert 'Reading content' in data

    def test_chapter_navigation(self, client, app):
        novel_id = None
        ch1_id = None
        ch2_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='nav-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch1 = Chapter(novel_id=novel.id, title='Chapter 1', content='Content 1', order=1)
            ch2 = Chapter(novel_id=novel.id, title='Chapter 2', content='Content 2', order=2)
            db.session.add_all([ch1, ch2])
            db.session.commit()
            novel_id = novel.id
            ch1_id = ch1.id
            ch2_id = ch2.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel_id}/read/{ch1_id}', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'next' in data.lower() or 'Chapter 2' in data

    def test_save_reading_progress(self, client, app):
        novel_id = None
        chapter_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='progress-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='Content', order=1)
            db.session.add(ch)
            db.session.commit()
            novel_id = novel.id
            chapter_id = ch.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post('/api/progress', json={
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'scroll_position': 300
        })
        assert response.status_code == 200

        with app.app_context():
            from app.models import ReadingProgress
            progress = ReadingProgress.query.filter_by(user_id=1, novel_id=novel_id).first()
            assert progress is not None
            assert progress.chapter_id == chapter_id
            assert progress.scroll_position == 300

    def test_add_bookmark(self, client, app):
        novel_id = None
        chapter_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='bookmark-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='Content', order=1)
            db.session.add(ch)
            db.session.commit()
            novel_id = novel.id
            chapter_id = ch.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post('/api/bookmark', json={
            'novel_id': novel_id,
            'chapter_id': chapter_id,
            'title': 'my bookmark',
            'position': 150
        })
        assert response.status_code == 200

        with app.app_context():
            from app.models import Bookmark
            bm = Bookmark.query.filter_by(user_id=1, novel_id=novel_id).first()
            assert bm is not None
            assert bm.title == 'my bookmark'

    def test_delete_bookmark(self, client, app):
        bookmark_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Bookmark
            user = User(username='admin', password='admin123')
            novel = Novel(title='bm-delete-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='Content', order=1)
            db.session.add(ch)
            db.session.commit()
            bm = Bookmark(user_id=user.id, novel_id=novel.id, chapter_id=ch.id, title='test bm', position=100)
            db.session.add(bm)
            db.session.commit()
            bookmark_id = bm.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/api/bookmark/{bookmark_id}/delete')
        assert response.status_code == 200

        with app.app_context():
            from app.models import Bookmark
            bm = Bookmark.query.get(bookmark_id)
            assert bm is None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_reading.py -v
```
Expected: FAIL

- [ ] **Step 3: 创建阅读模块 `app/reading.py`**

```python
from flask import Blueprint, render_template, request, jsonify, session
from app.models import db, Novel, Chapter, ReadingProgress, Bookmark
from app.auth import login_required

reading_bp = Blueprint('reading', __name__)


@reading_bp.route('/novels/<int:novel_id>/read/<int:chapter_id>')
@login_required
def read_chapter(novel_id, chapter_id):
    novel = Novel.query.get_or_404(novel_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    
    chapters = Chapter.query.filter_by(novel_id=novel_id).order_by(Chapter.order).all()
    current_index = next((i for i, ch in enumerate(chapters) if ch.id == chapter_id), 0)
    prev_chapter = chapters[current_index - 1] if current_index > 0 else None
    next_chapter = chapters[current_index + 1] if current_index < len(chapters) - 1 else None
    
    return render_template('reading/reader.html', novel=novel, chapter=chapter,
                          prev_chapter=prev_chapter, next_chapter=next_chapter)


@reading_bp.route('/api/progress', methods=['POST'])
@login_required
def save_progress():
    user_id = session.get('user_id')
    data = request.get_json()
    
    progress = ReadingProgress.query.filter_by(user_id=user_id, novel_id=data['novel_id']).first()
    if progress:
        progress.chapter_id = data['chapter_id']
        progress.scroll_position = data['scroll_position']
    else:
        progress = ReadingProgress(
            user_id=user_id,
            novel_id=data['novel_id'],
            chapter_id=data['chapter_id'],
            scroll_position=data['scroll_position']
        )
        db.session.add(progress)
    db.session.commit()
    
    return jsonify({'status': 'ok'})


@reading_bp.route('/api/bookmark', methods=['POST'])
@login_required
def add_bookmark():
    user_id = session.get('user_id')
    data = request.get_json()
    
    bookmark = Bookmark(
        user_id=user_id,
        novel_id=data['novel_id'],
        chapter_id=data['chapter_id'],
        title=data['title'],
        position=data['position']
    )
    db.session.add(bookmark)
    db.session.commit()
    
    return jsonify({'status': 'ok', 'id': bookmark.id})


@reading_bp.route('/api/bookmark/<int:bookmark_id>/delete', methods=['POST'])
@login_required
def delete_bookmark(bookmark_id):
    user_id = session.get('user_id')
    bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
    return jsonify({'status': 'ok'})
```

- [ ] **Step 4: 注册 reading_bp 到 `app/__init__.py`**

```python
from app.reading import reading_bp
app.register_blueprint(reading_bp)
```

- [ ] **Step 5: 创建阅读模板 `app/templates/reading/reader.html`**

```html
<!DOCTYPE html>
<html>
<head><title>{{ novel.title }} - {{ chapter.title }}</title></head>
<body>
<h1>{{ chapter.title }}</h1>
<div>{{ chapter.content }}</div>
<div>
  {% if prev_chapter %}<a href="{{ url_for('reading.read_chapter', novel_id=novel.id, chapter_id=prev_chapter.id) }}">Prev</a>{% endif %}
  {% if next_chapter %}<a href="{{ url_for('reading.read_chapter', novel_id=novel.id, chapter_id=next_chapter.id) }}">Next</a>{% endif %}
</div>
</body>
</html>
```

- [ ] **Step 6: 运行测试验证通过**

```bash
pytest tests/unit/test_reading.py -v
```
Expected: 5 PASS

- [ ] **Step 7: 提交**

```bash
git add tests/unit/test_reading.py app/reading.py app/__init__.py app/templates/reading/reader.html
git commit -m "feat: add reading module with progress and bookmark"
```

---

### Task 5: 实现在线编辑模块（Edit）

**Files:**
- Create: `app/editor.py`
- Modify: `app/__init__.py` (register editor_bp)
- Test: `tests/unit/test_editor.py`

**功能说明：** 在线编辑章节标题与正文，保存后立即生效。

- [ ] **Step 1: 编写编辑功能测试**

```python
import pytest


class TestEditor:
    def test_edit_chapter_form(self, client, app):
        novel_id = None
        chapter_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='edit-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Original Title', content='Original Content', order=1)
            db.session.add(ch)
            db.session.commit()
            novel_id = novel.id
            chapter_id = ch.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel_id}/chapter/{chapter_id}/edit', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'Original Title' in data
        assert 'Original Content' in data

    def test_edit_chapter_save(self, client, app):
        novel_id = None
        chapter_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='edit-save-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Original Title', content='Original Content', order=1)
            db.session.add(ch)
            db.session.commit()
            novel_id = novel.id
            chapter_id = ch.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel_id}/chapter/{chapter_id}/edit', data={
            'title': 'New Title',
            'content': 'New Content'
        }, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Chapter
            updated = Chapter.query.get(chapter_id)
            assert updated.title == 'New Title'
            assert updated.content == 'New Content'
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_editor.py -v
```
Expected: FAIL

- [ ] **Step 3: 创建编辑模块 `app/editor.py`**

```python
from flask import Blueprint, render_template, redirect, url_for, request
from app.models import db, Novel, Chapter
from app.auth import login_required

editor_bp = Blueprint('editor', __name__)


@editor_bp.route('/novels/<int:novel_id>/chapter/<int:chapter_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_chapter(novel_id, chapter_id):
    novel = Novel.query.get_or_404(novel_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == 'POST':
        chapter.title = request.form.get('title')
        chapter.content = request.form.get('content')
        db.session.commit()
        return redirect(url_for('reading.read_chapter', novel_id=novel_id, chapter_id=chapter_id))
    
    return render_template('editor/edit.html', novel=novel, chapter=chapter)
```

- [ ] **Step 4: 注册 editor_bp 到 `app/__init__.py`**

```python
from app.editor import editor_bp
app.register_blueprint(editor_bp)
```

- [ ] **Step 5: 创建编辑模板 `app/templates/editor/edit.html`**

```html
<!DOCTYPE html>
<html>
<head><title>Edit Chapter</title></head>
<body>
<h1>Edit: {{ chapter.title }}</h1>
<form method="post">
  <input type="text" name="title" value="{{ chapter.title }}">
  <textarea name="content">{{ chapter.content }}</textarea>
  <button type="submit">Save</button>
</form>
</body>
</html>
```

- [ ] **Step 6: 运行测试验证通过**

```bash
pytest tests/unit/test_editor.py -v
```
Expected: 2 PASS

- [ ] **Step 7: 提交**

```bash
git add tests/unit/test_editor.py app/editor.py app/__init__.py app/templates/editor/edit.html
git commit -m "feat: add chapter editor module"
```

---

### Task 6: 实现 TXT 导入模块（Import - 4步向导）

**Files:**
- Create: `app/importer.py`
- Modify: `app/__init__.py` (register importer_bp)
- Create: `app/templates/import/` (step1-step4 templates)
- Test: `tests/unit/test_importer.py`

**功能说明：** 4步向导式 TXT 导入：Step1 上传转码 → Step2 选择规则 → Step3 预览章节 → Step4 保存

- [ ] **Step 1: 编写导入功能测试**

```python
import pytest
import io
import os


class TestImporter:
    def test_import_step1_upload(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        data = {
            'file': (io.BytesIO('第一章 开始\n这是第一章内容\n第二章 继续\n这是第二章内容'.encode('utf-8')), 'test.txt')
        }
        response = client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code == 200

    def test_import_step1_get(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/import', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'upload' in data.lower() or 'import' in data.lower()
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_importer.py -v
```
Expected: FAIL

- [ ] **Step 3: 创建导入模块 `app/importer.py`**

```python
import os
import re
import chardet
from flask import Blueprint, render_template, redirect, url_for, request, session
from werkzeug.utils import secure_filename
from app.models import db, Novel, Chapter, ChapterRule, NovelChapterRule
from app.auth import login_required
from app.utils import DEFAULT_RULES

importer_bp = Blueprint('importer', __name__, url_prefix='/novels/import')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')


@importer_bp.route('', methods=['GET', 'POST'])
@login_required
def step1():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return render_template('import/step1.html', error='No file selected')
        
        filename = secure_filename(file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        raw_data = open(filepath, 'rb').read()
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')
        
        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        utf8_path = filepath + '.utf8'
        with open(utf8_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        session['import_filepath'] = utf8_path
        session['import_filename'] = os.path.splitext(filename)[0]
        
        return redirect(url_for('importer.step2'))
    
    return render_template('import/step1.html')


@importer_bp.route('/step2', methods=['GET', 'POST'])
@login_required
def step2():
    if 'import_filepath' not in session:
        return redirect(url_for('importer.step1'))
    
    from app.models import ChapterRule
    rules = ChapterRule.query.filter_by(enabled=True).order_by(ChapterRule.sort_order).all()
    
    if request.method == 'POST':
        selected_rule_id = request.form.get('rule_id')
        custom_pattern = request.form.get('custom_pattern')
        save_custom = request.form.get('save_custom')
        
        if selected_rule_id:
            rule = ChapterRule.query.get(selected_rule_id)
            pattern = rule.pattern
        elif custom_pattern:
            pattern = custom_pattern
        else:
            pattern = DEFAULT_RULES[0]['pattern']
        
        filepath = session['import_filepath']
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        chapter_titles = []
        for line in lines:
            line = line.strip()
            if line and re.match(pattern, line):
                chapter_titles.append(line)
        
        session['import_pattern'] = pattern
        session['import_chapter_titles'] = [{'title': t, 'index': i} for i, t in enumerate(chapter_titles)]
        
        return redirect(url_for('importer.step3'))
    
    return render_template('import/step2.html', rules=rules)


@importer_bp.route('/step3', methods=['GET', 'POST'])
@login_required
def step3():
    if 'import_chapter_titles' not in session:
        return redirect(url_for('importer.step1'))
    
    chapter_titles = session.get('import_chapter_titles', [])
    
    if request.method == 'POST':
        delete_index = request.form.get('delete_index')
        if delete_index is not None:
            idx = int(delete_index)
            chapter_titles = [t for i, t in enumerate(chapter_titles) if i != idx]
            session['import_chapter_titles'] = chapter_titles
            return render_template('import/step3.html', chapter_titles=chapter_titles)
        
        return redirect(url_for('importer.step4'))
    
    return render_template('import/step3.html', chapter_titles=chapter_titles)


@importer_bp.route('/step4', methods=['GET', 'POST'])
@login_required
def step4():
    if 'import_chapter_titles' not in session:
        return redirect(url_for('importer.step1'))
    
    if request.method == 'POST':
        title = request.form.get('title', session.get('import_filename', 'Untitled'))
        author = request.form.get('author', '')
        category_id = request.form.get('category_id')
        
        filepath = session['import_filepath']
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = session.get('import_pattern', '')
        chapter_titles = session.get('import_chapter_titles', [])
        
        parts = re.split(f'({pattern})', content, flags=re.MULTILINE)
        
        novel = Novel(title=title, author=author if author else None)
        if category_id:
            novel.category_id = int(category_id)
        db.session.add(novel)
        db.session.commit()
        
        chapter_order = 0
        preamble = parts[0].strip() if parts else ''
        if preamble:
            chapter_order += 1
            ch = Chapter(novel_id=novel.id, title='序章', content=preamble, order=chapter_order)
            db.session.add(ch)
        
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                ch_title = parts[i].strip()
                ch_content = parts[i + 1].strip()
                chapter_order += 1
                ch = Chapter(novel_id=novel.id, title=ch_title, content=ch_content, order=chapter_order)
                db.session.add(ch)
        
        novel.chapter_count = chapter_order
        novel.word_count = sum(len(c.content) for c in novel.chapters)
        db.session.commit()
        
        session.pop('import_filepath', None)
        session.pop('import_filename', None)
        session.pop('import_pattern', None)
        session.pop('import_chapter_titles', None)
        
        return redirect(url_for('novels.detail', id=novel.id))
    
    chapter_count = len(session.get('import_chapter_titles', []))
    return render_template('import/step4.html', chapter_count=chapter_count)
```

- [ ] **Step 4: 注册 importer_bp 到 `app/__init__.py`**

```python
from app.importer import importer_bp
app.register_blueprint(importer_bp)
```

- [ ] **Step 5: 创建导入模板**

`app/templates/import/step1.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Import Step 1</title></head>
<body>
<h1>Upload TXT</h1>
<form method="post" enctype="multipart/form-data">
  <input type="file" name="file" accept=".txt">
  <button type="submit">Upload</button>
</form>
</body>
</html>
```

`app/templates/import/step2.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Import Step 2</title></head>
<body>
<h1>Select Rule</h1>
<form method="post">
  <select name="rule_id">
    {% for rule in rules %}
    <option value="{{ rule.id }}">{{ rule.name }}</option>
    {% endfor %}
  </select>
  <input type="text" name="custom_pattern" placeholder="Custom regex">
  <button type="submit">Next</button>
</form>
</body>
</html>
```

`app/templates/import/step3.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Import Step 3</title></head>
<body>
<h1>Preview Chapters</h1>
<form method="post">
  {% for t in chapter_titles %}
  <div>{{ t.title }} <button type="submit" name="delete_index" value="{{ loop.index0 }}">Delete</button></div>
  {% endfor %}
  <button type="submit">Next</button>
</form>
</body>
</html>
```

`app/templates/import/step4.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Import Step 4</title></head>
<body>
<h1>Confirm</h1>
<p>Chapters: {{ chapter_count }}</p>
<form method="post">
  <input type="text" name="title" placeholder="Title">
  <input type="text" name="author" placeholder="Author (optional)">
  <input type="number" name="category_id" placeholder="Category ID">
  <button type="submit">Import</button>
</form>
</body>
</html>
```

- [ ] **Step 6: 运行测试验证**

```bash
pytest tests/unit/test_importer.py -v
```
Expected: 2 PASS

- [ ] **Step 7: 提交**

```bash
git add tests/unit/test_importer.py app/importer.py app/__init__.py app/templates/import/
git commit -m "feat: add TXT import 4-step wizard module"
```

---

### Task 7: 实现 Flask-Admin 后台

**Files:**
- Modify: `app/__init__.py` (add flask-admin setup)
- Modify: `requirements.txt` (add flask-admin)
- Test: `tests/unit/test_admin.py`

**功能说明：** Flask-Admin 管理后台，提供数据模型管理界面，需登录鉴权。

- [ ] **Step 1: 安装 flask-admin 并编写测试**

```bash
pip install flask-admin
```

```python
import pytest


class TestAdmin:
    def test_admin_requires_login(self, client, app):
        response = client.get('/admin', follow_redirects=False)
        assert response.status_code == 302

    def test_admin_accessible_when_logged_in(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/admin', follow_redirects=True)
        assert response.status_code == 200
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_admin.py -v
```
Expected: FAIL

- [ ] **Step 3: 在 `app/__init__.py` 中添加 Flask-Admin**

```python
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

# 在 create_app 函数中:
admin = Admin(app, name='Novel Admin', template_mode='bootstrap4')

from app.models import User, Category, Novel, Chapter, ChapterRule, NovelChapterRule, Tag, Favorite, Rating, ReadingProgress, Bookmark

class AuthModelView(ModelView):
    def is_accessible(self):
        from flask import session
        return 'user_id' in session
    
    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

admin.add_view(AuthModelView(User, db.session))
admin.add_view(AuthModelView(Category, db.session))
admin.add_view(AuthModelView(Novel, db.session))
admin.add_view(AuthModelView(Chapter, db.session))
admin.add_view(AuthModelView(ChapterRule, db.session))
admin.add_view(AuthModelView(NovelChapterRule, db.session))
admin.add_view(AuthModelView(Tag, db.session))
admin.add_view(AuthModelView(Favorite, db.session))
admin.add_view(AuthModelView(Rating, db.session))
admin.add_view(AuthModelView(ReadingProgress, db.session))
admin.add_view(AuthModelView(Bookmark, db.session))
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_admin.py -v
```
Expected: 2 PASS

- [ ] **Step 5: 提交**

```bash
git add tests/unit/test_admin.py app/__init__.py requirements.txt
git commit -m "feat: add Flask-Admin backend with authentication"
```

---

### Task 8: 生成完整测试报告

**Files:**
- Create: `tests/reports/test_report_20260713_final.md`

**功能说明：** 运行所有测试并生成完整测试报告。

- [ ] **Step 1: 运行全部测试**

```bash
pytest tests/unit/ -v --tb=short 2>&1
```

- [ ] **Step 2: 生成覆盖率报告**

```bash
pytest tests/unit/ --cov=app --cov-report=term --cov-report=html
```

- [ ] **Step 3: 创建测试报告文档**

在 `tests/reports/test_report_20260713_final.md` 中汇总所有测试结果。

- [ ] **Step 4: 提交**

```bash
git add tests/reports/test_report_20260713_final.md
git commit -m "docs: add final test report"
```

---

## 任务依赖关系

```
Task 1 (Favorites) -- 无依赖，可并行
Task 2 (Export)    -- 无依赖，可并行
Task 3 (Search)    -- 无依赖，可并行
Task 4 (Reading)   -- 无依赖，可并行
Task 5 (Editor)    -- 无依赖，可并行
Task 6 (Import)    -- 依赖 Task 5 (rules 已存在)
Task 7 (Admin)     -- 依赖 pip install flask-admin
Task 8 (Report)    -- 依赖 Task 1-7 全部完成
```

---

*计划生成时间：2026-07-13*