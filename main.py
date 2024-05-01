############################ IMPORT #################################
# pip install Flask-SQLAlchemy
from flask import Flask, render_template, redirect, request, url_for,flash, jsonify,send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_restful import Resource,Api,fields,marshal_with,reqparse
from werkzeug.security import generate_password_hash, check_password_hash
import json 
import requests
from jinja2 import Template
# from flask_cors import CORS
from datetime import datetime
import os
import datetime
import re
from base64 import b64decode
from flask import Flask
import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from flask import session
import secrets
from functools import wraps



########################### CONFIGURATION ############################


app = Flask(__name__)
# CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/subbu/Desktop/Library Mangement System V2/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = './templates/book_files/'
app.config['SECRET_KEY']='The book was on the table'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.secret_key='librarykey'
current_date_time = datetime.now()

# Extract the current date
current_date = current_date_time.date()


api = Api(app)

db = SQLAlchemy(app)  #creating a model db

def require_api_token(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        # Check to see if it's in their session
        if 'api_session_token' not in session:
            # If it isn't return our access denied message (you can also return a redirect or render_template)
            return jsonify({"Status": "Access denied"})

        # Otherwise just send them where they wanted to go
        return func(*args, **kwargs)

    return check_token

########################### MODELS ###############################
    
class Section(db.Model):
  section_id = db.Column(db.Integer, primary_key=True, autoincrement = True,unique=True, nullable = False)
  name = db.Column(db.String, nullable=False)
  date_created = db.Column(db.String, nullable=True)
  description = db.Column(db.String, nullable=False)


class Books(db.Model):
  book_id = db.Column(db.Integer,
                   nullable=False,primary_key=True, autoincrement = True,unique=True)
  title = db.Column(db.String,
                        nullable=False)
  author=db.Column(db.String, nullable=False)
  isbn=db.Column(db.Integer, nullable=False)
  section_id=db.Column(db.Integer,db.ForeignKey("section.section_id"), nullable=False)
  publication_year=db.Column(db.Integer, nullable = False)
  rating=db.Column(db.Integer, nullable = False)
  volume=db.Column(db.Integer, nullable = False)
  pages=db.Column(db.Integer, nullable = False)
  file_path = db.Column(db.String, nullable = False, unique = True)

class Member(db.Model):
  member_id = db.Column(db.Integer,
                      nullable=False,
                      unique=True,
                      primary_key=True, autoincrement = True)
  name= db.Column(db.String,
                   nullable=False)
  email = db.Column(db.String, nullable=False)
  phone_number = db.Column(db.Integer, nullable=False)
  username=db.Column(db.String, nullable=False, unique=True)
  password=db.Column(db.String, nullable=False)
  type=db.Column(db.String, nullable=True)
  last_visited=db.Column(db.String, nullable=True)


class Transaction(db.Model):
  transaction_id = db.Column(db.Integer,
                       nullable=False,
                       unique=True,
                       primary_key=True, autoincrement=True)
  book_id=db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable = False)
  member_id=db.Column(db.Integer, db.ForeignKey("member.member_id"), nullable = False)
  issued_date = db.Column(db.String,
                      nullable=False)
  return_date = db.Column(db.String, nullable=False)
  due_date = db.Column(db.String, nullable=False)
  overdue = db.Column(db.Integer, nullable=False)
  rating_given = db.Column(db.Integer, nullable = False)


###################################### Data Validation Fns #############################
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validemail(email):
  valid_email = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
  if re.match(valid_email,email):
    return True
  return False

########################### MODELS-API ##############################


########################### APP ROUTE FNS ###############################
########################### WELCOME ###################################
### CORS section
@app.after_request
def after_request_func(response):
    origin = request.headers.get('Origin')
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'x-csrf-token')
        response.headers.add('Access-Control-Allow-Methods',
                            'GET, POST, OPTIONS, PUT, PATCH, DELETE')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)

    return response
    ### end CORS section



@app.route('/templates/<path:path>')
def send_templates(path):
    return send_from_directory('templates', path)

@app.route('/',methods=['GET'])

########################### LOGIN ###################################

@app.route('/login/<username>', methods=['GET', 'POST','OPTIONS'])
def loginbyusername(username):
    session['api_session_token'] = secrets.token_urlsafe(32)
    data = request.get_json()
    customer= Member.query.filter_by(username=username).first()
    if customer is None:
        return jsonify({'status': -5, 'Reason': 'MemberNotFound'})
    else:
        if customer.password == data['password']:
            members_list = {'id': customer.member_id, 'name':customer.name, 'email': customer.email, 'phone_number': customer.phone_number,'username': customer.username,'type':customer.type,'last_visited':customer.last_visited}
            return jsonify({'status':1,'member': members_list})
        else:
            return jsonify({'status': -7, 'Reason': 'Incorrect Password'})
    

@app.route('/logout', methods=['POST'])
@require_api_token
def logout():
    session.pop('api_session_token',None)
    return redirect('templates/login.html')
########################### SIGNUP  ##############################

@app.route('/signup', methods=['GET', 'POST'])
@require_api_token
def signup():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = Member(name=data['name'],phone_number=data['phone_number'], type='Customer',username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'})

########################### Books - API   ##############################

@app.route('/books', methods=['GET'])
@require_api_token
def getbooks():
    allbooks = Books.query.all()
    books_list = [{'id': book.book_id, 'title':book.title ,'author': book.author, 'isbn': book.isbn,'section_id': book.section_id,'publication_year': book.publication_year, 'rating': book.rating, 'volume': book.volume, 'pages': book.pages, 'file_path':book.file_path} for book in allbooks]
    return jsonify({'allbooks': books_list})

@app.route('/<int:id>/books', methods=['GET','POST'])
@require_api_token
def getbooksbyid(id):
    book = Books.query.filter_by(book_id=id).first()
    if book is None:
        return jsonify({'status': -2, 'Reason': 'BookNotFound'})
    else:
        book_list = {'id': book.book_id, 'title':book.title, 'author': book.author, 'isbn': book.isbn,'section_id': book.section_id,'publication_year': book.publication_year, 'rating': book.rating, 'volume': book.volume, 'pages': book.pages, 'file_path':book.file_path}
        return jsonify({'book_details': book_list})
    
@app.route('/books/<int:id>/section', methods=['GET','POST'])
@require_api_token
def getbooksbysectid(id):
    books = Books.query.filter_by(section_id=id).all()
    if books is None:
        return jsonify({'status': -2, 'Reason': 'BookNotFound'})
    else:
        book_list = [{'id': book.book_id, 'title':book.title, 'author': book.author, 'isbn': book.isbn,'section_id': book.section_id,'publication_year': book.publication_year, 'rating': book.rating, 'volume': book.volume, 'pages': book.pages, 'file_path':book.file_path}for book in books]
        return jsonify({'book_details': book_list})

@app.route('/book/add', methods=['POST'])
@require_api_token
def addbook():
    data = request.get_json()
    if 'file_path' not in data:
        return jsonify({'error': 'No file part'})
    b=Books(title=data['title'],author=data['author'],isbn=data['isbn'],section_id=data['section_id'],publication_year=data['publication_year'],rating=data['rating'],volume=data['volume'],pages=data['pages'], file_path = data['file_path'])
    file = data['pdfFile']
    header, encoded = file.split("base64,", 1)
    file_data = b64decode(encoded)
    if data['file_path'] == '':
        return jsonify({'error': 'No selected file'})
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], data["file_path"])
        with open(file_path, "wb") as f:
            f.write(file_data)
        db.session.add(b)
        db.session.commit()
        return jsonify({'status': 'Success', 'file_path': file_path, 'filename': data["file_path"]})

@app.route('/book/<int:id>/update', methods=['PUT'])
@require_api_token
def updatebook(id):
    data = request.get_json()
    b=Books.query.filter_by(book_id=id).first()
    file = data['pdfFile']
    header, encoded = file.split("base64,", 1)
    file_data = b64decode(encoded)
    if data['file_path'] == '':
        return jsonify({'error': 'No selected file'})
    if b is None:
        return jsonify({'status': -2, 'Reason': 'BookNotFound'})
    else:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], data["file_path"])
        with open(file_path, "wb") as f:
            f.write(file_data)
        b.title=data['title']
        b.author=data['author']
        b.isbn=data['isbn']
        b.section_id=data['section_id']
        b.publication_year=data['publication_year']
        b.rating=data['rating']
        b.volume=data['volume']
        b.pages=data['pages']
        b.file_path = data['file_path']
        db.session.add(b)
        db.session.commit()
        return jsonify({'status': 'Success'})
    

@app.route('/bookrate/<int:id>/<int:o_id>/update', methods=['PUT'])
@require_api_token
def updateratingofbook(id,o_id):
    data = request.get_json()
    book=Books.query.filter_by(book_id=id).first()
    order=Transaction.query.filter_by(transaction_id=o_id).first()
    if book is None:
        return jsonify({'status': -2, 'Reason': 'BookNotFound'})
    if order.rating_given == 1:
        return jsonify({'status': -10, 'Reason': 'AlreadyRated'})
    else:
        oord = {'transaction_id': order.transaction_id, 'book_id':order.book_id, 'member': order.member_id, 'issued_date':order.issued_date,'return_date':order.return_date, 'due_date':order.due_date, 'overdue':order.overdue, 'rating_given':order.rating_given}
        book_list = {'id': book.book_id, 'title':book.title, 'author': book.author, 'isbn': book.isbn,'section_id': book.section_id,'publication_year': book.publication_year, 'rating': book.rating, 'volume': book.volume, 'pages': book.pages, 'file_path':book.file_path}
        c=len(oord)
        current_rating = book.rating
        given_rating = int(data['rating'])
        new_rating = (current_rating*c+given_rating)/(c+1)
        book.title=book.title
        book.author=book.author
        book.isbn=book.isbn
        book.section_id=book.section_id
        book.publication_year=book.publication_year
        book.rating=new_rating
        book.volume=book_list['volume']
        book.pages=book_list['pages']
        book.file_path = book_list['file_path']
        order.rating_given = 1
        db.session.add(book)
        db.session.add(order)
        db.session.commit()
        return jsonify({'status': 'Success'})
    

@app.route('/book/<int:id>/delete', methods=['DELETE'])
@require_api_token
def deletebook(id):
    b=Books.query.filter_by(book_id=id).first()
    if b is None:
        return jsonify({'status': -2, 'Reason': 'BookNotFound'})
    else:
        db.session.delete(b)
        db.session.commit()
        return jsonify({'status': 'Success'})


########################### Member - API   ##############################

@app.route('/member', methods=['GET', 'POST','OPTIONS'])
@require_api_token
def getmember():
    allmembers = Member.query.all()
    members_list = [{'id': customer.member_id, 'name':customer.name, 'email': customer.email, 'phone_number': customer.phone_number,'username': customer.username,'password': customer.password,'type':customer.type,'last_visited':customer.last_visited} for customer in allmembers]
    return jsonify({'allmembers': members_list})

@app.route('/member/<int:id>', methods=['GET', 'POST','OPTIONS'])
@require_api_token
def getmemberbyid(id):
    data = request.get_json()
    customer= Member.query.filter_by(member_id=id).first()
    if customer is None:
        return jsonify({'status': -5, 'Reason': 'MemberNotFound'})
    else:
        members_list = {'id': customer.member_id, 'name':customer.name, 'email': customer.email, 'phone_number': customer.phone_number,'username': customer.username,'password': customer.password,'type':customer.type,'last_visited':customer.last_visited}
        return jsonify({'member': members_list})
    
@app.route('/member/<username>', methods=['GET', 'POST','OPTIONS'])
@require_api_token
def getmemberbyusername(username):
    data = request.get_json()
    customer= Member.query.filter_by(username=username).first()
    if customer is None:
        return jsonify({'status': -5, 'Reason': 'MemberNotFound'})
    else:
        members_list = {'id': customer.member_id, 'name':customer.name, 'email': customer.email, 'phone_number': customer.phone_number,'username': customer.username,'type':customer.type,'last_visited':customer.last_visited}
        return jsonify({'member': members_list})



@app.route('/member/add', methods=['POST'])
@require_api_token
def addmember():
    data = request.get_json()
    m=Member(name = data['name'], email=data['email'], phone_number=data['phone_number'],username= data['username'],password=data['password'],type=data['type'],last_visited=data['last_visited'])
    db.session.add(m)
    db.session.commit()
    return jsonify({'status': 'Success'})

@app.route('/member/<int:id>/update', methods=['PUT'])
@require_api_token
def updatemember(id):
    data = request.get_json()
    m=Member.query.filter_by(member_id=id).first()
    if m is None:
        return jsonify({'status': -5, 'Reason': 'MemberNotFound'})
    else:
        m.id = data['id']
        m.name =data['name']
        m.email=data['email']
        m.phone_number=data['phone_number']
        m.username=data['username']
        m.password=data['password']
        m.type=data['type']
        m.last_visited=data['last_visited']
        db.session.add(m)
        db.session.commit()
        return jsonify({'status': 'Success'})

@app.route('/member/<int:id>/delete', methods=['DELETE'])
@require_api_token
def deletemember(id):
    m=Member.query.filter_by(member_id=id).first()
    if m is None:
        return jsonify({'status': -5, 'Reason': 'MemberNotFound'})
    else:
        db.session.delete(m)
        db.session.commit()
        return jsonify({'status': 'Success'})

########################### Section - API   ##############################

@app.route('/section', methods=['GET', 'POST'])
@require_api_token
def getsection():
    allsection = Section.query.all()
    sections_list = [{'section_id': s.section_id, 'name':s.name, 'date_created': s.date_created, 'description':s.description} for s in allsection]
    return jsonify({'allsections': sections_list})

@app.route('/section/<int:id>', methods=['GET', 'POST'])
@require_api_token
def getsectionbyid(id):
    s= Section.query.filter_by(section_id=id).first()
    if s is None:
        return jsonify({'status': -4, 'Reason': 'SectionNotFound'})
    else:
        section_list = {'section_id': s.section_id, 'name':s.name, 'date_created': s.date_created, 'description':s.description}
        return jsonify({'section': section_list})

@app.route('/section/add', methods=['POST'])
@require_api_token
def addsection():
    data = request.get_json()
    s=Section(name=data['name'], date_created=data['date_created'], description=data['description'])
    db.session.add(s)
    db.session.commit()
    return jsonify({'status': 'Success'})

@app.route('/section/<int:id>/update', methods=['PUT'])
@require_api_token
def updatesection(id):
    data = request.get_json()
    s=Section.query.filter_by(section_id=id).first()
    if s is None:
        return jsonify({'status': -4, 'Reason': 'SectionNotFound'})
    else:
        s.name =data['name']
        s.description=data['description']
        db.session.add(s)
        db.session.commit()
        return jsonify({'status': 'Success'})

@app.route('/section/<int:id>/delete', methods=['DELETE'])
@require_api_token
def deletesection(id):
    s=Section.query.filter_by(section_id=id).first()
    b=Books.query.filter_by(section_id=id).all()
    if s is None:
        return jsonify({'status': -4, 'Reason': 'SectionNotFound'})
    else:
        db.session.delete(s)
        db.session.delete(b)
        db.session.commit()
        return jsonify({'status': 'Success'})
    
@app.route('/section/<int:id>/deletebooks', methods=['DELETE'])
@require_api_token
def deletesectionb(id):
    s=Section.query.filter_by(section_id=id).first()
    b=Books.query.filter_by(section_id=id).all()
    if s is None:
        return jsonify({'status': -4, 'Reason': 'SectionNotFound'})
    else:
        for i in b:
            db.session.delete(i)
        db.session.delete(s)
        db.session.commit()
        return jsonify({'status': 'Success'})

########################### Transaction - API   ##############################

@app.route('/orderdetails', methods=['GET', 'POST'])
@require_api_token
def getorderdetails():
    allorder = Transaction.query.all()
    orders_list = [{'transaction_id': order.transaction_id, 'book_id':order.book_id, 'member': order.member_id, 'issued_date':order.issued_date,'return_date':order.return_date, 'due_date':order.due_date, 'overdue':order.overdue, 'rating_given':order.rating_given} for order in allorder]
    return jsonify({'alltransaction': orders_list})

@app.route('/orderdetails/<int:m_id>', methods=['GET', 'POST'])
@require_api_token
def getorderdetailsbymemberid(m_id):
    orders= Transaction.query.filter_by(member_id=m_id).all()
    if orders is None:
        return jsonify({'status': -3, 'Reason': 'TransactionDetailsNotFound'})
    order_list = [{'transaction_id': order.transaction_id, 'book_id':order.book_id, 'member': order.member_id, 'issued_date':order.issued_date,'return_date':order.return_date, 'due_date':order.due_date, 'overdue':order.overdue, 'rating_given':order.rating_given} for order in orders]
    return jsonify({'order': order_list})

@app.route('/orderdetailsreturned/<int:m_id>', methods=['GET', 'POST'])
@require_api_token
def getorderdetailsretbymemberid(m_id):
    orders = Transaction.query.filter_by(member_id=m_id,return_date="Not Returned").all()
    if not orders:
        return jsonify({'status': -3, 'Reason': 'TransactionDetailsNotFound'})
    
    all_book_info = []
    for order in orders:
        book = Books.query.get(order.book_id)
        if book:
            order_info = {
                'transaction_id': order.transaction_id,
                'book_id': order.book_id,
                'member': order.member_id,
                'issued_date': order.issued_date,
                'return_date': order.return_date,
                'due_date': order.due_date,
                'overdue': order.overdue,
                'book_title': book.title,
                'book_author': book.author,
                'book_isbn': book.isbn,
                'book_pages':book.pages,
                'book_sectionid':book.section_id,
                'rating_given':order.rating_given
            }
            all_book_info.append(order_info)
    
    return jsonify({'order': all_book_info})


@app.route('/orderdetails/<int:o_id>', methods=['GET', 'POST'])
@require_api_token
def getorderdetailsbyid(o_id):
    orders= Transaction.query.filter_by(transaction_id=o_id).all()
    if orders is None:
        return jsonify({'status': -3, 'Reason': 'TransactionDetailsNotFound'})
    order_list = [{'transaction_id': order.transaction_id, 'book_id':order.book_id, 'member': order.member_id, 'issued_date':order.issued_date,'return_date':order.return_date, 'due_date':order.due_date, 'overdue':order.overdue, 'rating_given':order.rating_given} for order in orders]
    return jsonify({'order': order_list})

@app.route('/orderdetails/add', methods=['POST']) # Not updating Product and Order and what to do if Order does not exist
@require_api_token
def addorderdetails():
    data = request.get_json()
    ex = Transaction.query.filter_by(book_id=data['book_id'],member_id=data['member_id'],return_date="Not Returned").first()
    if ex is None:
        od=Transaction(book_id=data['book_id'], member_id= data['member_id'], issued_date=data['issued_date'], return_date=data['return_date'], due_date=data['due_date'], overdue=data['overdue'], rating_given=0)
        db.session.add(od)
        db.session.commit()
        return jsonify({'status': 'Success'})
    else:
        return jsonify({'status': -9, 'Reason': 'DataExist'})

@app.route('/orderdetails/<int:o_id>/<int:m_id>/update', methods=['PUT'])
@require_api_token
def updateorderdetails(o_id,m_id):
    data = request.get_json()
    od=Transaction.query.filter_by(transaction_id=o_id ,member_id = m_id ).first()
    O=Transaction.query.filter_by(transaction_id=o_id).first()
    if od is None:
        return jsonify({'status':-3, 'Reason': 'OrderDetailsNotFound'})
    else:
        od.trasaction_id=data['transaction_id']
        od.book_id=data['book_id']
        od.member_id=data['member_id'] 
        od.issued_date=data['issued_date']
        od.return_date=data['return_date']
        od.due_date=data['due_date']
        od.overdue=data['overdue']
        db.session.add(od)
        db.session.commit()
        return jsonify({'status': 'Success'})
    
@app.route('/orderdetails/<int:o_id>/update', methods=['PUT'])
@require_api_token
def updateorderdetailsbyid(o_id):
    data = request.get_json()
    od=Transaction.query.filter_by(transaction_id=o_id).first()
    if od is None:
        return jsonify({'status':-3, 'Reason': 'OrderDetailsNotFound'})
    else:
        od.return_date=data['return_date']
        db.session.add(od)
        db.session.commit()
        return jsonify({'status': 'Success'})

@app.route('/orderdetails/<int:o_id>/<int:m_id>/<int:b_id>/delete', methods=['DELETE'])
@require_api_token
def deleteorderdetails(o_id,b_id,m_id):
    od=Transaction.query.filter_by(transaction_id=o_id ,member_id = m_id ).first()
    B=Books.query.filter_by(book_id=b_id).first()
    if B is None:
        return jsonify({'status':-2, 'Reason':'BookNotFound'})
    if od is None:
        return jsonify({'status':-3, 'Reason': 'OrderDetailsNotFound'})
    db.session.delete(od)
    db.session.commit()
    return jsonify({'status': 'Success'})

@app.route('/orderdetails/<int:o_id>/delete', methods=['DELETE'])
@require_api_token
def deleteorderdetailsbyorderid(o_id):
    od=Transaction.query.filter_by(transaction_id=o_id).all()
    if od is None:
        return jsonify({'status': -1, 'Reason': 'OrderNotFound'})
    else:
        O=Transaction.query.filter_by(transaction_id=o_id).first()
        for i in od:
            db.session.delete(i)
        db.session.commit()
        return jsonify({'status': 'Success'})
    
@app.route('/bookorderdetails/<int:m_id>', methods=['GET', 'POST'])
@require_api_token
def getinfoofallbooksfromorderdetailsbymember_id(m_id):
    orders = Transaction.query.filter_by(member_id=m_id).all()
    if not orders:
        return jsonify({'status': -3, 'Reason': 'TransactionDetailsNotFound'})
    
    all_book_info = []
    for order in orders:
        book = Books.query.get(order.book_id)
        if book:
            order_info = {
                'transaction_id': order.transaction_id,
                'book_id': order.book_id,
                'member': order.member_id,
                'issued_date': order.issued_date,
                'return_date': order.return_date,
                'due_date': order.due_date,
                'overdue': order.overdue,
                'book_title': book.title,
                'book_author': book.author,
                'book_isbn': book.isbn,
                'book_pages':book.pages,
                'book_sectionid':book.section_id,
                'rating_given':order.rating_given
            }
            all_book_info.append(order_info)
    
    return jsonify({'order': all_book_info})

@app.route('/bookfile/<int:b_id>', methods=['GET', 'POST'])
@require_api_token
def get_file(b_id):
    book = Books.query.filter_by(book_id=b_id).first()
    if book is None:
        return jsonify({'status': -1, 'reason': 'BookNotFound'})
    else:
        b = {'book_id': book.book_id, 'pdf_path': book.file_path}  
        return jsonify({'the_book': b})  
    
@app.route('/login', methods=['GET', 'POST','OPTIONS'])
def login():
    data = request.get_json()
    user = Member.query.filter_by(username=data['username'], type="General Customer").first()
    libuser = Member.query.filter_by(username=data['username'], type="Librarian").first()

    if user and check_password_hash(user.password, data['password']):
        return jsonify({'status':100,'message': 'Login successful'})
    elif libuser and check_password_hash(libuser.password, data['password']):
        return jsonify({'status':200,'message': 'Librarian login successful'})
    else:
        return jsonify({'status':404,'message': 'Login failed. Check your username and password'})
####################################### SCHEDULE JOBS ############################
import smtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Template

def create_report(id):
    all_books = Transaction.query.filter_by(member_id=id).all()
    overdue_books = Transaction.query.filter_by(member_id=id, overdue=1).all()
    all_order_list = [{'transaction_id': order.transaction_id, 'book_id':order.book_id, 'member': order.member_id, 'issued_date':order.issued_date, 'return_date':order.return_date, 'due_date':order.due_date, 'overdue':order.overdue, 'rating_given':order.rating_given} for order in all_books]
    overdue_order_list = [{'transaction_id': order.transaction_id, 'book_id':order.book_id, 'member': order.member_id, 'issued_date':order.issued_date, 'return_date':order.return_date, 'due_date':order.due_date, 'overdue':order.overdue, 'rating_given':order.rating_given} for order in overdue_books]

    html_template = """
    <html>
    <head><title>Activity Report</title></head>
    <body>
    <h1>Monthly Activity Report</h1>

    <h2>All Books</h2>
    <table border="1">
    <tr>
    <th>Transaction ID</th>
    <th>Book ID</th>
    <th>Member ID</th>
    <th>Issued Date</th>
    <th>Return Date</th>
    <th>Due Date</th>
    <th>Overdue</th>
    <th>Rating Given</th>
    </tr>
    {% for order in all_order_list %}
    <tr>
    <td>{{ order.transaction_id }}</td>
    <td>{{ order.book_id }}</td>
    <td>{{ order.member }}</td>
    <td>{{ order.issued_date }}</td>
    <td>{{ order.return_date }}</td>
    <td>{{ order.due_date }}</td>
    <td>{{ order.overdue }}</td>
    <td>{{ order.rating_given }}</td>
    </tr>
    {% endfor %}
    </table>

    <h2>Overdue Books</h2>
    <table border="1">
    <tr>
    <th>Transaction ID</th>
    <th>Book ID</th>
    <th>Member ID</th>
    <th>Issued Date</th>
    <th>Return Date</th>
    <th>Due Date</th>
    <th>Overdue</th>
    <th>Rating Given</th>
    </tr>
    {% for order in overdue_order_list %}
    <tr>
    <td>{{ order.transaction_id }}</td>
    <td>{{ order.book_id }}</td>
    <td>{{ order.member }}</td>
    <td>{{ order.issued_date }}</td>
    <td>{{ order.return_date }}</td>
    <td>{{ order.due_date }}</td>
    <td>{{ order.overdue }}</td>
    <td>{{ order.rating_given }}</td>
    </tr>
    {% endfor %}
    </table>

    </body>
    </html>
    """

    rendered_html = Template(html_template).render(all_order_list=all_order_list, overdue_order_list=overdue_order_list)
    return rendered_html

def send_email_reminder():
    with app.app_context():
        current_date = datetime.now().strftime('%Y-%m-%d')  # Get current date
        allmembers = Member.query.all()
        members_list = [{'id': customer.member_id, 'name':customer.name, 'email': customer.email, 'phone_number': customer.phone_number,'username': customer.username,'password': customer.password,'type':customer.type,'last_visited':customer.last_visited} for customer in allmembers]
        for i in members_list:
            if i['last_visited'] != current_date:
                reminder_message = "Hi there! Don't forget to visit our app today."
                msg = MIMEText(reminder_message)
                msg['Subject'] = 'Reminder: Visit Our App'
                msg['From'] = 'vs.projectdevelopment@gmail.com'
                msg['To'] = i['email']
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.connect("smtp.gmail.com",465)
                    smtp.login('vs.projectdevelopment', 'hyvq ijnb wmma ohjg')
                    smtp.send_message(msg)


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path

def send_email_report():
    with app.app_context():
        allmembers = Member.query.all()
        members_list = [{'id': customer.member_id, 'name': customer.name, 'email': customer.email, 'phone_number': customer.phone_number, 'username': customer.username, 'password': customer.password, 'type': customer.type, 'last_visited': customer.last_visited} for customer in allmembers]
        for i in members_list:
            msg = MIMEMultipart()
            msg['Subject'] = 'Report'
            msg['From'] = 'vs.projectdevelopment@gmail.com'
            msg['To'] = i['email']

            html_content = create_report(i['id'])  
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('vs.projectdevelopment', 'hyvq ijnb wmma ohjg')
                smtp.send_message(msg)

# Define your app name
APP_NAME = "Library"

# Schedule the job to run
scheduler = BackgroundScheduler()
scheduler.add_job(send_email_reminder, 'cron', hour=18) 
scheduler.add_job(send_email_report,'cron',day=1) # Adjust the hour as per your preference
scheduler.start()
scheduler.shutdown()

# send_email_reminder()
# send_email_report()



########################### RUN ###################################

if __name__ == '__main__':
  #app.run(debug=True)
  app.debug=True
  app.run(host='0.0.0.0', port='8081')