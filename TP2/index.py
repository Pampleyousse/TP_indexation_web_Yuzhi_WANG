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


def remove_stopwords_punctuation(text):
    """
    Remove stopwords and punctuation from the given text and return lowercase tokens.

    This function uses spaCy to process the text, filtering out stopwords and punctuation,
    and converts all tokens to lowercase.

    Args:
        text (str): The input text to process.

    Returns:
        list: A list of lowercase tokens without stopwords and punctuation.
    """
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    tokens = [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]
    return tokens


# Extraitre les informations de chaque URL : ID produit (numéro après la tld) et Variante (si présente)
# url exemple : https://web-scraping.dev/product/1?variant=orange-small
def extract_info_url(urls):
    """
    Extract product ID and variant information from a list of URLs.

    Parses each URL to extract the product ID from the path and the variant from the query parameters.
    Example URL: https://web-scraping.dev/product/1?variant=orange-small

    Args:
        urls (list): A list of URL strings to parse.

    Returns:
        list: A list of dictionaries, each containing 'url', 'product_id', and 'variant' keys.
    """
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
    """
    Create a dictionary mapping each unique token to its positions in the token list.

    Args:
        tokens (list): A list of tokens (strings).

    Returns:
        dict: A dictionary where keys are tokens and values are lists of their positions (indices).
    """
    positions = {}
    for index, token in enumerate(tokens):
        if token not in positions:
            positions[token] = []
        positions[token].append(index)
    return positions


# Création des index inversés pour les champs 'title' et 'description'
def create_inverted_index(data, field):
    """
    Create an inverted index for a specified field in the data.

    Processes the text in the given field for each URL, tokenizes it, and builds an index
    mapping tokens to URLs and their positions in the text.

    Args:
        data (pd.DataFrame): The dataframe containing the data.
        field (str): The field name to index (e.g., 'title', 'description').

    Returns:
        dict: An inverted index dictionary where keys are tokens and values are dictionaries
              mapping URLs to lists of positions.
    """
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
    """
    Create an index for product reviews, calculating statistics for each product.

    For each product, computes the total number of reviews, mean rating, and last rating.

    Args:
        data (pd.DataFrame): The dataframe containing product data with 'product_reviews' column.

    Returns:
        dict: A dictionary mapping URLs to review statistics: 'total_reviews', 'mean_mark', 'last_rating'.
    """
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
    """
    Create an inverted index for a specific feature in the product features.

    Tokenizes the feature value and maps tokens to lists of URLs that have that feature.

    Args:
        data (pd.DataFrame): The dataframe containing product data with 'product_features' column.
        feature (str): The feature name to index (e.g., 'brand', 'made in', 'material').

    Returns:
        dict: A dictionary mapping tokens to lists of URLs that contain those tokens in the feature.
    """
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
    """
    Export an index dictionary to a JSON file in the output_test directory.

    If the file already exists, it is removed before writing the new one.

    Args:
        index (dict): The index dictionary to export.
        filename (str): The base filename for the JSON file (without extension).
    """
    json_file = f"output_test/{filename}.json"
    if os.path.exists(json_file):
        print(f"Le fichier {json_file} existe déjà, suppression en cours.")
        os.remove(json_file)

    index_json = json.dumps(index, indent=4)
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(index_json)


def main():
    """
    Main entry point for the indexing script.

    Loads product data from JSONL file, creates various indexes (title, description, reviews,
    brand, origin, material), and exports them to JSON files.
    """
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



