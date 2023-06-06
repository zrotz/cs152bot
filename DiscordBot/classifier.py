import os
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import pickle 

import re
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import confusion_matrix, accuracy_score
import re
import nltk
stemmer = nltk.SnowballStemmer("english")
from nltk.corpus import stopwords
import string
stopword=set(stopwords.words('english'))


#function from https://www.kaggle.com/code/pranjalpatil0205/hate-offensive-language?scriptVersionId=113248567&cellId=35
def clean_text(text):
    text = str(text).lower()
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('https?://\S+|www\.\S+', '', text)
    text = re.sub('<.*?>+', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    text = [word for word in text.split(' ') if word not in stopword]
    text=" ".join(text)
    text = [stemmer.stem(word) for word in text.split(' ')]
    text=" ".join(text)
    return text

def models(model):
    ds = pd.read_csv("./labeled_data.csv")
    ds = ds[['class', 'tweet']]
    y = ds.iloc[:, :-1].values
    ohv = ColumnTransformer(transformers=[('encoder', OneHotEncoder(), [0])], remainder='passthrough')
    y = np.array(ohv.fit_transform(y))
    y_df = pd.DataFrame(y)
    y_hate = np.array(y_df[0])
    ds["cleaned_tweet"] = ds["tweet"].apply(clean_text)
    cleaned = ds.cleaned_tweet.values.tolist()
    tfid = TfidfVectorizer()
    fitted_vectorizer = tfid.fit(cleaned)
    X = fitted_vectorizer.transform(cleaned).toarray()
    X_train, X_test, y_train, y_test = train_test_split(X, y_hate, test_size = 0.1, random_state = 0)
    if model == "dt":
        classifier = DecisionTreeClassifier(criterion = 'entropy', random_state = 0)
        print("Training...")
        classifier.fit(X_train, y_train)
        pickle.dump(classifier, open("./TFid_DT.pickle", "wb"))
        pickle.dump(fitted_vectorizer, open("./DT_vect.pickle", "wb"))
    elif model == "rf":
        classifier = RandomForestClassifier(n_estimators = 10, criterion = 'entropy', random_state = 0)
        print("Training...")
        classifier.fit(X_train, y_train)
        pickle.dump(classifier, open("./TFid_RF.pickle", "wb"))
        pickle.dump(fitted_vectorizer, open("./RF_vect.pickle", "wb"))
    elif model == "lr":
        classifier = LogisticRegression(random_state = 0)
        print("Training...")
        classifier.fit(X_train, y_train)
        pickle.dump(classifier, open("./TFid_LR.pickle", "wb"))
        pickle.dump(fitted_vectorizer, open("./LR_vect.pickle", "wb"))

        
    return classifier, fitted_vectorizer

def classify(text, model):
    if model == "dt":
        if not os.path.exists("./TFid_DT.pickle"):
            models("dt")
        classifier = pickle.load(open("./TFid_DT.pickle", "rb"))
        fitted_vectorizer = pickle.load(open("./DT_vect.pickle", "rb"))
    elif model == "rf":
        if not os.path.exists("./TFid_RF.pickle"):
            models("rf")
        classifier = pickle.load(open("./TFid_RF.pickle", "rb"))
        fitted_vectorizer = pickle.load(open("./RF_vect.pickle", "rb"))
    elif model == "lr":
        if not os.path.exists("./TFid_LR.pickle"):
            models("lr")
        classifier = pickle.load(open("./TFid_LR.pickle", "rb"))
        fitted_vectorizer = pickle.load(open("./LR_vect.pickle", "rb"))
        
    cleaned = []
    cleaned.append(clean_text(text))
    x = fitted_vectorizer.transform(cleaned)
    print("Predicting...")
    out = classifier.predict(x)
    print(out)
    return out

print(classify(" i hate jews", "dt"))
print(classify("We need the Apartheid to happen again", "dt"))
print(classify("kill the jews", "dt"))
