import pandas as pd 
from urllib.parse import urlparse, urljoin, parse_qs
import json
import os
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


# Un peu de NLP
def remove_stopwords_punctuation(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    tokens = [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]
    return tokens


# Extraitre les informations de chaque URL : ID produit (numéro après la tld) et Variante (si présente)
# url exemple : https://web-scraping.dev/product/1?variant=orange-small
def extract_info_url(urls):
    info_list = []
    for url in urls:
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        path_parts = parsed_url.path.split('/')
        product_id = path_parts[2] if len(path_parts) > 2 else None
        variant = query.get('variant', [None])[0]
        info_list.append({'url': url, 'product_id': product_id, 'variant': variant})
    return info_list


# Trouver la position des mots dans un texte
def word_positions(tokens):
    positions = {}
    for index, token in enumerate(tokens):
        if token not in positions:
            positions[token] = []
        positions[token].append(index)
    return positions


# Création des index inversés pour les champs 'title' et 'description'
def create_inverted_index(data, field):
    index = {}

    for url, text in zip(data['url'], data[field]):
        tokens = remove_stopwords_punctuation(text)
        positions = word_positions(tokens)
        for token in tokens:
            if token not in index:
                index[token] = {}
            index[token][url] = positions[token]

    print(f"L'index de {field} est créé.")
    return index


# Création des index pour le reviews
def create_reviews_index(data):
    index = {}

    for url, reviews in zip(data['url'], data['product_reviews']):
        total_reviews = len(reviews)
        mean_mark = sum(review['rating'] for review in reviews) / total_reviews if total_reviews > 0 else 0
        last_rating = reviews[-1]['rating'] if total_reviews > 0 else None
        index[url] = {
            'total_reviews': total_reviews,
            'mean_mark': mean_mark,
            'last_rating': last_rating
        }
    
    print("L'index des reviews est créé.")
    return index


# Création des index inversés pour les features comme marque et origine.
def create_features_index(data, feature):
    index = {}

    for url, features in zip(data['url'], data['product_features']):
        feature_value = features.get(feature)
        feature_value = remove_stopwords_punctuation(feature_value) if feature_value else []
        for token in feature_value:
            if token not in index:
                index[token] = set()
            index[token].add(url)

    index = {token: list(urls) for token, urls in index.items()}
    print(f"L'index de feature {feature} est créé.")
    return index


def export_index_to_json(index, filename):
    json_file = f"output_test/{filename}.json"
    if os.path.exists(json_file):
        print(f"Le fichier {json_file} existe déjà, suppression en cours.")
        os.remove(json_file)

    index_json = json.dumps(index, indent=4)
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(index_json)


def main():
    data = pd.read_json('input/products.jsonl', lines=True)
    urls = data['url'].tolist()

    index_title = create_inverted_index(data, 'title')
    index_description = create_inverted_index(data, 'description')
    index_reviews = create_reviews_index(data)
    index_brand = create_features_index(data, 'brand')
    index_origin = create_features_index(data, 'made in')
    index_material = create_features_index(data, 'material')

    export_index_to_json(index_title, 'index_title')
    export_index_to_json(index_description, 'index_description')
    export_index_to_json(index_reviews, 'index_reviews')
    export_index_to_json(index_brand, 'index_brand')
    export_index_to_json(index_origin, 'index_origin')
    export_index_to_json(index_material, 'index_material')
    print("Les index sont exportés en format json.")


if __name__ == "__main__":
    main()



