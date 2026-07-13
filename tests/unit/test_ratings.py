import pytest
import math


class TestRatingsCRUD:
    def test_create_rating(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/rate', data={
            'score': 4,
            'comment': '很好看'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Rating
            rating = Rating.query.filter_by(user_id=user.id, novel_id=novel.id).first()
            assert rating is not None
            assert rating.score == 4
            assert rating.comment == '很好看'

    def test_update_rating(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, Rating
            user = User(username='admin', password='admin123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()
            
            rating = Rating(user_id=user.id, novel_id=novel.id, score=3, comment='一般')
            db.session.add(rating)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/rate', data={
            'score': 5,
            'comment': '非常好看'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Rating
            updated = Rating.query.filter_by(user_id=user.id, novel_id=novel.id).first()
            assert updated.score == 5
            assert updated.comment == '非常好看'

    def test_delete_rating(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel, Rating
            user = User(username='admin', password='admin123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()
            
            rating = Rating(user_id=user.id, novel_id=novel.id, score=4)
            db.session.add(rating)
            db.session.commit()

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel.id}/rate/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Rating
            assert Rating.query.filter_by(user_id=user.id, novel_id=novel.id).first() is None


class TestAverageRatingCalculation:
    def test_calculate_average_rating_single(self, app):
        with app.app_context():
            from app.models import db, User, Novel, Rating
            user = User(username='testuser', password='testpass123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()
            
            rating = Rating(user_id=user.id, novel_id=novel.id, score=4)
            db.session.add(rating)
            db.session.commit()

            from app.utils import calculate_average_rating
            avg = calculate_average_rating(novel.id)
            assert avg == 4

    def test_calculate_average_rating_multiple(self, app):
        with app.app_context():
            from app.models import db, User, Novel, Rating
            user1 = User(username='user1', password='pass1')
            user2 = User(username='user2', password='pass2')
            user3 = User(username='user3', password='pass3')
            novel = Novel(title='测试小说')
            db.session.add_all([user1, user2, user3, novel])
            db.session.commit()
            
            ratings = [
                Rating(user_id=user1.id, novel_id=novel.id, score=4),
                Rating(user_id=user2.id, novel_id=novel.id, score=5),
                Rating(user_id=user3.id, novel_id=novel.id, score=3)
            ]
            db.session.add_all(ratings)
            db.session.commit()

            from app.utils import calculate_average_rating
            avg = calculate_average_rating(novel.id)
            assert avg == 4

    def test_calculate_average_rating_rounding(self, app):
        with app.app_context():
            from app.models import db, User, Novel, Rating
            user1 = User(username='user1', password='pass1')
            user2 = User(username='user2', password='pass2')
            user3 = User(username='user3', password='pass3')
            novel = Novel(title='测试小说')
            db.session.add_all([user1, user2, user3, novel])
            db.session.commit()
            
            ratings = [
                Rating(user_id=user1.id, novel_id=novel.id, score=4),
                Rating(user_id=user2.id, novel_id=novel.id, score=4),
                Rating(user_id=user3.id, novel_id=novel.id, score=3)
            ]
            db.session.add_all(ratings)
            db.session.commit()

            from app.utils import calculate_average_rating
            avg = calculate_average_rating(novel.id)
            assert avg == 4

            ratings2 = [
                Rating(user_id=user1.id, novel_id=novel.id, score=3),
                Rating(user_id=user2.id, novel_id=novel.id, score=3),
                Rating(user_id=user3.id, novel_id=novel.id, score=3),
                Rating(user_id=user1.id, novel_id=novel.id, score=4)
            ]
            db.session.add_all(ratings2)
            db.session.commit()

            avg2 = calculate_average_rating(novel.id)
            assert avg2 == 3 or avg2 == 4

    def test_update_user_rating_after_rate(self, client, app):
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()

            assert novel.user_rating == 0

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        client.post(f'/novels/{novel.id}/rate', data={'score': 5}, follow_redirects=True)

        with app.app_context():
            from app.models import Novel
            updated_novel = Novel.query.get(novel.id)
            assert updated_novel.user_rating == 5

        with app.app_context():
            from app.models import db, User as UserModel
            user2 = UserModel(username='user2', password='pass2')
            db.session.add(user2)
            db.session.commit()

        client.post('/login', data={'username': 'user2', 'password': 'pass2'}, follow_redirects=True)
        client.post(f'/novels/{novel.id}/rate', data={'score': 3}, follow_redirects=True)

        with app.app_context():
            from app.models import Novel
            updated_novel = Novel.query.get(novel.id)
            assert updated_novel.user_rating == 4

    def test_user_rating_default_zero(self, app):
        with app.app_context():
            from app.models import Novel
            novel = Novel(title='测试小说')
            assert novel.user_rating == 0

            from app.utils import calculate_average_rating
            avg = calculate_average_rating(99999)
            assert avg == 0