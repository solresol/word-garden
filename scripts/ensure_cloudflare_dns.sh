#!/bin/sh
set -eu

credentials=${CLOUDFLARE_CREDENTIALS:-"$HOME/.cloudflare"}
api_base=${CLOUDFLARE_API_BASE:-https://api.cloudflare.com/client/v4}
zone_name=${CLOUDFLARE_ZONE:-symmachus.org}
origin_ipv4=${WORD_GARDEN_ORIGIN_IPV4:-59.167.239.92}
mode=${1:---check}

case "$mode" in
  --check|--apply) ;;
  *) echo "Usage: $0 [--check|--apply]" >&2; exit 2 ;;
esac

if [ ! -r "$credentials" ]; then
  echo "Cloudflare credentials are not readable: $credentials" >&2
  exit 1
fi

api_token=${CLOUDFLARE_API_TOKEN:-$(awk -F': *' '$1 == "API token" {print $2; exit}' "$credentials")}
zone_id=${CLOUDFLARE_ZONE_ID:-$(awk -F': *' '$1 == "ZoneID" {print $2; exit}' "$credentials")}
if [ -z "$api_token" ]; then
  echo "No API token found in CLOUDFLARE_API_TOKEN or $credentials" >&2
  exit 1
fi

cf_get() {
  /usr/bin/curl --fail-with-body --silent --show-error \
    -H "Authorization: Bearer $api_token" \
    -H 'Content-Type: application/json' \
    "$api_base/$1"
}

if [ -z "$zone_id" ]; then
  zone_response=$(cf_get "zones?name=$zone_name") || {
    echo "Could not look up Cloudflare zone $zone_name; add ZoneID to $credentials or grant Zone Read." >&2
    exit 1
  }
  zone_id=$(printf '%s' "$zone_response" | jq -r '.result[0].id // empty')
  if [ -z "$zone_id" ]; then
    echo "Cloudflare zone not found: $zone_name" >&2
    exit 1
  fi
fi

for label in pie esperanto toki solresol; do
  hostname="$label.$zone_name"
  records=$(cf_get "zones/$zone_id/dns_records?type=A&name=$hostname") || {
    echo "The token cannot read DNS records. Grant DNS Read and DNS Write for $zone_name." >&2
    exit 1
  }
  count=$(printf '%s' "$records" | jq '.result | length')
  if [ "$count" -gt 1 ]; then
    echo "Refusing to change $hostname: Cloudflare returned $count A records." >&2
    exit 1
  fi

  if [ "$count" -eq 1 ]; then
    record_id=$(printf '%s' "$records" | jq -r '.result[0].id')
    current=$(printf '%s' "$records" | jq -r '.result[0] | [.content, (.proxied|tostring)] | @tsv')
    expected=$(printf '%s\ttrue' "$origin_ipv4")
    if [ "$current" = "$expected" ]; then
      echo "OK $hostname -> $origin_ipv4 (proxied)"
      continue
    fi
    action=update
    endpoint="zones/$zone_id/dns_records/$record_id"
    method=PUT
  else
    action=create
    endpoint="zones/$zone_id/dns_records"
    method=POST
  fi

  if [ "$mode" = "--check" ]; then
    echo "WOULD_$action $hostname -> $origin_ipv4 (proxied)"
    continue
  fi

  payload=$(jq -n \
    --arg name "$hostname" \
    --arg content "$origin_ipv4" \
    '{type:"A", name:$name, content:$content, ttl:1, proxied:true, comment:"Word Garden static site on merah"}')
  response=$(/usr/bin/curl --fail-with-body --silent --show-error \
    -X "$method" \
    -H "Authorization: Bearer $api_token" \
    -H 'Content-Type: application/json' \
    --data "$payload" \
    "$api_base/$endpoint") || {
      echo "Cloudflare failed to $action $hostname" >&2
      exit 1
    }
  success=$(printf '%s' "$response" | jq -r '.success')
  if [ "$success" != true ]; then
    echo "Cloudflare did not confirm $action for $hostname" >&2
    exit 1
  fi
  echo "${action}d $hostname -> $origin_ipv4 (proxied)"
done
