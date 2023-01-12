import numpy as np
import matplotlib.pyplot as plt
import sklearn
import jieba
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans


def tokenize(text_list, stop):
    texts = []
    tokenized_texts = []
    for text in text_list:
        cut = [each for each in jieba.cut(text) if each not in stop and not re.match(r'\d+', each)]
        if cut:
            texts.append(text)
            tokenized_texts.append(cut)
    return texts, tokenized_texts

def get_best_n_topics(n_candidates, data):
    sse = []
    for n in n_candidates:
        print(f"Kmeans with {n} centers")
        kmeans = KMeans(n_clusters=n, n_init=5)
        kmeans.fit(X=data)
        sse.append(kmeans.inertia_)
    return sse

def fit_kmeans(n, data):
    kmeans = KMeans(n_clusters=n, n_init=5, random_state=10)
    pred = kmeans.fit_transform(X=data)
    return kmeans, pred


def get_key_words(text_vec, vectorizer):
    idx_to_word = {k: v for v, k in vectorizer.vocabulary_.items()}
    key_index = np.array(np.argmax(text_vec, axis=-1)).squeeze()
    return [idx_to_word[k] for k in key_index]

if __name__ == '__main__':
    contents = [each.strip() for each in open("./index1.txt", encoding="utf-8").readlines()]
    stopwords = set(each.strip() for each in open("./stopwords.txt", encoding="utf-8").readlines())
    stopwords.add(" ")

    texts, tokenized_texts = tokenize(contents, stopwords)

    inputs = [" ".join(each) for each in tokenized_texts]
    vectorizer = TfidfVectorizer(max_features=1000)
    text_vec = vectorizer.fit_transform(inputs)


    # sse = get_best_n_topics(list(range(1, 11)), text_vec)
    # plt.plot(sse)
    # plt.show()

    n = 7
    kmeans, pred = fit_kmeans(7, text_vec)
    pred_cls = np.argmin(pred, axis=-1)
    key_words = get_key_words(text_vec, vectorizer)
    res = pd.DataFrame({"标题": texts, "关键词": key_words, "类别": pred_cls})
    res.to_csv("分类结果.csv", index=False)
