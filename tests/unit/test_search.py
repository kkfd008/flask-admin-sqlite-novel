import pytest


class TestSearch:
    def test_search_keyword(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='search-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='The sword of destiny', order=1)
            db.session.add(ch)
            db.session.commit()

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