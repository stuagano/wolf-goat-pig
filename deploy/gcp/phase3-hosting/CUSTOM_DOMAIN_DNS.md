# Custom-domain DNS handoff for Jeff

This runbook puts a real domain in front of the existing Firebase Hosting site.
It deliberately does **not** contain guessed A, CNAME, or TXT values: Firebase
generates records for the chosen hostname and those values can differ by domain
and site. The Firebase console is the source of truth.

## Information the app owner must fill in

Use one hostname consistently. Store it in `deploy/gcp/config.env` rather than
copying it into scripts or application code (`config.env` is gitignored; its
documented template is `deploy/gcp/config.env.example`).

```bash
# From the repository root. Hostname only: no scheme, path, or trailing slash.
source deploy/gcp/config.env
test -n "$CUSTOM_DOMAIN" && test -n "$FIREBASE_SITE"
```

Recommended setup: make the apex domain (for example, `example.com`) the
canonical hostname and add `www.example.com` as a redirect to it. If the apex
already hosts something else, use a dedicated subdomain instead. Decide this
before generating records because apex and subdomain records are not
interchangeable.

## App owner: generate Jeff's exact records

1. Open [Firebase Hosting](https://console.firebase.google.com/) and select the
   project that owns `$FIREBASE_SITE`.
2. Open **Hosting**, click **Add custom domain**, and enter `$CUSTOM_DOMAIN`.
3. Choose whether this hostname serves the site or redirects to the canonical
   hostname. Do not advance past a redirect choice without confirming the
   canonical URL.
4. Firebase will display the ownership and Hosting records it requires. Copy
   the record table exactly into the handoff below. Include the record **type**,
   **host/name**, **value/target**, and any TTL requested by Firebase. A
   screenshot is useful as a cross-check, but send the values as text so Jeff
   does not have to transcribe them.
5. If Firebase reports conflicting A, AAAA, or CNAME records, send Jeff the
   specific conflicts shown. Do not ask him to remove unrelated TXT or MX
   records; those may provide email or other domain services.

Do not close or cancel the Firebase wizard while DNS is being changed. Firebase
will continue checking the pending domain.

## Copy/paste handoff to Jeff

Replace every bracketed field with the values displayed by Firebase.

> **Subject: DNS changes for Wolf Goat Pig Firebase Hosting**
>
> Jeff — please make the DNS changes below for **`[CUSTOM_DOMAIN]`**. These
> values came directly from the Firebase Hosting custom-domain wizard for the
> Wolf Goat Pig production site.
>
> | Action | Type | Host / name | Value / target | TTL |
> | --- | --- | --- | --- | --- |
> | Add | `[TXT/A/AAAA/CNAME]` | `[exact host from Firebase]` | `[exact value from Firebase]` | `[Firebase value, or provider default]` |
> | Add | `[additional record, if shown]` | `[exact host]` | `[exact value]` | `[TTL]` |
> | Remove | `[only if Firebase identifies a conflict]` | `[exact host]` | `[old conflicting value]` | N/A |
>
> Please enter host names the way your DNS provider expects. Some providers use
> `@` for the apex and automatically append the zone name; please avoid ending
> up with a duplicated name such as `www.example.com.example.com`.
>
> Please keep the Firebase ownership TXT record in place after verification.
> Do not delete or change any MX, DKIM, SPF, DMARC, or unrelated TXT records.
> If the DNS provider offers HTTP/CDN proxying, set these Firebase records to
> **DNS only** until Firebase has issued its TLS certificate.
>
> Reply when the changes are saved, with a screenshot or exported record list
> showing the final type, name, value, and TTL.

If Firebase supplies more than two records, add rows rather than combining
values. DNS providers may display the apex as `@`, blank, or the full domain;
Jeff should use the convention required by the authoritative DNS provider.

## App owner: verify DNS and finish the cutover

After Jeff confirms the change, inspect the public authoritative answer. Run
the commands for every record type Firebase requested:

```bash
dig +short TXT "$CUSTOM_DOMAIN"
dig +short A "$CUSTOM_DOMAIN"
dig +short AAAA "$CUSTOM_DOMAIN"
dig +short CNAME "www.$CUSTOM_DOMAIN"
```

It is normal for unused record types to return nothing. Compare populated
answers with Firebase's values, not with this document. Then return to the
Firebase Hosting domain panel and wait for both statuses:

- domain ownership/connection is complete; and
- the Firebase-managed TLS certificate is provisioned.

DNS caches and certificate provisioning are not instantaneous. Do not route
users or remove the current `web.app` hostname until HTTPS works end to end:

```bash
curl --fail --show-error --silent --location \
  --output /dev/null --write-out '%{http_code}\n' \
  "https://${CUSTOM_DOMAIN}/"
curl --fail --show-error --silent --location \
  --output /dev/null --write-out '%{http_code}\n' \
  "https://${CUSTOM_DOMAIN}/login"
```

Finally, the app owner—not Jeff—must complete the application configuration:

1. Set `FRONTEND_URL=https://${CUSTOM_DOMAIN}` in
   `deploy/gcp/phase1-cloud-run/env.production.yaml` and redeploy Cloud Run. The
   backend uses this setting for CORS and public links.
2. Add `https://${CUSTOM_DOMAIN}` to the Auth0 application's **Allowed Callback
   URLs**, **Allowed Logout URLs**, and **Allowed Web Origins**. Keep the
   Firebase hostnames during the verification/rollback window.
3. Update uptime checks and any external links only after HTTPS and login have
   both been tested. Keep the Firebase-provided domain as a rollback path.

## Rollback

If the custom hostname fails, leave the Firebase Hosting release untouched and
direct users to `https://${FIREBASE_SITE}.web.app`. DNS changes do not delete or
replace the deployed application. Restore previous DNS records only from a
captured pre-change record set; do not improvise a rollback zone.

Firebase's current reference for this workflow is
[Connect a custom domain](https://firebase.google.com/docs/hosting/custom-domain).
