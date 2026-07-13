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