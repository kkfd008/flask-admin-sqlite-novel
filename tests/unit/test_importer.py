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
            'mode': 'manual',
            'custom_pattern': '^节\\d+',
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '节1' in html, f'自定义规则应匹配章节，实际: {html[:500]}'
        assert '节2' in html

    def test_step3_session_persists_with_many_chapters(self, client, app):
        """大量章节时 session 不应丢失，step3 应正常显示预览"""
        with app.app_context():
            from app.models import db, User, ChapterRule
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            db.session.add_all([user, rule])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 生成大量章节（模拟 session cookie 超过 4KB 限制）
        lines = []
        for i in range(1, 201):
            lines.append(f'第{i}章 章节标题{"很" * 30}')
            lines.append(f'这是第{i}章的内容{"。" * 40}')
        content = '\n'.join(lines)

        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)

        # 提交 step2
        response = client.post('/novels/import/step2', data={}, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 应显示预览页，而非退回 step1
        assert '第1章' in html, f'大量章节时 session 不应丢失，实际: {html[:500]}'
        assert '第200章' in html
        assert '第三步' in html or '预览' in html or '识别' in html


class TestStep3DeleteMerge:
    def test_delete_chapter_merges_content_to_previous(self, client, app):
        """When a chapter is deleted in step3, its content merges into the previous chapter."""
        cat_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 中间\n这是第二章内容\n第3章 结束\n这是第三章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(rule_id)}, follow_redirects=True)

        # 删除第2章（index 1）
        response = client.post('/novels/import/step3', data={'delete_index': '1'}, follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # 第2章标题应被移除
        assert '第2章' not in html or '中间' not in html

        # 提交确认
        response = client.post('/novels/import/step4', data={
            'title': '测试小说',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Chapter
            chapters = Chapter.query.order_by(Chapter.order).all()
            assert len(chapters) == 2, f'删除第2章后应有2章，实际: {len(chapters)}'

            # 第1章内容应包含原第1章 + 第2章的内容
            assert '这是第一章内容' in chapters[0].content
            assert '这是第二章内容' in chapters[0].content, f'第1章应包含第2章内容, got: {chapters[0].content[:100]}'

            # 第2章（原第3章）内容应只有原第3章内容
            assert '这是第三章内容' in chapters[1].content

    def test_delete_first_chapter_removes_it(self, client, app):
        """Deleting the first chapter just removes it, no merge."""
        cat_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 继续\n这是第二章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(rule_id)}, follow_redirects=True)

        # 删除第1章（index 0）
        client.post('/novels/import/step3', data={'delete_index': '0'}, follow_redirects=True)

        response = client.post('/novels/import/step4', data={
            'title': '测试小说',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Chapter
            chapters = Chapter.query.order_by(Chapter.order).all()
            assert len(chapters) == 1, f'删除第1章后应有1章，实际: {len(chapters)}'
            assert '这是第二章内容' in chapters[0].content

    def test_step4_title_defaults_to_filename(self, client, app):
        """小说标题默认携带上传文件名"""
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是内容\n第2章 继续\n更多内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), '剑来.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={}, follow_redirects=True)

        response = client.get('/novels/import/step4', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 标题输入框应默认填文件名
        assert '剑来' in html, f'标题应默认显示文件名，实际: {html[:500]}'

    def test_step4_shows_categories_as_radio(self, client, app):
        """分类全部显示为单选框，非必选"""
        cat_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={}, follow_redirects=True)

        response = client.get('/novels/import/step4', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 分类应以 radio 形式显示，非必选
        assert '武侠' in html
        assert f'value="{cat_id}"' in html, f'radio 应有 value="{cat_id}"'
        assert 'type="radio"' in html, '分类应为 radio 单选框'
        import re as _re
        cat_input = _re.search(r'<input[^>]*name="category_id"[^>]*>', html)
        assert cat_input is not None, '应有 category_id radio'
        assert 'required' not in cat_input.group(), '分类 radio 不应为必选'

    def test_step4_submit_creates_novel(self, client, app):
        """提交 step4 应成功创建小说，不报 AttributeError"""
        cat_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 开始\n这是第一章内容\n第2章 继续\n这是第二章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={}, follow_redirects=True)

        # 提交 step4
        response = client.post('/novels/import/step4', data={
            'title': '测试小说',
            'author': '测试作者',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 应跳转到小说详情页
        assert '测试小说' in html, f'应显示小说详情，实际: {html[:500]}'
        assert '测试作者' in html

        with app.app_context():
            from app.models import Novel
            novel = Novel.query.filter_by(title='测试小说').first()
            assert novel is not None, '小说应成功创建'
            assert novel.author == '测试作者'
            assert novel.category_id == cat_id
            assert novel.chapter_count == 2

    def test_step4_chapter_content_and_word_count(self, app, client):
        """导入后章节应有内容且 word_count 不为 0"""
        cat_id = None
        sys_rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            sys_rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 模拟真实小说内容
        content = '第1章 开始\n这是第一章内容，有很多文字。\n第二行内容。\n第2章 继续\n这是第二章内容，也有很多文字。\n第二行。'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(sys_rule_id)}, follow_redirects=True)

        response = client.post('/novels/import/step4', data={
            'title': '测试小说',
            'author': '作者',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.filter_by(title='测试小说').first()
            assert novel is not None
            assert novel.chapter_count == 2

            chapters = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).all()
            assert len(chapters) == 2

            for ch in chapters:
                assert ch.word_count > 0, f'章节 {ch.title} 的 word_count 应为正数，实际为 {ch.word_count}'
                assert ch.content, f'章节 {ch.title} 应有内容'
                assert len(ch.content) > 0, f'章节 {ch.title} 的内容不应为空'

            # 总字数应为各章字数之和
            assert novel.word_count == sum(c.word_count for c in chapters)

    def test_step4_import_uses_actual_content_not_chapter_titles(self, app, client):
        """导入时使用 re.split 拆分实际内容，而非仅用 session 中的章节标题"""
        cat_id = None
        sys_rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章.*$', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            sys_rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 标题\n第一章具体内容\n第2章 标题\n第二章具体内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(sys_rule_id)}, follow_redirects=True)

        client.post('/novels/import/step4', data={
            'title': '测试小说2',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.filter_by(title='测试小说2').first()
            chapters = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).all()

            assert len(chapters) == 2
            assert chapters[0].content.strip() == '第一章具体内容', f'章节内容应为正文，实际: {chapters[0].content!r}'
            assert chapters[1].content.strip() == '第二章具体内容'
            assert chapters[0].word_count == len('第一章具体内容')
            assert chapters[1].word_count == len('第二章具体内容')

    def test_step4_import_with_preamble(self, app, client):
        """有前导文本时，导入创建序章"""
        cat_id = None
        sys_rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第\\d+章', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            sys_rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '前言内容\n这是前言\n第1章 开始\n第一章内容\n第2章 继续\n第二章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(sys_rule_id)}, follow_redirects=True)

        client.post('/novels/import/step4', data={
            'title': '有前言的小说',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.filter_by(title='有前言的小说').first()
            chapters = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).all()

            assert len(chapters) == 3  # 序章 + 2 章
            assert chapters[0].title == '序章'
            assert '前言' in chapters[0].content
            assert chapters[0].word_count > 0

    def test_re_split_handles_none_elements(self, app):
        """re.split 返回 None 元素时不应抛出 AttributeError"""
        import re
        # 模拟默认规则 pattern 被 step2 组合后 step4 再包裹的情况
        default_pattern = '^第[零一二三四五六七八九十百千万\\d]+章.*$'
        combined = f'(?:{default_pattern})'
        wrapped = f'({combined})'

        # 各种可能的内容
        contents = [
            '第1章 开始\n这是内容\n第2章 继续\n更多',
            '第1章\n内容',
            '\n第1章 开始\n内容',
            '第1章 开始\r\n这是内容\r\n第2章 继续\r\n更多',  # CRLF
            '第1章 开始\n第2章 继续',  # 连续章节
            '前言\n第1章 开始\n内容',  # 前导文本
        ]

        for content in contents:
            parts = re.split(wrapped, content, flags=re.MULTILINE)
            for i, p in enumerate(parts):
                if p is None:
                    # re.split 返回了 None — 这是 bug 的根源
                    pytest.fail(f're.split returned None at index {i} for content: {content!r}')
                # 验证 .strip() 不会报错
                p.strip()