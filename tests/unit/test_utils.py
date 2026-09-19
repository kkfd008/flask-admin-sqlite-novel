import os

from app.utils import convert_file_to_utf8


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
