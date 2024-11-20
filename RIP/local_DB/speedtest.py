import redis as valkey
import time

v = valkey.Redis(host='127.0.0.1', port=6379)

t0 = time.time()
for j in range(10):
    for i in range(10000):
        v.set('key'+str(i), 'value'+str(i))

    t1 = time.time()
    #print("It took", t1-t0 ,"seconds to creat the list")

    v.exists('key9998')
    t2 = time.time()
    print("It took", t2-t1 ,"seconds to check if key9998 exists")

    # Virker urealistisk hurtigt men kan ikke tænke på en mere præcis test
    # Rammer cirka 0,00004 sekunder, 0,04 milisekunder

    print("")
