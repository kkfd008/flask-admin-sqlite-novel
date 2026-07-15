#!/usr/bin/env python3
"""批量上传小说文件到上传保存目录和上传表。

用法:
    python tool/batch_upload.py <源目录路径>

    源目录中的所有 .txt 文件会被上传到 uploads/YYMMDD/ 目录，
    并在 Upload 表中创建对应记录。重名文件计入失败。

示例:
    python tool/batch_upload.py ~/novels/
"""
import os
import sys
import shutil
from datetime import datetime

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Upload

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'instance', 'novel.db')


def batch_upload(source_dir):
    if not os.path.isdir(source_dir):
        print(f'错误: 源目录不存在: {source_dir}')
        sys.exit(1)

    # 收集所有 .txt 文件
    txt_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.txt')]
    if not txt_files:
        print('未找到 .txt 文件')
        return

    print(f'找到 {len(txt_files)} 个 .txt 文件\n')

    app = create_app({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{DB_PATH}',
    })
    success = []
    failed = []

    with app.app_context():
        for filename in txt_files:
            raw_name = os.path.splitext(filename)[0]
            original_ext = os.path.splitext(filename)[1]
            saved_filename = raw_name + original_ext
            src_path = os.path.join(source_dir, filename)

            # 检查重名
            existing = Upload.query.filter_by(title=raw_name).first()
            if existing:
                failed.append((filename, '文件重名：上传表中已存在同名记录'))
                print(f'  ✗ {filename} — 跳过（重名）')
                continue

            # 复制文件到日期目录
            date_dir = datetime.now().strftime('%y%m%d')
            date_folder = os.path.join(UPLOAD_FOLDER, date_dir)
            os.makedirs(date_folder, exist_ok=True)

            dest_path = os.path.join(date_folder, saved_filename)
            try:
                shutil.copy2(src_path, dest_path)
            except OSError as e:
                failed.append((filename, f'文件复制失败: {e}'))
                print(f'  ✗ {filename} — 复制失败')
                continue

            file_size = os.path.getsize(dest_path)
            rel_path = os.path.join('uploads', date_dir, saved_filename)

            upload = Upload(title=raw_name, file_path=rel_path, file_size=file_size)
            db.session.add(upload)
            db.session.commit()

            success.append(filename)
            print(f'  ✓ {filename}')

    # 输出汇总
    print(f'\n{"=" * 50}')
    print(f'上传完成: 成功 {len(success)} 个, 失败 {len(failed)} 个')
    print(f'{"=" * 50}')

    if failed:
        print('\n失败详情:')
        for name, reason in failed:
            print(f'  ✗ {name} — {reason}')

    if success:
        print('\n成功列表:')
        for name in success:
            print(f'  ✓ {name}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python tool/batch_upload.py <源目录路径>')
        sys.exit(1)

    batch_upload(sys.argv[1])