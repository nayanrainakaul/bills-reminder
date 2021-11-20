import requests

url = "https://google-translate1.p.rapidapi.com/language/translate/v2"

payload = "q=Hello%2C%20world!&target=es&source=en"
headers = {
    'content-type': "application/x-www-form-urlencoded",
    'accept-encoding': "application/gzip",
    'x-rapidapi-key': "653bc70edemsh5bc55e427250cddp1e42ccjsnb6f381c4fefb",
    'x-rapidapi-host': "google-translate1.p.rapidapi.com"
    }

response = requests.request("POST", url, data=payload, headers=headers)

print(response.text)