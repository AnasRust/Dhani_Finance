from urllib.parse import quote_plus
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session
from pymongo import MongoClient
import datetime

username = quote_plus("dhani_admin")
password = quote_plus("Anascool@2001")  # use your actual password

uri = f"mongodb+srv://{username}:{password}@finance.1osnvho.mongodb.net/?retryWrites=true&w=majority&appName=Finance"
client = MongoClient(uri)

db = client["Dhani_Finance"]
collection = db["loan_applications"]


app = Flask(__name__)
app.secret_key = 'dhani_secret_2025' 

# Homepage Route
@app.route('/')
def home():
    return render_template("index.html")

# Loan Application Route
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

            # Mask Aadhaar and PAN
            masked_aadhaar = mask_aadhaar(aadhaar)
            masked_pan = mask_pan(pan)

            # Create document
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

            # Insert into MongoDB
            collection.insert_one(application)

            flash("🎉 Application submitted successfully!", "success")
            return redirect(url_for('success'))

        except Exception as e:
            flash("❌ Error: " + str(e), "danger")
            return redirect(url_for('apply'))

    return render_template("apply.html")


# Admin Dashboard Route
@app.route('/admin')
def admin():
    try:
        applications = list(collection.find())
        for application in applications:
            application['loan_amount_fmt'] = f"{int(application['loan_amount']):,}" if application.get("loan_amount") else "0"
            application['status'] = 'Approved'
        return render_template("admin_dashboard.html", apps=applications)
    except Exception as e:
        return f"Admin Page Error: {str(e)}", 500
    

@app.route('/success')
def success():
    return render_template("success.html")



# Nav bar Route's
@app.route('/our-story')
def our_story():
    return render_template('our_story.html')

@app.route('/loan/car')
def loan_car():
    latest = collection.find().sort("submitted_at", -1).limit(1)
    return render_template('loan_car.html', recent=latest)


@app.route('/loan/home')
def loan_home():
    latest = collection.find().sort("submitted_at", -1).limit(1)
    return render_template('loan_home.html', recent=latest)

@app.route('/loan/personal')
def loan_personal():  # ✅ Unique function name
    latest = collection.find().sort("submitted_at", -1).limit(1)
    return render_template('loan_personal.html', recent=latest)

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')


# Aadhaar Masking
def mask_aadhaar(aadhaar):
    return "XXXX-XXXX-" + aadhaar[-4:]

# PAN Masking
def mask_pan(pan):
    return "XXXXX" + pan[-5:]

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
