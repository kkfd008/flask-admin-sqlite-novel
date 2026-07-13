import pytest


class TestChapterRulesCRUD:
    def test_create_rule(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post('/rules/create', data={
            'name': 'custom-rule',
            'pattern': '^第\\d+节.*$',
            'description': 'custom chapter rule',
            'enabled': True
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            rule = ChapterRule.query.filter_by(name='custom-rule').first()
            assert rule is not None
            assert rule.pattern == '^第\\d+节.*$'
            assert rule.category == '用户'
            assert rule.enabled is True

    def test_read_rules(self, client, app):
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule1 = ChapterRule(name='rule1', pattern='^rule1$', category='系统', enabled=True)
            rule2 = ChapterRule(name='rule2', pattern='^rule2$', category='用户', enabled=False)
            db.session.add_all([user, rule1, rule2])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/rules', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'rule1' in data
        assert 'rule2' in data

    def test_update_user_rule(self, client, app):
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='rule1', pattern='^rule1$', category='用户')
            db.session.add_all([user, rule])
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/rules/{rule_id}/edit', data={
            'name': 'rule1-updated',
            'pattern': '^updated-rule$',
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            updated = ChapterRule.query.get(rule_id)
            assert updated.name == 'rule1-updated'
            assert updated.pattern == '^updated-rule$'

    def test_update_system_rule_blocked(self, client, app):
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='sys-rule', pattern='^sys$', category='系统')
            db.session.add_all([user, rule])
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/rules/{rule_id}/edit', data={
            'name': 'hacked',
            'pattern': '^hacked$',
            'enabled': False
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            unchanged = ChapterRule.query.get(rule_id)
            assert unchanged.name == 'sys-rule'

    def test_toggle_rule(self, client, app):
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='rule1', pattern='^rule1$', category='系统', enabled=True)
            db.session.add_all([user, rule])
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/rules/{rule_id}/toggle', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            updated = ChapterRule.query.get(rule_id)
            assert updated.enabled is False

        response = client.post(f'/rules/{rule_id}/toggle', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            updated = ChapterRule.query.get(rule_id)
            assert updated.enabled is True

    def test_delete_user_rule(self, client, app):
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='rule1', pattern='^rule1$', category='用户')
            db.session.add_all([user, rule])
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/rules/{rule_id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            assert ChapterRule.query.get(rule_id) is None

    def test_delete_system_rule_blocked(self, client, app):
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='sys-rule', pattern='^sys$', category='系统')
            db.session.add_all([user, rule])
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/rules/{rule_id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            assert ChapterRule.query.get(rule_id) is not None


def test_disabled_system_rule_still_visible(client, app):
    """系统规则禁用后仍然显示在列表中，只是状态变为禁用"""
    rule_id = None
    with app.app_context():
        from app.models import db, User, ChapterRule
        user = User(username='admin', password='admin123')
        rule = ChapterRule(name='可见规则', pattern='^visible$', category='系统', enabled=True)
        db.session.add_all([user, rule])
        db.session.commit()
        rule_id = rule.id

    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

    # 先确认规则在列表中可见
    response = client.get('/rules', follow_redirects=True)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert '可见规则' in data

    # 禁用规则
    client.post(f'/rules/{rule_id}/toggle', follow_redirects=True)

    # 禁用后仍然可见
    response = client.get('/rules', follow_redirects=True)
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert '可见规则' in data, '禁用后的系统规则应该仍然显示在列表中'
    assert '启用' in data, '禁用后的按钮应该显示"启用"'


class TestDefaultRules:
    def test_default_rules_count(self, app):
        with app.app_context():
            from app.models import ChapterRule
            from app.utils import init_default_rules

            init_default_rules()

            rules = ChapterRule.query.all()
            assert len(rules) >= 8

    def test_default_rules_are_system(self, app):
        with app.app_context():
            from app.models import ChapterRule
            from app.utils import init_default_rules

            init_default_rules()

            rules = ChapterRule.query.all()
            for rule in rules:
                assert rule.category == '系统'


class TestNovelChapterRules:
    def test_create_novel_rule(self, client, app):
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel_id}/rules/create', data={
            'pattern': '^custom-novel-rule$',
            'description': 'novel specific rule'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import NovelChapterRule
            rule = NovelChapterRule.query.filter_by(novel_id=novel_id).first()
            assert rule is not None
            assert rule.pattern == '^custom-novel-rule$'

    def test_read_novel_rule(self, client, app):
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, NovelChapterRule
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            novel_id = novel.id

            rule = NovelChapterRule(novel_id=novel_id, pattern='^novel-rule$', description='description')
            db.session.add(rule)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel_id}/rules', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'novel-rule' in data

    def test_update_novel_rule(self, client, app):
        novel_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, Novel, NovelChapterRule
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            novel_id = novel.id

            rule = NovelChapterRule(novel_id=novel_id, pattern='^novel-rule$')
            db.session.add(rule)
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel_id}/rules/{rule_id}/edit', data={
            'pattern': '^updated-novel-rule$',
            'description': 'updated description'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import NovelChapterRule
            updated = NovelChapterRule.query.get(rule_id)
            assert updated.pattern == '^updated-novel-rule$'

    def test_delete_novel_rule(self, client, app):
        novel_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, Novel, NovelChapterRule
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            novel_id = novel.id

            rule = NovelChapterRule(novel_id=novel_id, pattern='^novel-rule$')
            db.session.add(rule)
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel_id}/rules/{rule_id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import NovelChapterRule
            assert NovelChapterRule.query.get(rule_id) is None