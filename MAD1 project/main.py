from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, session, url_for, abort
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import request

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisismysecretkey'
app.config['PASSWORD_HASH'] = "sha512"
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()


class Admin(db.Model):
    __tablename__='Admin'
    id= db.Column(db.Integer , primary_key=True)
    username=db.Column(db.String(20),unique=True,nullable=False)
    passhash = db.Column(db.String(256),nullable=False)

class Professional(db.Model):
    __tablename__='Professional'
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    passhash = db.Column(db.String(70),nullable=False)
    name = db.Column(db.String(50),unique=True,nullable=True)
    experience = db.Column(db.Integer , nullable=False)
    address = db.Column(db.String , nullable=False)
    pincode = db.Column(db.Integer , nullable=False)
    status=db.Column(db.String(20),default="pending")

class Customer(db.Model):
    __tablename__='Customer'
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    passhash=db.Column(db.String(70),nullable=False)
    name=db.Column(db.String(50),unique=True,nullable=False)
    address=db.Column(db.String(100) , nullable=False)
    pincode = db.Column(db.String(10),nullable=False)
    fraudulent_reports = db.Column(db.Integer , default=0)
    status=db.Column(db.String(20),default="active")
    admin_id = db.Column(db.Integer , db.ForeignKey('Admin.id') , nullable=True)

class Service(db.Model):
    __tablename__ = 'Service'
    id = db.Column(db.Integer , primary_key = True , autoincrement=True)
    name = db.Column(db.String(50), unique=True,nullable=False )
    description = db.Column(db.String(250) , nullable=True)
    base_price = db.Column(db.Integer,nullable=False)
    time_required = db.Column(db.String(50) , nullable=False)

class ServiceRequest(db.Model):
    __tablename__='ServiceRequest'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_id = db.Column(db.Integer, db.ForeignKey('Service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)
    professional_id = db.Column(db.Integer , db.ForeignKey('Professional.id'),nullable=True)
    date_of_request = db.Column(db.DateTime, nullable=False)
    date_of_completion = db.Column(db.DateTime, nullable=True)
    service_status = db.Column(db.String(20), default='requested')
    customer_rating = db.Column(db.Integer,nullable=True)

    service = db.relationship('Service', backref=db.backref('requests', lazy=True))
    customer = db.relationship('Customer', backref=db.backref('requests', lazy=True))
    professional = db.relationship('Professional', backref=db.backref('requests', lazy=True))


with app.app_context():
    db.create_all()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")

@app.route('/home')
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login_admin')
def login_admin():
    return render_template('login_admin.html')

@app.route('/login_admin',methods=['POST'])
def login_admin_post():
    username=request.form.get('username')
    password=request.form.get('password')
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            flash("Logged in successfully as Admin.", "success")
            return render_template('admin_dashboard.html') 
    else:
        flash("Invalid username or password.", "danger")

    return render_template('login_admin.html')

@app.route('/login_professional')
def login_professional():
    return render_template('login_professional.html')

@app.route('/login_professional',methods=['POST','GET'])
def login_professional_post():
    name = request.form.get('name')
    password = request.form.get('password')
    if not name or not password:
        flash('Please fill out the fields',"danger")
        return render_template('login_professional.html')
        
    professional = Professional.query.filter_by(name=name).first()

    if not professional:
        flash('Professional does not exist!',"danger")
        return redirect(url_for('login_professional'))

    if not check_password_hash(professional.passhash,password):
        flash('Incorrect password',"danger")
        return redirect(url_for('login_professional'))
        
    if professional.status != 'approved':
        flash('Your account is not approved by admin.','error')
        return redirect(url_for('login_professional'))
    
    session['professional_id']=professional.id
    session['professional_logged_in'] = True
    flash('Login Successful','success')
    return redirect(url_for('professional_dashboard'))
    

@app.route('/login_customer')
def login_customer():
    return render_template("login_customer.html")

@app.route('/login_customer',methods=['POST'])
def login_customer_post():
    name = request.form.get('name')
    password = request.form.get('password')

    if not name or not password:
        flash('Please fill out the fields',"danger")
        return render_template('login_customer.html')
    
    customer = Customer.query.filter_by(name=name).first()

    if not customer:
        flash('Customer does not exist!',"danger")
        return redirect(url_for('login_customer'))

    if not check_password_hash(customer.passhash,password):
        flash('Incorrect password',"danger")
        return redirect(url_for('login_customer'))
    
    session['customer_id']=customer.id
    session['customer_logged_in']=True
    flash('Login Successful','success')
    return redirect(url_for('customer_dashboard'))
     


@app.route('/customer/signup')
def register_customer():
    return render_template("customer_signup.html")

@app.route('/professional/signup')
def register_professional():
    return render_template("professional_signup.html")

@app.route('/professional/signup',methods=['GET','POST'])
def register_professional_post():
    if request.method=="POST":
        password = request.form.get('password')
        name = request.form.get('name')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        experience=request.form.get('experience')

        if  not password or not name or not address or not experience :
            flash('Please fill out this fields',"danger")
            return redirect(url_for('register_professional'))

        profs = Professional.query.filter_by(name=name).first()
        if profs:
            flash('Professional already exists',"danger")
            return render_template('professional_signup.html')
        
        password_hash=generate_password_hash(password)
        new_professional = Professional( passhash=password_hash , name=name , experience=experience , address=address , pincode=pincode ,  status="pending") 
        db.session.add(new_professional)
        db.session.commit()
        flash("Registration successful! Wait for Admin approval", "info")
        return redirect(url_for('login_professional'))

    return render_template('professional_signup.html')

@app.route('/customer/signup',methods=['POST'])
def register_customer_post():
    password = request.form.get('password')
    name = request.form.get('name')
    address = request.form.get('address')
    pincode = request.form.get('pincode')

    if  not password or not name or not address:
        flash('Please fill out this fields',"danger")
        return redirect(url_for('register_customer'))

    cust=Customer.query.filter_by(name=name).first()
    if cust:
        flash('Customer already exists!',"danger")
        return render_template('customer_signup.html')
    
    password_hash=generate_password_hash(password)
    new_customer = Customer( passhash=password_hash , name=name , address=address , pincode=pincode) 
    print(new_customer)
    db.session.add(new_customer)
    db.session.commit()
    return redirect(url_for('login_customer'))

@app.route('/admin/dashboard',methods=['GET','POST'])
def admin_dashboard():  
    services=Service.query.all()
    pending_professionals =Professional.query.filter_by(status='pending').all()
    customers = Customer.query.all()
    professionals = Professional.query.all()
    if request.method=="POST":
        professional_id = request.form.get('professional_id')
        action = request.form.get('action')
        professional = Professional.query.get(professional_id)

        if professional:
            if action == 'approve':
                professional.status = 'approved'
                flash('Professional approved successfully!', 'success')
            elif action == 'reject':
                professional.status = 'rejected'
                flash('Professional rejected successfully!', 'success')
            db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template("admin_dashboard.html",pending_professionals=pending_professionals,services=services,customers=customers,professionals=professionals)

@app.route('/admin/add_service',methods=['GET','POST'])
def add_service():
    name = request.form.get('name')
    desc = request.form.get('description')
    price = request.form.get('price')
    time = request.form.get('time_required')

    if not price or not name or not time:
        flash("Please fill out this fields","danger")
        return render_template("add_service.html") 
    
    add=Service.query.filter_by(name=name).first()
    if add:
        flash('Service already exists',"danger")
        return render_template('add_service.html')
    
    new_service = Service(name=name , description = desc , base_price = int(price), time_required=time)
    db.session.add(new_service)
    db.session.commit()
    flash("Service added successfully!","success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_service/<int:service_id>',methods=['GET','POST'])
def update_service(service_id):
    service = Service.query.get_or_404(service_id)

    if request.method == "POST":
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.base_price = request.form.get('price')
        service.time_required = request.form.get('time_required')

        db.session.commit()
        flash('Service updated successfully',"success")
        return redirect(url_for('admin_dashboard'))
    return render_template('update_service.html',service=service)

@app.route('/admin/delete_service/<int:service_id>',methods=["POST"])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)

    db.session.delete(service)
    db.session.commit()
    flash('Service deleted Successfully',"success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_all' , methods=["POST"])
def delete_all():
    db.session.query(Service).delete()
    db.session.commit()
    return render_template('admin_dashboard.html')

@app.route('/customer_dashboard',methods=['GET',"POST"])
def customer_dashboard():
    if not session.get('customer_id'):
        flash('Please log in first', 'error')
        return redirect(url_for('login_customer'))
    
    customer_id =session['customer_id']
    customer = Customer.query.get(customer_id)
    
    all_services = Service.query.all()
    service_requests = ServiceRequest.query.filter_by(customer_id=customer_id).all()

    if request.method=='POST':
        service_id = request.form.get('service_id')
        date_of_request=datetime.now()

        newrequest = ServiceRequest(service_id = service_id , customer_id=customer_id , date_of_request=date_of_request , service_status="requested",professional_id=None)
        db.session.add(newrequest)
        db.session.commit()

        flash("Service booked Successfully","success")
        return redirect(url_for('customer_dashboard'))
    return render_template('customer_dashboard.html' , customer = customer , all_services=all_services , service_requests=service_requests)

@app.route('/customer/delete_request/<int:request_id>',methods=["POST"])
def delete_service_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    db.session.delete(service_request)
    db.session.commit()

    flash('Service request deleted successfully',"success")
    return redirect(url_for('customer_dashboard'))


@app.route('/professional_dashboard',methods=['GET','POST'])
def professional_dashboard():
    if not session.get('professional_id'):
        flash('Please log in first', 'error')
        return redirect(url_for('login_professional'))
    professional_id= session['professional_id']
    pending_requests = ServiceRequest.query.filter_by(professional_id=None, service_status ="requested").all()
    accepted_requests = ServiceRequest.query.filter_by(professional_id=professional_id, service_status ="in-progress").all()
    completed_requests = ServiceRequest.query.filter_by(professional_id=professional_id, service_status="completed").all()

    customer_id = request.args.get('customer_id') 
    customer=None 

    if customer_id:
        customer = Customer.query.get(customer_id)

    if request.method == "POST":
        request_id = request.form.get('request_id')
        action = request.form.get('action')

        service_request = ServiceRequest.query.get(request_id)

        if service_request:
            if  action == 'accept':
                service_request.professional_id=professional_id
                service_request.service_status = 'in-progress'
            elif action == 'reject':
                service_request.service_status = 'rejected'

            db.session.commit()
        flash(f"Service request {action}ed successfully!", "success")
        return redirect(url_for('professional_dashboard'))
    
    return render_template('professional_dashboard.html',pending_requests = pending_requests,accepted_requests=accepted_requests,completed_requests=completed_requests,customer=customer , customer_id=customer_id)

@app.route('/close_service_request/<int:request_id>',methods=['GET','POST'])
def close_service_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)

    if service_request.service_status != 'in-progress':
        flash('This service request cannot be closed!', 'error')
        return redirect(url_for('customer_dashboard'))
    
    if request.method=="POST":
        rating = int(request.form.get('rating'))
        if 1 <= rating <= 5:
            service_request.customer_rating = rating
            service_request.service_status = 'closed'
            service_request.date_of_completion=datetime.now()

            db.session.commit()
            flash('Service request closed and rating submitted!', 'success')
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Rating must be between 1 and 5!', 'error')
        service_request.service_status = "completed"
        service_request.date_of_completion = datetime.now()
        service_request.customer_rating = rating
        db.session.commit()

    flash("Service request closed and professional rated!", "success")
    return render_template('close_service_request.html', service_request=service_request)

@app.route('/logout_admin')
def logout_admin():
    session.pop('admin_logged_in',None)
    flash("You have been logged out","success")
    return redirect(url_for('login_admin'))

@app.route('/logout_professional')
def logout_professional():
    session.pop('professional_logged_in',None)
    session.pop('professional_id',None)
    flash("You have been logged out","success")
    return redirect(url_for('login_professional'))

@app.route('/logout_customer')
def logout_customer():
    session.pop('customer_logged_in',None)
    session.pop('customer_id',None)
    return redirect(url_for('login_customer'))

@app.route('/search')
def search():
    query=request.args.get('query')
    results = {'customers':[],'services':[]}

    if query:
        customers = Customer.query.filter(Customer.name.ilike(f"%{query}%")).all()
        services = Service.query.filter(Service.name.ilike(f"%{query}%")).all()
        results['customers'] = customers
        results['services']=services
    return render_template('search.html',results=results,query=query)

@app.route('/admin/block_customer/<int:customer_id>',methods=['POST'])
def block_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.status = "blocked"
    db.session.commit()
    flash(f"Customer has been blocked","success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unblock_customer/<int:customer_id>',methods=['POST'])
def unblock_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.status = "active"
    db.session.commit()
    flash(f"Customer has been unblocked","success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/block_professional/<int:professional_id>',methods=['POST'])
def block_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    professional.status = "blocked"
    db.session.commit()
    flash(f"Professional has been blocked","success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unblock_professional/<int:professional_id>',methods=['POST'])
def unblock_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    professional.status = "active"
    db.session.commit()
    flash(f"Professional has been unblocked","success")
    return redirect(url_for('admin_dashboard'))

@app.route('/professional/summary')
def professional_summary():
    if not session.get('professional_logged_in'):
        return redirect(url_for('login_professional'))
    total_requests = ServiceRequest.query.count()
    completed_requests = ServiceRequest.query.filter_by(service_status="completed").count()
    pending_requests = ServiceRequest.query.filter_by(service_status="pending").count()
    return render_template(
        'professional_summary.html',
        total_requests=total_requests,
        completed_requests=completed_requests,
        pending_requests=pending_requests
    )

@app.route('/admin/summary')
def admin_summary():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login_admin'))
    approved_professionals = Professional.query.filter_by(status="approved").count()
    pending_professionals = Professional.query.filter_by(status="pending").count()
    blocked_professionals = Professional.query.filter_by(status="blocked").count()
    return render_template("admin_summary.html" , approved_professionals=approved_professionals , pending_professionals=pending_professionals , blocked_professionals=blocked_professionals)

@app.route("/customer/summary")
def customer_summary():
    if not session.get('customer_logged_in'):
        return redirect(url_for('login_customer'))
    total_services = Service.query.count()
    booked_services = ServiceRequest.query.filter_by(customer_id=session['customer_id']).count()
    return render_template("customer_summary.html",total_services=total_services , booked_services=booked_services)

if __name__ == '__main__':
    app.run(debug=True)

