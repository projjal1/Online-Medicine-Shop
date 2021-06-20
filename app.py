from flask import Flask,render_template,request,session,send_from_directory
from flask.helpers import url_for
from werkzeug.utils import redirect
from db import Graph
from PIL import Image
from datetime import datetime, date
from pyinvoice.models import InvoiceInfo, ServiceProviderInfo, ClientInfo, Item, Transaction
from pyinvoice.templates import SimpleInvoice
import os 

app = Flask(__name__)
app.secret_key = 'soverysecret'
ls=[]

graph = Graph("bolt://localhost:7687","neo4j","WhiteFoxis7")
print("Connection to Neo4j established.")

def call(dat,full_name,street,country,state,post_code,email):
    ls_files=len(os.listdir('invoices/'))
    file_id='invoices/invoice'+str(ls_files+1)+'.pdf'
    doc = SimpleInvoice(file_id)

    # Paid stamp, optional
    doc.is_paid = True

    doc.invoice_info = InvoiceInfo(1023, datetime.now(), datetime.now())  # Invoice info, optional

    # Service Provider Info, optional
    doc.service_provider_info = ServiceProviderInfo(
        name='Medical Shop',
        street='Canal Street',
        city='Kolkata',
        state='West Bengal',
        country='India',
        post_code='700056',
        vat_tax_number='ITPR5446'
    )      

    # Client info, optional
    doc.client_info = ClientInfo(name=full_name, street=street, state=state, country=country, post_code=post_code, email=email)

    # Add Item
    for each in dat:
        doc.add_item(Item(each[0], each[1], each[2], each[3]))
 
    # Tax rate, optional
    doc.set_item_tax_rate(18)  # 18%

    # Transactions detail optional
    doc.add_transaction(Transaction('Cash on Delivery', '#4631', datetime.now(), 1))

    # Optional
    doc.set_bottom_tip("Email: medical_shop@rcciit.org<br />Don't hesitate to contact us for any questions.")

    doc.finish()

@app.route("/")
def index():
    nm=""
    try:
        nm=session["email"]
    except:
        pass
    return render_template('home.html',display_name=nm)

@app.route("/signin", methods =["GET", "POST"])
def login():
    if request.method=="GET":
        return render_template("signin.html")
    else:
        email=request.form.get("email")
        password=request.form.get("pwd")
        #add user
        flag=graph.session.read_transaction(graph.signin,email,password)
        #Check 
        if not flag:
            return render_template("signin.html",error="Incorrect username or password.")

        #Create session 
        session["email"]=email
        #Redirect 
        return redirect(url_for('index'))

@app.route("/sign")
def sign_page():
    return render_template("sign.html")

@app.route("/signout")
def logout():
    session.pop("email")
    ls=[]
    return redirect(url_for('index'))

@app.route("/register", methods =["GET", "POST"])
def register():
    if request.method=="GET":
        return render_template("signup.html")
    else:
        first_name=request.form.get("fname")
        last_name=request.form.get("lname")
        email=request.form.get("email")
        password=request.form.get("pwd")
        category=request.form.get("cat")
        #Check if username exists 
        flag=graph.session.read_transaction(graph.signin,email,password)
        #Condition
        if flag:
            return render_template("signup.html",error="Username already taken.")
        #add user
        print (graph.session.read_transaction(graph.register,first_name,last_name,email,password,category))
        #Create session 
        session["email"]=email
        #Redirect 
        return redirect(url_for('index'))


@app.route("/list", methods =["GET", "POST"])
def list_item():
    if request.method=="GET":
        flag=graph.session.read_transaction(graph.check_user,username=session["email"])
        if not flag:
            return render_template("list_item.html",error="You are not registered as a seller. So you cannot list item.")
        else:
            return render_template("list_item.html")

    else:
        name=request.form.get("iname")
        desc=request.form.get("desc")
        stock=int(request.form.get("stock"))
        seller=session["email"]
        price=int(request.form.get("ppu"))
        image=request.files["img"]
        category=request.form.get("cat")       
        hash=name+seller

        #Read image
        img=Image.open(image)
        img.save('static/portal_images/'+hash+'.jpg')
        #Store data 
        print (graph.session.read_transaction(graph.add_data,name,desc,stock,price,seller,hash))
        print (graph.session.read_transaction(graph.add_category,hash,category))

        return render_template("list_item.html",success="Item listed")


@app.route("/display/<category>")
def search(category):
    record=graph.session.read_transaction(graph.fetch_product,category)
    #Format result-set into 2d array of 4 elements each 
    arr,intermediate=[],[]
    i=0
    for rec in record:
        if i%3==0:
            if len(intermediate)!=0:
                arr.append(intermediate)
            intermediate=[rec]
        else:
            intermediate.append(rec)
        i+=1
        
    if len(intermediate)!=0:
        arr.append(intermediate)

    if len(ls)!=0:
        msg="Item added to cart!"
    else:
        msg=""

    return render_template("disp_product.html",records=arr,success=msg)


@app.route("/explore/<hash>")
def explore(hash):
    record=graph.session.read_transaction(graph.details,hash)
    return render_template("details_prod.html",r=record)

@app.route("/checkout")
def checkout():
    email=session["email"]
    record=graph.session.read_transaction(graph.user_details,email)
    fname,lname=record["fname"],record["lname"]

    items=[]
    total_sum=0
    for each in ls:
        hash=each[0]
        qty=int(each[1])
        record=graph.session.read_transaction(graph.details,hash)
        name=record['name']

        #Compute price 
        total_price_product=int(record['price'])*qty
        total_sum+=total_price_product
        items.append((name,total_price_product))

    return render_template("checkout.html",fname=fname,lname=lname,email=email,disp_prod=items,total_sum=total_sum,no=len(items))


@app.route("/transact",methods=["POST"])
def transaction():
    dat=[]
    global ls
    for each in ls:
        hash=each[0]
        qty=int(each[1])
        graph.session.read_transaction(graph.reduce_stock,hash,qty)
        dat.append(graph.session.read_transaction(graph.price_cat,hash,qty))

    fname=request.form.get("fname")
    lname=request.form.get("lname")
    full_name=fname+" "+lname
    email=request.form.get("email")
    address=request.form.get("add")
    state=request.form.get("state")
    zip=request.form.get("zip")

    ls=[]

    call(dat,full_name,street=address,country="India",state=state,post_code=zip,email=email)
    return render_template("get_invoice.html")

@app.route("/cart/<hash>",methods=["POST"])
def cart(hash):
    qty = request.form.get('qty')
    print(qty,hash)
    ls.append((hash,qty))

    return redirect(url_for("search",category="all"))

@app.route("/invoice",methods=["POST"])
def invoice():
    ls=len(os.listdir('invoices/'))
    # Appending app path to upload folder path within app root folder
    uploads = os.path.join(app.root_path, 'invoices/')
    # Returning file from appended path
    return send_from_directory(directory=uploads, path='invoice'+str(ls)+".pdf")

if __name__=="__main__":
    app.run(debug=True, port=8000)