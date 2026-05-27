import requests
r = requests.post('http://localhost:8002/api/smart-chat/upload-analysis', 
    files={'file': ('test.txt', b'test content', 'text/plain')},
    data={'case_id': '3', 'user_message': ''})
print('Status:', r.status_code)
print('Response:', r.text)