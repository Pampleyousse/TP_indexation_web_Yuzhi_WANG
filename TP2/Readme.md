# Product Indexing System

This project implements a small indexing pipeline for product data. It parses a dataset of products, processes textual and structured fields, and builds several indexes that can later be used for search or analysis purposes.

---

## Project Structure

```
.
├── index.py                # Main script that builds all indexes
├── input/
│   └── products.jsonl      # Input dataset (one product per line, JSONL format)
├── output_test/
│   ├── index_title.json
│   ├── index_description.json
│   ├── index_reviews.json
│   ├── index_brand.json
│   ├── index_origin.json
│   └── index_material.json
└── README.md
```

---

## Index Structures

### 1. Title Inverted Index (`index_title.json`)

**Type:** Inverted index with word positions

**Structure:**

```json
{
  "token": {
    "url_1": [0, 3],
    "url_2": [1]
  }
}
```

* Each token comes from the product `title`.
* Stopwords and punctuation are removed using **spaCy**.
* Tokens are lowercased.
* For each token, the index stores:

  * The product URL
  * The list of positions where the token appears in the title

---

### 2. Description Inverted Index (`index_description.json`)

**Type:** Inverted index with word positions

**Structure:**

```json
{
  "token": {
    "url_1": [2, 10, 15]
  }
}
```

* Same structure and processing as the title index.
* Built from the product `description` field.

---

### 3. Reviews Index (`index_reviews.json`)

**Type:** Aggregated statistics per product

**Structure:**

```json
{
  "url": {
    "total_reviews": 5,
    "mean_mark": 4.2,
    "last_rating": 5
  }
}
```

For each product URL, the index stores:

* Total number of reviews
* Average rating
* Rating of the most recent review

---

### 4. Brand Index (`index_brand.json`)

**Type:** Inverted index (token → list of URLs)

**Structure:**

```json
{
  "gamefuel": ["url_1", "url_3"]
}
```

* Built from `product_features["brand"]`.
* Feature values are tokenized after stopword and punctuation removal.
* Each token points to all product URLs sharing that brand token.

---

### 5. Origin Index (`index_origin.json`)

**Type:** Inverted index (token → list of URLs)

* Built from `product_features["made in"]`.
* Same structure and processing as the brand index.

---

### 6. Bonus feature index: Material Index (`index_material.json`)

**Type:** Inverted index (token → list of URLs)

* Built from `product_features["material"]`.
* Allows filtering or searching products by material keywords.
* Same structure and processing as the brand index.
* Can use the same function `create_features_index` to create indexes for other features

---

## Implementation Choices

* **Python** for simplicity and readability
* **pandas** for loading and iterating over JSONL data
* **spaCy (`en_core_web_sm`)** for:

  * Tokenization
  * Stopword removal
  * Punctuation filtering
* **Inverted indexes** to support efficient keyword-based search
* **JSON output** for easy inspection and reuse in other systems

---

## Usage Examples

### Example 1: Find products containing a word in the title

```python
with open("output_test/index_title.json") as f:
    index = json.load(f)

index.get("shoes", {})
```

### Example 2: Get average rating of a product

```python
with open("output_test/index_reviews.json") as f:
    reviews = json.load(f)

reviews["https://example.com/product/1"]["mean_mark"]
```

### Example 3: Find all products made of cotton

```python
with open("output_test/index_material.json") as f:
    materials = json.load(f)

materials.get("cotton", [])
```

---

## How to Run the Code

### 1. Install dependencies

```bash
pip install pandas spacy
python -m spacy download en_core_web_sm
```

### 2. Prepare the input data

Place the file `products.jsonl` in the `input/` directory. (Already existed)

### 3. Run the script

```bash
python index.py
```

### 4. Output

All generated indexes will be available as JSON files in the `output_test/` directory.

---

## Possible Extensions

* Create specific index function for other features than brand and origine?
