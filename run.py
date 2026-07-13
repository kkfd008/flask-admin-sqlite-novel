import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.utils import init_default_rules

# 确保 necessary directories 存在
os.makedirs('instance', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'novel.db')
app = create_app({
    'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_default_rules()
    app.run(host='0.0.0.0', port=5000, debug=True)