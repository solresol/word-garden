# Deployment

## Host layout

Static files are published as `wordgarden:wordgarden` to:

```text
/var/www/vhosts/pie.symmachus.org/htdocs/
/var/www/vhosts/esperanto.symmachus.org/htdocs/
/var/www/vhosts/toki.symmachus.org/htdocs/
/var/www/vhosts/solresol.symmachus.org/htdocs/
```

The required OpenBSD `httpd` blocks are in `infra/httpd.conf`. They deliberately omit directory indexes and CGI.

After an administrator adds the blocks:

```sh
doas httpd -n
doas rcctl reload httpd
```

## DNS

Create proxied `A` records for the four hostnames, pointing to the same origin IPv4 address as the existing Symmachus sites on `merah`:

```text
pie.symmachus.org
esperanto.symmachus.org
toki.symmachus.org
solresol.symmachus.org
```

Verify both Cloudflare’s API result and public resolution. A dashboard form or successful API request is not enough by itself.

The repository helper defaults to check-only mode and reads `ZoneID:` / `API token:` from `~/.cloudflare` without printing the credential. If `ZoneID:` is absent, it falls back to a zone-name lookup, which requires `Zone Read` in addition to DNS access:

```sh
scripts/ensure_cloudflare_dns.sh --check
scripts/ensure_cloudflare_dns.sh --apply
```

It changes only the four explicit `A` records, keeps them proxied, refuses ambiguous duplicate records, and currently expects the live `merah` origin IPv4 `59.167.239.92`. Override that after a host move with `WORD_GARDEN_ORIGIN_IPV4`.

## GitHub secrets

The dedicated key’s public half belongs in `/home/wordgarden/.ssh/authorized_keys`; its private half belongs only in the repository Actions secret `DEPLOYMENT_SSH_KEY`.

Capture the host key from a trusted existing SSH connection and store the complete known-hosts line in `DEPLOY_KNOWN_HOSTS`. The workflow does not use `StrictHostKeyChecking=no`.

## Manual fallback

From an authorised checkout whose SSH key is accepted by the service account:

```sh
DEPLOY_USER=wordgarden DEPLOY_HOST=merah.cassia.ifost.org.au scripts/deploy.sh
```

## Release evidence

A completed release requires all of the following:

- tests and generated-link/feed verification pass;
- the Actions deploy job passes;
- each remote vhost contains `build.json` for the intended revision;
- all four public HTTPS roots and feeds return 200;
- the public pages show the intended `today.json` date and headword.
