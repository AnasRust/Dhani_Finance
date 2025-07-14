from urllib.parse import quote_plus
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
import datetime

app = Flask(__name__)
app.secret_key = 'supersecret'

# MongoDB Atlas connection
username = quote_plus("dhani_admin")
password = quote_plus("Anascool@2001")
uri = f"mongodb+srv://{username}:{password}@finance.1osnvho.mongodb.net/?retryWrites=true&w=majority&tls=true&appName=Finance"
client = MongoClient(uri)
db = client["Dhani_Finance"]
collection = db["loan_applications"]

# Helper functions
def mask_aadhaar(aadhaar):
    return "XXXX-XXXX-" + aadhaar[-4:] if aadhaar else "XXXX-XXXX-0000"

def mask_pan(pan):
    return "XXXXX" + pan[-5:] if pan else "XXXXX0000"

# Home Page
@app.route('/')
def home():
    return render_template("index.html")

# Apply Loan Page
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        try:
            name = request.form['name']
            mobile = request.form['mobile']
            email = request.form['email']
            loan_amount = request.form['loan_amount']
            aadhaar = request.form['aadhaar']
            pan = request.form['pan']
            bank_account = request.form['bank_account']
            ifsc = request.form['ifsc']

            masked_aadhaar = mask_aadhaar(aadhaar)
            masked_pan = mask_pan(pan)

            application = {
                "name": name,
                "mobile": mobile,
                "email": email,
                "loan_amount": loan_amount,
                "aadhaar": masked_aadhaar,
                "pan": masked_pan,
                "bank_account": bank_account,
                "ifsc": ifsc,
                "submitted_at": datetime.datetime.now()
            }

            collection.insert_one(application)
            session['user_email'] = email

            return redirect(url_for('profile'))

        except Exception as e:
            flash(f"❌ Error: {str(e)}", "danger")
            return redirect(url_for('apply'))

    return render_template("apply.html")


# Loan Category Pages
@app.route('/loan/car')
def loan_car():
    latest = collection.find().sort("submitted_at", -1).limit(1)
    return render_template('loan_car.html', recent=latest)

@app.route('/loan/home')
def loan_home():
    latest = collection.find().sort("submitted_at", -1).limit(1)
    return render_template('loan_home.html', recent=latest)

@app.route('/loan/personal')
def loan_personal():
    latest = collection.find().sort("submitted_at", -1).limit(1)
    return render_template('loan_personal.html', recent=latest)

@app.route('/loan')
def loan():
    return render_template("loan.html")

@app.route('/about')
def about():
    return render_template("about.html")

# Next Page (Glitch + Profile + Withdraw)
@app.route('/next')
def next_page():
    user_email = session.get('user_email')

    if not user_email:
        flash("Please submit an application first.", "warning")
        return redirect(url_for('apply'))

    user = collection.find_one({'email': user_email})

    user_data = {
        'user_name': user.get('name', 'John D.'),
        'aadhaar': user.get('aadhaar', 'XXXX-XXXX-1234'),
        'bank_account': 'XXXXXX' + user.get('bank_account', '')[-4:],
        'mobile': '*****' + user.get('mobile', '')[-4:]
    } if user else {
        'user_name': 'John D.',
        'aadhaar': 'XXXX-XXXX-1234',
        'bank_account': 'XXXXXX0000',
        'mobile': '*****0000'
    }

    return render_template("next.html", user_data=user_data)


# Withdraw Page
@app.route('/withdraw')
def withdraw():
    user_email = session.get('user_email')

    if user_email:
        user = collection.find_one({"email": user_email}, sort=[("submitted_at", -1)])
        if user:
            return render_template('withdraw.html',
                                   user_name=user.get('name', 'John D.'),
                                   masked_aadhaar=user.get('aadhaar', 'XXXX-XXXX-1234'),
                                   masked_account='XXXXXX' + user.get('bank_account', '')[-4:],
                                   masked_mobile='*****' + user.get('mobile', '')[-4:])
        else:
            flash("User data not found.", "danger")
            return redirect(url_for('apply'))

    flash("Please submit an application first.", "warning")
    return redirect(url_for('apply'))

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if request.method == 'POST':
        account_no = request.form['accountNo']
        ifsc = request.form['ifsc']
        amount = request.form['amount']
        # TODO: Add logic to store transaction / verify / respond
        flash(f'₹{amount} is scheduled to be transferred to {account_no} ({ifsc})', 'success')
        return redirect('/transfer')
    return render_template('transfer.html')


# Profile Page (Shows submitted user details)
@app.route('/profile')
def profile():
    user_email = session.get('user_email')

    if not user_email:
        flash("Please submit your loan application first.", "warning")
        return redirect(url_for('apply'))

    user = collection.find_one({'email': user_email})

    if not user:
        flash("User data not found.", "danger")
        return redirect(url_for('apply'))

    return render_template('profile.html', user=user)

# Customer Care Page
@app.route('/customer-care')
def customer_care():
    return render_template('customer_care_page.html')


# User Login Page using existing loan_applications data
@app.route('/userlogin', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Mobile number

        user = collection.find_one({'name': username, 'mobile': password})

        if user:
            session['logged_user_name'] = user['name']
            session['logged_user_mobile'] = user['mobile']
            flash("✅ Login successful!", "success")
            return redirect(url_for('user_dashboard'))
        else:
            flash("❌ Invalid name or mobile number.", "danger")
            return redirect(url_for('user_login'))

    return render_template('user_login.html')


@app.route('/user-dashboard')
def user_dashboard():
    if 'logged_user_name' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('user_login'))

    user = collection.find_one({
        'name': session['logged_user_name'],
        'mobile': session['logged_user_mobile']
    })

    if not user:
        flash("❌ User data not found.", "danger")
        return redirect(url_for('user_login'))

    return render_template('user_dashboard.html', user=user)



# Run the App
if __name__ == '__main__':
    app.run(debug=True)

# Only used if running manually (not with Gunicorn)
if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 80, app, use_debugger=True, use_reloader=True)

