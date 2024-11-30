from app import application, db
from flask import render_template, flash, redirect, url_for, jsonify, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, FarmerDataForm, PostForm, PredictionForm, PastProductionForm
from app.models import User, Post, FarmerData, Comment, RegionProductionData, PostLike
from app.serverlibrary import *
import numpy as np

@application.route('/')
@application.route('/index')
@login_required
def index():
    """
    Render the home page with crop production graphs by region.
    The data is grouped and sorted by region and year.
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]
    regions_data = {}

    # Query all region production data
    data = RegionProductionData.query.all()

    # Organize data by region
    for entry in data:
        if entry.region not in regions_data:
            regions_data[entry.region] = {'year': [], 'productions': []}
        
        # Add or update production data for each year
        if entry.year not in regions_data[entry.region]['year']:
            regions_data[entry.region]['year'].append(entry.year)
            regions_data[entry.region]['productions'].append(entry.production)
        else:
            # Update the production value if the year already exists
            year_index = regions_data[entry.region]['year'].index(entry.year)
            regions_data[entry.region]['productions'][year_index] = entry.production

    # Sort the data by year for each region
    for region, values in regions_data.items():
        sorted_data = sorted(zip(values['year'], values['productions']), key=lambda x: x[0])
        regions_data[region]['year'], regions_data[region]['productions'] = zip(*sorted_data)

    return render_template('index.html', title='Home', regions=regions_data, prefix=prefix)


@application.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    Redirect authenticated users to the appropriate dashboard.
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)

        # Redirect to the next page if specified, otherwise to the dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        if user.is_government():
            return redirect(url_for('government_dashboard'))
        else:
            return redirect(url_for('farmer_dashboard'))

    return render_template('login.html', title='Sign In', form=form, prefix=prefix)


@application.route('/logout')
def logout():
    """
    Log the user out and redirect to the home page.
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]
    logout_user()
    return redirect(url_for('index'))


@application.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    Register new users as either farmers or government officials.
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Create a new user and save to the database
        user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form, prefix=prefix)


@application.route('/predict', methods=['POST'])
@login_required
def predict():
    """
    Predict crop production based on input features.
    Only accessible by government users.
    """
    if not current_user.is_government():
        return jsonify({'error': 'Unauthorized: Only government users can predict.'}), 403

    try:
        # Extract input data from the request
        input_data = request.get_json()

        # Apply Transformation - Polynomial Terms of 6th-order Precipitation
        precipitation_power6 = input_data['total_precipitation'] ** 6 

        features = np.array([
            precipitation_power6, 
            input_data['average_temperature'],
            input_data['total_arable_land'],
            input_data['fertilizer_consumption'],
            input_data['gdp'],
            input_data['population']
        ]).reshape(1, -1)

        # Perform prediction using the linear regression model
        prediction = predict_linreg(features, BETA_FINAL, np.array(PRECOMPUTED_MEANS), np.array(PRECOMPUTED_STDS))
        return jsonify({'predicted_production': round(prediction[0, 0], 2)})
    except KeyError as e:
        return jsonify({'error': f'Missing field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@application.route('/farmer_dashboard', methods=['GET', 'POST'])
@login_required
def farmer_dashboard():
    """
    Render the farmer dashboard.
    Allows farmers to input and view their crop production data.
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]
    
    if not current_user.is_farmer():
        flash('Only farmers can access their dashboard.')
        return redirect(url_for('index'))

    form = FarmerDataForm()
    if form.validate_on_submit():
        # Add new crop production data
        data = FarmerData(
            farmer_id=current_user.id,
            month=form.month.data,
            year=form.year.data,
            production=form.production.data
        )
        db.session.add(data)
        db.session.commit()
        flash('Data added successfully.')
        return redirect(url_for('farmer_dashboard'))

    # Query and organize farmer production data for display
    farmer_data = FarmerData.query.filter_by(farmer_id=current_user.id).order_by(FarmerData.year, FarmerData.month).all()
    months = [f"{data.month:02}/{data.year}" for data in farmer_data]
    productions = [data.production for data in farmer_data]

    return render_template('farmer_dashboard.html', title='Farmer Dashboard', form=form, months=months, productions=productions, prefix=prefix)


@application.route('/government_dashboard', methods=['GET', 'POST'])
@login_required
def government_dashboard():
    """
    Render the government dashboard for managing predictions and past production data.
    Handles two forms:
    1. Prediction Form: To predict crop production using input features.
    2. Past Production Form: To record historical production data.
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]

    # Restrict access to government users only
    if not current_user.is_government():
        flash('Only government officials can access their dashboard.')
        return redirect(url_for('index'))
    
    # Initialize forms for prediction and past production input
    prediction_form = PredictionForm()
    past_production_form = PastProductionForm()
    
    # Handle prediction form submission
    if prediction_form.validate_on_submit():
        # Prepare input data for prediction
        input_data = {
            'total_precipitation': prediction_form.total_precipitation.data,
            'average_temperature': prediction_form.average_temperature.data,
            'total_arable_land': prediction_form.total_arable_land.data,
            'fertilizer_consumption': prediction_form.fertilizer_consumption.data,
            'gdp': prediction_form.gdp.data,
            'population': prediction_form.population.data
        }

        # Perform prediction using the regression model
        features = np.array([input_data[key] for key in input_data]).reshape(1, -1)
        predicted_production = predict_linreg(features, BETA_FINAL, np.array(PRECOMPUTED_MEANS), np.array(PRECOMPUTED_STDS))

        # Save predicted production as a new database entry
        new_entry = RegionProductionData(region=prediction_form.region.data,
                                         year=prediction_form.year.data,
                                         production=predicted_production[0, 0],
                                         predicted=True)
        db.session.add(new_entry)
        db.session.commit()

        flash(f'Prediction successful! Predicted production for {prediction_form.region.data} in {prediction_form.year.data}: {predicted_production[0, 0]:.2f} (tonnes). Data saved.', 'success')
        return redirect(url_for('government_dashboard'))

    # Handle past production form submission
    if past_production_form.validate_on_submit():
        # Save historical production data as a new database entry
        new_entry = RegionProductionData(region=past_production_form.region.data,
                                         year=past_production_form.year.data,
                                         production=past_production_form.production.data,
                                         predicted=False)
        db.session.add(new_entry)
        db.session.commit()

        flash('Past production data saved.', 'success')
        return redirect(url_for('government_dashboard'))

    # Retrieve posts for the forum section
    posts = Post.query.order_by(Post.timestamp.desc()).all()

    return render_template('government_dashboard.html', 
                           title="Government Dashboard", 
                           prediction_form=prediction_form,
                           past_production_form=past_production_form,
                           posts=posts,
                           prefix=prefix)


@application.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    """
    Handle the creation of new posts.
    Only government users are allowed to post insights or updates.
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]

    # Restrict access to government users only
    if not current_user.is_government():
        flash('Only government users can post insights.', 'danger')
        return redirect(url_for('index'))

    form = PostForm()
    if form.validate_on_submit():
        # Save the new post to the database
        post = Post(title=form.title.data, content=form.content.data.strip(), author_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been added!', 'success')
        return redirect(url_for('government_dashboard'))

    return render_template('add_post.html', title='Add Post', form=form, prefix=prefix)


@application.route('/forum')
@login_required
def forum():
    """
    Display the forum with all posts.
    Posts are ordered by their timestamp (most recent first).
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('forum.html', title='Forum', posts=posts, prefix=prefix)


@application.route('/view_post/<int:post_id>')
@login_required
def view_post(post_id):
    """
    Display a specific post along with its associated comments.
    """
    prefix = getattr(application.wsgi_app, 'prefix', '')[:-1]

    # Fetch the post by its ID or return a 404 error if not found
    post = Post.query.get_or_404(post_id)

    # Retrieve all comments associated with the post, ordered by timestamp
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.desc()).all()

    return render_template(
        'view_post.html',
        title=f"Post: {post.title}",
        post=post,
        comments=comments,
        prefix=prefix
    )


@application.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    """
    Add a comment to a specific post.
    Ensure the content is not empty before submission.
    """
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')

    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    # Save the new comment to the database
    comment = Comment(post_id=post_id, author_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    flash('Comment added successfully.', 'success')
    return redirect(url_for('view_post', post_id=post_id))


@application.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    """
    Allow users to like or unlike a post.
    Updates the like count and returns the new status via JSON.
    """
    post = Post.query.get_or_404(post_id)

    # Check if the user has already liked the post
    existing_like = PostLike.query.filter_by(post_id=post.id, user_id=current_user.id).first()

    if existing_like:
        # If the user already liked the post, remove the like
        db.session.delete(existing_like)
        if post.likes_count > 0:
            post.likes_count -= 1
        liked = False
    else:
        # If the post is not liked yet, add a new like
        new_like = PostLike(post_id=post.id, user_id=current_user.id)
        db.session.add(new_like)
        post.likes_count += 1
        liked = True

    db.session.commit()

    # Return the updated like count and like status as JSON
    return jsonify({
        'likes_count': post.likes_count,
        'liked': liked
    })
