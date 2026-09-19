import os
import re

from app.utils import convert_file_to_utf8, split_chapters


def test_convert_file_to_utf8_preserves_relative_dirs(tmp_path):
    """utf8 转换后应保留与 uploads 相同的相对目录结构"""
    uploads_root = tmp_path / 'uploads'
    src_dir = uploads_root / '260919' / 'book'
    src_dir.mkdir(parents=True)
    src = src_dir / '测试.txt'
    src.write_bytes('第一章 内容\n'.encode('gbk'))

    utf8_dir = tmp_path / 'utf8'
    dest = convert_file_to_utf8(str(src), str(utf8_dir), upload_root=str(uploads_root))

    assert dest == str(utf8_dir / '260919' / 'book' / '测试.txt')
    assert os.path.exists(dest)
    with open(dest, 'rb') as f:
        assert f.read().decode('utf-8') == '第一章 内容\n'


def test_convert_file_to_utf8_falls_back_to_basename_outside_root(tmp_path):
    """源文件不在上传根目录内时，退化为仅保留文件名，不写到 utf8 目录之外"""
    src = tmp_path / 'outside.txt'
    src.write_bytes('第一章 内容\n'.encode('utf-8'))

    utf8_dir = tmp_path / 'utf8'
    uploads_root = tmp_path / 'uploads'
    dest = convert_file_to_utf8(str(src), str(utf8_dir), upload_root=str(uploads_root))

    assert dest == str(utf8_dir / 'outside.txt')
    assert os.path.exists(dest)


CHAPTER_PATTERN = re.compile(r'^第\d+章.*$', re.MULTILINE)


def _make_novel(chapter_count, body_repeat=300):
    toc = '\n'.join(f'第{i}章 标题{i}' for i in range(1, chapter_count + 1))
    body = '\n'.join(f'第{i}章 标题{i}\n' + ('正文内容。' * body_repeat)
                     for i in range(1, chapter_count + 1))
    return toc, body


def test_split_chapters_dedupes_toc_entries():
    """正文前的章节目录不应被当成章节，避免章节数翻倍。"""
    toc, body = _make_novel(30)
    content = '目录\n' + toc + '\n\n' + body

    chapters = split_chapters(content, CHAPTER_PATTERN)

    assert len(chapters) == 30, f'目录条目应被去重，实际得到 {len(chapters)} 章'
    assert chapters[0][0] == '第1章 标题1'
    assert '正文内容' in chapters[0][1]


def test_split_chapters_keeps_chapters_without_toc():
    """没有目录时，正常章节不应被误删。"""
    _, body = _make_novel(5, body_repeat=1)

    chapters = split_chapters(body, CHAPTER_PATTERN)

    assert len(chapters) == 5


def test_split_chapters_keeps_real_preface():
    """真正的序章（有正文）应保留。"""
    content = '序章\n' + ('这是一段写在正文之前的序言内容。' * 10) + '\n第1章 开始\n内容一'

    chapters = split_chapters(content, CHAPTER_PATTERN)

    assert len(chapters) == 2
    assert chapters[0][0] == '序章'
    assert '序言' in chapters[0][1]


def test_split_chapters_dedupes_toc_without_preface():
    """目录前没有“目录”抬头时，同样应去掉重复的目录条目。"""
    toc, body = _make_novel(20)
    content = toc + '\n\n' + body

    chapters = split_chapters(content, CHAPTER_PATTERN)

    assert len(chapters) == 20, f'实际得到 {len(chapters)} 章'
    assert chapters[0][0] == '第1章 标题1'

