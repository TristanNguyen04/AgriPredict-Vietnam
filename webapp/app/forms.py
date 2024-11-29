from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, FloatField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, EqualTo
from app.models import User
import calendar

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', 
                               validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('farmer', 'Farmer'), ('government', 'Government')], default='farmer')
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
		
class PredictForm(FlaskForm):
    precipitation = IntegerField('Total Precipitation (mm)', validators=[DataRequired()])
    temperature = IntegerField('Average Temperature (°C)', validators=[DataRequired()])
    arable_land = IntegerField('Total Arable Land (hectares)', validators=[DataRequired()])
    fertilizer = IntegerField('Fertilizer Consumption (kg/hectare)', validators=[DataRequired()])
    gdrp = IntegerField('Gross Regional Domestic Product (million $)', validators=[DataRequired()])
    population = IntegerField('Population (people)', validators=[DataRequired()])
    submit = SubmitField('Predict')

class FarmerDataForm(FlaskForm):
    month = SelectField(
        'Month', 
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],  # 1-12
        coerce=int,
        validators=[DataRequired()]
    )
    year = IntegerField('Year', validators=[DataRequired()])
    production = IntegerField('Crop Production (tonnes)', validators=[DataRequired()])
    submit = SubmitField('Add Data')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()], render_kw={'rows': 10, 'placeholder': 'Write your post here...'})
    submit = SubmitField('Post')

class PredictionForm(FlaskForm):
    region = StringField('Region', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired()])
    total_precipitation = FloatField('Total Precipitation (mm)', validators=[DataRequired()])
    average_temperature = FloatField('Average Temperature (°C)', validators=[DataRequired()])
    total_arable_land = FloatField('Total Arable Land (hectares)', validators=[DataRequired()])
    fertilizer_consumption = FloatField('Fertilizer Consumption (kg/hectare)', validators=[DataRequired()])
    gdp = FloatField('GDP (million USD)', validators=[DataRequired()])
    population = IntegerField('Population', validators=[DataRequired()])
    submit = SubmitField('Predict')

class PastProductionForm(FlaskForm):
    region = StringField('Region', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired()])
    production = FloatField('Past Production (tonnes)', validators=[DataRequired()])
    submit = SubmitField('Save Past Production')