import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Category
from app.utils import init_default_rules


def init_database():
    """初始化数据库：创建表、默认用户、默认规则"""
    # 确保目录存在
    os.makedirs('instance', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'novel.db')
    app = create_app({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
    })

    with app.app_context():
        # 1. 创建所有数据表
        db.create_all()
        print('[OK] 数据表创建完成')

        # 2. 创建默认管理员用户
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin123')
            db.session.add(admin)
            db.session.commit()
            print('[OK] 默认管理员创建完成 (admin / admin123)')
        else:
            print('[SKIP] 管理员用户已存在')

        # 3. 初始化 8 大类默认章节规则
        init_default_rules()
        print('[OK] 默认章节规则初始化完成')

        # 4. 创建默认分类
        default_categories = ['玄幻', '武侠', '都市', '历史', '科幻', '言情', '悬疑', '其它']
        for name in default_categories:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name))
        db.session.commit()
        print('[OK] 默认分类创建完成')

        print('\n初始化完成！运行 python run.py 启动服务')


if __name__ == '__main__':
    init_database()