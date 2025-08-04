# DESC: Scan port's. Uso: scan <ip> o <url> -web -vpn -db -geo -full -email -ftp -iot -leak>
from socket import *
import requests
print("""
\033[36m******************************
*   By styx                  *    
*   Scanner Simple           *
******************************\033[0m
""")
def sexo():
    entrada = input('\033[33mIngrese objetivo: <hentaila.com> o <ip> -full -db): \033[0m')
    partes = entrada.strip().split()

    objetivo = partes[0]
    modo = partes[1] if len(partes) > 1 else None
    return objetivo, modo

def modos(modo):
    if modo == '-full':
        return list(range(1, 65536))
    elif modo == '-db':
        return [3306, 5432, 1521, 1433, 5000, 27017, 6379, 9042, 9200, 4984, 16000, 8091, 8086, 9042, 26257, 4000, 9000, 3306, 5433, 8812, 7687, 8529, 14240, 8080, 19530, 6333, 8000]
    elif modo == '-web':
        return [80, 443, 8080, 8443, 8000, 3000, 5000]
    elif modo == '-email':
        return [25, 110, 143, 465, 587, 993, 995]
    elif modo == '-ftp':
        return [20, 21, 989, 990]
    elif modo == '-vpn':
        return [1194, 1701, 1723, 500, 4500]
    elif modo == 'iot':
        return [23, 81, 554, 8001, 88, 161, 37777]
    elif modo == '-leak':
        return [9200, 27017, 6379, 5984, 15672, 5000]
    elif modo == '-geo':
        return None
    else:
        return obtener_puertos()
def geo(ip):
    url = f"http://ip-api.com/json/{ip}"
    try:
        respuesta = requests.get(url, timeout=5).json()
        if respuesta["status"] == "success":
            return {
                "IP": respuesta["query"],
                "País": respuesta["country"],
                "Región": respuesta["regionName"],
                "Ciudad": respuesta["city"],
                "Latitud": respuesta["lat"],
                "Longitud": respuesta["lon"],
                "ISP": respuesta["isp"],
                "Organización": respuesta["org"]
            }
        else:
            return {"error": "No se pudo geolocalizar la IP"}
    except Exception as e:
        return {"error": str(e)}

def obtener_puertos():
    puertos = input('\033[33mIngrese puertos separados por coma (ej: 22,80,443): \033[0m')
    return [int(p.strip()) for p in puertos.split(',') if p.strip().isdigit()]

def nombre_servicio(puerto):
    try:
        return getservbyport(puerto)
    except:
        return "desconocido"

def conScan(tgHost, tgtPort):
    try:
        const = socket(AF_INET, SOCK_STREAM)
        const.connect((tgHost, tgtPort))
        print(f'\033[32m[+] {tgtPort}abierto ({nombre_servicio(tgtPort)})\033[0m')
        const.close()
    except:
        print(f'\033[31m[-] {tgtPort}cerrado\033[0m')

def portScan(tgHost, tgtPorts):
    try:
        tgip = gethostbyname(tgHost)
    except Exception as e:
        print(f'\033[31m[-] No se pudo resolver el host: {tgHost} ({e})\033[0m')
        return

    try:
        tgname = gethostbyaddr(tgip)
        print(f'\n\033[36m[+] Resultado del scan para: {tgname[0]} ({tgip})\033[0m')
    except:
        print(f'\n\033[36m[+] Resultado del scan para: {tgip}\033[0m')
    
    setdefaulttimeout(1)
    for port in tgtPorts:
        print(f'\033[34mEscaneando puerto: {port}\033[0m')
        conScan(tgHost, int(port))

if __name__ == "__main__":
    objetivo, modo = sexo()
    
    if modo == '-geo':
        resultado = geo(objetivo)
        print("\n\033[36m[+] Info geo:\033[0m")
        for clave, valor in resultado.items():
            print(f"{clave}: {valor}")
    else:
        puertos = modos(modo)
        portScan(objetivo, puertos)
