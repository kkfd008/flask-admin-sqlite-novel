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

    # 默认 expire_on_commit=True 会在 commit 后过期所有属性；测试常在嵌套
    # app_context 结束后仍读取这些实例（此时已分离），从而抛出
    # DetachedInstanceError。关闭过期后，已加载属性在分离状态下仍可读取。
    from app import db
    db.session.session_factory.configure(expire_on_commit=False)

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