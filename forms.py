from datetime import date
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    IntegerField,
    TextAreaField,
    DateField,
    SelectMultipleField,
    FloatField,
    widgets
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional
)

# ---------------- REGISTER ----------------
class RegistrationForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, max=128)]
    )
    confirm = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password')]
    )
    role = SelectField(
        'Role',
        choices=[('coach', 'Coach'), ('player', 'Player')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Register')


# ---------------- LOGIN ----------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# ---------------- TEAM ----------------
class TeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired()])
    season = StringField('Season', validators=[Optional()])
    submit = SubmitField('Create Team')


# ---------------- PLAYER ----------------
class PlayerForm(FlaskForm):
    name = StringField('Player Name', validators=[DataRequired()])
    position = StringField('Position', validators=[Optional()])
    team = SelectField(
        'Team',
        coerce=int,
        validators=[DataRequired()]
    )
    age = IntegerField(
        'Age',
        validators=[Optional(), NumberRange(min=10, max=60)]
    )
    submit = SubmitField('Add Player')


# ---------------- PERFORMANCE / STATS ----------------
class StatForm(FlaskForm):
    date = DateField(
        'Date',
        default=date.today,
        validators=[DataRequired()]
    )
    goals = IntegerField('Goals', default=0)
    assists = IntegerField('Assists', default=0)
    passes_completed = IntegerField('Passes Completed', default=0)
    passes_attempted = IntegerField('Passes Attempted', default=0)
    tackles = IntegerField('Tackles', default=0)
    rating = FloatField(
        'Rating (0–10)',
        validators=[DataRequired(), NumberRange(min=0, max=10)]
    )
    submit = SubmitField('Record Performance')


# ---------------- TRAINING ----------------
class TrainingForm(FlaskForm):
    team_id = SelectField(
        "Team",
        coerce=int,
        validators=[DataRequired()]
    )
    date = DateField(
        "Date",
        validators=[DataRequired()]
    )
    focus = TextAreaField(
        "Focus / Description",
        validators=[Optional()]
    )
    duration = IntegerField(
        "Duration (minutes)",
        validators=[DataRequired()]
    )

    attendance = SelectMultipleField(
        "Players Attending",
        coerce=int,
        choices=[],  # ✅ ΠΟΛΥ ΣΗΜΑΝΤΙΚΟ
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False)
    )

    submit = SubmitField("Create Training")


# ---------------- CHAT ----------------
class MessageForm(FlaskForm):
    receiver = SelectField(
        "Send To",
        coerce=int,
        validators=[DataRequired()]
    )
    content = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(max=500)]
    )
    submit = SubmitField("Send")
