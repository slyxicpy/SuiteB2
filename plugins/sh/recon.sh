# DESC: Reconocimiento completo de dominio. uso: recon hentaila.com

usage() {
    echo "Uso: $0 <dominio>"
    echo "Ejemplo: $0 xvideos.com"
    exit 1
}

if [ $# -ne 1 ]; then
    usage
fi

domain="$1"
if ! [[ $domain =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "Error: Dominio inválido. Debe ser un dominio válido (ejemplo: hentaiLa.com)"
    exit 1
fi

timestamp=$(date +%Y%m%d_%H%M%S)
output_dir="recon_${domain}_${timestamp}"
mkdir -p "$output_dir"
if [ $? -ne 0 ]; then
    echo "Error: No se pudo crear el directorio de salida $output_dir"
    exit 1
fi

json_summary="$output_dir/recon.json"
echo "{" > "$json_summary"

log_command() {
    local cmd_name="$1"
    local cmd_output="$2"
    echo "=== $cmd_name ===" | tee -a "$output_dir/$cmd_name.txt"
    echo "$cmd_output" | tee -a "$output_dir/$cmd_name.txt"
    echo "" | tee -a "$output_dir/$cmd_name.txt"
}

add_to_json() {
    local key="$1"
    local value="$2"
    echo "  \"$key\": $value," >> "$json_summary"
}

check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "Advertencia: $1 no está instalado. Algunas funciones estarán limitadas."
        return 1
    fi
    return 0
}

tools=("nslookup" "whois" "dig" "host" "curl" "traceroute" "openssl" "whatweb" "jq")
missing_tools=()
for tool in "${tools[@]}"; do
    check_tool "$tool" || missing_tools+=("$tool")
done
if [ ${#missing_tools[@]} -ne 0 ]; then
    echo "Herramientas faltantes: ${missing_tools[*]}. Instálelas para funcionalidad completa (sudo apt install ${missing_tools[*]})."
fi

echo "Iniciando reconocimiento para $domain..." | tee "$output_dir/recon.txt"
echo "Fecha: $(date)" | tee -a "$output_dir/recon_summary.txt"
echo "---------------------------------------" | tee -a "$output_dir/recon.txt"
add_to_json "domain" "\"$domain\""
add_to_json "date" "\"$(date)\""

echo "Resolviendo IPs asociadas..."
ip_output=$(dig +short "$domain" A 2>&1)
if [ $? -eq 0 ] && [ -n "$ip_output" ]; then
    log_command "ip_resolution" "$ip_output"
    add_to_json "ip_addresses" "[$(echo "$ip_output" | sed 's/\n/","/g' | sed 's/,$//')]"
else
    echo "No se encontraron IPs para $domain"
    add_to_json "ip_addresses" "[]"
fi

echo "Obteniendo geo de IPs..."
ip_list=($ip_output)
geo_data=""
for ip in "${ip_list[@]}"; do
    if [ -n "$ip" ]; then
        geo_output=$(curl -s "http://ip-api.com/json/$ip?fields=status,country,regionName,city,lat,lon,isp,org,query" 2>/dev/null)
        if [ $? -eq 0 ] && [[ "$geo_output" =~ "success" ]]; then
            geo_data="$geo_data\nIP: $ip\n$(echo "$geo_output" | jq .)"
        else
            geo_data="$geo_data\nIP: $ip\nError: No se pudo obtener geolocalización"
        fi
        sleep 1
    fi
done
log_command "geolocation" "$geo_data"
add_to_json "geolocation" "$(echo "$geo_data" | jq -R . | jq -s .)"

echo "Ejecutando nslookup..."
nslookup_output=$(nslookup -type=ANY "$domain" 2>&1)
log_command "nslookup" "$nslookup_output"
add_to_json "nslookup" "$(echo "$nslookup_output" | jq -R . | jq -s .)"

echo "Ejecutando whois..."
whois_output=$(whois "$domain" 2>&1)
log_command "whois" "$whois_output"
registrar=$(echo "$whois_output" | grep -i "Registrar:" | head -n 1 | awk -F: '{print $2}' | xargs)
creation_date=$(echo "$whois_output" | grep -i "Creation Date:" | head -n 1 | awk -F: '{print $2}' | xargs)
add_to_json "whois_registrar" "\"${registrar:-Desconocido}\""
add_to_json "whois_creation_date" "\"${creation_date:-Desconocido}\""

echo "Ejecutando dig para registros DNS..."
dig_output=$(dig +nocmd "$domain" ANY +multiline +noall +answer 2>&1)
log_command "dig" "$dig_output"
add_to_json "dns_records" "$(echo "$dig_output" | jq -R . | jq -s .)"

echo "Ejecutando host..."
host_output=$(host -a "$domain" 2>&1)
log_command "host" "$host_output"
add_to_json "host" "$(echo "$host_output" | jq -R . | jq -s .)"

echo "Buscando subdominios..."
subdomains=("www" "mail" "ftp" "ns1" "ns2" "webmail" "smtp" "pop" "imap" "admin" "api" "dev" "staging")
subdomain_ips=""
found_subdomains=()
if [ -f "subdomains.txt" ]; then
    mapfile -t wordlist < subdomains.txt
    subdomains+=("${wordlist[@]}")
fi
for sub in "${subdomains[@]}"; do
    subdomain="${sub}.${domain}"
    sub_host_output=$(host "$subdomain" 2>&1)
    if [[ ! $sub_host_output =~ "not found" ]]; then
        log_command "subdomain_${sub}" "$sub_host_output"
        found_subdomains+=("$subdomain")
        sub_ip=$(echo "$sub_host_output" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
        if [ -n "$sub_ip" ]; then
            subdomain_ips="$subdomain_ips\n$subdomain: $sub_ip"
        fi
    fi
done
log_command "subdomains_ips" "$subdomain_ips"
add_to_json "subdomains" "[$(printf '"%s",' "${found_subdomains[@]}" | sed 's/,$//')]"

echo "Ejecutando traceroute..."
traceroute_output=$(traceroute "$domain" 2>&1)
log_command "traceroute" "$traceroute_output"
add_to_json "traceroute" "$(echo "$traceroute_output" | jq -R . | jq -s .)"

echo "Obteniendo cabeceras HTTP/HTTPS..."
http_output=$(curl -s -I "http://$domain" 2>&1)
https_output=$(curl -s -I "https://$domain" 2>&1)
log_command "http_headers" "$http_output"
log_command "https_headers" "$https_output"
add_to_json "http_headers" "$(echo "$http_output" | jq -R . | jq -s .)"
add_to_json "https_headers" "$(echo "$https_output" | jq -R . | jq -s .)"

if check_tool openssl; then
    echo "Analizando certificado SSL..."
    ssl_output=$(echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null | openssl x509 -noout -text 2>&1)
    if [ $? -eq 0 ]; then
        log_command "ssl_certificate" "$ssl_output"
        add_to_json "ssl_certificate" "$(echo "$ssl_output" | jq -R . | jq -s .)"
    else
        echo "No se pudo obtener certificado SSL"
        add_to_json "ssl_certificate" "\"No disponible\""
    fi
fi

if check_tool whatweb; then
    echo "Detectando tecnologías web..."
    whatweb_output=$(whatweb -a 3 "$domain" 2>&1)
    log_command "whatweb" "$whatweb_output"
    add_to_json "web_technologies" "$(echo "$whatweb_output" | jq -R . | jq -s .)"
fi

echo "Enumerando directorios comunes..."
dirs=("admin" "login" "wp-admin" "phpmyadmin" "config" "backup" ".git" ".env")
found_dirs=()
for dir in "${dirs[@]}"; do
    dir_response=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain/$dir/" 2>/dev/null)
    if [ "$dir_response" == "200" ] || [ "$dir_response" == "301" ] || [ "$dir_response" == "302" ]; then
        found_dirs+=("$dir")
        log_command "directory_$dir" "Directorio encontrado: https://$domain/$dir/ (Código: $dir_response)"
    fi
done
add_to_json "directories" "[$(printf '"%s",' "${found_dirs[@]}" | sed 's/,$//')]"

echo "Generando resumen..."
{
    echo "Resumen de Reconocimiento"
    echo "================================"
    echo "Dominio: $domain"
    echo "Fecha: $(date)"
    echo "Directorio de resultados: $output_dir"
    echo ""
    echo "IPs encontradas: ${ip_list[*]}"
    echo "Subdominios encontrados: ${found_subdomains[*]}"
    echo "Directorios accesibles: ${found_dirs[*]}"
    echo ""
    echo "Archivos generados para analisis:"
    ls -1 "$output_dir" | while read -r file; do
        echo "- $file"
    done
} | tee -a "$output_dir/recon.txt"

sed -i '$ s/,$//' "$json_summary"
echo "}" >> "$json_summary"

echo "Reconocimiento completado. Resultados guardados en $output_dir/"
echo "Resumen JSON generado en $output_dir/recon.json"