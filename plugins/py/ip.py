# DESC: Analisis de ip. uso: ip 192.175.11.176
import sys
import json
import time
import socket
import requests
import os
import re
import threading
import subprocess
import random
import hashlib
import base64
from urllib.parse import quote, urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings("ignore")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

PROXIES = [
    {"http": "http://proxy1.example.com:8080", "https": "https://proxy1.example.com:8080"},
    {"http": "http://proxy2.example.com:8080", "https": "https://proxy2.example.com:8080"},
    {"http": "http://proxy3.example.com:8080", "https": "https://proxy3.example.com:8080"}
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def make_request(url, timeout=10, retries=3):
    for attempt in range(retries):
        try:
            headers = get_random_headers()
            proxy = random.choice(PROXIES) if PROXIES and random.random() > 0.7 else None
            response = requests.get(url, headers=headers, proxies=proxy, timeout=timeout, verify=False)
            return response
        except:
            time.sleep(random.uniform(0.5, 2.0))
    return None

def usage():
    print("Uso: ip <ip>")
    print("Ejemplo: ip 192.175.11.165")
    sys.exit(1)

if len(sys.argv) != 2:
    usage()

ip = sys.argv[1]
if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", ip):
    print("Error: IP inválida")
    sys.exit(1)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"ip{ip}_{timestamp}"
os.makedirs(output_dir, exist_ok=True)

print(f"Análisis para IP: {ip}")
print(f"[DIRECTORIO] {output_dir}")

all_data = {"target_ip": ip, "timestamp": timestamp, "analysis": {}}

def save_data(category, data):
    all_data["analysis"][category] = data
    with open(f"{output_dir}/{category}.json", "w") as f:
        json.dump(data, f, indent=2)

def print_section(title, data):
    print(f"\n{'='*60}")
    print(f"[{title.upper()}]")
    print('='*60)
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{key}: {json.dumps(value, indent=2)}")
            else:
                print(f"{key}: {value}")
    elif isinstance(data, list):
        for item in data:
            print(json.dumps(item, indent=2))
    else:
        print(data)

print("Consultando Apis...")
geo_services = [
    ("ip-api", f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,mobile,proxy,hosting,query"),
    ("ipinfo", f"https://ipinfo.io/{ip}/json"),
    ("freegeoip", f"https://freegeoip.app/json/{ip}"),
    ("ipgeolocation", f"https://api.ipgeolocation.io/ipgeo?apiKey=free&ip={ip}"),
    ("ipwhois", f"https://ipwhois.app/json/{ip}"),
    ("ip2location", f"https://api.ip2location.io/?ip={ip}"),
    ("ipstack", f"http://api.ipstack.com/{ip}?access_key=free"),
    ("ipdata", f"https://api.ipdata.co/{ip}?api-key=free"),
    ("abstractapi", f"https://ipgeolocation.abstractapi.com/v1/?api_key=free&ip_address={ip}"),
    ("keycdn", f"https://tools.keycdn.com/geo.json?host={ip}"),
    ("extreme-ip", f"https://extreme-ip-lookup.com/json/{ip}"),
    ("geojs", f"https://get.geojs.io/v1/ip/geo/{ip}.json"),
    ("ipfind", f"https://ipfind.co/me?ip={ip}"),
    ("db-ip", f"https://api.db-ip.com/v2/free/{ip}")
]

geo_data = {}
def fetch_geo(name, url):
    try:
        response = make_request(url)
        if response and response.status_code == 200:
            data = response.json()
            geo_data[name] = data
            print(f"[GEO] {name}: {data.get('country', 'N/A')} - {data.get('city', 'N/A')} - {data.get('isp', 'N/A')}")
        else:
            geo_data[name] = {"error": f"HTTP {response.status_code if response else 'timeout'}"}
    except Exception as e:
        geo_data[name] = {"error": str(e)}

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fetch_geo, name, url) for name, url in geo_services]
    for future in as_completed(futures):
        future.result()

save_data("geolocation", geo_data)
print_section("GEOLOCALIZACIÓN", geo_data)

print("\nResolución DNS")
dns_data = {}

try:
    reverse_dns = socket.gethostbyaddr(ip)[0]
    dns_data["reverse_dns"] = reverse_dns
    print(f"Reverse DNS: {reverse_dns}")
except:
    dns_data["reverse_dns"] = None
    print("Reverse DNS: No encontrado")

dns_servers = ["8.8.8.8", "1.1.1.1", "208.67.222.222", "9.9.9.9"]
for dns_server in dns_servers:
    try:
        result = subprocess.run(["nslookup", ip], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            dns_data[f"nslookup_{dns_server}"] = result.stdout
            break
    except:
        continue

save_data("dns", dns_data)
print_section("DNS", dns_data)

print("\nInformación WHOIS y ASN")
whois_data = {}

whois_sources = [
    f"https://rdap.arin.net/registry/ip/{ip}",
    f"https://rdap.apnic.net/ip/{ip}",
    f"https://rdap.db.ripe.net/ip/{ip}",
    f"https://rdap.lacnic.net/rdap/ip/{ip}",
    f"https://whois.arin.net/rest/ip/{ip}.json"
]

for i, url in enumerate(whois_sources):
    try:
        response = make_request(url)
        if response and response.status_code == 200:
            data = response.json()
            whois_data[f"source_{i}"] = data
            print(f"whois Fuente {i}: Datos obtenidos")
            break
    except:
        continue

try:
    response = make_request(f"https://api.bgpview.io/ip/{ip}")
    if response and response.status_code == 200:
        bgp_data = response.json()
        whois_data["bgp_view"] = bgp_data
        print(f"[BGP] ASN: {bgp_data.get('data', {}).get('prefixes', [{}])[0].get('asn', {}).get('asn', 'N/A')}")
except:
    pass

save_data("whois", whois_data)
print_section("WHOIS/ASN", whois_data)

print("\nEscaneo de puertos")
all_ports = list(range(1, 1024)) + [1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017]
open_ports = []
services = {}

def scan_port(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            open_ports.append(port)
            try:
                sock.send(b"HEAD / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
                banner = sock.recv(1024).decode(errors="ignore").strip()
                services[port] = banner[:200] if banner else "Sin banner"
            except:
                services[port] = "Sin banner"
        sock.close()
    except:
        pass

with ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(scan_port, port) for port in all_ports]
    for future in as_completed(futures):
        future.result()

port_data = {"open_ports": sorted(open_ports), "services": services}
save_data("ports", port_data)
print_section("PUERTOS", port_data)

print("\huella de servicios web")
web_data = {}

web_ports = [port for port in open_ports if port in [80, 443, 8080, 8443, 8000, 8888]]
for port in web_ports:
    for scheme in ["http", "https"]:
        try:
            url = f"{scheme}://{ip}:{port}"
            response = make_request(url, timeout=15)
            if response:
                web_info = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content_length": len(response.content),
                    "title": re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE).group(1) if re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE) else None,
                    "server": response.headers.get("Server", "Unknown"),
                    "technologies": []
                }
                
                tech_patterns = {
                    "WordPress": r"wp-content|wp-includes|wordpress",
                    "Drupal": r"drupal|sites/default",
                    "Joomla": r"joomla|option=com_",
                    "Apache": r"Apache/",
                    "Nginx": r"nginx",
                    "IIS": r"Microsoft-IIS",
                    "PHP": r"X-Powered-By.*PHP",
                    "ASP.NET": r"X-AspNet-Version|X-Powered-By.*ASP.NET"
                }
                
                content_lower = response.text.lower()
                headers_str = str(response.headers).lower()
                
                for tech, pattern in tech_patterns.items():
                    if re.search(pattern, content_lower + headers_str, re.IGNORECASE):
                        web_info["technologies"].append(tech)
                
                web_data[f"{scheme}_{port}"] = web_info
                print(f"[WEB] {scheme}://{ip}:{port} - {response.status_code} - {web_info['server']}")
                
                common_paths = ["/robots.txt", "/sitemap.xml", "/.well-known/security.txt", "/admin", "/login", "/wp-admin", "/phpmyadmin", "/.git/config", "/.env", "/api", "/dashboard", "/config.php", "/backup"]
                for path in common_paths:
                    try:
                        path_response = make_request(f"{url}{path}", timeout=5)
                        if path_response and path_response.status_code in [200, 301, 302, 403]:
                            if path not in web_data[f"{scheme}_{port}"]:
                                web_data[f"{scheme}_{port}"]["paths"] = {}
                            web_data[f"{scheme}_{port}"]["paths"][path] = {
                                "status": path_response.status_code,
                                "size": len(path_response.content)
                            }
                            print(f"[PATH] {path} - {path_response.status_code}")
                    except:
                        pass
                    time.sleep(0.1)
        except:
            pass

save_data("web", web_data)
print_section("WEB SERVICES", web_data)

print("\nReputación y amenazas")
reputation_data = {}

reputation_sources = [
    ("virustotal", f"https://www.virustotal.com/vtapi/v2/ip-address/report?apikey=free&ip={ip}"),
    ("abuseipdb", f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90&verbose"),
    ("threatminer", f"https://api.threatminer.org/v2/host.php?q={ip}&rt=1"),
    ("otx", f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general"),
    ("greynoise", f"https://api.greynoise.io/v3/community/{ip}"),
    ("shodan", f"https://api.shodan.io/shodan/host/{ip}?key=free"),
    ("censys", f"https://search.censys.io/api/v2/hosts/{ip}"),
    ("maltiverse", f"https://api.maltiverse.com/ip/{ip}"),
    ("ipqualityscore", f"https://ipqualityscore.com/api/json/ip/free/{ip}"),
    ("fraudguard", f"https://api.fraudguard.io/ip/{ip}")
]

def fetch_reputation(name, url):
    try:
        response = make_request(url)
        if response and response.status_code == 200:
            data = response.json()
            reputation_data[name] = data
            print(f"[REP] {name}: Datos obtenidos")
        else:
            reputation_data[name] = {"error": f"HTTP {response.status_code if response else 'timeout'}"}
    except Exception as e:
        reputation_data[name] = {"error": str(e)}

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(fetch_reputation, name, url) for name, url in reputation_sources]
    for future in as_completed(futures):
        future.result()

save_data("reputation", reputation_data)
print_section("REPUTACIÓN", reputation_data)

print("\nConectividad y latencia")
connectivity_data = {}

ping_results = []
for i in range(5):
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((ip, 80 if 80 in open_ports else 443 if 443 in open_ports else 22))
        end = time.time()
        latency = int((end - start) * 1000)
        ping_results.append(latency)
        sock.close()
    except:
        ping_results.append(-1)
    time.sleep(0.5)

valid_pings = [p for p in ping_results if p > 0]
if valid_pings:
    connectivity_data["latency"] = {
        "min": min(valid_pings),
        "max": max(valid_pings),
        "avg": sum(valid_pings) // len(valid_pings),
        "results": ping_results
    }
else:
    connectivity_data["latency"] = {"error": "No se pudo medir latencia"}

try:
    response = make_request(f"https://api.hackertarget.com/mtr/?q={ip}")
    if response and response.status_code == 200:
        connectivity_data["traceroute"] = response.text.split('\n')
except:
    connectivity_data["traceroute"] = ["Error en traceroute"]

save_data("connectivity", connectivity_data)
print_section("CONECTIVIDAD", connectivity_data)

print("\nBúsqueda de subdominios y dominios relacionados")
domain_data = {}

if dns_data.get("reverse_dns"):
    domain = dns_data["reverse_dns"]
    
    subdomains = []
    common_subs = ["www", "mail", "ftp", "admin", "test", "dev", "api", "app", "blog", "shop", "secure", "vpn", "remote", "portal", "dashboard"]
    
    def check_subdomain(sub):
        try:
            full_domain = f"{sub}.{domain}"
            socket.gethostbyname(full_domain)
            subdomains.append(full_domain)
            print(f"[SUB] Encontrado: {full_domain}")
        except:
            pass
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_subdomain, sub) for sub in common_subs]
        for future in as_completed(futures):
            future.result()
    
    domain_data["subdomains"] = subdomains
    
    try:
        response = make_request(f"https://crt.sh/?q={domain}&output=json")
        if response and response.status_code == 200:
            crt_data = response.json()
            cert_domains = list(set([entry.get("name_value", "").replace("*.", "") for entry in crt_data if entry.get("name_value")]))
            domain_data["certificate_domains"] = cert_domains[:50]
            print(f"[CERT] Encontrados {len(cert_domains)} dominios en certificados")
    except:
        pass

save_data("domains", domain_data)
print_section("DOMINIOS", domain_data)

print("\nSSL/TLS")
ssl_data = {}

ssl_ports = [port for port in open_ports if port in [443, 8443, 993, 995, 465, 587]]
for port in ssl_ports:
    try:
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((ip, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=ip) as ssock:
                cert = ssock.getpeercert()
                ssl_data[f"port_{port}"] = {
                    "subject": dict(x[0] for x in cert.get("subject", [])),
                    "issuer": dict(x[0] for x in cert.get("issuer", [])),
                    "version": cert.get("version"),
                    "notBefore": cert.get("notBefore"),
                    "notAfter": cert.get("notAfter"),
                    "serialNumber": cert.get("serialNumber"),
                    "subjectAltName": cert.get("subjectAltName", [])
                }
                print(f"[SSL] Puerto {port}: {ssl_data[f'port_{port}']['subject'].get('commonName', 'N/A')}")
    except:
        ssl_data[f"port_{port}"] = {"error": "No se pudo obtener certificado SSL"}

save_data("ssl", ssl_data)
print_section("SSL/TLS", ssl_data)

print("\nBúsqueda en motores")
search_data = {}

search_queries = [
    f'"{ip}"',
    f'site:{ip}',
    f'"{ip}" filetype:pdf',
    f'"{ip}" "admin" OR "login"',
    f'"{ip}" "database" OR "sql"'
]

for i, query in enumerate(search_queries):
    try:
        encoded_query = quote(query)
        response = make_request(f"https://www.google.com/search?q={encoded_query}&num=20")
        if response and response.status_code == 200:
            results = re.findall(r'<h3[^>]*>.*?</h3>', response.text)
            search_data[f"query_{i}"] = {"query": query, "results_count": len(results), "sample_results": results[:5]}
            print(f"[SEARCH] Query {i}: {len(results)} resultados")
    except:
        search_data[f"query_{i}"] = {"query": query, "error": "Error en búsqueda"}
    time.sleep(random.uniform(2, 5))

save_data("search", search_data)
print_section("BÚSQUEDAS", search_data)

print("\n[RESUMEN FINAL]")
summary = {
    "target": ip,
    "timestamp": timestamp,
    "analysis_duration": time.time() - time.time(),
    "total_sources": len(geo_services) + len(whois_sources) + len(reputation_sources),
    "open_ports_count": len(open_ports),
    "web_services_count": len(web_data),
    "reputation_sources": len(reputation_data),
    "key_findings": {
        "country": next((data.get("country") for data in geo_data.values() if isinstance(data, dict) and data.get("country")), "N/A"),
        "organization": next((data.get("org") or data.get("isp") for data in geo_data.values() if isinstance(data, dict) and (data.get("org") or data.get("isp"))), "N/A"),
        "open_ports": sorted(open_ports)[:10],
        "technologies": list(set([tech for web_info in web_data.values() if isinstance(web_info, dict) for tech in web_info.get("technologies", [])])),
        "subdomains_found": len(domain_data.get("subdomains", [])),
        "ssl_ports": len(ssl_data)
    }
}

with open(f"{output_dir}/final_summary.json", "w") as f:
    json.dump(all_data, f, indent=2)

print_section("RESUMEN EJECUTIVO", summary)
print(f"\nListo! Análisis guardado en {output_dir}/")
print(f"[ARCHIVOS] {len(os.listdir(output_dir))} archivos generados")
print(f"[DATOS] {len(all_data['analysis'])} categorías analizadas")