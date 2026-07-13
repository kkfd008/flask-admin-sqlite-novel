import os
import pytest


def create_test_app():
    app = __import__('app').create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
    })
    return app


@pytest.fixture(scope='function')
def app():
    app = create_test_app()
    with app.app_context():
        from app.models import db
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    return app.test_cli_runner()