import pytest


class TestAdmin:
    def test_admin_requires_login(self, client, app):
        response = client.get('/admin', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_admin_accessible_when_logged_in(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/admin', follow_redirects=True)
        assert response.status_code == 200