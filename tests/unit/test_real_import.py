import pytest
import os


class TestRealNovelImport:
    def test_import_real_novel_file(self, app, client):
        """使用真实小说文件导入，验证章节数、字数、内容正确"""
        cat_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第[零一二三四五六七八九十百千万\\d]+章.*$', category='系统', enabled=True, sort_order=0)
            cat = Category(name='都市', sort_order=1)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 上传真实小说文件
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                               'uploads', '重生80年代：我的首富兄弟.txt')
        with open(filepath, 'rb') as f:
            data = {'file': (f, '重生80年代：我的首富兄弟.txt')}
            response = client.post('/novels/import', data=data, content_type='multipart/form-data',
                                   follow_redirects=True)
        assert response.status_code == 200

        # Step2: 选择规则
        response = client.post('/novels/import/step2', data={'rule_ids': str(rule_id)},
                               follow_redirects=True)
        assert response.status_code == 200

        # Step4: 提交保存
        response = client.post('/novels/import/step4', data={
            'title': '重生80年代：我的首富兄弟',
            'author': '呀宝贝',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.filter_by(title='重生80年代：我的首富兄弟').first()
            assert novel is not None, '小说应成功导入'
            assert novel.author == '呀宝贝'
            assert novel.category_id == cat_id

            total_chapters = Chapter.query.filter_by(novel_id=novel.id).count()
            # 文件开头有推荐介绍，会作为序章
            # 然后从第1章到第627章，总计最少 627 + 1 = 628 章
            assert total_chapters >= 627, f'至少应有 627 章，实际 {total_chapters}'
            assert novel.chapter_count == total_chapters

            # 第一章可能是序章（如果有前言）
            first = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).first()
            assert first is not None
            assert first.word_count > 0
            assert len(first.content) > 0

            # 找到真正的第一章（正文第一章）
            first_body = Chapter.query.filter_by(novel_id=novel.id)\
                .filter(Chapter.title.contains('第1章'))\
                .first()
            assert first_body is not None, '正文第一章应存在'

            # 验证最后一章
            last = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order.desc()).first()
            assert last is not None
            assert '完结章' in last.title
            assert last.word_count > 0

            # 验证所有章节字数均不为0
            chapters = Chapter.query.filter_by(novel_id=novel.id).all()
            zero_word_count = [c for c in chapters if c.word_count == 0]
            assert len(zero_word_count) == 0, f'有 {len(zero_word_count)} 章字数为0'

            zero_content = [c for c in chapters if not c.content or len(c.content.strip()) == 0]
            assert len(zero_content) == 0, f'有 {len(zero_content)} 章内容为空'

            # 验证总字数
            computed_total = sum(c.word_count for c in chapters)
            assert novel.word_count == computed_total, f'总字数: {novel.word_count} != {computed_total}'
            assert novel.word_count > 100000  # 一个正常小说至少10万字

            # 验证章节顺序连续
            orders = sorted([c.order for c in chapters])
            assert orders == list(range(1, len(chapters) + 1)), '章节顺序应连续从1开始'

    def test_import_real_novel_step3_preview(self, app, client):
        """真实小说导入 step3 预览页应显示章节列表"""
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第[零一二三四五六七八九十百千万\\d]+章.*$', category='系统', enabled=True, sort_order=0)
            cat = Category(name='都市', sort_order=1)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                               'uploads', '重生80年代：我的首富兄弟.txt')
        with open(filepath, 'rb') as f:
            data = {'file': (f, '重生80年代：我的首富兄弟.txt')}
            client.post('/novels/import', data=data, content_type='multipart/form-data',
                        follow_redirects=True)

        response = client.post('/novels/import/step2', data={'rule_ids': str(rule_id)},
                               follow_redirects=True)
        html = response.data.decode('utf-8')

        # step3 预览页应显示部分章节标题
        assert '第1章' in html, f'预览页应显示章节标题，实际: {html[:500]}'
        assert '第2章' in html
        assert '预览' in html or '识别' in html or '第三步' in html

        # 确认没有退回 step1
        assert '第一步' not in html