import pytest


class TestFavoritesCRUD:
    def test_favorite_novel(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            user_id = user.id
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/favorites/novels/{novel_id}/favorite', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Favorite
            fav = Favorite.query.filter_by(user_id=user_id, novel_id=novel_id).first()
            assert fav is not None

    def test_unfavorite_novel(self, client, app):
        user_id = None
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Favorite
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            fav = Favorite(user_id=user.id, novel_id=novel.id)
            db.session.add(fav)
            db.session.commit()
            user_id = user.id
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/favorites/novels/{novel_id}/unfavorite', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Favorite
            fav = Favorite.query.filter_by(user_id=user_id, novel_id=novel_id).first()
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

        response = client.get('/favorites/', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'test novel' in data
        assert 'test novel 2' not in data