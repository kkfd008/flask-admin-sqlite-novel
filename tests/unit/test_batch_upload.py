"""batch_upload.py 批量导入顺序测试：一本处理完成后再处理下一本。"""
import batch_upload as bu


def _write_novel(path, chapter_count=3):
    parts = [f'第{i}章 标题{i}\n' + ('正文内容。' * 50) for i in range(1, chapter_count + 1)]
    path.write_text('\n'.join(parts), encoding='utf-8')


def _prepare_source(tmp_path):
    src = tmp_path / 'src'
    (src / 'A类').mkdir(parents=True)
    (src / 'B类').mkdir(parents=True)
    _write_novel(src / 'A类' / '甲书.txt')
    _write_novel(src / 'B类' / '乙书.txt')
    return src


def _redirect_output_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(bu, 'UPLOAD_FOLDER', str(tmp_path / 'uploads'))
    monkeypatch.setattr(bu, 'UTF8_FOLDER', str(tmp_path / 'utf8'))


def test_batch_upload_imports_each_book_before_next(tmp_path, monkeypatch, capsys):
    """last-step=4 时，前一本导入完成后才应开始处理下一本。"""
    src = _prepare_source(tmp_path)
    _redirect_output_dirs(tmp_path, monkeypatch)
    db_path = str(tmp_path / 'novel.db')

    bu.batch_upload(str(src), depth=2, db_path=db_path, last_step=4)

    out = capsys.readouterr().out
    pos_a_header = out.find('甲书.txt')
    pos_a_import = out.find('导入书库完成')
    pos_b_header = out.find('乙书.txt')

    assert pos_a_header != -1 and pos_a_import != -1 and pos_b_header != -1, out
    assert pos_a_header < pos_a_import < pos_b_header, (
        '应先完成甲书的上传与导入，再处理乙书\n' + out
    )


def test_batch_upload_saves_all_books_with_chapters(tmp_path, monkeypatch, capsys):
    """顺序导入后，两本书及其章节、上传关联都应正确入库。"""
    src = _prepare_source(tmp_path)
    _redirect_output_dirs(tmp_path, monkeypatch)
    db_path = str(tmp_path / 'novel.db')

    bu.batch_upload(str(src), depth=2, db_path=db_path, last_step=4)

    app = bu.create_app({'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}'})
    with app.app_context():
        from app.models import Novel, Chapter, Upload
        for title in ('甲书', '乙书'):
            novel = Novel.query.filter_by(title=title).first()
            assert novel is not None, f'{title} 应已入库'
            assert novel.chapter_count == 3, f'{title} 应有 3 章，实际 {novel.chapter_count}'
            rows = Chapter.query.filter_by(novel_id=novel.id).count()
            assert rows == 3, f'{title} 章节行数应为 3，实际 {rows}'
            assert Chapter.query.filter_by(novel_id=novel.id, content='').count() == 0, 'step4 应保存章节内容'

            upload = Upload.query.filter_by(title=title).first()
            assert upload is not None, f'{title} 上传记录应存在'
            assert upload.novel_id == novel.id, f'{title} 上传记录应关联到小说'


def test_batch_upload_last_step_1_uploads_only(tmp_path, monkeypatch, capsys):
    """last-step=1 时只上传，不创建书籍与章节。"""
    src = _prepare_source(tmp_path)
    _redirect_output_dirs(tmp_path, monkeypatch)
    db_path = str(tmp_path / 'novel.db')

    bu.batch_upload(str(src), depth=2, db_path=db_path, last_step=1)

    app = bu.create_app({'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}'})
    with app.app_context():
        from app.models import Novel, Upload
        assert Upload.query.count() == 2
        assert Novel.query.count() == 0
