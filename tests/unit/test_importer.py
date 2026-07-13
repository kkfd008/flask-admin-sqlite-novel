import pytest
import io


class TestImporter:
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

    def test_import_step1_upload(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        data = {
            'file': (io.BytesIO(b'\xe7\xac\xac\xe4\xb8\x80\xe7\xab\xa0 \xe5\xbc\x80\xe5\xa7\x8b\n'
                               b'\xe8\xbf\x99\xe6\x98\xaf\xe7\xac\xac\xe4\xb8\x80\xe7\xab\xa0\xe5\x86\x85\xe5\xae\xb9\n'
                               b'\xe7\xac\xac\xe4\xba\x8c\xe7\xab\xa0 \xe7\xbb\xa7\xe7\xbb\xad\n'
                               b'\xe8\xbf\x99\xe6\x98\xaf\xe7\xac\xac\xe4\xba\x8c\xe7\xab\xa0\xe5\x86\x85\xe5\xae\xb9'),
                     'test.txt')
        }
        response = client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code == 200

    def test_import_step2_select_rule(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 继续\n这是第二章内容'
        data = {
            'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')
        }
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        response = client.get('/novels/import/step2', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'rule' in data.lower() or 'chinese' in data.lower() or 'chapter' in data.lower()

    def test_import_step3_preview(self, client, app):
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='Chinese', pattern='^第\\d+章', category='chinese-number', enabled=True)
            db.session.add_all([user, rule])
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 继续\n这是第二章内容'
        data = {
            'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')
        }
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        import_response = client.post('/novels/import/step2', data={'rule_id': str(rule_id)}, follow_redirects=True)
        assert import_response.status_code == 200
        data_text = import_response.data.decode('utf-8')
        assert '第1章' in data_text
        assert '第2章' in data_text