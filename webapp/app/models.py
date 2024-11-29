from app import db
from app import login
from datetime import datetime 
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta

# Define the GMT+8 offset
gmt_plus_8 = timezone(timedelta(hours=8))

@login.user_loader
def load_user(id):
    """
    Flask-Login function to load a user by their ID.
    """
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    """
    User model for storing user authentication data and roles.
    """
    id = db.Column(db.Integer, primary_key=True) # Unique user ID
    username = db.Column(db.String(64), unique=True, nullable=False) # Username must be unique
    password_hash = db.Column(db.String(128), nullable=False) # Hashed password for security
    role = db.Column(db.String(32), nullable=False, default="farmer")  # User role ('farmer' or 'government')

    # Relationship to track liked posts
    liked_posts = db.relationship('PostLike', back_populates='user', lazy='dynamic', overlaps="user_likes")

    def set_password(self, password):
        """
        Hash and set the user's password.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify the user's password against the stored hash.
        """
        return check_password_hash(self.password_hash, password)

    def is_government(self):
        """
        Check if the user's role is 'government'.
        """
        return self.role == "government"

    def is_farmer(self):
        """
        Check if the user's role is 'farmer'.
        """
        return self.role == "farmer"


class Post(db.Model):
    """
    Model representing a blog post or user-generated content.
    """
    id = db.Column(db.Integer, primary_key=True) # Unique post ID
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) # Author's user ID
    title = db.Column(db.String(128), nullable=True) # Optional title for the post
    content = db.Column(db.Text, nullable=False) # Post content
    timestamp = db.Column(
        db.DateTime, 
        index=True, 
        default=lambda: datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(gmt_plus_8), 
        nullable=False
    ) # Creation timestamp with GMT+8 timezone

    # Relationships
    author = db.relationship('User', backref='posts', lazy=True) # Post's author
    likes = db.relationship(
        'PostLike', backref='liked_post', lazy=True, cascade="all, delete-orphan", overlaps="post_likes,liked_post"
    ) # Likes associated with the post
    likes_count = db.Column(db.Integer, default=0) # Track the number of likes on the post

    def is_liked_by(self, user):
        """
        Check if the post is liked by a specific user.
        """
        return PostLike.query.filter_by(post_id=self.id, user_id=user.id).first() is not None

    def __repr__(self):
        """
        String representation of a Post object.
        """
        return f"<Post {self.id}, Title: {self.title}, Author: {self.author_id}>"


class Comment(db.Model):
    """
    Model representing a comment on a post.
    """
    id = db.Column(db.Integer, primary_key=True) # Unique comment ID
    post_id = db.Column(db.Integer, db.ForeignKey('post.id')) # Associated post ID
    author_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Author's user ID
    content = db.Column(db.Text) # Comment content
    timestamp = db.Column(
        db.DateTime, 
        index=True, 
        default=lambda: datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(gmt_plus_8), 
        nullable=False
    ) # Creation timestamp with GMT+8 timezone

    # Relationship
    author = db.relationship('User', backref='comments') # Author of the comment

class FarmerData(db.Model):
    """
    Model representing production data reported by farmers.
    """
    id = db.Column(db.Integer, primary_key=True) # Unique data ID
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Farmer's user ID
    month = db.Column(db.Integer, nullable=False) # Month of the data entry
    year = db.Column(db.Integer, nullable=False) # Year of the data entry
    production = db.Column(db.Float, nullable=False) # Reported production value

    # Relationship
    farmer = db.relationship('User', backref='farmer_data') # Farmer who reported the data

class RegionProductionData(db.Model):
    """
    Model representing regional crop production data.
    """
    id = db.Column(db.Integer, primary_key=True) # Unique data ID
    region = db.Column(db.String(64), nullable=False) # Region name
    year = db.Column(db.Integer, nullable=False) # Year of the data entry
    production = db.Column(db.Float, nullable=False) # Production value in tonnes
    predicted = db.Column(db.Boolean, default=False)  # True if the data is predicted, False if it's historical
    # Timestamp for when the data was recorded
    timestamp = db.Column(
        db.DateTime, 
        index=True, 
        default=lambda: datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(gmt_plus_8), 
        nullable=False
    ) # Creation timestamp with GMT+8 timezone

    def __repr__(self):
        """
        String representation of a RegionProductionData object.
        """
        return f'<RegionProductionData {self.region} - {self.year}>'
    
class PostLike(db.Model):
    """
    Model representing a 'like' on a post.
    """
    id = db.Column(db.Integer, primary_key=True) # Unique ID for the like
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False) # ID of the liked post
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # ID of the user who liked the post

    # Relationships
    post = db.relationship('Post', backref='post_likes', lazy=True, overlaps="likes,liked_post")
    user = db.relationship('User', backref='user_likes', lazy=True, overlaps="liked_posts")

    def __repr__(self):
        """
        String representation of a PostLike object.
        """
        return f'<PostLike user_id={self.user_id} post_id={self.post_id}>'
