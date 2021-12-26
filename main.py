from typing import Optional,List
from fastapi import FastAPI,Depends,status,Response,HTTPException
from pydantic import BaseModel
import uvicorn
from blog import schemas
from blog import models
from blog.database import engine,SessionLocal
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import re #regular expression
import nltk #natural language Toolkit
import string
import heapq

def preprocess(text,stopwords):
    formatted_text=text.lower()
    tokens=[]
    for token in nltk.word_tokenize(formatted_text):
        tokens.append(token)
  # print(tokens)
    tokens=[word for word in tokens if word not in stopwords and word not in string.punctuation]
    formatted_text=' '.join(element for element in tokens)
    return formatted_text

def do_summary(original_text=" "):
    original_text=re.sub(r'\s+',' ',original_text)
    stopwords=nltk.corpus.stopwords.words("english")
    print(stopwords)
    formatted_text=preprocess(original_text,stopwords)
    word_frequency=nltk.FreqDist(nltk.word_tokenize(formatted_text))
    highest_frequency=max(word_frequency.values())
    for word in word_frequency.keys():
        word_frequency[word]=(word_frequency[word]/highest_frequency)
    sentence_list=nltk.sent_tokenize(original_text)

    score_sentences={}
    for sentence in sentence_list:
    # print(sentence)
        for word in nltk.word_tokenize(sentence.lower()):
            #print(word)
            if sentence not in score_sentences.keys():
                score_sentences[sentence]=word_frequency[word]
            else:
                score_sentences[sentence] += word_frequency[word]
    best_sentences=heapq.nlargest(3,score_sentences,key=score_sentences.get)
    summary=' '.join(best_sentences)
    return summary
    
    

# original_text="""
# Experts say the rise of artificial intelligence will make most people better off over the next decade, 
# but many have concerns about how advances in AI will affect what it means to be human, 
# to be productive and to exercise free will.
# Artificial general intelligence (AGI) is the hypothetical ability of an intelligent agent to understand or learn any intellectual task that a human being can.
# It is a primary goal of some artificial intelligence research and a common topic in science fiction and futures studies. 
# AGI can also be referred to as strong AI, full AI, or general intelligent action (Although academic sources reserve the term "strong AI" for computer programs that experience sentience or consciousness.).

# In contrast to strong AI, weak AI or "narrow AI" is not intended to have general cognitive abilities; rather, weak AI is any program that is designed to solve exactly one problem
# """
# original_text=re.sub(r'\s+',' ',original_text)
# stopwords=nltk.corpus.stopwords.words("english")
# print(stopwords)

# def preprocess(text):
#     formatted_text=text.lower()
#     tokens=[]
#     for token in nltk.word_tokenize(formatted_text):
#         tokens.append(token)
#   # print(tokens)
#     tokens=[word for word in tokens if word not in stopwords and word not in string.punctuation]
#     formatted_text=' '.join(element for element in tokens)
#     return formatted_text

# formatted_text=preprocess(original_text)
# word_frequency=nltk.FreqDist(nltk.word_tokenize(formatted_text))
# highest_frequency=max(word_frequency.values())
# for word in word_frequency.keys():
#       word_frequency[word]=(word_frequency[word]/highest_frequency)
# sentence_list=nltk.sent_tokenize(original_text)

# score_sentences={}
# for sentence in sentence_list:
#   # print(sentence)
#   for word in nltk.word_tokenize(sentence.lower()):
#     #print(word)
#     if sentence not in score_sentences.keys():
#       score_sentences[sentence]=word_frequency[word]
#     else:
#       score_sentences[sentence] += word_frequency[word]
# best_sentences=heapq.nlargest(3,score_sentences,key=score_sentences.get)
# summary=' '.join(best_sentences)

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

class Blog(BaseModel):
    title:str 
    body:str 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/blog",status_code=status.HTTP_201_CREATED)
async def create(request: schemas.Blog,db:Session=Depends(get_db)):
    new_blog=models.Blog(title=request.title,body=request.body)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    
    return new_blog

@app.get("/blog",response_model=List[schemas.ShowBlog])
def all(db:Session=Depends(get_db)):
    blogs=db.query(models.Blog).all()
    return blogs

@app.get("/blog/{id}",status_code=status.HTTP_200_OK)
def show(id,db:Session=Depends(get_db)):
    blog=db.query(models.Blog).filter(models.Blog.id==id).first()
    if not blog:
        # Response.status_code=status.HTTP_404_NOT_FOUND
        # return {"detail":"Blog not found with id: "+str(id)}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Blog not found with id: "+str(id))
    return blog
    
    
@app.delete("/blog/{id}")
def destroy(id,db:Session=Depends(get_db)):
    blog=db.query(models.Blog).filter(models.Blog.id==id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Blog not found with id: "+str(id))
    db.delete(blog)
    db.commit()
    # db.query(models.Blog).filter(models.Blog.id==id).delete(synchronize_session=False)
    # db.commit()
    # return "Blog deleted"
    return blog 

# Update

@app.put("/blog/{id}",status_code=status.HTTP_202_ACCEPTED)
async def update(id,request: schemas.Blog,db:Session=Depends(get_db)):
    blog=db.query(models.Blog).filter(models.Blog.id==id)
    if not blog.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Blog not found with id: "+str(id))
    blog.update( {"title":request.title,"body":request.body} )
    db.commit()
    return "Updated Successfully"
 
pwd_cxt=CryptContext(schemes=["bcrypt"],deprecated="auto")  
  
@app.post("/user") 
def create_user(request: schemas.User,db:Session=Depends(get_db)):
    hashedPassword=pwd_cxt.hash(request.password)
    new_user=models.User(name=request.name,password=hashedPassword ,email=request.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user 

@app.post("/summary")
def create_summary(request:schemas.Summary):
    summary=do_summary(request.text)
    return {"summary":summary}