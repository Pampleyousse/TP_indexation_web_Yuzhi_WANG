import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
import os

headers = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
}


# Fonction qui s’assure que le crawler a le droit de parser une page
def can_crawl(url):
    """
    Check if the crawler is allowed to crawl a given URL by examining the robots.txt file.

    This function sends a request to the robots.txt file of the domain and checks if
    crawling is disallowed for all user agents.

    Args:
        url (str): The URL to check for crawling permission.

    Returns:
        bool: True if crawling is allowed, False otherwise.
    """
    robots_url = url + "/robots.txt"
    response = requests.get(robots_url)
    if response.status_code == 200:
        robots_txt = response.text
        if "Disallow: /" in robots_txt:
            return False
    return True


# Fonction pour parser le HTML et extraire les informations
def parse_html(url, soup):
    """
    Parse the HTML content of a webpage to extract product information.

    This function searches for product-related elements in the BeautifulSoup object
    and extracts details such as title, description, features, links, and reviews.

    Args:
        url (str): The URL of the webpage being parsed.
        soup (BeautifulSoup): The parsed HTML content of the webpage.

    Returns:
        list: A list of dictionaries, each containing product information.
              Each dictionary has keys: 'url', 'title', 'description', 'features',
              'links', 'reviews'.
    """
    url = url
    products = []
    product_elements = soup.find_all("body")
    for element in product_elements:

        name = element.find("h3", class_="card-title product-title mb-3")
        if name:
            name = name.text.strip()
        else:
            name = soup.find("title").text.strip()

        description_text = element.find("p", class_="product-description")
        if description_text:
            description_text = description_text.text.strip()
        else:
            description_text = ""

        features = element.find_all("tr", class_="feature")
        links = element.find_all("a")
        reviews = element.find_all("div", class_="mt-4")

        reviews_list = []
        for review in reviews:
            classes = review.get("class", [])
            review_id = None
            for cls in classes:
                if cls.startswith("review-") and cls != "review":
                    review_id = cls.replace("review-", "")
                    break

            rating = len(review.find_all("svg"))

            p = review.find("p")
            content = p.text.strip() if p else None

            reviews_list.append({
                "id": review_id,
                "rating": rating,
                "content": content
            })

        products.append({
            "url": url,
            "title": name,
            "description": description_text,
            "features": {feature.find("td", class_="feature-label")
                         .text.strip():
                         feature.find("td", class_="feature-value")
                         .text.strip() for feature in features},
            "links": [link.get("href") for link in links],
            "reviews": reviews_list
        })
    return products


def crawl(url, nb_pages):
    """
    Crawl a website starting from a given URL and extract product information from pages.

    This function performs a breadth-first search crawl, prioritizing product pages.
    It respects robots.txt and limits the number of pages crawled.

    Args:
        url (str): The starting URL for crawling.
        nb_pages (int): The maximum number of pages to crawl.

    Returns:
        list: A list of product dictionaries extracted from the crawled pages.
    """
    output = []
    urls_priority = []
    urls_non_priority = []
    visited = set()
    pages_max = 50
    i = 0

    urls_priority.append(url)

    if nb_pages > pages_max:
        nb_pages = pages_max
        print(f"Le nombre de pages demandé dépasse la limite maximale de "
              f"{pages_max}. Le nombre de pages sera limité à {pages_max}.")

    for url in urls_priority:

        if i >= nb_pages:
            print("Page maximum to crawl:", nb_pages)
            break

        print("Crawling URL:", url)
        if not url.startswith("http://") and not url.startswith("https://"):
            print(f"Skipping invalid URL: {url}")
            continue
        if can_crawl(url):
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            # print(soup.title)
            products = parse_html(url, soup)
            list_url = products[0]['links']
            for url in list_url:
                if url is None:
                    continue
                path = urlparse(url).path
                if path.startswith("/product/") and url not in visited:
                    urls_priority.append(url)
                    visited.add(url)
                elif url not in urls_non_priority:
                    urls_non_priority.append(url)
            # print(products)
            output.extend(products)
            i += 1
            print(i)
        else:
            print("Crawling not allowed for this URL.", url)

    return output


def main():
    """
    Main entry point for the web crawler script.

    This function sets up the crawling parameters, runs the crawl, and saves
    the extracted product data to a JSONL file.
    """
    url = "https://web-scraping.dev/products"
    nb_pages = 50

    jsonl_file = "output/output.jsonl"
    if os.path.exists(jsonl_file):
        print(f"Le fichier {jsonl_file} existe déjà, suppression en cours.")
        os.remove(jsonl_file)

    output = crawl(url, nb_pages)

    with open(jsonl_file, "w", encoding="utf-8") as f:
        for page in output:
            f.write(json.dumps(page, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
