import redis as valkey
client = valkey.StrictRedis(host='127.0.0.1', port=6379)
client.set('key1', 'value1')
print('key1.value :', client.get('key1'))
