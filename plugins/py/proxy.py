# DESC: Scrapeo de proxys Lives. Uso: proxy -c 10 -txt
import requests
from bs4 import BeautifulSoup
import socket
import sys
import random
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import argparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class proxyScraper:
    def __init__(self, max_workers=50, timeout=5):
        self.max_workers = max_workers
        self.timeout = timeout
        self.proxies_vivos = []
        self.lock = Lock()
        self.contador_vivos = 0
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&format=textplain",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=https&timeout=10000&country=all&format=textplain",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://www.proxy-list.download/api/v1/get?type=https",
            "https://free-proxy-list.net/",
            "https://www.sslproxies.org/",
            "https://www.us-proxy.org/",
            "https://socks-proxy.net/",
            "https://www.proxyscan.io/download?type=http",
            "https://www.proxyscan.io/download?type=https",
            "https://proxyspace.pro/http.txt",
            "https://proxyspace.pro/https.txt"
        ]
    
    def crear_session(self):
        session = requests.Session()
        session.headers.update(self.headers)
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def validar_formato_proxy(self, proxy):
        try:
            if ':' not in proxy or proxy.count(':') != 1:
                return False
            
            ip, puerto = proxy.split(':')
            
            partes_ip = ip.split('.')
            if len(partes_ip) != 4:
                return False
            
            for parte in partes_ip:
                if not parte.isdigit():
                    return False
                num = int(parte)
                if not (0 <= num <= 255):
                    return False
            
            if not puerto.isdigit():
                return False
            puerto_num = int(puerto)
            if not (1 <= puerto_num <= 65535):
                return False
            
            if ip.startswith(('10.', '192.168.', '127.', '0.', '169.254.')):
                return False
            if ip.startswith('172.') and len(partes_ip) > 1 and partes_ip[1].isdigit():
                if 16 <= int(partes_ip[1]) <= 31:
                    return False
                    
            return True
        except:
            return False
    
    def extraer_de_html(self, soup, url):
        proxies = set()
        
        try:
            tablas = soup.find_all('table')
            for tabla in tablas:
                filas = tabla.find_all('tr')
                for fila in filas:
                    celdas = fila.find_all(['td', 'th'])
                    if len(celdas) >= 2:
                        ip_texto = celdas[0].get_text(strip=True)
                        puerto_texto = celdas[1].get_text(strip=True)
                        
                        ip_texto = re.sub(r'[^\d\.]', '', ip_texto)
                        puerto_texto = re.sub(r'[^\d]', '', puerto_texto)
                        
                        if ip_texto and puerto_texto:
                            proxy = f"{ip_texto}:{puerto_texto}"
                            if self.validar_formato_proxy(proxy):
                                proxies.add(proxy)
            
            texto_completo = soup.get_text()
            patron = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})\b')
            matches = patron.findall(texto_completo)
            
            for ip, puerto in matches:
                proxy = f"{ip}:{puerto}"
                if self.validar_formato_proxy(proxy):
                    proxies.add(proxy)
                    
        except Exception:
            pass
        
        return proxies
    
    def scrape_fuente(self, url):
        proxies_encontrados = set()
        
        try:
            session = self.crear_session()
            response = session.get(url, timeout=10, verify=False)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'html' in content_type:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    proxies_encontrados = self.extraer_de_html(soup, url)
                
                elif 'json' in content_type:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, str) and self.validar_formato_proxy(item):
                                    proxies_encontrados.add(item)
                        elif isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, str) and self.validar_formato_proxy(item):
                                            proxies_encontrados.add(item)
                    except:
                        pass
                
                else:
                    lineas = response.text.strip().split('\n')
                    for linea in lineas:
                        linea = linea.strip()
                        if linea and self.validar_formato_proxy(linea):
                            proxies_encontrados.add(linea)
                        else:
                            patron = re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})\b')
                            matches = patron.findall(linea)
                            for ip, puerto in matches:
                                proxy = f"{ip}:{puerto}"
                                if self.validar_formato_proxy(proxy):
                                    proxies_encontrados.add(proxy)
            
        except Exception:
            pass
        
        return proxies_encontrados
    
    def obtener_todos_proxies(self):
        todos_proxies = set()
        print("Iniciando scraping...")
        
        for url in self.sources:
            try:
                proxies_fuente = self.scrape_fuente(url)
                if proxies_fuente:
                    todos_proxies.update(proxies_fuente)
                    print(f"OK: {len(proxies_fuente)} proxies de {url.split('/')[2]}")
            except Exception as e:
                continue
        
        print(f"Total scrapeado: {len(todos_proxies)}")
        return list(todos_proxies)
    
    def verificar_proxy(self, proxy):
        try:
            ip, puerto = proxy.split(':')
            puerto = int(puerto)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            resultado = sock.connect_ex((ip, puerto))
            sock.close()
            
            if resultado == 0:
                with self.lock:
                    self.contador_vivos += 1
                    self.proxies_vivos.append(proxy)
                    print(f"[LIVE] {proxy}")
                return True
            
        except Exception:
            pass
        
        return False
    
    def verificar_proxies_masivo(self, proxies, limite):
        if not proxies:
            print("No hay proxies para verificar")
            return []
        
        print(f"Verificando {len(proxies)} proxies...")
        random.shuffle(proxies)
        
        max_verificar = min(len(proxies), limite * 20)
        proxies_a_verificar = proxies[:max_verificar]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for proxy in proxies_a_verificar:
                if len(self.proxies_vivos) >= limite:
                    break
                future = executor.submit(self.verificar_proxy, proxy)
                futures.append(future)
            
            for future in as_completed(futures):
                if len(self.proxies_vivos) >= limite:
                    break
                future.result()
        
        return self.proxies_vivos
    
    def guardar_resultados(self, proxies, formato_txt=False, formato_json=False):
        timestamp = int(time.time())
        
        if formato_txt:
            archivo_txt = f"proxies_vivos.txt"
            with open(archivo_txt, 'w', encoding='utf-8') as f:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            print(f"Guardado: {archivo_txt}")
        
        if formato_json:
            archivo_json = f"proxies_vivos.json"
            datos = {
                "timestamp": timestamp,
                "total_proxies": len(proxies),
                "proxies": proxies
            }
            with open(archivo_json, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2)
            print(f"Guardado: {archivo_json}")

def main():
    parser = argparse.ArgumentParser(description="Proxy Scraper")
    parser.add_argument('-c', '--cantidad', type=int, default=100)
    parser.add_argument('-t', '--threads', type=int, default=50)
    parser.add_argument('-timeout', '--timeout', type=int, default=5)
    parser.add_argument('-txt', action='store_true')
    parser.add_argument('-json', action='store_true')
    
    args = parser.parse_args()
    
    if args.cantidad > 200000:
        print("Error! Cantidad máxima es 200,000")
        sys.exit(1)
    
    scraper = ProxyScraperUltra(max_workers=args.threads, timeout=args.timeout)
    
    try:
        proxies_totales = scraper.obtener_todos_proxies()
        
        if not proxies_totales:
            print("Error: No se obtuvieron proxies. Verificar conexión a internet.")
            sys.exit(1)
        
        proxies_vivos = scraper.verificar_proxies_masivo(proxies_totales, args.cantidad)
        
        if proxies_vivos:
            print(f"\nTotal: {len(proxies_vivos)} proxies vivos")
            
            if args.txt or args.json:
                scraper.guardar_resultados(proxies_vivos, args.txt, args.json)
        else:
            print("No se encontraron proxies vivos ;c")
    
    except KeyboardInterrupt:
        if scraper.proxies_vivos:
            print(f"\nEncontrados: {len(scraper.proxies_vivos)}")
            if args.txt or args.json:
                scraper.guardar_resultados(scraper.proxies_vivos, args.txt, args.json)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
