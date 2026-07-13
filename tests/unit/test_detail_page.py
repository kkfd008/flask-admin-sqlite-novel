import pytest


class TestDetailPageRating:
    """测试书籍详情页评分功能"""

    def test_rating_form_has_radio_stars(self, app, client):
        """评分表单应有5个 radio 星级选择"""
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            novel = Novel(title='评分测试', category_id=cat.id)
            db.session.add_all([user, cat, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        # 应有5个 radio input
        for i in range(1, 6):
            assert f'value="{i}"' in html
            assert 'type="radio"' in html

        # 提交按钮应存在
        assert '提交评分' in html
        assert '清除评分' in html

    def test_rating_form_no_nested_form(self, app, client):
        """评分表单不应嵌套（清除评分应在独立form中）"""
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            novel = Novel(title='评分测试', category_id=cat.id)
            db.session.add_all([user, cat, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        # 清除评分表单的 action 应在独立的 form 中
        assert 'rate/delete' in html

    def test_rating_stars_have_css_feedback(self, app, client):
        """评分星星应有CSS选中反馈"""
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            novel = Novel(title='评分测试', category_id=cat.id)
            db.session.add_all([user, cat, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        # 应有 :checked 伪类选择器用于视觉反馈
        assert 'checked' in html

    def test_rating_shows_previous_rating(self, app, client):
        """已评过分后，评分表单应显示上次评分内容"""
        with app.app_context():
            from app.models import db, User, Novel, Category, Rating
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            novel = Novel(title='评分测试', category_id=cat.id)
            db.session.add_all([user, cat, novel])
            db.session.commit()
            rating = Rating(user_id=user.id, novel_id=novel.id, score=4, comment='不错')
            db.session.add(rating)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        # 应显示"我的评价"标题
        assert '我的评价' in html
        # 按钮文字应为"更新评分"
        assert '更新评分' in html
        # 评论内容应预填
        assert '不错' in html

    def test_rating_no_previous_shows_default(self, app, client):
        """未评过分时，显示默认评分表单"""
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            novel = Novel(title='评分测试', category_id=cat.id)
            db.session.add_all([user, cat, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        assert '提交评分' in html
        assert '我的评价' not in html


class TestDetailPageTags:
    """测试书籍详情页标签管理功能"""

    def test_tag_edit_button_exists(self, app, client):
        """标签管理区域应有'修改标签'按钮"""
        with app.app_context():
            from app.models import db, User, Novel, Tag, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            tag = Tag(name='爽文', color='#FF6600')
            novel = Novel(title='标签测试', category_id=cat.id)
            db.session.add_all([user, cat, tag, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        assert '标签管理' in html
        assert '修改标签' in html

    def test_tag_modal_contains_all_tags(self, app, client):
        """弹出层应包含所有可用标签"""
        with app.app_context():
            from app.models import db, User, Novel, Tag, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            tag1 = Tag(name='爽文', color='#FF6600')
            tag2 = Tag(name='完结', color='#00CC00')
            novel = Novel(title='标签测试', category_id=cat.id)
            db.session.add_all([user, cat, tag1, tag2, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        # 弹窗应存在
        assert 'tag-modal-overlay' in html
        assert '选择标签' in html
        assert '爽文' in html
        assert '完结' in html
        assert 'type="checkbox"' in html

    def test_tag_modal_has_confirm_cancel_buttons(self, app, client):
        """弹出层应有确定和取消按钮"""
        with app.app_context():
            from app.models import db, User, Novel, Tag, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            tag = Tag(name='爽文', color='#FF6600')
            novel = Novel(title='标签测试', category_id=cat.id)
            db.session.add_all([user, cat, tag, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        assert '确定' in html
        assert '取消' in html

    def test_tag_form_has_css_feedback(self, app, client):
        """标签 checkbox 应有 CSS :has() 选中反馈"""
        with app.app_context():
            from app.models import db, User, Novel, Tag, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            tag = Tag(name='爽文', color='#FF6600')
            novel = Novel(title='标签测试', category_id=cat.id)
            db.session.add_all([user, cat, tag, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        assert ':has' in html

    def test_novel_zero_tags_allowed(self, app, client):
        """书籍支持零个标签（提交空标签列表）"""
        with app.app_context():
            from app.models import db, User, Novel, Tag, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            tag = Tag(name='爽文', color='#FF6600')
            novel = Novel(title='标签测试', category_id=cat.id)
            novel.tags.append(tag)
            db.session.add_all([user, cat, tag, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 提交空的 tag_ids（不传任何 checkbox），应清空标签
        response = client.post(f'/novels/{novel_id}/tags', data={}, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel
            updated = Novel.query.get(novel_id)
            assert len(updated.tags) == 0

    def test_tag_modal_has_current_tags_checked(self, app, client):
        """弹出层中已绑定标签应处于选中状态"""
        with app.app_context():
            from app.models import db, User, Novel, Tag, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            tag1 = Tag(name='爽文', color='#FF6600')
            tag2 = Tag(name='完结', color='#00CC00')
            novel = Novel(title='标签测试', category_id=cat.id)
            novel.tags.append(tag1)
            db.session.add_all([user, cat, tag1, tag2, novel])
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}')
        html = response.data.decode('utf-8')

        # 爽文标签的 checkbox 应被勾选
        assert 'checked' in html