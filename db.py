from neo4j import GraphDatabase

class Graph:
    def __init__(self,url,username,password):
        self.driver = driver = GraphDatabase.driver(url, auth=(username,password), encrypted=False)
        self.session = self.driver.session()

    def close(self):
        self.driver.close()

    def get_session(self,tx):
        return session == None

    #Add product data
    def add_data(self,tx,name,desc,stock,price,seller,hash):
        query="create (p:Product{name:'"+name+"',desc:'"+desc+"',price:'"+str(price)+"',stock:'"+str(stock)+"',seller:'"+seller+"',hash:'"+hash+"'})"
        try:
            tx.run(query)
            return {"status":"true"}
        except:
            return {"status":"false"}

    #Add category data 
    def add_category(self,tx,hash,category):
        query="match(p:Product),(c:Category) where p.hash='"+hash+"' and c.name='"+category+"' merge (p)-[:type]->(c)"
        try:
            tx.run(query)
            return {"status":"true"}
        except:
            return {"status":"false"}

    #Login user
    def signin(self,tx,email,password):
        query="match (u:User) where u.email='"+email+"'and u.password='"+password+"' return count(u)"
        try:
            record=tx.run(query)
            counter=record.single().value()
            if counter==0:
                return False
            else:
                return True
        except:
            return {"status":"false"}

    #Register User
    def register(self,tx,first_name,last_name,email,password,category):
        query="create (u:User{fname:'"+first_name+"',lname:'"+last_name+"',email:'"+email+"',password:'"+password+"',category:'"+category+"'})"
        
        try:
            tx.run(query)
            return {"status":"true"}
        except:
            return {"status":"false"}

    #Check if user exists as a seller 
    def check_user(self,tx,username):
        query="match (u:User) where u.email='"+username+"' return u.category"
        print(query)

        try:
            record=tx.run(query)
            counter=record.single().value()
            if counter!="seller":
                return False
            else:
                return True
        except:
            return {"status":"false"}


    #Fetch all the data 
    def fetch_product(self,tx,category):
        if category=="all":
            query="match(p:Product) return p"
        else:
            query="match(p:Product)-[:type]->(c:Category) where c.name='"+category+"' return p"

        record=[]
        for var in tx.run(query):
            record.append({'name':var['p']['name'],'price':int(var['p']['price']),'stock':int(var['p']['stock']),'img':"/static/portal_images/"+var['p']['hash']+".jpg",'hash':var['p']['hash']})

        return record

    #Fetch all details of product
    def details(self,tx,hash):
        query="match(p:Product) where p.hash='"+hash+"' return p"
        record=[]
        for var in tx.run(query):
            record.append({'name':var['p']['name'],'desc':var['p']['desc'],'price':int(var['p']['price']),'seller':var['p']['seller'],
            'stock':int(var['p']['stock']),'img':"/static/portal_images/"+var['p']['hash']+".jpg",'hash':var['p']['hash']})

        return record[0]

    #Fetch user details by email
    def user_details(self,tx,email):
        query="match(u:User) where u.email='"+email+"' return u"
        record=[]
        for var in tx.run(query):
            record.append({'fname':var['u']['fname'],'lname':var['u']['lname']})

        return record[0]

    #Reduce stock 
    def reduce_stock(self,tx,hash,qty):
        query1="match(p:Product) where p.hash='"+hash+"' return p.stock"
        rec=tx.run(query1)
        query2="match(p:Product) where p.hash='"+hash+"' set p.stock='"+ str(int(rec.single().value())-qty)+"'"
        tx.run(query2)


    #Fetch category,price 
    def price_cat(self,tx,hash,qty):
        query="match(p:Product)-[:type]->(c:Category) where p.hash='"+hash+"' return p,c"
        record=[]
        for var in tx.run(query):
            record.append((var['p']['name'],var['c']['name'],int(qty),int(var['p']['price'])))

        return record[0]