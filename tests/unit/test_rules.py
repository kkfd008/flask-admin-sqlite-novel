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
            'category': 'chinese-number',
            'description': 'custom chapter rule',
            'enabled': True
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            rule = ChapterRule.query.filter_by(name='custom-rule').first()
            assert rule is not None
            assert rule.pattern == '^第\\d+节.*$'
            assert rule.category == 'chinese-number'
            assert rule.enabled is True

    def test_read_rules(self, client, app):
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule1 = ChapterRule(name='rule1', pattern='^rule1$', category='chinese-number', enabled=True)
            rule2 = ChapterRule(name='rule2', pattern='^rule2$', category='special-chapter', enabled=False)
            db.session.add_all([user, rule1, rule2])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/rules', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'rule1' in data

    def test_update_rule(self, client, app):
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='rule1', pattern='^rule1$', category='chinese-number')
            db.session.add_all([user, rule])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/rules/{rule.id}/edit', data={
            'name': 'rule1-updated',
            'pattern': '^updated-rule$',
            'category': 'special-chapter',
            'enabled': False
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            updated = ChapterRule.query.get(rule.id)
            assert updated.name == 'rule1-updated'
            assert updated.pattern == '^updated-rule$'
            assert updated.enabled is False

    def test_toggle_rule(self, client, app):
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='rule1', pattern='^rule1$', category='chinese-number', enabled=True)
            db.session.add_all([user, rule])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/rules/{rule.id}/toggle', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            updated = ChapterRule.query.get(rule.id)
            assert updated.enabled is False

        response = client.post(f'/rules/{rule.id}/toggle', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            updated = ChapterRule.query.get(rule.id)
            assert updated.enabled is True

    def test_delete_rule(self, client, app):
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='rule1', pattern='^rule1$', category='chinese-number')
            db.session.add_all([user, rule])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/rules/{rule.id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import ChapterRule
            assert ChapterRule.query.get(rule.id) is None


class TestDefaultRules:
    def test_default_rules_count(self, app):
        with app.app_context():
            from app.models import ChapterRule
            from app.utils import init_default_rules

            init_default_rules()

            rules = ChapterRule.query.all()
            assert len(rules) >= 8

    def test_default_rules_categories(self, app):
        with app.app_context():
            from app.models import ChapterRule
            from app.utils import init_default_rules

            init_default_rules()

            categories = set([r.category for r in ChapterRule.query.all()])
            expected_categories = {'chinese-number', 'special-chapter', 'separator', 'english-number', 'special-symbol', 'pure-number', 'section-read', 'volume-part'}
            assert categories >= expected_categories


class TestNovelChapterRules:
    def test_create_novel_rule(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/rules/create', data={
            'pattern': '^custom-novel-rule$',
            'description': 'novel specific rule'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import NovelChapterRule
            rule = NovelChapterRule.query.filter_by(novel_id=novel.id).first()
            assert rule is not None
            assert rule.pattern == '^custom-novel-rule$'

    def test_read_novel_rule(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, NovelChapterRule
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            
            rule = NovelChapterRule(novel_id=novel.id, pattern='^novel-rule$', description='description')
            db.session.add(rule)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel.id}/rules', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'novel-rule' in data

    def test_update_novel_rule(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, NovelChapterRule
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            
            rule = NovelChapterRule(novel_id=novel.id, pattern='^novel-rule$')
            db.session.add(rule)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/rules/{rule.id}/edit', data={
            'pattern': '^updated-novel-rule$',
            'description': 'updated description'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import NovelChapterRule
            updated = NovelChapterRule.query.get(rule.id)
            assert updated.pattern == '^updated-novel-rule$'

    def test_delete_novel_rule(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, NovelChapterRule
            user = User(username='admin', password='admin123')
            novel = Novel(title='test novel')
            db.session.add_all([user, novel])
            db.session.commit()
            
            rule = NovelChapterRule(novel_id=novel.id, pattern='^novel-rule$')
            db.session.add(rule)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/rules/{rule.id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import NovelChapterRule
            assert NovelChapterRule.query.get(rule.id) is None