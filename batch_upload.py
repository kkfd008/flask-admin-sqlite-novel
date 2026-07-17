#!/usr/bin/env python3
"""批量上传小说文件到上传保存目录和上传表。

用法:
    python batch_upload.py -d <源目录> [--depth N] [--force] [--force-size] [--sqlite-db PATH] [--type EXT] [--last-step N]

    -d, --dir         指定准备上传图书的目录（必填）
    --depth N         查找图书的目录深度，默认 1（仅当前目录）
    --force           文件名重名时强制覆盖上传
    --force-size      只有源文件 size 大于目标文件 size 时才强制覆盖
    --sqlite-db PATH  指定 SQLite 数据库文件路径，默认 instance/novel.db
    -t, --type EXT    指定上传文件后缀，默认 .txt（如 -t .epub）
    --last-step N     1=仅上传（默认）, 3=上传+生成章节(无内容), 4=上传+完整导入

    上传流程与 web 端一致：直接复制文件 → 写入上传表。
    路径格式: uploads/YYMMDD/源文件所在上级目录名/文件名.txt

示例:
    python batch_upload.py -d ~/novels/
    python batch_upload.py -d ~/novels/ --depth 2 --force --sqlite-db /data/novel.db
    python batch_upload.py -d ~/novels/ --last-step 4
"""
import os
import sys
import shutil
import re
import argparse
from datetime import datetime

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Upload, Novel, Chapter, ChapterRule
from app.utils import get_best_pattern, split_chapters, split_by_fixed_length, init_default_rules

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
                # 保留源文件所在的最后一级目录名
                subdir = os.path.basename(os.path.dirname(full))
                txt_files.append((full, subdir))
            elif os.path.isdir(full) and current_depth < depth:
                walk(full, current_depth + 1)

    walk(source_dir, 1)
    return txt_files


def batch_upload(source_dir, depth=1, force=False, force_size=False, db_path=None, ext='.txt', last_step=1):
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
    print(f'数据库: {db_path}')
    print(f'模式: {"仅上传" if last_step == 1 else "上传+生成章节(无内容)" if last_step == 3 else "上传+完整导入"}\n')

    app = create_app({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
    })
    with app.app_context():
        db.create_all()
    success = []
    failed = []
    overwritten = []
    # 记录上传成功的文件路径，用于后续导入步骤
    uploaded = []  # [(upload_id, filepath, raw_name)]

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

            if last_step >= 3:
                uploaded.append((upload.id, dest_path, raw_name))

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

    # ---- 步骤 3/4: 导入书库 ----
    if last_step >= 3 and uploaded:
        print(f'\n{"=" * 50}')
        print(f'开始导入书库 ({"生成章节，无内容" if last_step == 3 else "完整导入"}):')
        print(f'{"=" * 50}')

        import_success = []
        import_failed = []

        with app.app_context():
            # 初始化默认规则（确保 get_best_pattern 可用）
            init_default_rules()

            for upload_id, filepath, raw_name in uploaded:
                try:
                    # 读取文件内容
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if not content.strip():
                        import_failed.append((raw_name, '文件内容为空'))
                        print(f'  ✗ {raw_name} — 文件内容为空')
                        continue

                    # 自动检测最佳章节匹配规则（使用系统规则）
                    best_rule, best_pattern, match_count = get_best_pattern(content)

                    # 分割章节
                    if best_pattern is None:
                        chapters = split_by_fixed_length(content)
                    else:
                        chapters = split_chapters(content, best_pattern)

                    if not chapters:
                        import_failed.append((raw_name, '未识别到章节'))
                        print(f'  ✗ {raw_name} — 未识别到章节')
                        continue

                    # 创建 Novel
                    novel = Novel(
                        title=raw_name,
                        author='',
                        category_id=None,
                    )
                    db.session.add(novel)
                    db.session.commit()

                    # 创建 Chapter
                    chapter_order = 0
                    total_word_count = 0
                    for ch_title, ch_content in chapters:
                        chapter_order += 1
                        if last_step == 3:
                            # 不保存内容
                            ch = Chapter(
                                novel_id=novel.id,
                                title=ch_title,
                                content='',
                                order=chapter_order,
                                word_count=len(ch_content),
                            )
                        else:
                            # 完整导入
                            ch = Chapter(
                                novel_id=novel.id,
                                title=ch_title,
                                content=ch_content,
                                order=chapter_order,
                                word_count=len(ch_content),
                            )
                        total_word_count += len(ch_content)
                        db.session.add(ch)

                    novel.chapter_count = chapter_order
                    novel.word_count = total_word_count
                    db.session.commit()

                    # 更新 Upload 的 novel_id
                    upload = Upload.query.get(upload_id)
                    if upload:
                        upload.novel_id = novel.id
                        upload.last_import_at = datetime.now()
                        db.session.commit()

                    import_success.append((raw_name, chapter_order, best_rule.name if best_rule else '固定长度'))
                    print(f'  ✓ {raw_name} → {chapter_order} 章 (规则: {best_rule.name if best_rule else "固定长度"})')

                except Exception as e:
                    db.session.rollback()
                    import_failed.append((raw_name, str(e)))
                    print(f'  ✗ {raw_name} — 导入失败: {e}')

        # 导入汇总
        print(f'\n{"=" * 50}')
        print(f'导入完成: 成功 {len(import_success)} / 失败 {len(import_failed)}')
        print(f'{"=" * 50}')

        if import_failed:
            print('\n导入失败详情:')
            for name, reason in import_failed:
                print(f'  ✗ {name} — {reason}')

        if import_success:
            print('\n导入成功列表:')
            for name, ch_count, rule_name in import_success:
                print(f'  ✓ {name} — {ch_count} 章 ({rule_name})')


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
    parser.add_argument('--last-step', type=int, default=1, choices=[1, 3, 4],
                        help='1=仅上传(默认), 3=上传+生成章节(无内容), 4=上传+完整导入')
    args = parser.parse_args()

    batch_upload(
        args.dir,
        depth=args.depth,
        force=args.force,
        force_size=args.force_size,
        db_path=args.sqlite_db,
        ext=args.type,
        last_step=args.last_step,
    )