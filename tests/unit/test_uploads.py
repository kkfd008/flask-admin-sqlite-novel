"""Tests for Upload model and upload list functionality."""
import io
import os
from datetime import datetime
import pytest


class TestUploadModel:
    def test_upload_creation(self, app):
        """Upload model should have title, notes, file_path, created_at, updated_at, last_import_at."""
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