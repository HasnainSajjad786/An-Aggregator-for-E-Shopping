import requests

r = requests.get("http://api.dataweave.in/v1/price_intelligence/findProduct/?api_key=6b4f4de21c08245c322bc3f398140781b80db3de&product=Micromax Canvas Doodle 2 A240 (Blue)&page=1&per_page=150")

data = r.json()['data']

count = 1
for d in data:
	print str(count) + "    " + str(d['source']) + "    " + str(d['available_price'])+ "    " + str(d['url'])
	"""+ "    " + str(d['available_price']) + "    " + str(d['url'])"""
	count = count + 1

