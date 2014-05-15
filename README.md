Bulk API
--------

Demonstrate best practices of using the TrustYou Bulk API to crawl many hotels at once. Written in Python, though the script can be rewritten in any other language, obviously. See crawl_bulk_api.py; Python is self-documenting ;)

Installation
------------

Runs with Python 2 and 3. Requires [Python Requests](http://docs.python-requests.org/en/latest/):

```
pip install requests
```

Example
-------

Crawl the seal and review summary widgets in French, Spanish and Italian for all TrustYou IDs contained in trustyou_ids.txt

```
cat trustyou_ids.txt | python crawl_bulk_api.py --api_key YOUR_API_KEY --widgets seal tops_flops --languages fr es it
```