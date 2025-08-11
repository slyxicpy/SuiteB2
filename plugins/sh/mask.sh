# DESC: Acorta y enmascara URLs. Uso: mask.sh https://PhishingUrls.com -d otheris.com -k secure,login

usage() {
    echo "Uso: $0 <url> [-d dominio] [-k keywords] [-o output]"
    echo "Ejemplo: $0 https://example.com -d login.micros.com -k secure,account -o json"
    echo "Opciones:"
    echo "  -d: Dominio para enmascarar (por defecto: login.live.com)"
    echo "  -k: Palabras clave separadas por comas (por defecto: login,secure,account)"
    echo "  -o: Formato de salida (text, json, both) (por defecto: both)"
    exit 1
}

urlencode() {
    local string="${1}"
    local strlen=${#string}
    local encoded=""
    local pos c o

    for (( pos=0 ; pos<strlen ; pos++ )); do
        c=${string:$pos:1}
        case "$c" in
            [-_.~a-zA-Z0-9] ) o="${c}" ;;
            * ) printf -v o '%%%02x' "'$c" ;;
        esac
        encoded+="${o}"
    done
    echo "${encoded}"
}

if [ $# -lt 1 ]; then
    usage
fi

url="$1"
shift
mask_domain="login.live.com"
keywords="login,secure,account"
output_format="both"

while getopts "d:k:o:" opt; do
    case $opt in
        d) mask_domain="$OPTARG";;
        k) keywords="$OPTARG";;
        o) output_format="$OPTARG";;
        *) usage;;
    esac
done

if ! [[ "$url" =~ ^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,} ]]; then
    echo "Error: URL inválida. Debe comenzar con http:// o https://"
    exit 1
fi

if ! [[ "$mask_domain" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "Error: Dominio de enmascaramiento inválido"
    exit 1
fi

if ! [[ "$output_format" =~ ^(text|json|both)$ ]]; then
    echo "Error: Formato de salida debe ser text, json o both"
    exit 1
fi

timestamp=$(date +%Y%m%d_%H%M%S)
url_clean=$(echo "$url" | sed 's|https\?://||' | sed 's|/.*||' | tr '.' '_')
output_dir="mask_${url_clean}_${timestamp}"

if ! mkdir -p "$output_dir"; then
    echo "Error: No se pudo crear el directorio de salida $output_dir"
    exit 1
fi

json_summary="$output_dir/mask.json"
echo "{" > "$json_summary"

log_command() {
    local cmd_name="$1"
    local cmd_output="$2"
    if [[ "$output_format" == "text" || "$output_format" == "both" ]]; then
        echo "=== $cmd_name ===" | tee -a "$output_dir/$cmd_name.txt"
        echo "$cmd_output" | tee -a "$output_dir/$cmd_name.txt"
        echo "" | tee -a "$output_dir/$cmd_name.txt"
    fi
}

add_to_json() {
    local key="$1"
    local value="$2"
    echo "  \"$key\": $value," >> "$json_summary"
}

check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "Advertencia: $1 no está instalado."
        return 1
    fi
    return 0
}

echo "Iniciando enmascaramiento para: $url"
echo "Dominio de máscara: $mask_domain"
echo "Keywords: $keywords"
echo ""

add_to_json "original_url" "\"$url\""
add_to_json "mask_domain" "\"$mask_domain\""
add_to_json "keywords" "\"$keywords\""
add_to_json "timestamp" "\"$(date -Iseconds)\""

echo "Acortando URL..."
shortened_urls=()

if check_tool "curl"; then
    # TinyURL
    echo "Probando TinyURL..."
    encoded_url=$(urlencode "$url")
    short_url=$(curl -s --max-time 10 "https://tinyurl.com/api-create.php?url=$encoded_url" 2>/dev/null)
    if [ $? -eq 0 ] && [[ "$short_url" =~ ^https?:// ]] && [[ ! "$short_url" =~ Error ]]; then
        shortened_urls+=("$short_url")
        echo "[OK] TinyURL: $short_url"
        log_command "tinyurl" "$short_url"
    else
        echo "[FAIL] TinyURL no disponible"
    fi
    
    # is.gd
    echo "Probando is.gd..."
    short_url=$(curl -s --max-time 10 "https://is.gd/create.php?format=simple&url=$encoded_url" 2>/dev/null)
    if [ $? -eq 0 ] && [[ "$short_url" =~ ^https?:// ]] && [[ ! "$short_url" =~ Error ]]; then
        shortened_urls+=("$short_url")
        echo "[OK] is.gd: $short_url"
        log_command "isgd" "$short_url"
    else
        echo "[FAIL] is.gd no disponible"
    fi
    
    # v.gd
    echo "Probando v.gd..."
    short_url=$(curl -s --max-time 10 "https://v.gd/create.php?format=simple&url=$encoded_url" 2>/dev/null)
    if [ $? -eq 0 ] && [[ "$short_url" =~ ^https?:// ]] && [[ ! "$short_url" =~ Error ]]; then
        shortened_urls+=("$short_url")
        echo "[OK] v.gd: $short_url"
        log_command "vgd" "$short_url"
    else
        echo "[FAIL] v.gd no disponible"
    fi
else
    echo "Error: curl no está instalado"
    exit 1
fi

if [ ${#shortened_urls[@]} -eq 0 ]; then
    echo "Error: No se pudo acortar la URL con ningún servicio"
    exit 1
fi

json_shortened_urls=$(printf '%s\n' "${shortened_urls[@]}" | sed 's/.*/"&"/' | paste -sd, -)
add_to_json "shortened_urls" "[$json_shortened_urls]"

echo ""
echo "Generando URLs enmascaradas..."

IFS=',' read -ra keyword_array <<< "$keywords"
masked_urls=()

for short_url in "${shortened_urls[@]}"; do
    for keyword in "${keyword_array[@]}"; do
        keyword=$(echo "$keyword" | xargs)
        
        random_id=$((RANDOM % 1000000))
        masked_url1="https://$mask_domain-$keyword.verification-$random_id@${short_url#https://}"
        masked_urls+=("$masked_url1")
        
        masked_url2="https://$mask_domain/$keyword-verification?redirect=$(urlencode "$short_url")&session=$random_id"
        masked_urls+=("$masked_url2")
        
        masked_url3="https://$mask_domain/auth/$keyword?url=$(urlencode "$short_url")&token=$random_id"
        masked_urls+=("$masked_url3")
    done
done

echo "URLs enmascaradas generadas: ${#masked_urls[@]}"
for masked_url in "${masked_urls[@]}"; do
    echo "[MASKED] $masked_url"
done

log_command "masked_urls" "$(printf '%s\n' "${masked_urls[@]}")"

json_masked_urls=$(printf '%s\n' "${masked_urls[@]}" | sed 's/.*/"&"/' | paste -sd, -)
add_to_json "masked_urls" "[$json_masked_urls]"
add_to_json "total_masked" "${#masked_urls[@]}"

echo ""
echo "Generando variaciones adicionales..."

variations=()
for short_url in "${shortened_urls[@]}"; do
    legitimate_domains=("login.microsoft.com" "accounts.google.com" "secure.paypal.com" "login.yahoo.com" "accounts.adobe.com")
    
    for domain in "${legitimate_domains[@]}"; do
        random_session=$((RANDOM % 999999))
        variation="https://$domain/verify?redirect=$(urlencode "$short_url")&session=$random_session"
        variations+=("$variation")
    done
done

echo "Variaciones generadas: ${#variations[@]}"
for variation in "${variations[@]:0:10}"; do
    echo "[VARIATION] $variation"
done

if [ ${#variations[@]} -gt 10 ]; then
    echo "... y $((${#variations[@]} - 10)) más"
fi

log_command "variations" "$(printf '%s\n' "${variations[@]}")"

json_variations=$(printf '%s\n' "${variations[@]}" | sed 's/.*/"&"/' | paste -sd, -)
add_to_json "variations" "[$json_variations]"
add_to_json "total_variations" "${#variations[@]}"

sed -i '$ s/,$//' "$json_summary"
echo "}" >> "$json_summary"

{
    echo "RESUMEN DE ENMASCARAMIENTO"
    echo "========================="
    echo "URL original: $url"
    echo "Dominio máscara: $mask_domain"
    echo "Keywords: $keywords"
    echo "Timestamp: $(date)"
    echo ""
    echo "URLs acortadas (${#shortened_urls[@]}):"
    printf '  %s\n' "${shortened_urls[@]}"
    echo ""
    echo "URLs enmascaradas (${#masked_urls[@]}):"
    printf '  %s\n' "${masked_urls[@]}"
    echo ""
    echo "Variaciones (${#variations[@]}):"
    printf '  %s\n' "${variations[@]:0:5}"
    if [ ${#variations[@]} -gt 5 ]; then
        echo "  ... y $((${#variations[@]} - 5)) más en $output_dir/variations.txt"
    fi
    echo ""
    echo "Archivos generados en $output_dir/:"
    ls -la "$output_dir/" | tail -n +2 | awk '{print "  " $9 " (" $5 " bytes)"}'
} | tee "$output_dir/resumen_final.txt"

echo ""
echo "Proceso completado exitosamente!"
echo "Directorio de salida: $output_dir/"
echo "Total de URLs generadas: $((${#shortened_urls[@]} + ${#masked_urls[@]} + ${#variations[@]}))"

if [[ "$output_format" == "json" || "$output_format" == "both" ]]; then
    echo "Resumen JSON: $json_summary"
fi
