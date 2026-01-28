import os
from datetime import date
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, TeamForm, PlayerForm, StatForm, TrainingForm, MessageForm
from models import db, User, Team, Player, Performance, Training, Message
from flask_migrate import Migrate
from flask_mail import Mail

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'replace-with-secure-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

# ---------------- DB INIT ----------------
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('adminpass'),
            role='admin',
            approved=1
        )
        db.session.add(admin)
        db.session.commit()

# ---------------- LOGIN ----------------
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('index.html')

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.email.data)
        ).first():
            flash('Username ή email υπάρχει ήδη.', 'danger')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                role=form.role.data,
                approved=0
            )
            db.session.add(user)
            db.session.commit()
            flash('Η εγγραφή υποβλήθηκε. Περιμένει έγκριση από admin.', 'info')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)

# -------- LOGIN --------
@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            if user.approved:
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Ο λογαριασμός σου περιμένει έγκριση από admin.', 'warning')
        else:
            flash('Λάθος στοιχεία σύνδεσης.', 'danger')

    return render_template('login.html', form=form)

# -------- LOGOUT --------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ---------------- APPROVE / REJECT ----------------
@app.route('/approve/<int:user_id>', methods=['POST'])
@login_required
def approve(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    user.approved = 1
    db.session.commit()

    # === AUTO-CREATE PLAYER PROFILE IF ROLE = "player" ===
    # === AUTO-CREATE OR LINK PLAYER PROFILE IF ROLE = "player" ===
    if user.role == "player":

        existing_player = Player.query.filter_by(
        name=user.username,
        user_id=None   # 👈 ΜΟΝΟ unregistered
    ).first()

    if existing_player:
        # 🔗 ΣΥΝΔΕΣΗ υπάρχοντος player με user
        existing_player.user_id = user.id
        db.session.commit()

    else:
        # ➕ Δημιουργία νέου player
        new_player = Player(
            name=user.username,
            age=0,
            position="Unknown",
            team_id=None,
            user_id=user.id
        )
        db.session.add(new_player)
        db.session.commit()


    flash(f"Ο χρήστης {user.username} εγκρίθηκε.", "success")
    return redirect(url_for('dashboard'))



@app.route('/reject/<int:user_id>', methods=['POST'])
@login_required
def reject(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash("Ο χρήστης απορρίφθηκε και διαγράφηκε.", "warning")
    return redirect(url_for('dashboard'))


# ---------------- PLAYER TEAM ASSIGNMENT ----------------
@app.route('/coach/assign/<int:player_id>', methods=['GET', 'POST'])
@login_required
def coach_assign_player(player_id):
    if current_user.role != "coach":
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    player = Player.query.get_or_404(player_id)
    teams = Team.query.filter_by(coach_id=current_user.id).all()

    if request.method == "POST":
        new_team_id = request.form.get("team_id")

        # Έλεγχος αν η ομάδα όντως ανήκει στον coach
        team = Team.query.filter_by(id=new_team_id, coach_id=current_user.id).first()

        if not team:
            flash("Δεν μπορείς να αναθέσεις παίκτη σε αυτή την ομάδα.", "danger")
            return redirect(url_for('coach_assign_player', player_id=player.id))

        player.team_id = team.id
        db.session.commit()

        flash(f"Ο παίκτης {player.name} προστέθηκε στην ομάδα {team.name}.", "success")
        return redirect(url_for('dashboard'))

    return render_template("assign_player.html", player=player, teams=teams)


# ---------------- ADMIN DELETE USER ----------------
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    if user.username == "admin":
        flash("Δεν μπορείς να διαγράψεις τον admin.", "danger")
        return redirect(url_for('dashboard'))

    if user.role == "coach":
        teams = Team.query.filter_by(coach_id=user.id).all()
        for team in teams:
            Player.query.filter_by(team_id=team.id).delete()
            Training.query.filter_by(team_id=team.id).delete()
            db.session.delete(team)

    if user.role == "player":
        Player.query.filter_by(user_id=user.id).delete()

    Message.query.filter(
        (Message.sender_id == user.id) | (Message.receiver_id == user.id)
    ).delete()

    db.session.delete(user)
    db.session.commit()

    flash("Ο χρήστης διαγράφηκε επιτυχώς.", "success")
    return redirect(url_for('dashboard'))

# ---------------- EMFANISH PAIXTON ----------------
@app.route('/coach/players')
@login_required
def coach_players():
    if current_user.role != "coach":
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    # Παίκτες που ΔΕΝ έχουν team_id
    available_players = Player.query.filter_by(team_id=None).all()

    return render_template("coach_players.html", players=available_players)


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
@login_required
def dashboard():

    if current_user.role == 'admin':
        pending = User.query.filter_by(approved=0).all()
        all_users = User.query.filter(User.username != "admin").all()
        teams = Team.query.order_by(Team.name).all()

        return render_template(
            'admin_dashboard.html',
            pending=pending,
            all_users=all_users,
            total_teams=len(teams),
            total_players=Player.query.count(),
            teams=teams
        )

    elif current_user.role == 'coach':

        old_trainings = (
            Training.query
            .join(Team, Training.team_id == Team.id)
            .filter(Team.coach_id == current_user.id)
            .filter(Training.date < date.today())
            .all()
        )

        for tr in old_trainings:
            db.session.delete(tr)

        db.session.commit()

        teams = Team.query.filter_by(coach_id=current_user.id).all()
        return render_template('coach_dashboard.html', teams=teams)

    elif current_user.role == 'player':
        player = Player.query.filter_by(user_id=current_user.id).first()

        if not player:
            flash("Δεν υπάρχει προφίλ παίκτη.", "danger")
            return redirect(url_for('logout'))

        team = Team.query.get(player.team_id)
        coach = User.query.get(team.coach_id) if team else None

        performances = Performance.query.filter_by(
            player_id=player.id
        ).order_by(Performance.date.asc()).all()

        return render_template(
            'player_dashboard.html',
            player=player,
            coach=coach,
            performances=performances
        )

    return redirect(url_for('logout'))

# ---------------- ADD TEAM ----------------
@app.route('/team/add', methods=['GET','POST'])
@login_required
def add_team():

    if current_user.role != 'coach':
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    form = TeamForm()

    if form.validate_on_submit():

        # === UNIQUE TEAM NAME BETWEEN COACHES ===
        existing_team = Team.query.filter_by(name=form.name.data).first()
        if existing_team and existing_team.coach_id != current_user.id:
            flash("Υπάρχει ήδη ομάδα με αυτό το όνομα από άλλον προπονητή.", "danger")
            return redirect(url_for('add_team'))

        # === Προαιρετικό: να μην κάνει ο ίδιος coach 2 φορές ίδια ομάδα ===
        same_coach_team = Team.query.filter_by(
            name=form.name.data,
            coach_id=current_user.id
        ).first()
        if same_coach_team:
            flash("Έχεις ήδη ομάδα με αυτό το όνομα.", "warning")
            return redirect(url_for('add_team'))

        team = Team(
            name=form.name.data,
            season=form.season.data,
            coach_id=current_user.id
        )
        db.session.add(team)
        db.session.commit()

        flash("Η ομάδα δημιουργήθηκε επιτυχώς.", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_team.html', form=form)


# ---------------- TEAM PLAYERS LIST ----------------
@app.route('/team/<int:team_id>/players')
@login_required
def team_players(team_id):

    team = Team.query.get_or_404(team_id)

    if not (
        current_user.role == 'admin' or
        (current_user.role == 'coach' and team.coach_id == current_user.id)
    ):
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    players = Player.query.filter_by(team_id=team_id).order_by(Player.name).all()

    return render_template('team_players.html', team=team, players=players)

# ---------------- ADD PLAYER ----------------
@app.route('/player/add', methods=['GET', 'POST'])
@login_required
def add_player():

    if current_user.role != 'coach':
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    form = PlayerForm()

    teams = Team.query.filter_by(coach_id=current_user.id).all()
    form.team.choices = [(t.id, t.name) for t in teams]

    if form.validate_on_submit():

        # 🔍 Έλεγχος: υπάρχει ήδη Player με ίδιο όνομα;
        existing_player = Player.query.filter_by(
            name=form.name.data
        ).first()

        if existing_player:
            flash(
                "Ο παίκτης υπάρχει ήδη. "
                "Αν δεν έχει ομάδα, πρόσθεσέ τον από τους Available Players.",
                "warning"
            )
            return redirect(url_for('coach_players'))

        # ✅ Δημιουργία ΝΕΟΥ unregistered player
        player = Player(
            name=form.name.data,
            position=form.position.data,
            age=form.age.data,
            team_id=form.team.data,
            user_id=None  # 👈 ξεκάθαρα unregistered
        )

        db.session.add(player)
        db.session.commit()

        flash("Ο παίκτης προστέθηκε επιτυχώς.", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_player.html', form=form)



# ---------------- COACH REMOVE PLAYER ----------------

@app.route('/coach/remove_player/<int:player_id>', methods=['POST'])
@login_required
def coach_remove_player(player_id):
    if current_user.role != "coach":
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    player = Player.query.get_or_404(player_id)

    # Επιτρέπεται ΜΟΝΟ για παίκτες της δικής του ομάδας
    team = Team.query.get(player.team_id)

    if not team or team.coach_id != current_user.id:
        flash("Δεν έχεις δικαίωμα να αφαιρέσεις αυτόν τον παίκτη.", "danger")
        return redirect(url_for('dashboard'))

    # 🔥 Βγάζουμε τον παίκτη από την ομάδα!
    player.team_id = None
    db.session.commit()

    flash(f"Ο παίκτης {player.name} μεταφέρθηκε στους Available Players.", "success")

    return redirect(url_for('team_players', team_id=team.id))


# ---------------- COACH ADD STATS ----------------
@app.route('/coach/add_stats/<int:player_id>', methods=['GET', 'POST'])
@login_required
def add_stats(player_id):
    if current_user.role != "coach":
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    player = Player.query.get_or_404(player_id)

    # Ο coach πρέπει να είναι προπονητής της ομάδας του παίκτη
    team = Team.query.get(player.team_id)
    if not team or team.coach_id != current_user.id:
        flash("Δεν έχεις δικαίωμα να προσθέσεις στατιστικά σε αυτόν τον παίκτη.", "danger")
        return redirect(url_for('dashboard'))

    form = StatForm()

    if form.validate_on_submit():
        perf = Performance(
            player_id=player.id,
            date=form.date.data,
            goals=form.goals.data,
            assists=form.assists.data,
            passes_completed=form.passes_completed.data,
            passes_attempted=form.passes_attempted.data,
            tackles=form.tackles.data,
            rating=form.rating.data
        )

        db.session.add(perf)
        db.session.commit()

        flash("Τα στατιστικά καταχωρήθηκαν επιτυχώς!", "success")
        return redirect(url_for('team_players', team_id=team.id))

    return render_template("add_stats.html", form=form, player=player)


# ---------------- ADD TRAINING ----------------
@app.route('/training/add', methods=['GET', 'POST'])
@login_required
def add_training():

    if current_user.role != 'coach':
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    form = TrainingForm()

    # ---- ΠΑΡΑΛΑΒΗ ΤΟΥ team_id ΑΠΟ ΤΟ URL ----
    preselected_team = request.args.get("team_id", type=int)

    # Φόρτωση όλων των ομάδων του coach
    teams = Team.query.filter_by(coach_id=current_user.id).all()
    form.team_id.choices = [(t.id, t.name) for t in teams]

    # ❗ Αν υπάρχει preselected team → προεπιλογή στο dropdown
    if preselected_team:
        form.team_id.data = preselected_team

        # Φόρτωσε παίκτες αυτής της ομάδας
        players = Player.query.filter_by(team_id=preselected_team).all()
    else:
        # Αν δεν έχει team_id ακόμα, δεν δείχνουμε παίκτες
        players = []

    # ❗ Δώσε τους παίκτες στο πεδίο attendance (checkboxes)
    form.attendance.choices = [(p.id, p.name) for p in players]

    # ---- SUBMIT ----
    if form.validate_on_submit():
        training = Training(
            team_id=form.team_id.data,
            date=form.date.data,
            focus=form.focus.data,
            duration=form.duration.data
        )
        db.session.add(training)
        db.session.commit()

        flash("Η προπόνηση προστέθηκε επιτυχώς.", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_training.html', form=form)



# ---------------- PLAYER TRAININGS ----------------
@app.route('/player/trainings')
@login_required
def player_trainings():

    if current_user.role != 'player':
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    player = Player.query.filter_by(user_id=current_user.id).first()
    if not player:
        flash("Δεν υπάρχει προφίλ παίκτη.", "danger")
        return redirect(url_for('dashboard'))

    trainings = Training.query.filter_by(
        team_id=player.team_id
    ).order_by(Training.date.desc()).all()

    return render_template('player_trainings.html', trainings=trainings)

# ---------------- COACH CHAT LIST ----------------
@app.route('/coach/chat')
@login_required
def coach_chat_list():
    if current_user.role != 'coach':
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    players = (
        Player.query
        .filter(Player.user_id.isnot(None))  # ✅ ΜΟΝΟ players με account
        .join(Team, Player.team_id == Team.id)
        .filter(Team.coach_id == current_user.id)
        .order_by(Player.name.asc())
        .all()
    )

    return render_template('coach_chat_list.html', players=players)


# ---------------- COACH VIEW ALL TRAININGS ----------------
@app.route('/coach/trainings')
@login_required
def coach_trainings():

    if current_user.role != 'coach':
        flash("Unauthorized", "danger")
        return redirect(url_for('dashboard'))

    trainings = (
        Training.query
        .join(Team, Training.team_id == Team.id)
        .filter(Team.coach_id == current_user.id)
        .order_by(Training.date.desc())
        .all()
    )

    return render_template('coach_trainings.html', trainings=trainings)

# ---------------- CHAT ----------------
@app.route('/message/chat/<int:user_id>', methods=['GET','POST'])
@login_required
def chat(user_id):

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        content = request.form.get("content", "").strip()

        if content:
            msg = Message(
                sender_id=current_user.id,
                receiver_id=user_id,
                content=content
            )
            db.session.add(msg)
            db.session.commit()

        return redirect(url_for('chat', user_id=user_id))

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()

    return render_template('chat.html', messages=messages, user=user)
# ---------------------- PLAYER DETAIL PAGE ----------------------
@app.route('/player/<int:player_id>')
@login_required
def player_detail(player_id):

    player = Player.query.get_or_404(player_id)
    team = Team.query.get(player.team_id)

    performances = Performance.query.filter_by(
        player_id=player.id
    ).order_by(Performance.date.asc()).all()

    # ---- TOTALS CALCULATION ----
    totals = {
        "goals": 0,
        "assists": 0,
        "tackles": 0,
        "passes_completed": 0,
        "passes_attempted": 0,
        "appearances": len(performances)
    }

    for r in performances:
        totals["goals"] += r.goals
        totals["assists"] += r.assists
        totals["tackles"] += r.tackles
        totals["passes_completed"] += r.passes_completed
        totals["passes_attempted"] += r.passes_attempted

    return render_template(
        'player_detail.html',
        player=player,
        team=team,
        performances=performances,
        totals=totals
    )


# ---------------------- API PLAYER PERFORMANCE ----------------------
@app.route('/api/player/<int:player_id>/performance')
@login_required
def api_player_performance(player_id):

    performances = Performance.query.filter_by(
        player_id=player_id
    ).order_by(Performance.date.asc()).all()

    labels = [p.date.strftime("%Y-%m-%d") for p in performances]
    values = [p.rating for p in performances]

    return {
        "labels": labels,
        "values": values
    }


# ---------------------- API ROUTE FOR TEAM PERFORMANCE ----------------------
@app.route('/api/team/<int:team_id>/performance')
@login_required
def api_team_performance(team_id):

    team = Team.query.get(team_id)
    if not team:
        return {"error": "Team not found"}, 404

    players = Player.query.filter_by(team_id=team_id).all()
    player_ids = [p.id for p in players]

    if not player_ids:
        return {"labels": [], "values": []}

    performances = (
        Performance.query
        .filter(Performance.player_id.in_(player_ids))
        .order_by(Performance.date.asc())
        .all()
    )

    if not performances:
        return {"labels": [], "values": []}

    from collections import defaultdict
    grouped = defaultdict(list)

    for p in performances:
        grouped[p.date].append(p.rating)

    labels = []
    values = []

    for d in sorted(grouped.keys()):
        ratings = grouped[d]
        avg_rating = sum(ratings) / len(ratings)
        labels.append(d.strftime("%Y-%m-%d"))
        values.append(round(avg_rating, 2))

    return {"labels": labels, "values": values}, 200


# ---------------- START ----------------
if __name__ == '__main__':
    app.run(debug=True)
