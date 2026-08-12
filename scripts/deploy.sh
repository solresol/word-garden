#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
deploy_host=${DEPLOY_HOST:-merah.cassia.ifost.org.au}
deploy_user=${DEPLOY_USER:-wordgarden}
build_date=${BUILD_DATE:-$(TZ=Australia/Sydney date +%F)}

cd "$project_root"
python3 scripts/build.py --today "$build_date"
python3 scripts/verify.py dist

for site in pie esperanto toki; do
  destination="/var/www/vhosts/${site}.symmachus.org/htdocs/"
  rsync -az --delete --exclude .DS_Store "dist/${site}/" "${deploy_user}@${deploy_host}:${destination}"
done

ssh "${deploy_user}@${deploy_host}" \
  'test -f /var/www/vhosts/pie.symmachus.org/htdocs/build.json &&
   test -f /var/www/vhosts/esperanto.symmachus.org/htdocs/build.json &&
   test -f /var/www/vhosts/toki.symmachus.org/htdocs/build.json'

echo "Deployed PIE, Esperanto, and Toki Pona sites for ${build_date} to ${deploy_host}."
