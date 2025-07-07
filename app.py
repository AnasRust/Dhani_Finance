from urllib.parse import quote_plus
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
import datetime
from reportlab.pdfgen import canvas
from flask import make_response
import io

app = Flask(__name__)
app.secret_key = 'supersecret'  # Needed for flash messages and sessions

# MongoDB Atlas connection
username = quote_plus("dhani_admin")
password = quote_plus("Anascool@2001")
uri = f"mongodb+srv://{username}:{password}@finance.1osnvho.mongodb.net/?retryWrites=true&w=majority&tls=true&appName=Finance"
client = MongoClient(uri)
db = client["Dhani_Finance"]
collection = db["loan_applications"]

# Homepage Route
@app.route('/')
def home():
    return render_template("index.html")

# Loan Application Route
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        try:
            import os
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

            # PDF generation
            from reportlab.pdfgen import canvas
            pdf_dir = os.path.join("static", "pdfs")
            os.makedirs(pdf_dir, exist_ok=True)

            filename = f"{name.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, filename)

            c = canvas.Canvas(pdf_path)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(180, 800, "DhrmaFinance Ltd")
            c.setFont("Helvetica", 12)
            c.drawString(100, 770, "Loan Application Acknowledgment")

            c.setFont("Helvetica", 10)
            c.drawString(50, 730, f"Name: {name}")
            c.drawString(50, 710, f"Email: {email}")
            c.drawString(50, 690, f"Mobile: {mobile}")
            c.drawString(50, 670, f"Aadhaar: {masked_aadhaar}")
            c.drawString(50, 650, f"PAN: {masked_pan}")
            c.drawString(50, 630, f"Bank Account: {bank_account}")
            c.drawString(50, 610, f"IFSC: {ifsc}")
            c.drawString(50, 590, f"Loan Amount: ₹{loan_amount}")

            c.setFont("Helvetica-Oblique", 10)
            c.drawString(50, 550, "This document acknowledges your submission of details to DhrmaFinance Ltd.")
            c.drawString(50, 535, "We hereby confirm no objection to processing your application with the above data.")
            c.drawString(50, 520, "For any queries, contact support@dhrmafinanceltd.co.in")

            c.setFont("Helvetica", 8)
            c.drawString(50, 480, "Generated on: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            c.save()

            return redirect(url_for('success', filename=filename))

        except Exception as e:
            flash("❌ Error: " + str(e), "danger")
            return redirect(url_for('apply'))

    return render_template("apply.html")

@app.route('/success')
def success():
    filename = request.args.get('filename')
    return render_template("success.html", filename=filename)

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

# Aadhaar Masking
def mask_aadhaar(aadhaar):
    return "XXXX-XXXX-" + aadhaar[-4:]

# PAN Masking
def mask_pan(pan):
    return "XXXXX" + pan[-5:]

# ✅ New Page Routes
@app.route('/loan')
def loan():
    return render_template("loan.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
