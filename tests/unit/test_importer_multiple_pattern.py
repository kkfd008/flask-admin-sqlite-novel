import pytest
import io


class TestImporterMultiplePatternBug:
    """测试多模式匹配 bug：匹配后索引错位，导致只创建了第一个章节"""

    def test_multiple_patterns_correctly_splits(self, app, client):
        """选择多个规则时，应正确拆分所有章节，不丢失内容"""
        cat_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            # 两个不同的模式
            rule1 = ChapterRule(name='第N章', pattern='^第\\d+章.*$', category='系统', enabled=True, sort_order=0)
            rule2 = ChapterRule(name='第N卷', pattern='^第\\d+卷.*$', category='系统', enabled=True, sort_order=1)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule1, rule2, cat])
            db.session.commit()
            cat_id = cat.id
            rule_ids = [str(rule1.id), str(rule2.id)]

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1卷 开始\n内容一\n第2卷 继续\n内容二\n第3章 第三章\n内容三\n第4章 第四章\n内容四'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': rule_ids}, follow_redirects=True)

        client.post('/novels/import/step4', data={
            'title': '多模式测试',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.filter_by(title='多模式测试').first()
            assert novel is not None

            chapters = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).all()

            # 应有 4 章 + 可能序章（这里没有）
            # 因为开头就是章节，parts[0]为空，不创建序章
            assert len(chapters) == 4, f'应为 4 章，实际 {len(chapters)}'
            assert novel.chapter_count == 4

            # 每个章节应有内容，字数不为零
            for i, ch in enumerate(chapters, 1):
                assert ch.word_count > 0, f'第 {i} 章字数应为正'
                assert len(ch.content.strip()) > 0, f'第 {i} 章应有内容'

            # 验证内容分配正确
            assert chapters[0].title.strip().startswith('第1卷')
            assert chapters[1].title.strip().startswith('第2卷')
            assert chapters[2].title.strip().startswith('第3章')
            assert chapters[3].title.strip().startswith('第4章')
            assert '内容一' in chapters[0].content
            assert '内容二' in chapters[1].content
            assert '内容三' in chapters[2].content
            assert '内容四' in chapters[3].content

    def test_pattern_with_capturing_groups_works(self, app, client):
        """模式本身包含捕获组时，导入仍应正常工作（索引不乱）"""
        cat_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            # 模式本身带有分组（用户可能自定义这样的模式）
            rule = ChapterRule(name='带分组模式', pattern='^(第\\d+[章卷]).*$', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        content = '第1章 标题\n第一章内容\n第2章 标题\n第二章内容'
        data = {'file': (io.BytesIO(content.encode('utf-8')), 'test.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(rule_id)}, follow_redirects=True)

        client.post('/novels/import/step4', data={
            'title': '带分组测试',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.filter_by(title='带分组测试').first()
            assert novel is not None

            chapters = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).all()
            assert len(chapters) == 2, f'应为 2 章，实际 {len(chapters)}'
            for ch in chapters:
                assert ch.word_count > 0
                assert len(ch.content.strip()) > 0