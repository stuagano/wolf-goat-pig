# Personal identity — one-time setup

Run these from a terminal/session launched **in a personal folder** (wolf-goat-pig, Divorce, Rachelle, Kayla) so the `personal` profile is active.
Check first:
```bash
echo $ACTIVE_PROFILE   # should print: personal
```

Full context: `~/.profiles/DIAGNOSIS-20260526.md`

The `personal` gcloud config exists but is empty, and `adc-personal.json` is missing — this builds both.

---

## 1. Add the gcloud CLI credential for the personal account
```bash
gcloud auth login stuagano@gmail.com
gcloud config set account stuagano@gmail.com --configuration=personal
```

## 2. Mint ADC for personal
```bash
gcloud auth application-default login          # sign in as stuagano@gmail.com
mv ~/.config/gcloud/application_default_credentials.json ~/.config/gcloud/adc-personal.json
```
(Use `python3 ~/Documents/vibe/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py login` instead if you want full Workspace scopes.)

## 3. Reload
Open a fresh terminal (or `direnv reload`) so the values load.

---

## Verify
```bash
echo $ACTIVE_PROFILE                                 # personal
gcloud config get-value account --configuration=personal   # stuagano@gmail.com
ls -la ~/.config/gcloud/adc-personal.json            # real file exists
[ -n "$GH_TOKEN" ] && echo "GH_TOKEN: set" || echo "GH_TOKEN: EMPTY"   # set (stuagano)
git config user.email                                # stuagano@gmail.com
```

> Note: gh for personal uses `stuagano` (already working). No gh changes needed here — that's already wired in `personal.env`.
