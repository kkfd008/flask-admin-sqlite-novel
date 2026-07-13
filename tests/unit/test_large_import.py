import pytest
import io


def generate_chinese_number(n):
    """生成中文数字 一到七百"""
    units = ['', '十', '百', '千', '万']
    digits = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    result = ''
    i = 0
    while n > 0:
        d = n % 10
        if d != 0:
            result = digits[d] + units[i] + result
        n = n // 10
        i += 1
    if result.startswith('一十'):
        result = result[1:]  # 十一不是一十一
    return result


def generate_large_novel(chapter_count=720, words_per_chapter=3000):
    """生成大体积小说，中文数字章节，每章约指定字数"""
    # 重复文本模板，足够生成约 3000 字（含 ~400 标点）
    paragraph_template = """山不在高，有仙则名。水不在深，有龙则灵。斯是陋室，惟吾德馨。苔痕上阶绿，草色入帘青。谈笑有鸿儒，往来无白丁。可以调素琴，阅金经。无丝竹之乱耳，无案牍之劳形。南阳诸葛庐，西蜀子云亭。孔子云：何陋之有？

离离原上草，一岁一枯荣。野火烧不尽，春风吹又生。远芳侵古道，晴翠接荒城。又送王孙去，萋萋满别情。

天街小雨润如酥，草色遥看近却无。最是一年春好处，绝胜烟柳满皇都。

朱雀桥边野草花，乌衣巷口夕阳斜。旧时王谢堂前燕，飞入寻常百姓家。

烟笼寒水月笼沙，夜泊秦淮近酒家。商女不知亡国恨，隔江犹唱后庭花。

君问归期未有期，巴山夜雨涨秋池。何当共剪西窗烛，却话巴山夜雨时。

云母屏风烛影深，长河渐落晓星沉。嫦娥应悔偷灵药，碧海青天夜夜心。

相见时难别亦难，东风无力百花残。春蚕到死丝方尽，蜡炬成灰泪始干。晓镜但愁云鬓改，夜吟应觉月光寒。蓬山此去无多路，青鸟殷勤为探看。

昨夜星辰昨夜风，画楼西畔桂堂东。身无彩凤双飞翼，心有灵犀一点通。隔座送钩春酒暖，分曹射覆蜡灯红。嗟余听鼓应官去，走马兰台类转蓬。

寒雨连江夜入吴，平明送客楚山孤。洛阳亲友如相问，一片冰心在玉壶。

青海长云暗雪山，孤城遥望玉门关。黄沙百战穿金甲，不破楼兰终不还。

黄河远上白云间，一片孤城万仞山。羌笛何须怨杨柳，春风不度玉门关。

山光悦鸟性，潭影空人心。万籁此都寂，但余钟磬音。

泉声浸着月光，听来格外清晰。那柔曼如提琴者，是草丛中淌过的小溪；那清脆如弹拨者，是石缝间漏下的滴泉；那厚重如倍司轰响者，应为万道细流汇于空谷；那雄浑如铜管齐鸣者，定是激流直下陡壁，飞瀑落下深潭。"""

    content = []
    for i in range(1, chapter_count + 1):
        ch_title = f'第{generate_chinese_number(i)}章\n'
        # 重复模板直到接近目标字数
        chapter_content = ''
        while len(chapter_content) < words_per_chapter:
            chapter_content += paragraph_template
        # 截断到大约目标字数
        chapter_content = chapter_content[:words_per_chapter]
        content.append(ch_title + chapter_content)
    return '\n'.join(content)


class TestLargeImport:
    def test_import_700_chapters_chinese_numbers(self, app, client):
        """导入 700+ 章中文数字标题的小说，每章约 3000 字，验证全部章节正常导入"""
        cat_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第[零一二三四五六七八九十百]+章.*$', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 生成 720 章小说
        novel_content = generate_large_novel(chapter_count=720, words_per_chapter=3000)
        data = {'file': (io.BytesIO(novel_content.encode('utf-8')), '大测试小说.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(rule_id)}, follow_redirects=True)

        response = client.post('/novels/import/step4', data={
            'title': '七百章大测试',
            'author': '测试作者',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.filter_by(title='七百章大测试').first()
            assert novel is not None
            assert novel.chapter_count == 720, f'应该导入 720 章，实际 {novel.chapter_count}'

            total_chapters = Chapter.query.filter_by(novel_id=novel.id).count()
            assert total_chapters == 720, f'章节总数应为 720，实际 {total_chapters}'

            # 抽样验证部分章节字数不为零，内容存在
            sample_chapters = Chapter.query.filter_by(novel_id=novel.id)\
                .order_by(Chapter.order)\
                .limit(10)\
                .all()

            for ch in sample_chapters:
                assert ch.word_count > 0, f'章节 {ch.id} {ch.title} word_count 应为正数，实际 {ch.word_count}'
                assert ch.content and len(ch.content.strip()) > 0, f'章节 {ch.id} {ch.title} 应有内容'
                assert ch.word_count == len(ch.content), f'字数应匹配: {ch.word_count} != {len(ch.content)}'

            # 验证首尾章节
            first = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).first()
            last = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order.desc()).first()
            assert '第一章' in first.title
            assert '第七百二十章' in last.title
            assert first.word_count > 2000
            assert last.word_count > 2000

            # 验证总字数
            total_word_count = sum(ch.word_count for ch in Chapter.query.filter_by(novel_id=novel.id).all())
            assert novel.word_count == total_word_count
            assert total_word_count > 720 * 2000  # 至少一百四十万字

    def test_import_check_punctuation_count(self, app, client):
        """验证导入后章节内容保留标点符号"""
        cat_id = None
        rule_id = None
        with app.app_context():
            from app.models import db, User, ChapterRule, Category
            user = User(username='admin', password='admin123')
            rule = ChapterRule(name='中文数字章节', pattern='^第[零一二三四五六七八九十百]+章.*$', category='系统', enabled=True, sort_order=0)
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, rule, cat])
            db.session.commit()
            cat_id = cat.id
            rule_id = rule.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 构造一章，包含大约 400 个标点
        punctuation_chars = '，。、；：？！“”‘’（）《》〈〉【】——…'
        content = '第一章 标点测试\n'
        # 重复添加带标点文本，直到约 400 标点
        while content.count('，') + content.count('。') + content.count('；') + content.count('：') + content.count('？') + content.count('！') < 400:
            content += '这是一句带标点的话，这里有逗号，这里有句号。这里是问号？这里是感叹号！这里有分号；这里是冒号：这里引号“里面”，还有括号（里面）。'

        data = {'file': (io.BytesIO(content.encode('utf-8')), '标点测试.txt')}
        client.post('/novels/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        client.post('/novels/import/step2', data={'rule_ids': str(rule_id)}, follow_redirects=True)

        client.post('/novels/import/step4', data={
            'title': '标点测试',
            'category_id': str(cat_id),
        }, follow_redirects=True)

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.filter_by(title='标点测试').first()
            assert novel is not None
            chapters = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).all()
            assert len(chapters) == 1
            ch = chapters[0]
            # 统计标点数量
            punctuation_count = sum(1 for c in ch.content if c in '，。、；：？！“”‘’（）')
            assert punctuation_count >= 350, f'应该有约 400 个标点，实际 {punctuation_count}'
            # 验证内容完整
            assert ch.word_count == len(ch.content)