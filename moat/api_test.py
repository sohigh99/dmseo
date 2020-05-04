import urllib3
import datetime

token = 'cTbOcDEJPPxoD6oQySLAUqxh1n7gH32y6qTdGNJw'
auth_header = 'Bearer {}'.format(token)
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
metrics = ('level1', 'loads')
query = {
    'metrics': ','.join(metrics),
    'start': yesterday,
    'end': yesterday
}
http = urllib3.PoolManager()
resp = http.request('GET', 'https://api.moat.com/1/stats.json',
                    fields=query,
                    headers={'Authorization': auth_header})

print(resp.status)
print(resp.data)