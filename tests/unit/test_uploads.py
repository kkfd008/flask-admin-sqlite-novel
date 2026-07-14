"""Tests for Upload model and upload list functionality."""
import io
import os
from datetime import datetime
import pytest


class TestUploadModel:
    def test_upload_creation(self, app):
        """Upload model should have title, notes, file_path, created_at, updated_at, last_import_at, novel_id."""
        with app.app_context():
            from app.models import db, Upload

            upload = Upload(
                title='剑来',
                notes='烽火戏诸侯作品',
                file_path='uploads/260714/剑来.txt'
            )
            db.session.add(upload)
            db.session.commit()

            assert upload.id is not None
            assert upload.title == '剑来'
            assert upload.notes == '烽火戏诸侯作品'
            assert upload.file_path == 'uploads/260714/剑来.txt'
            assert upload.created_at is not None
            assert upload.updated_at is not None
            assert upload.last_import_at is None
            assert upload.novel_id == 0

    def test_upload_last_import_at_update(self, app):
        """last_import_at should be updatable after import."""
        with app.app_context():
            from app.models import db, Upload

            upload = Upload(
                title='剑来',
                file_path='uploads/260714/剑来.txt'
            )
            db.session.add(upload)
            db.session.commit()

            assert upload.last_import_at is None

            now = datetime.now()
            upload.last_import_at = now
            db.session.commit()

            assert upload.last_import_at == now

    def test_upload_notes_optional(self, app):
        """notes should be optional."""
        with app.app_context():
            from app.models import db, Upload

            upload = Upload(
                title='剑来',
                file_path='uploads/260714/剑来.txt'
            )
            db.session.add(upload)
            db.session.commit()

            assert upload.notes is None

    def test_upload_default_sort_by_created_at_desc(self, app):
        """Uploads should be queryable ordered by created_at desc."""
        with app.app_context():
            from app.models import db, Upload

            upload1 = Upload(title='小说A', file_path='uploads/260714/A.txt')
            upload2 = Upload(title='小说B', file_path='uploads/260714/B.txt')
            db.session.add_all([upload1, upload2])
            db.session.commit()

            uploads = Upload.query.order_by(Upload.created_at.desc()).all()
            assert len(uploads) == 2
            # 后创建的在前
            assert uploads[0].title == '小说B'
            assert uploads[1].title == '小说A'


class TestUploadsRoute:
    def test_uploads_list_requires_login(self, client):
        """/novels/uploads should redirect to login when not authenticated."""
        response = client.get('/novels/uploads', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '登录' in html or 'login' in html.lower()

    def test_uploads_list_shows_empty_state(self, client, app):
        """/novels/uploads should show empty state when no uploads exist."""
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/uploads', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '暂无' in html or '上传' in html

    def test_uploads_list_shows_upload_records(self, client, app):
        """/novels/uploads should show upload records sorted by created_at desc."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            upload1 = Upload(title='剑来', file_path='uploads/260714/剑来.txt')
            upload2 = Upload(title='雪中悍刀行', file_path='uploads/260714/雪中悍刀行.txt')
            db.session.add_all([user, upload1, upload2])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/uploads', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '剑来' in html
        assert '雪中悍刀行' in html

    def test_uploads_list_pagination(self, client, app):
        """/novels/uploads should support pagination."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            for i in range(15):
                upload = Upload(title=f'小说{i}', file_path=f'uploads/260714/小说{i}.txt')
                db.session.add(upload)
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 默认第一页，每页 10 条
        response = client.get('/novels/uploads', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 应该只显示前 10 条
        assert '小说14' in html  # 最新的第一条
        # 第 11 条应该不在第一页
        # 应该有分页控件
        assert 'page' in html.lower() or '页' in html or '下一页' in html


class TestNavigationImportButton:
    def test_import_button_goes_to_import_when_empty(self, client, app):
        """When Upload table is empty, import button should link to /novels/import."""
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 访问任意页面，检查导航栏中导入按钮的链接
        response = client.get('/novels/', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 导入按钮应该指向 /novels/import
        assert '/novels/import' in html

    def test_import_button_goes_to_uploads_when_has_records(self, client, app):
        """When Upload table has records, import button should link to /novels/uploads."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            upload = Upload(title='剑来', file_path='uploads/260714/剑来.txt')
            db.session.add_all([user, upload])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 导入按钮应该指向 /novels/uploads
        assert '/novels/uploads' in html


class TestImportStep1Save:
    def test_step1_saves_to_date_directory(self, client, app):
        """step1 should save file to uploads/YYMMDD/ directory."""
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 继续\n这是第二章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        response = client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Upload
            upload = Upload.query.order_by(Upload.created_at.desc()).first()
            assert upload is not None, 'step1 should create an Upload record'
            assert upload.title is not None, 'Upload should have a title'
            # file_path should contain a date-based directory
            today_str = datetime.now().strftime('%y%m%d')
            assert today_str in upload.file_path, f'file_path should contain YYMMDD date dir, got: {upload.file_path}'

    def test_step1_upload_record_has_file_path(self, client, app):
        """step1 should save relative file path in Upload record."""
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        with app.app_context():
            from app.models import Upload
            upload = Upload.query.order_by(Upload.created_at.desc()).first()
            assert upload is not None
            assert 'uploads' in upload.file_path, f'file_path should be relative path under uploads, got: {upload.file_path}'
            assert 'test.txt' in upload.file_path, f'file_path should contain filename, got: {upload.file_path}'


class TestUploadNovelId:
    def test_upload_novel_id_defaults_to_zero(self, app):
        """novel_id should default to 0."""
        with app.app_context():
            from app.models import db, Upload

            upload = Upload(title='剑来', file_path='uploads/260714/剑来.txt')
            db.session.add(upload)
            db.session.commit()

            assert upload.novel_id == 0

    def test_upload_novel_id_can_be_set(self, app):
        """novel_id should be settable to a novel's ID."""
        with app.app_context():
            from app.models import db, Upload, Novel

            novel = Novel(title='剑来')
            db.session.add(novel)
            db.session.commit()

            upload = Upload(
                title='剑来',
                file_path='uploads/260714/剑来.txt',
                novel_id=novel.id
            )
            db.session.add(upload)
            db.session.commit()

            assert upload.novel_id == novel.id


class TestStep4UpdatesUploadNovelId:
    def test_step4_complete_updates_upload_novel_id(self, client, app):
        """After step4 import completes, the most recent Upload record should have novel_id set."""
        cat_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 继续\n这是第二章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), '测试小说.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(rule_id)}, follow_redirects=True)

        response = client.post('/novels/import/step4', data={
            'title': '测试小说',
            'author': '测试作者',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Upload, Novel
            upload = Upload.query.order_by(Upload.created_at.desc()).first()
            assert upload is not None
            assert upload.novel_id > 0, f'step4 should set novel_id on upload, got {upload.novel_id}'

            novel = Novel.query.get(upload.novel_id)
            assert novel is not None
            assert novel.title == '测试小说'

    def test_step4_no_upload_record_still_works(self, client, app):
        """step4 should still work even if no Upload record exists (backward compat)."""
        cat_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), '直接导入.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(rule_id)}, follow_redirects=True)

        response = client.post('/novels/import/step4', data={
            'title': '直接导入小说',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '直接导入小说' in html


class TestUploadsListConditionalButtons:
    def test_upload_with_novel_id_shows_read_button(self, client, app):
        """Upload with novel_id > 0 should show '阅读' button, not '导入书库'."""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Upload, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='剑来')
            db.session.add_all([user, novel])
            db.session.commit()
            novel_id = novel.id

            upload = Upload(title='剑来', file_path='uploads/260714/剑来.txt', novel_id=novel_id)
            db.session.add(upload)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/uploads', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '阅读' in html, '已导入的上传应显示阅读按钮'
        assert '导入书库' not in html, '已导入的上传不应显示导入书库按钮'
        assert f'/novels/{novel_id}' in html, '阅读按钮应链接到小说详情页'

    def test_upload_without_novel_id_shows_import_button(self, client, app):
        """Upload with novel_id == 0 should show '导入书库' button, not '阅读'."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            upload = Upload(title='剑来', file_path='uploads/260714/剑来.txt', novel_id=0)
            db.session.add_all([user, upload])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/uploads', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '导入书库' in html, '未导入的上传应显示导入书库按钮'
        assert '阅读' not in html, '未导入的上传不应显示阅读按钮'

    def test_mixed_uploads_shows_correct_buttons(self, client, app):
        """Mixed uploads: some imported show '阅读', some not show '导入书库'."""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Upload, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='剑来')
            db.session.add_all([user, novel])
            db.session.commit()
            novel_id = novel.id

            upload1 = Upload(title='剑来', file_path='uploads/260714/剑来.txt', novel_id=novel_id)
            upload2 = Upload(title='雪中悍刀行', file_path='uploads/260714/雪中悍刀行.txt', novel_id=0)
            db.session.add_all([upload1, upload2])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/uploads', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '阅读' in html
        assert '导入书库' in html
        assert f'/novels/{novel_id}' in html


class TestUploadFileSize:
    def test_upload_file_size_defaults_to_zero(self, app):
        """file_size should default to 0."""
        with app.app_context():
            from app.models import db, Upload

            upload = Upload(title='剑来', file_path='uploads/260714/剑来.txt')
            db.session.add(upload)
            db.session.commit()

            assert upload.file_size == 0

    def test_upload_file_size_can_be_set(self, app):
        """file_size should be settable."""
        with app.app_context():
            from app.models import db, Upload

            upload = Upload(title='剑来', file_path='uploads/260714/剑来.txt', file_size=102400)
            db.session.add(upload)
            db.session.commit()

            assert upload.file_size == 102400

    def test_step1_saves_file_size(self, client, app):
        """step1 should save file_size in Upload record."""
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 继续\n这是第二章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        with app.app_context():
            from app.models import Upload
            upload = Upload.query.order_by(Upload.created_at.desc()).first()
            assert upload is not None
            assert upload.file_size > 0, f'file_size should be > 0, got {upload.file_size}'

    def test_uploads_list_shows_file_size(self, client, app):
        """Uploads list should display file_size."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            upload = Upload(title='剑来', file_path='uploads/260714/剑来.txt', file_size=2048000)
            db.session.add_all([user, upload])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/uploads', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # 2MB = 2048000 bytes, should show formatted size
        assert 'MB' in html or 'KB' in html or '2048000' in html or '2.0' in html or '1.95' in html


class TestStep1DuplicateCheck:
    def test_step1_first_upload_goes_to_step2(self, client, app):
        """First upload of a filename should go directly to step2."""
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), '新小说.txt')}
        response = client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # 应该跳转到 step2
        assert '第二步' in html or 'step2' in html.lower() or '规则' in html

    def test_step1_duplicate_shows_compare_page(self, client, app):
        """Uploading same filename twice should show comparison page with overwrite option."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 第一次上传
        content1 = '第1章 开始\n这是第一章内容'
        data1 = {'file': (io.BytesIO(content1.encode('utf-8')), '剑来.txt')}
        client.post('/novels/import', data=data1, content_type='multipart/form-data', follow_redirects=True)

        # 第二次上传同名文件，不同大小
        content2 = '第1章 开始\n这是第一章内容\n更多内容'
        data2 = {'file': (io.BytesIO(content2.encode('utf-8')), '剑来.txt')}
        response = client.post('/novels/import', data=data2, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 应显示重复提示
        assert '重复' in html or '覆盖' in html or '已存在' in html
        # 应显示覆盖复选框
        assert 'checkbox' in html.lower() or '覆盖' in html
        # 应显示下一步按钮
        assert '下一步' in html

    def test_step1_duplicate_overwrite_goes_to_step2(self, client, app):
        """Checking overwrite and clicking next should go to step2."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 第一次上传
        content1 = '第1章 开始\n这是第一章内容'
        data1 = {'file': (io.BytesIO(content1.encode('utf-8')), '剑来.txt')}
        client.post('/novels/import', data=data1, content_type='multipart/form-data', follow_redirects=True)

        # 第二次上传同名文件，勾选覆盖
        content2 = '第1章 开始\n这是第一章内容\n更多内容'
        data2 = {'file': (io.BytesIO(content2.encode('utf-8')), '剑来.txt')}
        response = client.post('/novels/import', data={
            'file': (io.BytesIO(content2.encode('utf-8')), '剑来.txt'),
            'overwrite': '1',
        }, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '第二步' in html or '规则' in html, f'应跳转到step2, got: {html[:300]}'

    def test_step1_upload_page_shows_upload_button(self, client, app):
        """step1 GET page should show '上传' button, not '上传并继续'."""
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/import', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '上传' in html
        assert '上传并继续' not in html

    def test_step1_duplicate_shows_visible_checkbox(self, client, app):
        """Duplicate page should show a visible checkbox (not hidden) for overwrite."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content1 = '第1章 开始\n这是第一章内容'
        data1 = {'file': (io.BytesIO(content1.encode('utf-8')), '剑来.txt')}
        client.post('/novels/import', data=data1, content_type='multipart/form-data', follow_redirects=True)

        content2 = '第1章 开始\n更多内容'
        data2 = {'file': (io.BytesIO(content2.encode('utf-8')), '剑来.txt')}
        response = client.post('/novels/import', data=data2, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 必须有可见的 checkbox（非 hidden）
        assert 'type="checkbox"' in html, '重复页必须有可见的覆盖勾选框'
        assert 'name="overwrite"' in html, 'checkbox name 应为 overwrite'

    def test_step1_duplicate_shows_cancel_button(self, client, app):
        """Duplicate page should show cancel button linking to uploads list."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content1 = '第1章 开始\n这是第一章内容'
        data1 = {'file': (io.BytesIO(content1.encode('utf-8')), '剑来.txt')}
        client.post('/novels/import', data=data1, content_type='multipart/form-data', follow_redirects=True)

        content2 = '第1章 开始\n更多内容'
        data2 = {'file': (io.BytesIO(content2.encode('utf-8')), '剑来.txt')}
        response = client.post('/novels/import', data=data2, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '取消' in html, '重复页应有取消按钮'
        assert '/novels/uploads' in html, '取消按钮应链接到上传列表'

    def test_step1_overwrite_keeps_file_path(self, client, app):
        """Overwriting should keep the original file_path unchanged."""
        with app.app_context():
            from app.models import db, User, Upload
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content1 = '第1章 开始\n这是第一章内容'
        data1 = {'file': (io.BytesIO(content1.encode('utf-8')), '剑来.txt')}
        client.post('/novels/import', data=data1, content_type='multipart/form-data', follow_redirects=True)

        with app.app_context():
            first_upload = Upload.query.order_by(Upload.created_at.desc()).first()
            original_path = first_upload.file_path
            original_size = first_upload.file_size

        # 第二次上传同名文件，勾选覆盖
        content2 = '第1章 开始\n这是第一章内容\n更多内容'
        client.post('/novels/import', data={
            'file': (io.BytesIO(content2.encode('utf-8')), '剑来.txt'),
            'overwrite': '1',
        }, content_type='multipart/form-data', follow_redirects=True)

        with app.app_context():
            upload = Upload.query.order_by(Upload.updated_at.desc()).first()
            assert upload.file_path == original_path, f'覆盖后 file_path 应保持不变: {upload.file_path} != {original_path}'
            assert upload.file_size == len(content2.encode('utf-8')), f'file_size 应更新为新文件大小'
            assert upload.file_size > original_size, '新文件更大，file_size 应增大'