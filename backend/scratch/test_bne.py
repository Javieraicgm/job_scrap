import requests
from bs4 import BeautifulSoup

url = 'https://www.bne.cl/ofertas?q=data'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
response = requests.get(url, headers=headers)
print('Status:', response.status_code)

soup = BeautifulSoup(response.text, 'html.parser')
jobs = soup.select('div.oferta') # Guessing a class
print('Title tags:', len(soup.find_all('h2')))
print('Job divs:', len(jobs))
print(response.text[:500])
