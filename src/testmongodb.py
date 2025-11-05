from pymongo import MongoClient
from dotenv import load_dotenv
import os
 
load_dotenv()
 
MONGODB = os.getenv("PASS_MONGODB")
DATABASE = os.getenv("DATABASE")

client = MongoClient(MONGODB)
# 2️⃣ Sélection de la base
db = client["sample_mflix"]

# 3️⃣ Sélection de la collection (équivalent d'une table)
collection = db["movies"]

# 4️⃣ Requête équivalente à SELECT * FROM collection
documents = collection.find()

# 5️⃣ Affichage
for doc in documents:
    print(doc)
