#!/usr/bin/env python3
"""批量上传小说文件到上传保存目录和上传表。

用法:
    python batch_upload.py -d <源目录> [--depth N] [--force] [--force-size] [--sqlite-db PATH] [--type EXT]

    -d, --dir         指定准备上传图书的目录（必填）
    --depth N         查找图书的目录深度，默认 1（仅当前目录）
    --force           文件名重名时强制覆盖上传
    --force-size      只有源文件 size 大于目标文件 size 时才强制覆盖
    --sqlite-db PATH  指定 SQLite 数据库文件路径，默认 instance/novel.db
    -t, --type EXT    指定上传文件后缀，默认 .txt（如 -t .epub）

    上传流程与 web 端一致：直接复制文件 → 写入上传表。
    路径格式: uploads/YYMMDD/源文件所在上级目录名/文件名.txt

示例:
    python batch_upload.py -d ~/novels/
    python batch_upload.py -d ~/novels/ --depth 2 --force --sqlite-db /data/novel.db
"""
import os
import sys
import shutil
import argparse
from datetime import datetime

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Upload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'instance', 'novel.db')


def collect_txt_files(source_dir, depth, ext='.txt'):
    """按深度扫描目录，收集所有指定后缀的文件及其上级目录名。"""
    txt_files = []

    def walk(dirpath, current_depth):
        if current_depth > depth:
            return
        try:
            entries = sorted(os.listdir(dirpath))
        except PermissionError:
            return
        for entry in entries:
            full = os.path.join(dirpath, entry)
            if os.path.isfile(full) and entry.lower().endswith(ext.lower()):
                # 计算相对于源目录的上级目录名
                parent_dir = os.path.dirname(full)
                if parent_dir == source_dir:
                    subdir = ''
                else:
                    subdir = os.path.relpath(parent_dir, source_dir)
                txt_files.append((full, subdir))
            elif os.path.isdir(full) and current_depth < depth:
                walk(full, current_depth + 1)

    walk(source_dir, 1)
    return txt_files


def batch_upload(source_dir, depth=1, force=False, force_size=False, db_path=None, ext='.txt'):
    if not os.path.isdir(source_dir):
        print(f'错误: 源目录不存在: {source_dir}')
        sys.exit(1)

    if db_path is None:
        db_path = DEFAULT_DB_PATH

    txt_files = collect_txt_files(source_dir, depth, ext=ext)
    if not txt_files:
        print(f'未找到 {ext} 文件（深度={depth}）')
        return

    print(f'扫描到 {len(txt_files)} 个 {ext} 文件（深度={depth}）')
    print(f'数据库: {db_path}\n')

    app = create_app({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
    })
    with app.app_context():
        db.create_all()
    success = []
    failed = []
    overwritten = []

    with app.app_context():
        for src_path, subdir in txt_files:
            filename = os.path.basename(src_path)
            raw_name = os.path.splitext(filename)[0]
            original_ext = os.path.splitext(filename)[1]
            if not original_ext:
                original_ext = '.txt'
            saved_filename = raw_name + original_ext

            existing = Upload.query.filter_by(title=raw_name).first()

            if existing:
                if force_size:
                    if os.path.getsize(src_path) <= existing.file_size:
                        failed.append((filename, f'重名且源文件不大于已有文件 ({_format_size(os.path.getsize(src_path))} <= {_format_size(existing.file_size)})'))
                        print(f'  ✗ {filename} — 跳过（源文件不大于已有文件）')
                        continue
                elif not force:
                    failed.append((filename, '文件重名：上传表中已存在同名记录'))
                    print(f'  ✗ {filename} — 跳过（重名）')
                    continue

                # 覆盖：保持原路径，更新文件内容和元数据
                filepath = os.path.join(BASE_DIR, existing.file_path)
                try:
                    shutil.copy2(src_path, filepath)
                except OSError as e:
                    failed.append((filename, f'文件处理失败: {e}'))
                    print(f'  ✗ {filename} — 处理失败')
                    continue

                existing.file_size = os.path.getsize(src_path)
                existing.updated_at = datetime.now()
                existing.last_import_at = datetime.now()
                db.session.commit()

                overwritten.append(filename)
                tag = 'force-size' if force_size else 'force'
                print(f'  ↻ {filename} — 覆盖更新 ({tag})')
                continue

            # 新文件：上传到 uploads/YYMMDD/子目录/
            date_dir = datetime.now().strftime('%y%m%d')
            if subdir:
                dest_dir = os.path.join(UPLOAD_FOLDER, date_dir, subdir)
                rel_dir = os.path.join('uploads', date_dir, subdir)
            else:
                dest_dir = os.path.join(UPLOAD_FOLDER, date_dir)
                rel_dir = os.path.join('uploads', date_dir)

            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, saved_filename)
            try:
                shutil.copy2(src_path, dest_path)
            except OSError as e:
                failed.append((filename, f'文件复制失败: {e}'))
                print(f'  ✗ {filename} — 复制失败')
                continue

            file_size = os.path.getsize(dest_path)
            rel_path = os.path.join(rel_dir, saved_filename)
            upload = Upload(
                title=raw_name,
                file_path=rel_path,
                file_size=file_size,
            )
            db.session.add(upload)
            db.session.commit()

            success.append(filename)
            print(f'  ✓ {filename} → {rel_path}')

    # 汇总
    print(f'\n{"=" * 50}')
    total_new = len(success)
    total_overwrite = len(overwritten)
    total_fail = len(failed)
    print(f'上传完成: 新增 {total_new} / 覆盖 {total_overwrite} / 失败 {total_fail}')
    print(f'{"=" * 50}')

    if failed:
        print('\n失败详情:')
        for name, reason in failed:
            print(f'  ✗ {name} — {reason}')

    if overwritten:
        print('\n覆盖列表:')
        for name in overwritten:
            print(f'  ↻ {name}')

    if success:
        print('\n新增列表:')
        for name in success:
            print(f'  ✓ {name}')


def _format_size(size):
    if size >= 1048576:
        return f'{size / 1048576:.2f} MB'
    elif size >= 1024:
        return f'{size / 1024:.2f} KB'
    return f'{size} B'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='批量上传小说文件')
    parser.add_argument('-d', '--dir', required=True, help='准备上传图书的目录')
    parser.add_argument('--depth', type=int, default=1, help='查找图书的目录深度，默认 1')
    parser.add_argument('--force', action='store_true', help='文件名重名时强制覆盖')
    parser.add_argument('--force-size', action='store_true', help='源文件大于目标文件时才覆盖')
    parser.add_argument('--sqlite-db', default=None, help='SQLite 数据库文件路径，默认 instance/novel.db')
    parser.add_argument('-t', '--type', default='.txt', help='指定上传文件后缀，默认 .txt')
    args = parser.parse_args()

    batch_upload(
        args.dir,
        depth=args.depth,
        force=args.force,
        force_size=args.force_size,
        db_path=args.sqlite_db,
        ext=args.type,
    )