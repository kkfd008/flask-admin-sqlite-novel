import pytest


class TestTagsCRUD:
    def test_create_tag(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post('/tags/create', data={
            'name': 'shuangwen',
            'color': '#FF6600'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Tag
            tag = Tag.query.filter_by(name='shuangwen').first()
            assert tag is not None
            assert tag.name == 'shuangwen'
            assert tag.color == '#FF6600'

    def test_read_tags(self, client, app):
        with app.app_context():
            from app.models import db, User, Tag
            user = User(username='admin', password='admin123')
            tag1 = Tag(name='shuangwen', color='#FF6600')
            tag2 = Tag(name='wanjie', color='#00CC00')
            db.session.add_all([user, tag1, tag2])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/tags', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'shuangwen' in data
        assert 'wanjie' in data

    def test_update_tag(self, client, app):
        with app.app_context():
            from app.models import db, User, Tag
            user = User(username='admin', password='admin123')
            tag = Tag(name='shuangwen', color='#FF6600')
            db.session.add_all([user, tag])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/tags/{tag.id}/edit', data={
            'name': 'super-shuangwen',
            'color': '#FF0000'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Tag
            updated = Tag.query.get(tag.id)
            assert updated.name == 'super-shuangwen'
            assert updated.color == '#FF0000'

    def test_delete_tag(self, client, app):
        with app.app_context():
            from app.models import db, User, Tag, Novel
            user = User(username='admin', password='admin123')
            tag = Tag(name='shuangwen')
            novel = Novel(title='test novel')
            novel.tags.append(tag)
            db.session.add_all([user, tag, novel])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/tags/{tag.id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Tag, Novel
            assert Tag.query.get(tag.id) is None
            updated_novel = Novel.query.get(novel.id)
            assert len(updated_novel.tags) == 0


class TestNovelTagsRelation:
    def test_novel_add_tags(self, client, app):
        with app.app_context():
            from app.models import db, User, Tag, Novel
            user = User(username='admin', password='admin123')
            tag1 = Tag(name='shuangwen')
            tag2 = Tag(name='wanjie')
            novel = Novel(title='test novel')
            db.session.add_all([user, tag1, tag2, novel])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/tags', data={
            'tag_ids': [tag1.id, tag2.id]
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel
            updated_novel = Novel.query.get(novel.id)
            assert len(updated_novel.tags) == 2

    def test_novel_remove_tags(self, client, app):
        with app.app_context():
            from app.models import db, User, Tag, Novel
            user = User(username='admin', password='admin123')
            tag1 = Tag(name='shuangwen')
            tag2 = Tag(name='wanjie')
            novel = Novel(title='test novel')
            novel.tags.append(tag1)
            novel.tags.append(tag2)
            db.session.add_all([user, tag1, tag2, novel])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/tags', data={
            'tag_ids': [tag1.id]
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel
            updated_novel = Novel.query.get(novel.id)
            assert len(updated_novel.tags) == 1
            assert updated_novel.tags[0].name == 'shuangwen'

    def test_novel_multiple_tags(self, app):
        with app.app_context():
            from app.models import db, User, Tag, Novel
            user = User(username='admin', password='admin123')
            tags = [Tag(name=f'tag{i}') for i in range(5)]
            novel = Novel(title='test novel')
            for tag in tags:
                novel.tags.append(tag)
            db.session.add_all([user] + tags + [novel])
            db.session.commit()

            retrieved_novel = Novel.query.get(novel.id)
            assert len(retrieved_novel.tags) == 5