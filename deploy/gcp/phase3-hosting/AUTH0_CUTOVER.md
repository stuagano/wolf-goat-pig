# Auth0 cutover for Firebase Hosting

After deploying Firebase Hosting, add these URLs in the Auth0 dashboard for application
`qAZuRv5E9mPQ9uTGg7NWpkpfVj8bCeoB` (Wolf Goat Pig SPA):

## Allowed Callback URLs

```
https://seventh-country-232522.web.app
https://seventh-country-232522.firebaseapp.com
https://wolf-goat-pig.vercel.app
http://localhost:3000
```

## Allowed Logout URLs

```
https://seventh-country-232522.web.app
https://seventh-country-232522.firebaseapp.com
https://wolf-goat-pig.vercel.app
http://localhost:3000
```

## Allowed Web Origins

```
https://seventh-country-232522.web.app
https://seventh-country-232522.firebaseapp.com
https://wolf-goat-pig.vercel.app
http://localhost:3000
```

Keep Vercel URLs until decommission. Remove them after the Firebase URL is verified in production.
