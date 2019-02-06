# -*- coding: utf-8 -*-

from flask import Flask,render_template,session,request,flash,redirect,url_for
from flask import send_from_directory
from subprocess import *
from json import dumps,loads
from os import listdir,urandom
import os
from datetime import datetime
from time import time,sleep
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from PIL import Image

app = Flask(__name__)
app.secret_key="key"
app.config["uploads"] = "./uploads/"
profile = {"/register/":"Register","/login/":"Login"}

def wr(x):
    f = open("users","r")
    s = f.read()
    f.close()
    f = open("users","w")
    s += x + "END"
    f.write(s)
    f.close()

def rd(x):
    f = open("users","r")
    s = f.read().split("END")
    f.close()
    if "" in s:
    	s = s[:-1]
    for i in s:
    	tmp = loads(i)
    	if (tmp["username"] == x["username"])and(tmp["password"] == x["password"]):
    		return True,tmp
    return False,None

def img_resize(img):
	size = (200,200)
	tmp = Image.open(img)
	im = tmp.resize(size,Image.ANTIALIAS)
	im.save(img,"PNG")

def img_cres(img):
	dpi = (72,72)
	im = Image.open(img)
	im.save(img,dpi=dpi)

def img_optim(img):
	img_resize(img)
	img_cres(img)

def update_db(username,champ,new_info):
    f = open("users","r")
    s = f.read().split("END")
    f.close()
    if '' in s:
    	s = s[:-1]
    for n,i in enumerate(s):
    	tmp = loads(i)
    	if username == tmp["username"]:
    		tmp = loads(s[n])
    		tmp[champ] = new_info
    		s[n] = dumps(tmp)
    		break

    s = "END".join(s)
    f = open("users","w")
    f.write(s+"END")
    f.close()

@app.route("/",methods=["GET","POST"])
def index():
    global profile
    if "username" in session:
    	profile = {"/disconnect/":"Disconnect","/profile.{}/".format(session["username"]):session["username"]}
    	if (session["username"] == "qtty"):
        	profile["/admin/index/"] = "Admin"
    else:
    	profile = {"/register/":"Register","/login/":"Login"}
    if request.method == "POST":
    	w = request.form["w_name"]
    	try:
    		with open("./uploads/workshops/{}/participants".format(w),"r") as f:
    			s = f.read()
    	except:
    		s = ""
    	participant = {}
    	for i in ["nom","prenom","email"]:
    		participant[i] = request.form[i]
    	s = "END".join([dumps(participant),s])
    	with open("./uploads/workshops/{}/participants".format(w),"w") as f:
    		f.write(s)
    	flash("registered succesfully","succes")
    return render_template("index.html",profile = profile)

@app.route("/login/",methods=["GET","POST"])
def login():
	global profile
	if "username" in session:
		flash("you're already connected","error")
		return redirect(url_for("index"))
	if request.method == "POST":
		us = request.form["username"]
		pw = request.form["password"]
		try:
			r = request.form["remember me"]
		except:
			r = False
		if r:
			session.permanent = True
		x = {"username":us,"password":pw}
		res = rd(x)
		if res[0]:
			for i in ["nom","prenom","username","specialite","annee","email","matricule","password"]:
				session[i] = res[1]	[i]
			flash("connected succesfully","succes")
			return redirect(url_for("index"))
		else:
			flash("username/password wrong","error")
			return render_template("login.html",profile = profile)
	return render_template("login.html",profile = profile)

@app.route("/register/",methods=["GET","POST"])
def register():
	global profile
	info = {}
	if request.method == "POST":
		for i in ["nom","prenom","username","specialite","annee","email","matricule","password"]:
			info[i] = request.form[i]
		info["date"] = datetime.utcfromtimestamp(int(time())).strftime('%Y-%m-%d %H:%M:%S')
		x = dumps(info)
		wr(x)
		return redirect(url_for("index"))
	return render_template("register.html",profile = profile)

@app.route("/disconnect/")
def disc():
    session.pop("email",None)
    session.pop("username",None)
    session.pop("pw",None)
    return redirect(url_for("index"))

@app.route("/admin/<opt>/",methods=["GET","POST"])
def execute(opt = ""):
    global profile
    l = {"Update the index page":"index","Create A Post":"post","Create A Workshop/Traineeship":"workshop","Execute A Shell":"shell"}
    c_opt = {"post":["Post Cover","Description","Title","Create A Post"],"shell":["Command","Execute a Shell"],"workshop":["Workshop Cover","Description","Title","Teacher","Date","Create A Workshop"]}
    li = ["Description"]
    for i in ["President","Vice President","Secretary","Vice Secretary"]:
        li += [i+" Name",i+" First Cover",i+" Last Cover"]
    li.append("Update The Index Page")
    c_opt["index"] = li

    if ("username" in session)and(session["username"] == "qtty"):
        if request.method == "POST":
            if opt == "shell":
                comm = request.form["command"].split(" ")
                p = Popen(comm,stdout=PIPE)
                x = p.communicate()[0].decode("utf-8")
                return render_template("ter.html",profile = profile,ls = x,l = l,opts=c_opt[opt][:-1],title = c_opt[opt][-1])
            elif opt in ["index","post","workshop"]:
                desc = {}
                if opt == "index":
	                for i in li[:-1]:
	                	if (i.lower() in request.form)or(i.lower() in request.files):
	                		if ("Cover" in i)and(i.lower() in request.files):
	                			f = request.files[i.lower()]
	                			nf = i + ".png"
	                			f.save("static/index/{}".format(nf))
	                			img_optim("static/index/{}".format(nf))
	                		else:
	                			desc[i.lower()] = request.form[i.lower()]
	                with open("static/index/{}".format("desc"),"r") as d:
	                	x = d.read()
	                if x != "":
	                    x = loads(x)
	                    for i in x:
	                    	if (i in desc)and(desc[i] != ''):
	                    		x[i] = desc[i]
	                    with open("static/index/{}".format("desc"),"w") as d:
	                    	d.write(dumps(x))
	                else:
		                with open("static/index/{}".format("desc"),"w") as d:
	                		d.write(dumps(desc))
                else:
                    os.mkdir("./uploads/{}s/{}".format(opt,request.form["title"]))
                    for i in c_opt[opt][:-1]:
                        if "Cover" in i:
                            f = request.files[i.lower()]
                            nf = request.form["title"] +".png"
                            f.save(os.path.join(app.config['uploads'], "{}s/{}/{}".format(opt,request.form["title"],nf)))
                            img_optim(os.path.join(app.config['uploads'], "{}s/{}/{}".format(opt,request.form["title"],nf)))
                            flash("Uploaded succesfully","succes")
                        else:
                            desc[i.lower()] = request.form[i.lower()]
                    with open(app.config['uploads']+"{}s/{}/desc".format(opt,request.form["title"]),"w") as d:
                        d.write(dumps(desc))
                return render_template("ter.html",profile = profile,l = l,opts= c_opt[opt][:-1],title=c_opt[opt][-1],ls = "")
        else:
            return render_template("ter.html",profile = profile,l = l,opts= c_opt[opt][:-1],title=c_opt[opt][-1],ls = "")
    else:
        flash("admin only page")
    return redirect(url_for("index"))

@app.route("/profile.<usr>/",methods=["GET","POST"])

def Profile(usr):
	global profile
	if ("username" in session):
	    if request.method == "POST":
		    f = request.files["image"]
		    nf = f.filename.split(".")[1]
		    if nf in ["png","jpg","jpeg"]:
			    tmp = secure_filename(session["username"]+".png")
			    f.save(os.path.join(app.config['uploads'], tmp))
			    img_optim(os.path.join(app.config['uploads'], tmp))
			    flash("uploaded succesfully","succes")
		    else:
			    flash("the uploaded image must be either .png or .jpg(.jpeg)","error")
		    return redirect(url_for("Profile",usr=usr))
	    return render_template("profile.html",profile = profile,usr_info = session,c = 0)
	else:
		flash("you must be logged in to view this page")
	return redirect(url_for("index"))

@app.route("/profile.<usr>/<opt>",methods=["GET","POST"])
def reset(usr,opt):
	if "username" in session:
		global profile
		c = 1
		if opt == "pass":
			l = ["Current Password","New Password","Confirm Password"]
			if request.method != "POST":
				title = "Change Your Password"
			else:
				l = [i.lower() for i in l]
				if session["password"] == request.form[l[0]]:
					if request.form[l[1]] == request.form[l[2]]:
						flash("password changed succesfully","succes")
						session["password"] = request.form[l[1]]
						update_db(session["username"],"password",request.form[l[1]])
						return redirect(url_for("Profile",usr=usr))
					else:
						flash("passwords doesn't match","error")
						return redirect(url_for("reset",usr=usr,opt=opt))
				else:
					flash("incorrect password","error")
					return redirect(url_for("reset",usr=usr,opt=opt))
		elif opt == "eas":
			title = "Change Your Username"
			l = ["New Username","Confirm Username"]
			l1 = ["New Email","Confirm Email"]
			if request.method == "POST":
				l,l1 = [i.lower() for i in l],[i.lower() for i in l1]
				d = {"username":l,"email":l1}
				for x in d:
					if d[x][0] in request.form:
						if request.form[d[x][0]] == request.form[d[x][1]]:
							tmp = session["username"]
							flash("{} changed succesfully".format(x),"succes")
							if x == "username":
								profile.pop("/profile.{}/".format(tmp),None)
								l = listdir("./uploads/")
								k = [i.split(".")[0] for i in l]
								try:
									if tmp in k:
										os.rename(os.path.join(app.config['uploads'], l[k.index(tmp)]),os.path.join(app.config['uploads'], request.form[d[x][0]])+"."+l[k.index(tmp)].split(".")[-1])
								except:
									pass
								profile["/profile.{}/".format(request.form[d[x][0]])] = request.form[d[x][0]]
							session[x] = request.form[d[x][0]]
							update_db(tmp,x,request.form[d[x][0]])
							return redirect(url_for("Profile",usr=session["username"]))
						else:
							flash("{}s doesn't match".format(x),"error")
							return redirect(url_for("reset",usr=usr,opt=opt))

		elif opt == "prf":
			return redirect(url_for("Profile",usr=usr))
		else:
			c = 0
		return render_template("profile.html",title = title,l = l,c = c,profile = profile,usr_info = session)
	else:
		flash("you must be logged in to view this page","error")
		return redirect(url_for("index"))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['uploads'],filename)

@app.route('/uploads/<foldername>/<fname>/<filename>')
def up_file(filename,fname,foldername):
    path = safe_join(os.path.join(app.config['uploads'], foldername))
    if path is None:
        abort(404)
    files = os.listdir(path)
    if not files:
        abort(404)
    path = safe_join(os.path.join(path,fname))
    return send_from_directory(path, filename)


@app.context_processor
def utility_processor():
	def ver_img(x):
		l = listdir("./uploads")
		k = ["".join(i.split(".")[:-1]) for i in l]
		if x in k:
			img = l[k.index(x)]
		else:
			img = "default.png"
		return img
	return dict(ver_img=ver_img)

@app.context_processor
def utility_processor():
	def list(x):
		l = listdir(x)
		return l
	return dict(list=list)

@app.context_processor
def utility_processor():
	def enum(l):
		return enumerate(l)
	return dict(enum=enum)

@app.context_processor
def utility_processor():
	def jloads(l):
		with open(l,"r") as f:
			tmp = loads(f.read())
		return tmp
	return dict(jloads=jloads)

if __name__=="__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(debug=True,host='0.0.0.0', port=port)
