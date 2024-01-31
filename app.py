import requests
from bs4 import BeautifulSoup
from flask import Flask, flash, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    def __repr__(self):
        return f"User('{self.username}')"

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

def get_stock_data():
    url = 'https://nepalstock.com.np/today-price'

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table with the class 'table my-table'
        table = soup.find('table', class_='table my-table')

        # Extracting data for each row in the table
        data = []
        for row in table.find_all('tr')[1:]:  # Skip the header row
            columns = row.find_all('td')

            # Extracting only the necessary columns
            business_date = columns[1].text.strip()
            symbol = columns[3].text.strip()
            open_price = columns[5].text.strip()
            high_price = columns[6].text.strip()
            low_price = columns[7].text.strip()
            close_price = columns[8].text.strip()
            previous_day_close_price = columns[11].text.strip()
            total_trades = columns[16].text.strip()
            average_traded_price = columns[17].text.strip()
            market_capitalization = columns[18].text.strip()
            # Store the extracted data in a dictionary
            stock_info = {
                'business_date': business_date,
                'symbol': symbol,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price,
                'previous_day_close_price': previous_day_close_price,
                'total_trades': total_trades,
                'average_traded_price': average_traded_price,
                'market_capitalization': market_capitalization,
            }
            data.append(stock_info)

        return data

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

    # Extracting data from the website (Modify this based on the structure of the website)
    companies = soup.select('.stock-symbol')
    previous_prices = soup.select('.stock-previous-closing-price')
    latest_prices = soup.select('.stock-open-price')

    stock_data = []
    for company, prev_price, latest_price in zip(companies, previous_prices, latest_prices):
        stock_data.append({
            'company': company.text.strip(),
            'previous_price': prev_price.text.strip(),
            'latest_price': latest_price.text.strip(),
        })

    return stock_data


@app.route('/')
def home():
    stock_data = get_stock_data()

    if stock_data is not None:
        return render_template('home.html', stock_data=stock_data)
    else:
        return render_template('error.html', message="Failed to retrieve stock data")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, password=form.password.data).first()

        if user:
            flash('Login successful!', 'success')
            return redirect(url_for('home'))

        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')

    return render_template('login.html', form=form)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


