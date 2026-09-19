import pytest
import io


class TestChapterDirectory:
    """测试章节目录分页功能"""

    def test_chapter_directory_route_exists(self, app, client):
        """路由 novels/<id>/chapter 应返回 200"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='测试', category_id=cat.id, chapter_count=0, word_count=0)
            db.session.add(novel)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}/chapter')
        assert response.status_code == 200

    def test_chapter_default_pagination_20_per_page(self, app, client):
        """默认每页显示 20 章"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='分页测试', category_id=cat.id, chapter_count=45, word_count=0)
            db.session.add(novel)
            db.session.commit()
            for i in range(1, 46):
                ch = Chapter(novel_id=novel.id, title=f'第{i}章', content=f'内容{i}', order=i, word_count=3)
                db.session.add(ch)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}/chapter')
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 第一页应显示 20 章
        assert '第1章' in html
        assert '第20章' in html
        # 第21章不应出现在第一页
        assert '第21章' not in html

        # 应显示分页导航
        assert '下一页' in html or 'next' in html.lower() or '»' in html

    def test_chapter_page2_parameter(self, app, client):
        """page=2 参数显示第二页章节"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='分页2', category_id=cat.id, chapter_count=45, word_count=0)
            db.session.add(novel)
            db.session.commit()
            for i in range(1, 46):
                ch = Chapter(novel_id=novel.id, title=f'第{i}章', content=f'内容{i}', order=i, word_count=3)
                db.session.add(ch)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}/chapter?page=2')
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 第二页应显示第21-40章
        assert '第21章' in html
        assert '第40章' in html
        # 第1章不应出现在第二页
        assert '第1章' not in html

    def test_chapter_per_page_parameter(self, app, client):
        """per_page 参数控制每页章节数"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='每页50', category_id=cat.id, chapter_count=55, word_count=0)
            db.session.add(novel)
            db.session.commit()
            for i in range(1, 56):
                ch = Chapter(novel_id=novel.id, title=f'第{i}章', content=f'内容{i}', order=i, word_count=3)
                db.session.add(ch)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}/chapter?per_page=50')
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 每页 50，应显示 50 章
        assert '第1章' in html
        assert '第50章' in html
        assert '第51章' not in html

        # 第二页
        response = client.get(f'/novels/{novel_id}/chapter?per_page=50&page=2')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '第51章' in html
        assert '第55章' in html

    def test_chapter_per_page_options(self, app, client):
        """每页章节数选项：10, 20, 50, 100"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='选项测试', category_id=cat.id, chapter_count=100, word_count=0)
            db.session.add(novel)
            db.session.commit()
            for i in range(1, 101):
                ch = Chapter(novel_id=novel.id, title=f'第{i}章', content=f'内容{i}', order=i, word_count=3)
                db.session.add(ch)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 每页10
        response = client.get(f'/novels/{novel_id}/chapter?per_page=10')
        html = response.data.decode('utf-8')
        assert '第10章' in html
        assert '第11章' not in html

        # 每页20（默认）
        response = client.get(f'/novels/{novel_id}/chapter?per_page=20')
        html = response.data.decode('utf-8')
        assert '第20章' in html
        assert '第21章' not in html

        # 每页50
        response = client.get(f'/novels/{novel_id}/chapter?per_page=50')
        html = response.data.decode('utf-8')
        assert '第50章' in html
        assert '第51章' not in html

        # 每页100
        response = client.get(f'/novels/{novel_id}/chapter?per_page=100')
        html = response.data.decode('utf-8')
        assert '第100章' in html

    def test_detail_page_shows_chapter_link_not_list(self, app, client):
        """详情页应显示目录链接，而非直接显示章节列表"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='链接测试', category_id=cat.id, chapter_count=5, word_count=0)
            db.session.add(novel)
            db.session.commit()
            for i in range(1, 6):
                ch = Chapter(novel_id=novel.id, title=f'第{i}章', content=f'内容{i}', order=i, word_count=3)
                db.session.add(ch)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 应包含目录链接
        assert f'/novels/{novel_id}/chapter' in html
        assert '目录' in html or '查看全部' in html or '章节' in html

    def test_empty_chapter_directory(self, app, client):
        """无章节时应显示空状态"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='空目录', category_id=cat.id, chapter_count=0, word_count=0)
            db.session.add(novel)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}/chapter')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '暂无' in html or '没有' in html or '空' in html


class TestChapterDirectoryReimportButton:
    """章节目录页：上传表中存在该书记录时，显示「重新导入」按钮。"""

    def _seed(self, app, with_upload):
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Upload
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

            novel = Novel(title='目录页测试', chapter_count=2, word_count=0)
            db.session.add(novel)
            db.session.commit()
            db.session.add_all([
                Chapter(novel_id=novel.id, title='第1章', content='内容一', order=1, word_count=3),
                Chapter(novel_id=novel.id, title='第2章', content='内容二', order=2, word_count=3),
            ])
            upload_id = None
            if with_upload:
                upload = Upload(title='目录页测试', file_path='uploads/1/目录页测试.txt',
                                file_size=100, novel_id=novel.id)
                db.session.add(upload)
                db.session.commit()
                upload_id = upload.id
            return novel.id, upload_id

    def test_shows_reimport_button_when_upload_exists(self, app, client):
        novel_id, upload_id = self._seed(app, with_upload=True)

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        html = client.get(f'/novels/{novel_id}/chapter').data.decode('utf-8')

        assert '重新导入' in html, '上传表有记录时应显示重新导入按钮'
        assert f'/novels/import/reimport/{upload_id}' in html, '按钮应指向该书对应的上传记录'

    def test_hides_reimport_button_without_upload(self, app, client):
        novel_id, _ = self._seed(app, with_upload=False)

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        html = client.get(f'/novels/{novel_id}/chapter').data.decode('utf-8')

        assert '重新导入' not in html, '上传表无记录时不应显示重新导入按钮'


class TestChapterPerPageRememberedInSession:
    """章节目录页的每页行数选择用 session 记忆，并回显在选项上。"""

    def _seed(self, app, count=55):
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()
            novel = Novel(title='每页记忆', chapter_count=count, word_count=0)
            db.session.add(novel)
            db.session.commit()
            for i in range(1, count + 1):
                db.session.add(Chapter(novel_id=novel.id, title=f'第{i}章',
                                       content=f'内容{i}', order=i, word_count=3))
            db.session.commit()
            return novel.id

    def test_per_page_selection_is_remembered_and_applied(self, app, client):
        """不带参数再次访问时，应沿用上次选择的每页行数。"""
        novel_id = self._seed(app)
        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        client.get(f'/novels/{novel_id}/chapter?per_page=50')

        html = client.get(f'/novels/{novel_id}/chapter').data.decode('utf-8')
        assert 'class="active">50</a>' in html, '每页行数选项应回显上次选择'
        assert '第50章' in html
        assert '第51章' not in html, '应按记忆的每页 50 行分页'

    def test_default_per_page_is_20(self, app, client):
        """未选择时默认每页 20 行。"""
        novel_id = self._seed(app)
        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        html = client.get(f'/novels/{novel_id}/chapter').data.decode('utf-8')
        assert 'class="active">20</a>' in html
        assert '第20章' in html
        assert '第21章' not in html, '默认每页 20 行，第 21 章应在第二页'