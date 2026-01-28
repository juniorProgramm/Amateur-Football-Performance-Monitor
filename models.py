from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    approved = db.Column(db.Integer, default=0)
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    season = db.Column(db.String(20))
    def __repr__(self):
        return f'<Team {self.name}>'

class Player(db.Model):
    __tablename__ = 'player'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = db.relationship('User', backref='player_profile')

    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(50))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    age = db.Column(db.Integer)


class Performance(db.Model):
    __tablename__ = 'performance'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    date = db.Column(db.Date)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    passes_completed = db.Column(db.Integer, default=0)
    passes_attempted = db.Column(db.Integer, default=0)
    pass_accuracy = db.Column(db.Float, default=0.0)
    tackles = db.Column(db.Integer, default=0)
    rating = db.Column(db.Integer, default=0)
    def __repr__(self):
        return f'<Perf P{self.player_id} {self.date} R{self.rating}>'


class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    focus = db.Column(db.Text)
    duration = db.Column(db.Integer)
    attendance = db.Column(db.Integer, default=0)

    team = db.relationship('Team', backref='trainings')

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.receiver_id}>'

