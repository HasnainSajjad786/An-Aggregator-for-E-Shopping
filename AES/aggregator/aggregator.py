# all the imports
import sqlite3
import requests
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from functools import wraps


#login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

# configuration
DATABASE = '.\\tmp\\aggregator.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

#Dictionary for user logged in.
loggedInUser = {'fName':'','lName':'','uid':'','email':'','phone':''}

# app.secret_key = SECRET_KEY

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])



'''
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
'''

def compare(product,storesData):
    URL = "http://api.dataweave.in/v1/price_intelligence/findProduct/?api_key=6b4f4de21c08245c322bc3f398140781b80db3de&"
    final_url = URL + "product=" + str(product) + "&page=1&per_page=100"
    r = requests.get(final_url).json()
    #For handling any error.
    error = None
    print r['status_code']
    if (r['status_code'] != 200):
        error = str(r['status_code']) + ' - Product not found. Please try again.'
    else:
        values = r['data']
        count = 1
        productSet = set(str(product).lower().split(' '))
        for val in values:
            """if 'category' in val:
                print val['category']
            """
            titleSet = set(val['title'].lower().split(' '))
            #if ((str(product).lower() in str(val['title']).lower())):
            if (set(productSet).issubset(titleSet)):
                """and (('category' in val) and (str(category).lower() in str(val['category']).lower()))"""
                #print str(count) + ":   " + val['title'] + "       " + val['source'] + "   " + val['available_price']
                #Remove unavailable products
                if str(val['available_price']) != str(-1):
                    storesData.append({'count':str(count),'title':val['title'],'available_price':float(val['available_price']),'source':val['source'],'url':val['url']})
                #if category' in val:
                #    print val['category']
                count += 1
        #for removing duplicates
        #storesData = [dict(t) for t in set([tuple(d.items()) for d in storesData])]
    return error


#for removing duplicates
def removeDuplicates(storesData):
    uniqueData = []
    counter = 0
    uniqueData.append(storesData[counter])
    counter += 1
    while counter < len(storesData):
        #print storesData[counter]['title'] +" "+ storesData[counter-1]['title'] +" "+ storesData[counter]['available_price'] +" "+ storesData[counter-1]['available_price'] +" "+ storesData[counter]['source'] +" "+ storesData[counter]['source']
        if (storesData[counter]['title'] != storesData[counter-1]['title'] or storesData[counter]['available_price'] != storesData[counter-1]['available_price'] or storesData[counter]['source'] != storesData[counter-1]['source']):
            #print "Found"
            uniqueData.append(storesData[counter])
        counter += 1
    return uniqueData


@app.route('/', methods=['GET','POST'])
@login_required
def search_product():
    #if not session.get('logged_in'):
    #    abort(401)
    #cur = g.db.execute('select product from entries order by id desc')
    #entries = [dict(product=row0]) for row in cur.fetchall()]
    #cur = g.db.execute('select store from online_stores order by id desc')
    #stores = [dict(stores=row[0]) for row in cur.fetchall()]
    storesData=[]
    error = None    
    message = "Welcome back " + loggedInUser['fName'] + " " + loggedInUser['lName']
    if request.method == 'POST':
        product = request.form['product']
        record = int(request.form['record'])
        error = compare(product,storesData)
        if not error:        
            if request.form['order'] == 'asc':
                storesData = sorted(storesData,key = lambda k: k['available_price'])
            elif request.form['order'] == 'desc':
                storesData = sorted(storesData,key = lambda k: k['available_price'],reverse = True)
            storesData = removeDuplicates(storesData)
            count = 1
            storesData = storesData[:record]
            for store in storesData:
                store['count']= count
                count=count+1        
            #print storesData
    return render_template('search_product.html', stores=storesData,error=error,welcomeMessage=message)

'''
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (product) values (?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    #flash('New entry was successfully posted')
    #return redirect(url_for('search_product'))
'''

def validate(uname, password):
    g.db = connect_db()
    cur = g.db.execute('select * from userDetails')
    users = [dict(fName=row[1],lName=row[2],uid=row[3],key=row[4],email=row[5],phone=row[6]) for row in cur]
    for user in users:
        if user['uid'].lower() == uname.lower() and user['key'] == password:
            loggedInUser['fName'] = user['fName']
            loggedInUser['lName'] = user['lName']
            loggedInUser['uid'] = user['uid']
            loggedInUser['email'] = user['email']
            loggedInUser['phone'] = user['phone']
            return True
    return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        '''
        if request.form['username'] != app.config['USERNAME']:
            
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
            '''
        user = ['']
        if not validate(request.form['username'], request.form['password']):
            error = 'Invalid Username/ Password.'
        else:
            session['logged_in'] = True
            return redirect(url_for('search_product'))
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You are logged out')
    return redirect(url_for('login'))


def insertData(uid,fName,lName,key,phone,mail):
    g.db = connect_db()
    cur = g.db.execute('INSERT INTO userDetails(fName,lName,uid,key,email,phone) VALUES (?,?,?,?,?,?)',[fName,lName,uid,key,mail,phone])
    g.db.commit()
    g.db.close()


def isExisting(uname):
    g.db = connect_db()
    cur = g.db.execute('select * from userDetails')
    users = [dict(uid=row[3]) for row in cur]
    for user in users:
        if user['uid'].lower() == uname.lower():
            return True
    return False

@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    error = None
    if request.method == 'POST':
        uid = request.form['uid']
        fName = request.form['fName']
        lName = request.form['lName']
        key = request.form['key']
        phone = request.form['phone']
        mail = request.form['mail']
        print uid, fName, lName, key, phone, mail
        if isExisting(uid):
            error = "User name already exists."
        else:
            insertData(uid,fName,lName,key,phone,mail)
            flash('New account has been created, Login Now.')
            return redirect(url_for('login'))
    return render_template('signUp.html', error=error)


def updateData(fName,lName,key,phone,mail):
    g.db = connect_db()
    cur = g.db.execute("UPDATE userDetails SET fName=?,lName=?,key=?,email=?,phone=? WHERE uid=?",[fName,lName,key,mail,phone,loggedInUser['uid']])
    g.db.commit()
    g.db.close()


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    error = None
    if request.method == 'POST':
        #uid = request.form['uid']
        fName = request.form['fName']
        lName = request.form['lName']
        key = request.form['key']
        phone = request.form['phone']
        mail = request.form['mail']
        updateData(fName,lName,key,phone,mail)
        flash('Your account has been successfully updated.')
        return redirect(url_for('search_product'))
    return render_template('edit.html', error=error,user=loggedInUser)





if __name__ == '__main__':
    app.run(debug=True)