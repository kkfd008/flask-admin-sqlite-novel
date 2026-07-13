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
        assert 'text/plain' in response.headers['Content-Type']
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