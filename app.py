import tweepy
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from nltk.tokenize import word_tokenize
import re

class ui:
  def __init__(self,consumer_key = input('Input consumer key: '),
              consumer_secret = input('Input consumer secret: '),
              access_token = input('Input access token: '),
              access_token_secret = input('Input access token secret: '),
              word = input("search word: ")):
    
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.access_token = access_token
    self.access_token_secret = access_token_secret
    self.word = word

  def update_data(self):
    consumer_key = self.consumer_key
    consumer_secret = self.consumer_secret
    access_token = self.access_token
    access_token_secret = self.access_token_secret
      
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth,wait_on_rate_limit=True)
        
    search_word = self.word
    date_since = input("date (format: 2020-09-17): ")
    n = int(input("number of tweets: "))
    new_search = search_word + " -filter:retweets"

    tweets = tweepy.Cursor(api.search,
                            q=new_search,
                            since=date_since,
                            lang="id",tweet_mode='extended').items(n)
        
    #Cleanning Text

    file = open('normalisasi.txt','r')
    normal = file.readlines()
    words = []

    for i in normal:
      i = i.split('\t')
      for n in i:
        words.append(re.sub('\n','',n))

    dicts = {words[i]: words[i + 1] for i in range(0, len(words), 2)}

    tweet = []
    date=[]
    account =[]
    tweetid=[]
    for t in tweets:
      account.append('@%s'%(t.user.screen_name))
      date.append(t.created_at.date().strftime('20%y-%m-%d'))
      tweetid.append(t.id)
      full_text = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^A-Za-z \t])|(\w+:\/\/\S+)", " ", t.full_text).split()).lower().strip()
      token = word_tokenize(full_text)
      for n,i in enumerate(token):
        if i in dicts.keys():
          token[n]=dicts[i]
      tweet.append(' '.join(token))

        
    # Save to db
    value = [(tweetid[i],account[i],date[i],tweet[i]) for i in range(len(tweetid))]
    try:
      connection = sqlite3.connect("tweet.db")
      create_table = '''CREATE TABLE IF NOT EXISTS {} (
                  id INTEGER PRIMARY KEY,
                  account text NOT NULL,
                  date Date NOT NULL,
                  tweet text NOT NULL,
                  value INTEGER);'''.format(search_word)

      insert_value = """INSERT OR IGNORE INTO {}('id','account','date','tweet') VALUES (?,?,?,?);""".format(search_word)
      cursor = connection.cursor()
      cursor.execute(create_table)
      cursor.executemany(insert_value,value)
      connection.commit()
      cursor.close()
      connection.close()
      print('Update Data Successful!')

    except sqlite3.Error as error:
      print('error om :',error)

    finally:
      if (connection):
        connection.close()

  def update_sentiment(self):
    pos_list= open("kata_positif.txt","r")
    pos_kata = pos_list.readlines()
    neg_list= open("kata_negatif.txt","r")
    neg_kata = neg_list.readlines()
    
    try:
      connection = sqlite3.connect("tweet.db")
    
      query = '''SELECT id,tweet FROM {} WHERE value is NULL'''.format(self.word)
          
      cursor = connection.cursor()
      cursor.execute(query)
      tweets = cursor.fetchall()

      hasil=[]
      for i in tweets:
        for j in i:
          hasil.append(j)

      id=[]
      tweet=[]
      for n in range(0,len(hasil),2):
        id.append(hasil[n])
        tweet.append(hasil[n+1])

      S = []
      for item in tweet:
        count_p = 0
        count_n = 0
        for kata_pos in pos_kata:
          if kata_pos.strip() in item:
            count_p +=1
        for kata_neg in neg_kata:
          if kata_neg.strip() in item:
            count_n +=1
        S.append(count_p - count_n)

      value = [(S[i],id[i]) for i in range(len(S))]
      insert_value = """Update {} set value = ? where id = ?""".format(self.word)
      cursor.executemany(insert_value,value)
      connection.commit()
      cursor.close()
      connection.close()
      print('Update Sentiment Successful!')

    except sqlite3.Error as error:
      print('error om :',error)

    finally:
      if (connection):
        connection.close()

  def see_data(self):
    from_date = input('from date (format: 2020-09-17) :')
    to_date = input('to date (format: 2020-09-17) :')
    try:
      connection = sqlite3.connect('tweet.db')
      query = '''SELECT account,date,tweet FROM {} WHERE(date BETWEEN ? AND ?)'''.format(self.word)
      cursor = connection.cursor()
      cursor.execute(query,(from_date,to_date))
      data = cursor.fetchall()
      cursor.close()
      connection.close()

      hasil=[]
      for i in data:
        for j in i:
          hasil.append(j)

      account=[]
      date=[]
      tweet=[]
      for n in range(0,len(hasil),3):
        account.append(hasil[n])
        date.append(hasil[n+1])
        tweet.append(hasil[n+2])

      df = pd.DataFrame({'account':account,'date':date,'tweet':tweet})
      print(df)
    
    except sqlite3.Error as error:
      print('error om :',error)
    finally:
      if(connection):
        connection.close()

  def visualization(self): 
    from_date = input('from date (format: 2020-09-17) :')
    to_date = input('to date (format: 2020-09-17) :')

    try:
      connection = sqlite3.connect('tweet.db')

      query = '''SELECT value FROM {} WHERE(date BETWEEN ? AND ?)'''.format(self.word)
      cursor = connection.cursor()
      cursor.execute(query,(from_date,to_date))
      data = cursor.fetchall()
      cursor.close()
      connection.close()
        
      value=[]
      for i in data:
        for n in i:
          value.append(n)

      print ("Mean: "+str(np.mean(value)))
      print ("Standar deviation: "+str(np.std(value)))
      print ("median: "+str(np.median(value)))
      print(" ")

      if np.mean(value) >= 0:
        print("Sentiment: Positive")
      else:
        print("Sentiment: Negative")
            
      labels, counts = np.unique(value, return_counts=True)
      plt.bar(labels, counts, align='center')
      plt.gca().set_xticks(labels)
      plt.show()

    except sqlite3.Error as error:
      print('error om:',error)

    finally:
      if (connection):
        connection.close()

test = ui()

out = '''
What do you want to do 
    1. Update Data
    2. Update Sentiment
    3. See Data
    4. Visualization
    5. Exit
    Your input :
'''

value = int(input(out))
while True:
  if value == 1:
    test.update_data()
    value = int(input(out))
  elif value ==2:
    test.update_sentiment()
    value = int(input(out))
  elif value ==3:
    test.see_data()
    value = int(input(out))
  elif value == 4:
    test.visualization()
    value = int(input(out))
  elif value == 5:
    print("Thank you :D")
    break
  else:
    print('option not available')
    break
        



