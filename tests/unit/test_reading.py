import pytest
import json


class TestReading:
    def test_read_chapter(self, client, app):
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

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel_id}/read/{ch1_id}', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'next' in data.lower() or 'Chapter 2' in data

    def test_save_reading_progress(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='progress-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='Content', order=1)
            db.session.add(ch)
            db.session.commit()
            user_id = user.id
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
            progress = ReadingProgress.query.filter_by(user_id=user_id, novel_id=novel_id).first()
            assert progress is not None
            assert progress.chapter_id == chapter_id
            assert progress.scroll_position == 300

    def test_add_bookmark(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, Chapter
            user = User(username='admin', password='admin123')
            novel = Novel(title='bookmark-test')
            db.session.add_all([user, novel])
            db.session.commit()
            ch = Chapter(novel_id=novel.id, title='Chapter 1', content='Content', order=1)
            db.session.add(ch)
            db.session.commit()
            user_id = user.id
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
            bm = Bookmark.query.filter_by(user_id=user_id, novel_id=novel_id).first()
            assert bm is not None
            assert bm.title == 'my bookmark'

    def test_delete_bookmark(self, client, app):
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