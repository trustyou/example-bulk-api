#!/usr/bin/env python
"""
Make requests to the TrustYou Bulk API.

This script demonstrates best practices of crawling the TrustYou Bulk API. Pipe TrustYou IDs to it on stdin, and receive success or error messages on stdout.

Example:
cat trustyou_ids.txt | python crawl_bulk_api.py --api_key YOUR_API_KEY --widgets seal tops_flops --languages fr es it
"""

import json
import logging
import sys

from requests import post

def parse_args():
	from argparse import ArgumentParser
	argp = ArgumentParser(__doc__)
	argp.add_argument("--api_key", help="Your API key", required=True)
	argp.add_argument("--widgets", nargs="+", help="Widgets to be crawled, e.g. 'seal tops_flops'", default=["seal", "tops_flops"])
	argp.add_argument("--languages", nargs="+", help="Languages to be crawled, e.g. 'en de'", default=["en", "de"])
	return argp.parse_args()

def create_requests(ty_ids, widgets, languages):
	"""
	This function yields all requests to be crawled, i.e. all combinations
	of TrustYou IDs, widgets and languages.

	@param ty_ids: Iterable of TrustYou IDs
	@param widgets: List of widgets to be crawled, e.g. ["seal"]
	@param languages: List of languages to be crawled, e.g. ["de"]
	"""

	# Note that requests to the same TrustYou ID should be grouped in the
	# same bulk request, if possible. The order of nested for loops here
	# is chosen for this reason.
	for ty_id in ty_ids:
		for widget in widgets:
			for language in languages:
				yield "/hotels/{ty_id}/{widget}.json?lang={language}".format(
					ty_id=ty_id,
					widget=widget,
					language=language
				)

def batch(iterable, batch_size):
	"""
	Split an iterable into batches of size batch_size. Used to split
	requests into chunks that fit into a single Bulk API call.

	>>> list(batch(range(7), batch_size=3))
	[[0, 1, 2], [3, 4, 5], [6]]
	"""

	buffer = []
	for el in iterable:
		buffer.append(el)
		if len(buffer) >= batch_size:
			yield buffer
			buffer = []
	if buffer:
		yield buffer

if __name__ == "__main__":
	
	logging.basicConfig(stream=sys.stderr, level=logging.INFO)

	args = parse_args()

	logging.info("Crawling widgets %s in languages %s from TrustYou API",
		     ", ".join(args.widgets),
		     ", ".join(args.languages)
	)

	# TrustYou IDs are piped to stdin
	ty_ids = (line.rstrip("\n") for line in sys.stdin)
	# We transform them into requests to a specific widget and language ...
	requests = create_requests(ty_ids, args.widgets, args.languages)
	# ... and split them in batches of 100, which is the maximum number of
	# requests that can be sent to Bulk API at once.
	batched_requests = batch(requests, 100)

	for request_list in batched_requests:
		
		# Do the request via POST. GET is also supported, but there is a
		# limit on URL length in most web servers.
		bulk_req_data = {
			# request_list is a JSON-encoded list
			"request_list": json.dumps(request_list),
			# Always pass your API key to Bulk API. Note it does not
			# need to be passed inside every request in request_list.
			"key": args.api_key
		}
		# Do the actual request, and parse the JSON. Error handling of
		# connection issues is ommitted here.
		bulk_req = post("http://api.trustyou.com/bulk", data=bulk_req_data)
		bulk_res = bulk_req.json()

		# Check if the bulk request was successful.
		if bulk_res["meta"]["code"] != 200:
			logging.warning("Bulk request failed with error %s", bulk_res["meta"]["code"])
			continue

		# Go through each individual returned response. Responses are in
		# the same order as the request_list we passed in, so we can
		# just "zip" requests and responses together!
		for request, response in zip(request_list, bulk_res["response"]["response_list"]):
			# Check if the individual request was successful. If one
			# fails, e.g. due to invalid parameters, the rest of the
			# requests are unaffected.
			if response["meta"]["code"] != 200:
				logging.warning("Widget request %s failed with error %s", request, response["meta"]["code"])
				continue
			print("Ok: {}".format(request))
