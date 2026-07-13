import pytest


class TestCategoriesCRUD:
    def test_create_category(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post('/categories/create', data={
            'name': 'xuanhuan',
            'description': 'xuanhuan novel category',
            'sort_order': 1
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Category
            category = Category.query.filter_by(name='xuanhuan').first()
            assert category is not None
            assert category.name == 'xuanhuan'
            assert category.description == 'xuanhuan novel category'
            assert category.sort_order == 1

    def test_read_category(self, client, app):
        with app.app_context():
            from app.models import db, User, Category
            user = User(username='admin', password='admin123')
            cat1 = Category(name='xuanhuan', description='xuanhuan novel')
            cat2 = Category(name='kehuan', description='kehuan novel')
            db.session.add_all([user, cat1, cat2])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/categories', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'xuanhuan' in data
        assert 'kehuan' in data

    def test_update_category(self, client, app):
        category_id = None
        
        with app.app_context():
            from app.models import db, User, Category
            user = User(username='admin', password='admin123')
            category = Category(name='xuanhuan', description='original desc')
            db.session.add_all([user, category])
            db.session.commit()
            category_id = category.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/categories/{category_id}/edit', data={
            'name': 'xuanhuan-update',
            'description': 'updated description',
            'sort_order': 2
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Category
            updated = Category.query.get(category_id)
            assert updated.name == 'xuanhuan-update'
            assert updated.description == 'updated description'
            assert updated.sort_order == 2

    def test_delete_category(self, client, app):
        category_id = None
        novel_id = None
        
        with app.app_context():
            from app.models import db, User, Category, Novel
            user = User(username='admin', password='admin123')
            category = Category(name='xuanhuan')
            db.session.add_all([user, category])
            db.session.commit()
            
            novel = Novel(title='test novel', category_id=category.id)
            db.session.add(novel)
            db.session.commit()
            
            category_id = category.id
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/categories/{category_id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Category, Novel
            assert Category.query.get(category_id) is None
            updated_novel = Novel.query.get(novel_id)
            assert updated_novel.category_id is None