from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Message, Notification, Patient
from app.translate import translate
from app.main import bp
from app.auth.forms import PatientForm

from mapbox import Geocoder
from geopy.distance import vincenty


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, name=form.name.data, height=form.height.data, weight=form.weight.data, bmi=form.bmi.data, bmireport=form.bmireport.data, author=current_user,
                    language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)

@bp.route('/addpatient', methods=['GET', 'POST'])
def addpatient():
    
    form = PatientForm()
    if form.validate_on_submit():
        user = User(patientname=form.patient_name.data, patientdescription=form.patient_description.data, patientlat=form.patient_lat.data, patientlng=form.patient_lng.data)
        
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you have now registered a Patient!'))
        return redirect(url_for('main.patients'))
    return render_template('auth/addpatient.html', title=_('Patient'),
                           form=form)

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


# ================================================================================
#  Initial map rendering
# ================================================================================

@bp.route('/map')

def display_map():
    """Display the initial map"""

    waypoints = session['waypoints']

    return render_template('mapbox.html', 
                            waypoints=waypoints)


@bp.route('/initial_patients.geojson')
def initial_patients_json():
    """Pull a limited set of patients for initial map display."""

    initial_patients_geojson = {
                        "type": "FeatureCollection",
                        "features": [
                            {
                            "type": "Feature",
                            "properties": {
                                "name": patient.patient_name,
                                "description": patient.patient_description
                                },
                            "geometry": {
                                "coordinates": [
                                    patient.patient_lng,
                                    patient.patient_lat],
                                "type": "Point"
                            },
                            "id": patient.patient_id
                            }
                        for patient in patient.query.limit(20)
                        # for patient in Rating.query.order_by(Rating.user_score.desc()).limit(20)
                        # for patient in Patient.query.order_by(Patient.ratings.user_score.desc()).limit(20)
                        # FIXME
                        ]
                    }

    return jsonify(initial_patients_geojson)


@bp.route('/patients.geojson')
def patients_json():
    """Send patient data for map layer as Geojson from database."""

    features = []


    for patient in Patient.query.all():
        # get the first image of a patient, if any
        image = ""
        if len(patient.images) > 0:
            image = patient.images[0].imageurl 
        # get the average rating of a patient
        avg_rating = ""
        rating_scores = [r.user_score for r in patient.ratings]
        if len(rating_scores) > 0:
            avg_rating = float(sum(rating_scores))/len(rating_scores)
        
        features.append({
                        "type": "Feature",
                        "properties": {
                            "name": patient.patient_name,
                            "description": patient.patient_description
                            },
                        "geometry": {
                            "coordinates": [
                                patient.patient_lng,
                                patient.patient_lat],
                            "type": "Point"
                        },
                        "id": patient.patient_id,
                        'image': image,
                        'avg_rating': avg_rating,
                        })
    
    patients_geojson = {
                        "type": "FeatureCollection",
                        "features": features,
                        }

    return jsonify(patients_geojson)


@bp.route('/saved.geojson')
def saved_patients_json():
    """Send patient data for saved patients layer as Geojson from database."""

    features = []
    saved = []
    user_id = session['user_id']
   
    patients = UserSaved.query.filter(UserSaved.user_id==user_id).all()
    for patient in patients:
        patient = Patient.query.filter(Patient.patient_id==patient.patient_id).first()
        if patient:

            image = ""
            if len(patient.images) > 0:
                image = patient.images[0].imageurl 
            
            avg_rating = ""
            rating_scores = [r.user_score for r in patient.ratings]
            if len(rating_scores) > 0:
                avg_rating = float(sum(rating_scores))/len(rating_scores)

            features.append({
                            "type": "Feature",
                            "properties": {
                                "name": patient.patient_name,
                                "description": patient.patient_description
                            },
                            "geometry": {
                                "coordinates": [
                                    patient.patient_lng,
                                    patient.patient_lat],
                                "type": "Point"
                            },
                            "id": patient.patient_id,
                            'image': image,
                            'avg_rating': avg_rating,
                            })
    
    saved_geojson = {
                        "type": "FeatureCollection",
                        "features": features,
                        }

    return jsonify(saved_geojson)