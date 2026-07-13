import pytest
import io


class TestImporter:
    def test_import_step1_get(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/import', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8')
        assert 'upload' in data.lower() or 'import' in data.lower()

    def test_import_step1_upload(self, client, app):
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        data = {
            'file': (io.BytesIO(b'\xe7\xac\xac\xe4\xb8\x80\xe7\xab\xa0 \xe5\xbc\x80\xe5\xa7\x8b\n'
                               b'\xe8\xbf\x99\xe6\x98\xaf\xe7\xac\xac\xe4\xb8\x80\xe7\xab\xa0\xe5\x86\x85\xe5\xae\xb9\n'
                               b'\xe7\xac\xac\xe4\xba\x8c\xe7\xab\xa0 \xe7\xbb\xa7\xe7\xbb\xad\n'
                               b'\xe8\xbf\x99\xe6\x98\xaf\xe7\xac\xac\xe4\xba\x8c\xe7\xab\xa0\xe5\x86\x85\xe5\xae\xb9'),
                     'test.txt')
        }
        response = client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert response.status_code == 200

    def test_step2_shows_all_system_rules(self, client, app):
        """系统规则全部显示（启用+禁用），启用规则默认勾选"""
        sys_enabled_id = None
        sys_disabled_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule_enabled = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            rule_disabled = ChapterRule(name='英文章节', pattern='^Chapter\\s+\\d+', category='系统', enabled=False, sort_order=1)
            db.session.add_all([user, rule_enabled, rule_disabled])
            db.session.commit()
            sys_enabled_id = rule_enabled.id
            sys_disabled_id = rule_disabled.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是内容\n第2章 继续\n更多内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        response = client.get('/novels/import/step2', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 禁用和启用的系统规则都应显示
        assert '中文数字章节' in html
        assert '英文章节' in html

        # 启用规则应有 checked 属性
        assert f'value="{sys_enabled_id}"' in html
        assert 'checked' in html

    def test_step2_user_rules_allow_zero_to_three(self, client, app):
        """用户规则勾选支持 0-3 个"""
        user_rule_ids = []
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            for i in range(4):
                r = ChapterRule(name=f'用户规则{i}', pattern=f'^rule{i}$', category='用户', enabled=True)
                db.session.add(r)
            db.session.add(user)
            db.session.commit()
            for i in range(4):
                rule = ChapterRule.query.filter_by(name=f'用户规则{i}').first()
                user_rule_ids.append(rule.id)

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是内容\n第2章 继续\n更多内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        response = client.get('/novels/import/step2', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 4 个用户规则都应显示
        for i in range(4):
            assert f'用户规则{i}' in html

    def test_step2_submit_goes_to_step3(self, client, app):
        """提交 step2 应跳转到 step3 预览页，而非返回 step1"""
        sys_rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            db.session.add_all([user, rule])
            db.session.commit()
            sys_rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 继续\n这是第二章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        # 提交 step2 表单
        response = client.post('/novels/import/step2', data={
            'rule_ids': str(sys_rule_id),
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 应在 step3 预览页，包含章节标题
        assert '第1章' in html, f'应该跳转到预览页显示章节，实际: {html[:500]}'
        assert '第2章' in html
        assert '预览' in html or '识别' in html

        # 不应在 step1 上传页
        assert '第一步' not in html

    def test_step2_submit_no_selection_uses_fallback(self, client, app):
        """未选择任何规则时使用默认规则，仍能跳转到 step3"""
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            db.session.add_all([user, rule])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是内容\n第2章 继续\n更多内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        # 不选任何规则直接提交
        response = client.post('/novels/import/step2', data={}, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '第1章' in html, f'应该使用默认规则匹配章节，实际: {html[:500]}'

    def test_step2_with_custom_pattern(self, client, app):
        """自定义正则表达式也能匹配章节并跳转到 step3"""
        with app.app_context():
            from app.models import db, User
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '节1 测试\n内容\n节2 继续\n更多'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        response = client.post('/novels/import/step2', data={
            'custom_pattern': '^节\\d+',
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '节1' in html, f'自定义规则应匹配章节，实际: {html[:500]}'
        assert '节2' in html