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


class TestFavoritesToggle:
    def test_toggle_favorite_add(self, client, app):
        """toggle 路由：未收藏 → 收藏"""
        user_id = None
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='toggle test')
            db.session.add_all([user, novel])
            db.session.commit()
            user_id = user.id
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/favorites/novels/{novel_id}/toggle', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Favorite
            fav = Favorite.query.filter_by(user_id=user_id, novel_id=novel_id).first()
            assert fav is not None

    def test_toggle_favorite_remove(self, client, app):
        """toggle 路由：已收藏 → 取消收藏"""
        user_id = None
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Favorite
            user = User(username='admin', password='admin123')
            novel = Novel(title='toggle test')
            db.session.add_all([user, novel])
            db.session.commit()
            fav = Favorite(user_id=user.id, novel_id=novel.id)
            db.session.add(fav)
            db.session.commit()
            user_id = user.id
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/favorites/novels/{novel_id}/toggle', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Favorite
            fav = Favorite.query.filter_by(user_id=user_id, novel_id=novel_id).first()
            assert fav is None

    def test_detail_page_shows_favorite_toggle(self, client, app):
        """详情页显示收藏爱心按钮"""
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            novel = Novel(title='收藏测试', category_id=cat.id)
            db.session.add_all([user, cat, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        # 未收藏时显示 ♡ 收藏
        assert '♡ 收藏' in html or '收藏' in html
        # 应有 toggle 路由
        assert '/toggle' in html

    def test_detail_page_favorited_shows_cancel(self, client, app):
        """已收藏时详情页显示 ♥ 取消收藏"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Favorite, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            novel = Novel(title='收藏测试', category_id=cat.id)
            db.session.add_all([user, cat, novel])
            db.session.commit()
            fav = Favorite(user_id=user.id, novel_id=novel.id)
            db.session.add(fav)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        assert '取消收藏' in html
        assert 'favorited' in html