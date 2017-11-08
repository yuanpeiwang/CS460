######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Mona Jalal (jalal@bu.edu), Baichuan Zhou (baichuan@bu.edu) and Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import os
# for image uploading
# from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = '9611'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '9611'
app.config['MYSQL_DATABASE_DB'] = 'PHOTOSHARES'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()

cursor = conn.cursor()
cursor.execute("SELECT EMAIL FROM USER")
users = cursor.fetchall()


def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT EMAIL FROM USER")
    return cursor.fetchall()

def getIdList():
    cursor = conn.cursor()
    cursor.execute("SELECT UID from USER")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()

    cursor.execute("SELECT PASSWORD FROM USER WHERE EMAIL = '{0]'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login',methods = ['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return render_template('login.html',supress = 'True')

    email = flask.request.form['email']
    cursor = conn.cursor()
    cursor.execute("SELECT PASSWORD FROM USER WHERE EMAIL='{0}'".format(email))
    check = cursor.fetchall()
    print('check email',check)
    if (check):

        print("data",check)
        pwd = str(check[0][0])
        if flask.request.form['password'] == pwd:
            user=User()
            user.id = email
            flask_login.login_user(user)
            uid = getUserIdFormEmail(flask_login.current_user.id)
            print("user",uid)
            return flask.redirect(flask.url_for('protected'))
    return "<a href = '/login'> Try again</a>\
     </br><a href= '/register'>or make an account</a>"

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html',message = 'You have logged out')


@app.route('/profile')
@flask_login.login_required
def protected():
    return render_template('profile.html', name = flask_login.current_user.id,
                           message = 'here is you profile')

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('hello.html')

@app.route("/register",methods = ['GET'])
def register():
    return render_template('register.html',supress = 'True')

@app.route("/register",methods = ['POST'])
def register_user():

    email = request.form.get('email')
    password = request.form.get('password')
    FNAME = request.form.get('FNAME')
    LNAME = request.form.get("LNAME")
    gender = request.form.get("gender")
    DOB = request.form.get("DOB")
    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        cursor = conn.cursor()
        query = "INSERT INTO USER (GENDER,EMAIL,PASSWORD,FNAME,LNAME,DOB) VALUES (%s, %s, %s, %s, %s, %s)"
        data = (gender, email, password, FNAME, LNAME, DOB)
        cursor.execute(query,data)
        conn.commit()
        user = User()
        user.id = email
        flask_login.login_user(user)
        uid = getUserIdFormEmail(flask_login.current_user.id)
        print("uid",uid)
        return render_template('profile.html', name = email, message = 'Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))


def isEmailUnique(email):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM USER WHERE EMAIL = '{0}'".format(email))
    count = cursor.fetchall()[0][0]

    if count == 0:
        return True
    else:
        return False





@app.route("/create_album", methods = ['GET'])
def create_album():
    return render_template('create_album.html',supress = 'True')

@app.route("/create_album", methods= ['POST'])
@flask_login.login_required
def create_album_user():
    uid = getUserIdFormEmail(flask_login.current_user.id)
    name = request.form.get("Name")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ALBUM (NAME,UID) VALUES ('{0}','{1}')".format(name,uid))
    conn.commit()
    return render_template('profile.html',name = flask_login.current_user.id, message = 'Album created!')

@app.route("/album",methods = ['GET','POST'])
@flask_login.login_required
def album():
    uid = getUserIdFormEmail(flask_login.current_user.id)
    print(getUsersAlbums(uid))
    print(uid)
    if (request.method == 'GET'):
        aid = request.args.get('AID')

        if (aid == None):
            return render_template('album.html',message = "Here is your album",albums = getUsersAlbums(uid),name = flask_login.current_user.id)
        else:
            photolist = getPhotoList(aid)
            return render_template('photo.html',photos = photolist, name = flask_login.current_user.id)

@app.route("/photo", methods = ['GET','POST'])
@flask_login.login_required
def photo():
    uid = getUserIdFormEmail(flask_login.current_user.id)

    if (request.method == 'GET'):
        pid = request.args.get ("PID")
        if (pid == None):
            return render_template('photo.html',photos=getUsersPhotos(uid), message="Here's your photos!",name=flask_login.current_user.id)
        else:
            return render_template('photo.html',photo = getphoto(pid), name = flask_login.current_user.id)


@app.route("/search", methods = ['GET','POST'])
@flask_login.login_required
def search():


    uid = getUserIdFormEmail(flask_login.current_user.id)
    if (request.method == 'GET'):
        return render_template('search.html',name=flask_login.current_user.id)
    else:
        tags = request.form.get('tags')
        type = request.form.get('type')
        taglist = tags.split(" ")
        photolists = []
        resultpid = getPhotoTag(taglist)


        if (type == "myphotos"):
            for p in resultpid:
                newphoto = getmyphoto(uid,p[0])
                photolists += newphoto
                print('list',photolists)
        else:
            for p in resultpid:
                newphoto = getallphoto(p[0])
                photolists += newphoto


        return render_template('photo.html', photos=photolists, name=flask_login.current_user.id, message = "Results!")





@app.route("/delete",methods = ['GET'])
def delete():
    uid = getUserIdFormEmail(flask_login.current_user.id)
    aid = request.args.get('aid')
    pid = request.args.get('pid')
    print("pid",pid)
    if (aid != None):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ALBUM WHERE AID = '{0}'".format(aid))
        conn.commit()
        return render_template('album.html', albums=getUsersAlbums(uid), message="Album deleted!",
                           name=flask_login.current_user.id)
    elif (pid != None):
        print("check",isOwnphoto(uid,pid))
        if (isOwnphoto(uid,pid)):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM PHOTO WHERE PID = '{0}'".format(pid))
            conn.commit()
            return render_template('photo.html',message = 'You have deleted this photo')
        else:
            return render_template('photo.html',message = "You don't have permission to delete this photo", photo = getphoto(pid) )







@app.route('/upload', methods = ['GET','POST'])
@flask_login.login_required
def upload():
    uid = getUserIdFormEmail(flask_login.current_user.id)
    if request.method =='POST':
        AID = request.form.get('aid')
        if AID == None:
            return render_template('profile.html', message = " You need to create an album")
        else:
            imgfile = request.files['photo']
            photo_data = base64.standard_b64encode(imgfile.read())
            caption = request.form.get('caption')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM PHOTO WHERE DATA = '{0}' and AID = '{1}'".format(photo_data,AID) )
            checkphoto = cursor.fetchall()[0][0]
            if (checkphoto != 0):
                return render_template('profile.html', message="Photo already uploaded")
            else:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO PHOTO (DATA, CAPTION, AID) VALUES (%s,%s,%s)",(photo_data,caption,AID))
                conn.commit()

                cursor = conn.cursor()
                cursor.execute("SELECT PID FROM PHOTO WHERE DATA = '{0}'".format(photo_data))
                pid = cursor.fetchone()[0]


                tags = request.form.get('tags')
                taglist = []
                taglist = tags.split(',')

                for tag in taglist:
                    if (istagexist(tag) == False):
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO TAG (HASHTAG) VALUES ('{0}')".format(tag))
                        conn.commit()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO ASSOCIATE (PID, HASHTAG) VALUES ('{0}','{1}')".format(pid,tag))
                    conn.commit()
                return render_template('profile.html', name=flask_login.current_user.id, message='Photo uploaded!'
                                   )
    else:
        uid = getUserIdFormEmail(flask_login.current_user.id)
        return render_template('upload.html', albums=getUsersAlbums(uid))

def isOwnphoto(uid,pid):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ALBUM AS A, PHOTO AS P WHERE (P.PID ='{0}') AND (A.UID = '{1}') AND A.AID = P.PID".format(uid,pid))
    count = cursor.fetchall()[0][0]
    print('count',count)
    if (count == 0):
        return False
    else:
        return True




def getUserIdFormEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT UID FROM USER WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]

def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT DATA, PID, CAPTION, AID FROM PHOTO WHERE AID IN(SELECT AID FROM ALBUM WHERE UID = '{0}')".format(uid))
    return cursor.fetchall()

def getPhotoList(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT DATA, PID, CAPTION, AID FROM PHOTO WHERE AID = '{0}'".format(aid))
    return cursor.fetchall()

def getallphoto(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT DATA ,PID, CAPTION, AID FROM PHOTO WHERE PID = '{0}'".format(pid))
    return cursor.fetchall()

def getmyphoto(uid,pid):
    cursor = conn.cursor()
    cursor.execute("SELECT P.DATA ,P.PID, P.CAPTION, P.AID FROM  PHOTO AS P, ALBUM AS A WHERE (P.PID = '{0}') AND (A.UID = '{1}') AND (P.AID = A.AID)".format(pid,uid))
    return cursor.fetchall()

def getPhotoTag(tags):
    taglist = tags

    pidlist = []
    for tag in taglist:
        cursor= conn.cursor()
        cursor.execute("SELECT PID FROM ASSOCIATE WHERE HASHTAG ='{0}'".format(tag))
        plst = cursor.fetchall()
        pidlist += plst

    return pidlist

def getPhotoTag(tags):
    taglist = tags

    pidlist = []
    for tag in taglist:
        cursor= conn.cursor()
        cursor.execute("SELECT PID FROM ASSOCIATE WHERE HASHTAG ='{0}'".format(tag))
        plst = cursor.fetchall()
        pidlist += plst

    return pidlist

def getUsersAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT AID, Name, UID FROM ALBUM WHERE UID = '{0}'".format(uid))
    return cursor.fetchall()


def istagexist(tag):
    cursor = conn.cursor()
    count = cursor.execute("SELECT count(*) FROM TAG WHERE HASHTAG = '{0}'".format(tag))
    count = cursor.fetchall()[0][0]
    if (count):
        return True
    else:
        return False











# default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welcome to Online photo sharing')


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
