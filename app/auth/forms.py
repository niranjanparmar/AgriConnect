from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models.user import User


class LoginForm(FlaskForm):
    """User authentication form."""
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Enter a valid email address", check_deliverability=False),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required")],
    )
    remember_me = BooleanField("Remember me on this device")
    submit = SubmitField("Secure Login")


class RegistrationForm(FlaskForm):
    """User registration form supporting both Farmer and Consumer roles."""
    role = SelectField(
        "Account Type",
        choices=[("farmer", "Farmer (Producer)"), ("consumer", "Consumer (Buyer)")],
        default="farmer",
        validators=[DataRequired()],
    )
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(message="Full name is required"), Length(min=2, max=100)],
    )
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Enter a valid email address", check_deliverability=False),
        ],
    )
    phone = StringField(
        "Phone Number",
        validators=[DataRequired(message="Phone number is required"), Length(min=10, max=15)],
    )
    state = SelectField(
        "State",
        choices=[
            ("Gujarat", "Gujarat"),
            ("Maharashtra", "Maharashtra"),
            ("Madhya Pradesh", "Madhya Pradesh"),
            ("Rajasthan", "Rajasthan"),
            ("Punjab", "Punjab"),
            ("Haryana", "Haryana"),
            ("Karnataka", "Karnataka"),
        ],
        default="Gujarat",
        validators=[DataRequired()],
    )
    district = StringField(
        "District / City",
        validators=[DataRequired(message="District is required"), Length(min=2, max=100)],
    )
    farm_name = StringField(
        "Farm Name (Farmers only)",
        validators=[Optional(), Length(max=150)],
    )
    address = TextAreaField(
        "Street / Farm Address",
        validators=[Optional(), Length(max=300)],
    )
    pincode = StringField(
        "PIN Code",
        validators=[Optional(), Length(min=6, max=10)],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required"),
            Length(min=8, message="Password must be at least 8 characters long"),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password"),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        """Ensure email is unique across all user accounts."""
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account with this email address is already registered.")


class ProfileUpdateForm(FlaskForm):
    """User profile and farm details editing form."""
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(message="Full name is required"), Length(min=2, max=100)],
    )
    phone = StringField(
        "Phone Number",
        validators=[DataRequired(message="Phone number is required"), Length(min=10, max=15)],
    )
    state = StringField(
        "State",
        validators=[DataRequired(), Length(max=100)],
    )
    district = StringField(
        "District",
        validators=[DataRequired(), Length(max=100)],
    )
    farm_name = StringField(
        "Farm / Business Name",
        validators=[Optional(), Length(max=150)],
    )
    address = TextAreaField(
        "Address",
        validators=[Optional(), Length(max=300)],
    )
    pincode = StringField(
        "PIN Code",
        validators=[Optional(), Length(min=6, max=10)],
    )
    current_password = PasswordField("Current Password", validators=[Optional()])
    new_password = PasswordField(
        "New Password",
        validators=[
            Optional(),
            Length(min=8, message="New password must be at least 8 characters"),
        ],
    )
    submit = SubmitField("Save Profile Changes")
