import time
import subprocess
import random
import sys

def send_quic_request(f, index_file = 'test.img'):
    ip_addr = "https://127.0.0.1:4433"
    print(time.time(), 'get request sent')
    # get = subprocess.Popen(['cargo', 'run', '--bin', 'quiche-client', '--', 'https://172.29.72.153:4433', '--no-verify'],  stdout=f, stderr=subprocess.STDOUT)
    # get = subprocess.Popen(['cargo', 'run', '--bin', 'quiche-client', '--', 'https://www.cloudflare.com/page-data/sq/d/3050177178.json', '--no-verify'],  stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) 
    get = subprocess.Popen(['cargo', 'run', '--bin', 'quiche-client', '--', f'{ip_addr}', '--no-verify', '--index', f'{index_file}'],  stdout=f, stderr=subprocess.STDOUT)
    return get

def switch_ip(f, ip, migration_wait):
    t = send_quic_request(f)
    print(time.time(), f"waiting {migration_wait}")
    time.sleep(migration_wait)
    print(time.time(), 'network switch begins')
    # switch = subprocess.run(['sudo', 'ifconfig', 'enp0s8', ip, 'netmask', '255.255.128.0', 'broadcast', '172.29.127.255']) 
    # switch = subprocess.run(['sudo', 'ifconfig', 'enp0s8', ip, 'netmask', '255.255.255.0', 'broadcast', '192.168.1.255'])
    switch = subprocess.run(['sudo', 'ifconfig', 'en6', ip, 'netmask', '255.255.252.0', 'broadcast', '50.110.27.255'])
    print(time.time(), 'network switch completed')
    return t

def test_connection_migration(f, migration_wait = 0.25):
    new_ip = '50.110.11.{}'.format(random.randint(2, 254))
    print(f"new IP: {new_ip}")
    t = switch_ip(f, ip = new_ip, migration_wait = migration_wait)
    return t

def test_packet_loss(f, loss_percentage = 10):
    subprocess.run(['sudo', 'tc', 'qdisc', 'add', 'dev', 'enp0s8', 'root', 'netem', 'loss', f'{loss_percentage}%'])
    t = send_quic_request(f)
    time.sleep(0.25)
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'enp0s8', 'root'])
    return t

def test_throughput(f, duration = 10):
    start_time = time.time()
    t = send_quic_request(f, index_file = f'throughput.img')
    while time.time() - start_time < duration:
        pass
    try:
        t.terminate()
        t.wait(timeout = 2)
    except subprocess.TimeoutExpired:
        t.kill()
    return t

if __name__ == '__main__':
    ## to generate file of 1GB
    ## dd if=/dev/urandom iflag=fullblock of=test.img bs=1G count=1
    with open("stdout.txt", "wb") as out:
        for i in range(len(sys.argv)):
            if sys.argv[i] == '--loss':
                loss = int(sys.argv[i + 1])
                print("=" * 50)
                start = time.time()
                print(time.time(), f"starting packet loss test for {loss}%...")
                test_packet_loss(out, loss_percentage = loss).wait()
                print(time.time(), "packet loss test completed: ", time.time() - start)
                print("=" * 50)
            if sys.argv[i] == '--throughput':
                print("=" * 50)
                duration = float(sys.argv[i + 1])
                start = time.time()
                print(start, f"starting throughput test for {duration} seconds...")
                test_throughput(out, duration = duration).wait()
                print(time.time(), "throughput test completed: ", time.time() - start)
                print("=" * 50)
            if sys.argv[i] == '--migration':
                migration_wait = float(sys.argv[i + 1])
                print("=" * 50)
                start = time.time()
                print(start, "starting connection migration test...")
                test_connection_migration(out, migration_wait = migration_wait).wait()
                print(time.time(), "connection migration test completed: ", time.time() - start)
                print("=" * 50)
            if sys.argv[i] == '--simple':
                print("=" * 50)
                start = time.time()
                send_quic_request(out).wait()
                print(time.time(), "get request received: ", time.time() - start)
                print("=" * 50)
