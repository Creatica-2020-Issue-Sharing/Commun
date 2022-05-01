from re import S
from flask import Flask, render_template, url_for, flash, redirect, request, session
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt

from werkzeug.utils import secure_filename

import os
import uuid

from sqlalchemy import func

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from sqlalchemy import Column, Integer, DateTime, String, Text

from models import User, Issue, Link, Discussion, Community

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret"
app.config['UPLOAD_FOLDER'] = './static/uploads'
bcrypt = Bcrypt(app)

Base = declarative_base()


db_uri = os.environ['DATABASE_URL'].replace("postgresql://", "cockroachdb://")
try:
    engine = create_engine(db_uri)
except Exception as e:
    print("Failed to connect to database.")
    print(f"{e}")

Session = sessionmaker(bind=engine)

currentIssue = {}

@app.route('/', methods= ['GET', 'POST'])
@app.route('/home', methods= ['GET', 'POST'])
def home():
    if request.method == 'GET':
        #orderByRecent = run_transaction(Session, lambda s: getOrderByRecent(s, ''))

        return render_template('index.html')
    else:
        if request.form['chosen'] == '':
            searchInput = request.form['communitySearch']
            print('POST' + searchInput)
            orderByRecent = run_transaction(sessionmaker(bind=engine), lambda s: getOrderByRecent(s, searchInput.lower().strip()))
        else:
            issueID = request.form['chosen']
            run_transaction(Session, lambda s : setIssue(s, issueID))
            return redirect(url_for('issue'))

        return render_template('index.html', issues = orderByRecent, searchInput = searchInput)

def setIssue(s, issueID):
    issue = s.query(Issue).filter(Issue.id == issueID).first()
    currentIssue['title'] = issue.title
    currentIssue['dateof'] = issue.dateof
    currentIssue['about'] = issue.about
    currentIssue['imagepath'] = issue.imagepath

    listOfLinks = []
    links = s.query(Link).filter(Link.issueid == issueID).all()
    for link in links:
        listOfLinks.append({'title' : link.title, 'ref' : link.ref})
    
    currentIssue['links'] = listOfLinks

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'userInfo' in session:
            return redirect(url_for('home'))
        else:
            username = request.form['username']
            password = request.form['password']
            login = run_transaction(Session, lambda s: loginUser(s, username, password))
            if not login:
                return redirect(url_for('login'))
            
            if 'prevPage' not in session:
                session['prevPage'] = 'home'

            return redirect(url_for(session['prevPage']))
    else: #GET
        return render_template('login.html')

def loginUser(s, username, password):
    user = s.query(User).filter_by(username = username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        flash('Incorrect username and/or password. Please try again.', 'error')
        return False
    else:
        userInfo = { 'id' : user.id, 'username' : user.username, 'email' : user.email, 'datecreated' : user.datecreated }
        session['userInfo'] = userInfo
        session['userID'] = user.id
        print('successful')
        return True

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username = request.form['username']
        success = True
        email = request.form['email']
        pfpimage = request.files['pfp']
        if not pfpimage or pfpimage.filename == '':
            success = False
        elif uploadPhoto(pfpimage) != '':
            success = True
        #check if input is valid

        if username.strip() == '' or not username.isalnum():
            flash('Username must contain letter and/or number characters.', 'error')
            success = False
        elif request.form['password'] != request.form['confirmpassword']:
            flash('Passwords do not match.', 'error')
            success = False
        
        elif run_transaction(Session, lambda s: isUser(s, username)):
            flash('Username already taken.', 'error')
            success = False


        if success:
            hashedPassword = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
            newUser = User(id = uuid.uuid4(), username = username, email = email, password = hashedPassword, datecreated = datetime.utcnow().strftime("%Y-%m-%d"), profilepic = pfpimage.filename )
            run_transaction(Session, lambda s: s.add(newUser))
            flash('Successfully registered.')
            return redirect(url_for('login'))
        else:
            return redirect(url_for('register'))   
def isUser(s, username):
    return s.query(User.username).filter(User.username == username).count() > 0
@app.route('/logout')
def logout():
    session.pop('userInfo')
    session.pop('userID')

    return redirect(url_for('login'))

@app.route('/account')
def account():
    if 'userInfo' in session:
        return render_template('myAccount.html', user = session['userInfo'])
    else:
        return redirect(url_for('login'))

@app.route('/issue', methods = ['GET', 'POST'])
def issue():
    #return render_template('issue.html')

    if 'title' in currentIssue:
        if request.method == 'GET':
            return render_template('issueTemplate.html', issue = currentIssue)
        else:
            
        
            

            #run_transaction(Session, lambda s: newIssueAndLink(s, title, dateof, text, links))

            return redirect(url_for('home'))
        

@app.route('/post-message', methods = ['POST'])
def postMessage():
    if request.method == 'POST':
        msgContent = request.form['content']
        dateposted = datetime.utcnow()
        authorid = session['userID']
        if 'imageUpload' in request.files:
            imageupload = request.files['imageUpload']
        else: 
            imageupload = None
        if not imageupload or imageupload.filename == '':
            hasImage = False
        else:
            filename = uploadPhoto(imageupload)
            if filename != '':
                newMessage = Discussion(id = uuid.uuid4(), content = msgContent, dateposted = dateposted, authorid = authorid, imageupload = imageupload.filename)
                hasImage = True

            else:
                hasImage = False
        if not hasImage:
            newMessage = Discussion(id = uuid.uuid4(), content = msgContent, dateposted = dateposted, authorid = authorid)
        
        run_transaction(Session, lambda s: s.add(newMessage))

        return redirect(url_for('issue'))


@app.route('/new', methods= ['GET', 'POST'])
def newIssue():

    if request.method == 'GET':
        return render_template('newIssue.html')
    else:
        title = request.form['infoTitle']
        dateof = request.form['date']
        if not dateof:
            dateof = datetime.utcnow().strftime('%Y-%m-%d')
        text = request.form['infoText']
        communityname = request.form['community'].strip()
        if 'image' in request.files:
            image = request.files['image']
            imagepath = uploadPhoto(image)
        else:
            imagepath = ''
        links = []

        index = 0
        while 'link' + str(index) in request.form:
            print('link' + str(index))
            if request.form['link' + str(index)].strip() != '' and request.form['linkTitle' + str(index)].strip() != '':
                links.append({'title': request.form['linkTitle' + str(index)].strip(), 'ref': request.form['link' + str(index)].strip()})
            index+=1
        print("Finish links")
        if run_transaction(Session, lambda s: isCommunity(s, communityname)):
            communityid = run_transaction(Session, lambda s: getCommunityID(s, communityname))
        else:
            newCommunity = Community(id = uuid.uuid4(), name = communityname)
            communityid = newCommunity.id
            print("idddd")
            run_transaction(Session, lambda s: s.add(newCommunity))
        print("Finish new commune")
        run_transaction(sessionmaker(bind=engine), lambda s: newIssueAndLink(s, communityid, title, imagepath, dateof, text, links))
        print("Finished")
        return redirect(url_for('home'))

def getCommunityID(s, name):
    return s.query(Community).filter(func.lower(Community.name) == name.lower()).first().id

def isCommunity(s, name):
    return s.query(Community).filter(func.lower(Community.name) == name.lower()).count() > 0


def newIssueAndLink(session, communityid, title, imagepath, dateof, text, links):
    newIssue = Issue(id = uuid.uuid4(), communityid = communityid, title = title, imagepath = imagepath, dateof = dateof, about = text)
    session.add(newIssue)

    for link in links:
        newLink = Link(id = uuid.uuid4(), title = link['title'], ref = link['ref'], issueid = newIssue.id)
        session.add(newLink)

def getOrderByRecent(session, searchInput = ''):

    items =  session.query(Community, Issue).join(Issue, Issue.communityid == Community.id).filter(func.lower(Community.name).like('%' + searchInput + '%')).order_by(Issue.dateof.desc()).all()
    newList = []
    for i in items:
        newList.append({'Issue' : { 'title' : i.Issue.title, 'about' : i.Issue.about, 'dateof' : i.Issue.dateof, 'id': i.Issue.id}, 'Community' : { 'name' : i.Community.name, 'id': i.Community.id}})
    return newList

def uploadPhoto(imagepath):
    if imagepath.filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'jfif']:
        filename = secure_filename(imagepath.filename)
        basedirectory = os.path.abspath(os.path.dirname(__file__))
        imagepath.save(os.path.join(basedirectory, app.config['UPLOAD_FOLDER'], filename))
        return filename
    else:
        return ''


if __name__ == '__main__':

    
    db_uri = os.environ['DATABASE_URL'].replace("postgresql://", "cockroachdb://")
    try:
        engine = create_engine(db_uri)
    except Exception as e:
        print("Failed to connect to database.")
        print(f"{e}")
    app.run(debug=True)



