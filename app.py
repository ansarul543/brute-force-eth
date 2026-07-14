import multiprocessing
import os
import signal
import sys
import json
import time
from coincurve import PrivateKey
from eth_utils import keccak

# JSON ফাইল থেকে অ্যাড্রেস লোড করা
def load_addresses_from_json(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            return {addr.lower().replace('0x', '') for addr in data}
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        sys.exit()

TARGET_ADDRESSES = load_addresses_from_json('addresses.json')

def find_match(target_set, counter):
    try:
        while True:
            # প্রাইভেট কি ও অ্যাড্রেস জেনারেশন
            priv_key_bytes = os.urandom(32)
            pk = PrivateKey(priv_key_bytes)
            public_key = pk.public_key.format(compressed=False)[1:]
            addr_hash = keccak(public_key)
            address = addr_hash[-20:].hex().lower()
            #print(address)
            # কাউন্টার আপডেট
            with counter.get_lock():
                counter.value += 1
            
            # ম্যাচ চেক
            if address in target_set:
                print(f"\n[!] MATCH FOUND!")
                print(f"Private Key: {priv_key_bytes.hex()}")
                print(f"Address: 0x{address}")
                # ম্যাচ পেলে ফাইলে সেভ হবে
                with open("found_keys.txt", "a") as f:
                    f.write(f"Address: 0x{address} | Key: {priv_key_bytes.hex()}\n")
                os._exit(0)
    except KeyboardInterrupt:
        sys.exit()

def show_speed(counter):
    last_count = 0
    while True:
        time.sleep(1)
        current_count = counter.value
        print(f"[*] Speed: {current_count - last_count} addr/sec | Total Checked: {current_count}")
        last_count = current_count

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    shared_counter = multiprocessing.Value('Q', 0)
    
    print(f"Loaded {len(TARGET_ADDRESSES)} addresses. Starting search... Press Ctrl+C to stop.")
    
    processes = []
    # ৪টি কোর ব্যবহার
    for _ in range(3):
        p = multiprocessing.Process(target=find_match, args=(TARGET_ADDRESSES, shared_counter))
        p.start()
        processes.append(p)

    # স্পিড কাউন্টার প্রসেস
    speed_p = multiprocessing.Process(target=show_speed, args=(shared_counter,))
    speed_p.start()
    processes.append(speed_p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\n[!] Stopping all processes...")
        for p in processes:
            p.terminate()
        print("[!] Done.")