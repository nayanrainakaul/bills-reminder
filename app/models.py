from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager,db
from datetime import datetime
from config import config
import hashlib
from flask import request
from markdown import markdown
import bleach
from flask_bcrypt import generate_password_hash,check_password_hash

class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16

# User Role
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic',passive_deletes=True)

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
           self.permissions = 0
    def __repr__(self):
            return '<Role {}>'.format(self.id)

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name       


class Follow(db.Model):
    __tablename__ = 'follow'
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),primary_key=True,nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),primary_key=True,nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# class MoneyManager(db.Model):
#     __tablename__ = 'money_manager'
#     id = db.Column(db.Integer,primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
#     income = db.Column(db.String(70))
#     expense = db.Column(db.String(70))


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True,autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(64), unique=True, index=True)

    email = db.Column(db.String(64), unique=True, index=True)
    phoneNo = db.Column(db.String(80))
    password = db.Column(db.String(128))
    location = db.Column(db.String(64), nullable=True)
    about_me = db.Column(db.Text())
    designation = db.Column(db.Text())
    photo = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='author', lazy='dynamic',passive_deletes=True)
    # manager = db.relationship('MoneyManager', backref='money_manager', lazy='dynamic')
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete="CASCADE"),nullable=False)
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined', passive_deletes=True),
                               lazy='dynamic'
                             )
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined', passive_deletes=True),
                                lazy='dynamic'
                               )
    comments = db.relationship('Comment', backref='author', lazy='dynamic',passive_deletes=True)
    post_liked = db.relationship('PostLike',foreign_keys='PostLike.user_id',backref='user', lazy='dynamic',passive_deletes=True)
    comment_liked = db.relationship('CommentLike',foreign_keys='CommentLike.user_id',backref='user', lazy='dynamic',passive_deletes=True)

    def like_post(self, post):
        if not self.has_liked_post(post):
            like = PostLike(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            PostLike.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_liked_post(self, post):
        return PostLike.query.filter(
            PostLike.user_id == self.id,
            PostLike.post_id == post.id).count() > 0


            
    def like_comment(self, comment):
        if not self.has_liked_comment(comment):
            like = CommentLike(user_id=self.id, comment_id=comment.id)
            db.session.add(like)

    def unlike_comment(self, comment):
        if self.has_liked_comment(comment):
            CommentLike.query.filter_by(
                user_id=self.id,
                comment_id=comment.id).delete()

    def has_liked_comment(self, comment):
        return CommentLike.query.filter(
            CommentLike.user_id == self.id,
            CommentLike.comment_id == comment.id).count() > 0



    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['BILL_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
        self.follow(self)

    # @property
    # def password(self):
    #     raise AttributeError('password is not a readable attribute')

    # @password.setter
    # def password(self, password):
    #     self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)



    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True



    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    # Role Verification
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)
    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()



    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)    


    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)




    def __repr__(self):
        return '<User %r>' % self.username





class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    def is_administrator(self):
        return False
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))



class Entry(db.Model):
    __tablename__ = 'entry'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    # username = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id', ondelete="CASCADE"),nullable=False)
    billName = db.Column(db.String(80))
    billCategory = db.Column(db.String(12))
    amount = db.Column(db.Integer)
    dueDate = db.Column(db.DateTime(3))
    dateOfAdd =  db.Column(db.String(120))
    notificationReminder= db.Column(db.Integer)
    answer = db.Column(db.String(12))
    repeatDays = db.Column(db.String(20))
    repeatTime = db.Column(db.String(20))
    note = db.Column(db.String(20))
    paidUnpaid= db.Column(db.String(30))


    def __repr__(self):
        return '<User %r>' % self.billName




class PostLike(db.Model):
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete="CASCADE"),nullable=False)

class CommentLike(db.Model):
    __tablename__ = 'comment_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete="CASCADE"),nullable=False)





class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),nullable=False)
    comments = db.relationship('Comment', backref='post', lazy='dynamic', passive_deletes=True )
    posts_like = db.relationship('PostLike', backref='like', lazy='dynamic',passive_deletes=True)


    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

db.event.listen(Post.body, 'set', Post.on_changed_body)




class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete="CASCADE"),nullable=False)
    comments_like = db.relationship('CommentLike', backref='like', lazy='dynamic',passive_deletes=True)


    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

db.event.listen(Comment.body, 'set', Comment.on_changed_body)

