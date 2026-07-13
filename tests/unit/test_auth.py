import pytest


class TestAuthLogin:
    def test_login_success(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'dashboard' in data or 'novel' in data.lower()

    def test_login_failure_wrong_password(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        response = client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpass'
        }, follow_redirects=True)

        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'login' in data.lower()

    def test_login_failure_empty_username(self, client):
        response = client.post('/login', data={
            'username': '',
            'password': 'admin123'
        }, follow_redirects=True)

        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'login' in data.lower()

    def test_logout(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

        response = client.get('/logout', follow_redirects=True)

        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'login' in data.lower()


class TestAuthPermission:
    def test_unauthenticated_access_redirect(self, client):
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_unauthenticated_access_novels_redirect(self, client):
        response = client.get('/novels', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_authenticated_access_allowed(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200