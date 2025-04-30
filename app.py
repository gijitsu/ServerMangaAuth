from flask import Flask
from flask_graphql import GraphQLView
from collections import namedtuple
from graphene import ObjectType, String, Int, Schema, Field,Boolean, List 
from fireBaseCallers import UserAndAnimeDatabase

app = Flask(__name__)


@app.route('/')
def index():
    return 'MangaLinkAPI!'


fb = UserAndAnimeDatabase()


UserValueObject = namedtuple("User", ["username", "password", "data", "ids"])
LoginValueObject = namedtuple("Login", ["user", "success"]) 
SignUpValueObject = namedtuple("SignUp", ["user", "success"])

PostValueObject = namedtuple("Post", ["username", "anime", "rating", "text", "animeId", "userId", "title", "seriesName"])
PostedValueObject = namedtuple("Posted", ["post", "success"])
PostListValueObject = namedtuple("PostList", ["posts", "success"])
UserPostValueObject = namedtuple("UserPost", ["post", "success"])
class User(ObjectType): 
    username = String()
    password = String()
    ids = Int() 
    data = String()

class Login(ObjectType):
    user = Field(User) 
    success = Boolean()


class SignUp(ObjectType): 
    user = Field(User) 
    success = Boolean() 

class Post(ObjectType):
    username = String()
    anime = String() 
    rating = Int() 
    text = String()
    animeId = Int() 
    userId = Int()
    title = String()
    seriesName = String() 


class Posted(ObjectType):
    post = Field(Post) 
    success = Boolean() 

class PostList(ObjectType): 
    posts = List(Post) 
    success = Boolean()

class PostListUser(ObjectType): 
    posts = List(Post) 
    success = Boolean()

class UserPost(ObjectType):
    post = Field(Post)
    success = Boolean()
    
class Query(ObjectType):
    hello = String(name=String(default_value="world"))
    number = Int(numbers=Int(default_value=-1))
    login = Field(Login,username = String(default_value="-1"), password=String(default_value=""))
    signup = Field(SignUp,username = String(default_value="-1"), password=String(default_value=""))
    posted = Field(Posted, username = String(default_value="-1"), anime=String(default_value=""), rating=Int(default_value=5), text=String(default_value=""), title=String(default_value=''), seriesName=String(default_value=''))
    postlist = Field(PostList, anime=String(default_value="-1"), start_at=Int(default_value=0), end_at=Int(default_value=10))
    postlistuser = Field(PostList, username=String(default_value="-1"), start_at=Int(default_value=0), end_at=Int(default_value=10))
    getuserpost = Field(UserPost, anime=String(default_value='-1'), username=String(default_value='-1'))
    imagestring = String(username=String(default_value=''))
    setimagestring = String(username=String(default_value=''), imagestrings=String(default_value=''))
    prediction = String(username=String(default_value=''), anime=String(default_value=''))

    def resolve_prediction(root, info, username, anime):
        try:
            return fb.getPrediction(username, anime)
        except:
            return "-1"
    def resolve_imagestring(root, info, username):
        vals = fb.getImage(username)
        if vals == -1:
            return ''
        else:
            return vals
    def resolve_setimagestring(root, info, username, imagestrings):
        vals = fb.setImage(username, imagestrings)
        if vals == -1:
            return ''
        else:
            return vals 
    def resolve_hello(root, info, name):
        return f'Hello {name}!'

    def resolve_number(root, info, numbers):
        return numbers
    def resolve_login(root, info, username, password):
        vals = fb.login(username, password)
        if(vals != -1):
            return LoginValueObject(user = UserValueObject(username = username, password = vals['password'], data = vals['data'], ids=vals['userId']), success=True)
        return LoginValueObject(user = UserValueObject(username = " ", password = " ", data = " ", ids=-1), success=False)
    def resolve_signup(root, info, username, password):
        vals = fb.signup(username, password)
        if(vals != -1):
            return SignUpValueObject(user = UserValueObject(username = username, password = password, data = " ", ids=vals), success=True)
        return SignUpValueObject(user = UserValueObject(username = " ", password = " ", data = " ", ids=-1), success=False)
    def resolve_posted(root, info, username, anime, rating, text, title, seriesName): 
        vals = fb.doReview(username, anime, text, rating, title, seriesName)
        if(vals != -1):
            return PostedValueObject(post=PostValueObject(username=username,anime=anime, rating=rating, text=text, animeId=vals[0], userId=vals[1], title=title, seriesName=seriesName), success=True)
        return PostedValueObject(post=PostValueObject(username=" ",anime=" ", rating=-1, text=" ", animeId=-1, userId=-1, title='', seriesName=''), success=False)
    
    def resolve_postlist(root, info, anime, start_at, end_at): 
        vals = fb.getReviewsList(anime, start_at, end_at) 
        if(vals == -1):
            return PostListValueObject(posts=[], success=False)
        return PostListValueObject(posts=[PostValueObject(**i) for i in vals], success=True)
    def resolve_postlistuser(root, info, username, start_at, end_at): 
        vals = fb.getReviewsListUser(username, start_at, end_at) 
        if(vals == -1):
            return PostListValueObject(posts=[], success=False)
        return PostListValueObject(posts=[PostValueObject(**i) for i in vals], success=True)
    def resolve_getuserpost(root, info, anime, username):
        vals = fb.getReview(username, anime)
        if(vals == -1):
            return UserPostValueObject(post=PostValueObject(username=" ",anime=" ", rating=-1, text=" ", animeId=-1, userId=-1, title='', seriesName=''), success = False)
        return UserPostValueObject(post=PostValueObject(**vals), success = True)
schema = Schema(query=Query)

#app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run(debug=True)
