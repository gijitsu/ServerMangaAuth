import pyrebase
import datetime
import json 
from textblob import TextBlob
from profanity_check import predict, predict_prob
import random
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv() 

def predicts(text):
    return predict([text])


def sigmoid(x): 
    return 1/(1 + np.exp(-x))

def stringProcess(x): 
    arr = np.array([float(i) for i in x.split(",")])
    return arr
def learnFromString(x, y, rating):
    rating = np.array([[rating]])
    xVector = stringProcess(x).reshape(1,-1)
    yVector = stringProcess(y).reshape(-1,1)
    i = 0 
    error = 10000
    while error*error > 1e-4 and i <= 5000:
        a = sigmoid(xVector @ yVector)
        errors = rating - a
        errorZ = (rating - a)*-1
        xVectorDelta = 0.1*(errorZ @ np.transpose(yVector))
        yVectorDelta = 0.1*(errorZ @ xVector)
        xVector = xVector - xVectorDelta
        yVector = yVector - np.transpose(yVectorDelta)
        error = errors[0][0]
        i += 1
    return error, xVector, yVector



def predictFromString(x, y): 
    xVector = stringProcess(x).reshape(1,-1)
    yVector = stringProcess(y).reshape(-1,1)
    val = sigmoid(xVector @ yVector)[0][0]
    return val

class UserAndAnimeDatabase():
    def __init__(self):
        firebaseConfig = {
            'apiKey': os.environ.get("FIREBASE_API_KEY"),
            'authDomain': os.environ.get("FIREBASE_AUTH_DOMAIN"),
            'databaseURL': os.environ.get("FIREBASE_DB_URL"),
            'projectId': os.environ.get("FIREBASE_PROJECT_ID"),
            'storageBucket': os.environ.get("FIREBASE_STORAGE_BUCKET"),
            'messagingSenderId': os.environ.get("FIREBASE_MSG_SENDER_ID"),
            'appId': os.environ.get("FIREBASE_APP_ID")
        }
        firebase = pyrebase.initialize_app(firebaseConfig)
        self.db = firebase.database()

    def login(self,user, password):
        datasets = self.db.child("Users").child(user).get()
        if(datasets.val() == None):
            return -1
        data = json.loads(json.dumps(datasets.val()))
        if(data != None and data['password'] == password): 
            return data
        else: 
            return -1
    
    def getImage(self,user):
        datasets = self.db.child("Users").child(user).get()
        if(datasets.val() == None):
            return -1
        data = json.loads(json.dumps(datasets.val()))
        if(data != None): 
            return data['data']
    def setImage(self,user, imageString):
        datasets = self.db.child("Users").child(user).get()
        if(datasets.val() == None):
            return -1
        data = json.loads(json.dumps(datasets.val()))
        if(data != None): 
            self.db.child("Users").child(user).child('data').set(imageString)
            return 1
    
    def signup(self,user, password):
        numbah = self.db.child("userNumber").get().val()
        datasets = self.db.child("Users").child(user).get()
        print(datasets.val())
        if(datasets.val() != None):
            return -1
        dictionary = {
            "Users/" + user + '/': {
                "password": password, 
                "data": "",
                "userId": numbah 
            }
        }
        self.db.update(dictionary)
        self.db.child("userNumber").set(numbah + 1)
        return numbah 
    def doReview(self, username, anime, text, rating, title, seriesName):
        try:
            if(predicts(text) or predicts(title)):
                return -1
            firstOne = self.db.child("Posts").order_by_child("anime").equal_to(anime).limit_to_first(1).get().val()
            userId = self.db.child("Users").child(username).child("userId").get().val()
            firstTwo = self.db.child("Posts").order_by_child("userId").equal_to(userId).get().val()
            if(isinstance(firstTwo, dict)):
                for key, value in firstTwo.items():
                    if value["anime"] == anime:
                        self.db.child("Posts").child(key).remove()
                        break
            
            if(firstOne == None):
                numberAnime = self.db.child("numberAnime").get().val()
                animeId = numberAnime
                self.db.child("numberAnime").set(numberAnime+1)
            else:
                actualVals = list(json.loads(json.dumps(firstOne)).values())[0]
                animeId = actualVals["animeId"]
            
            self.setPrediction(username,anime, rating/5)
            self.db.child("Posts").push({"username": username
                                    , "anime":anime
                                    , "animeId": animeId
                                    , "userId": userId
                                    , "text": text
                                    , "rating": rating,
                                    "title": title, 
                                    "seriesName": seriesName})
            
            return [animeId, userId]
        except Exception as e:
            print(e)
            return -1
        return -1

    def getReviewsList(self,  anime, start = 0, end = 10):
        datasets = self.db.child("Posts").order_by_child("anime").equal_to(anime).get()
        if(datasets.val() == None or isinstance(datasets.val(), list)):
            return -1
        actualVals = list(datasets.val().values())
        return actualVals[start:end]
    def getReviewsListUser(self,  username, start = 0, end = 10):
        datasets = self.db.child("Posts").order_by_child("username").equal_to(username).get()
        
        if(datasets.val() == None or isinstance(datasets.val(), list)):
            return -1
        actualVals = list(datasets.val().values())
        return actualVals[start:end]
    def getReview(self, username, anime):
        try:
            userId = self.db.child("Users").child(username).child("userId").get().val()
            firstTwo = self.db.child("Posts").order_by_child("userId").equal_to(userId).get().val()
            
            for key, value in firstTwo.items():
                    if value["anime"] == anime:
                        return dict(self.db.child("Posts").child(key).get().val())
            return -1
        except Exception as e:
            print(e)
            return -1
    def getPrediction(self, username, anime): 
        try: 
            user = self.db.child("UserVectors").child(username).get().val()
            if(user == None):
                randos = [str(random.uniform(0, 1)) for _ in range(50)]
                stringcsvUser = ','.join(randos)
                self.db.child("UserVectors").child(username).child("vectorValue").set(stringcsvUser)
            else:
                dictUser = dict(user) 
                stringcsvUser = dictUser['vectorValue']
            animeVal = self.db.child("AnimeVectors").child(anime).get().val()
            if(animeVal == None):
                randos = [str(random.uniform(-1, 1)) for _ in range(50)]
                stringcsvAnime = ','.join(randos)
                self.db.child("AnimeVectors").child(anime).child("vectorValue").set(stringcsvAnime)
            else:
                dictAnime = dict(animeVal) 
                stringcsvAnime = dictAnime['vectorValue']
            
            return str(predictFromString(stringcsvUser, stringcsvAnime)*5)
                 
        except Exception as e: 
            print(e)
            return -1
    def setPrediction(self, username, anime, rating):
        try: 
            user = self.db.child("UserVectors").child(username).get().val()
            if(user == None):
                randos = [str(random.uniform(0, 1)) for _ in range(50)]
                stringcsvUser = ','.join(randos)
            else:
                dictUser = dict(user) 
                stringcsvUser = dictUser['vectorValue']
            animeVal = self.db.child("AnimeVectors").child(anime).get().val()
            if(animeVal == None):
                randos = [str(random.uniform(-1, 1)) for _ in range(50)]
                stringcsvAnime = ','.join(randos)
            else:
                dictAnime = dict(animeVal) 
                stringcsvAnime = dictAnime['vectorValue']
            error, xVector, yVector = learnFromString(stringcsvUser, stringcsvAnime, rating)
            xVectorTwo = stringProcess(stringcsvUser).reshape(1,-1)
            yVectorTwo = stringProcess(stringcsvAnime).reshape(-1,1)
            xVector = xVector*0.7 + xVectorTwo*0.3
            yVector = yVector*0.7 + yVectorTwo*0.3
            yVector = yVector.reshape(1,-1)
            stringcsvUser = ','.join(['%.5f' % num for num in xVector[0]])
            stringcsvAnime = ','.join(['%.5f' % num for num in yVector[0]])
            self.db.child("AnimeVectors").child(anime).child("vectorValue").set(stringcsvAnime)
            self.db.child("UserVectors").child(username).child("vectorValue").set(stringcsvUser)
            return predictFromString(stringcsvUser, stringcsvAnime)
        except Exception as e: 
            print(e)
            return -1
if __name__ == '__main__':
    userdb = UserAndAnimeDatabase() 
    #print(userdb.doReview("Jeremy", "Your Lie in April", "It is a work of art that cannot be seen in this generation", 3))
    #print(userdb.signup("Jer4", "jerPass"))
    #userdb.doReview("Jer4", "Berserk", "It is a work of art that cannot be seen in this generation", 5)
    
    print(userdb.setPrediction("user2s", "anime1", 0.5))

    