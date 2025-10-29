# GHIN API Documentation

This document provides an overview of the reverse-engineered GHIN (Golf Handicap and Information Network) API used in this project.

## Authentication

The GHIN API uses JSON Web Tokens (JWTs) for authentication. To obtain a JWT, you need to send a POST request to the following endpoint:

**URL:** `https://api2.ghin.com/api/v1/golfer_login.json`

**Method:** `POST`

**Headers:**

*   `User-Agent`: `WolfGoatPig/1.0`
*   `Content-Type`: `application/json`

**Payload:**

```json
{
  "user": {
    "password": "YOUR_GHIN_PASSWORD",
    "email_or_ghin": "YOUR_GHIN_USERNAME_OR_EMAIL",
    "remember_me": false
  },
  "token": "YOUR_STATIC_TOKEN",
  "source": "GHINcom"
}
```

**Example Response:**

```json
{
  "golfer_user": {
    "golfer_user_token": "YOUR_JWT_TOKEN"
  }
}
```

## Golfer Search

Once you have a valid JWT, you can use it to search for golfers by name.

**URL:** `https://api2.ghin.com/api/v1/golfers/search.json`

**Method:** `GET`

**Headers:**

*   `Authorization`: `Bearer YOUR_JWT_TOKEN`
*   `User-Agent`: `WolfGoatPig/1.0`
*   `Accept`: `application/json`

**Parameters:**

*   `last_name`: The golfer's last name (required).
*   `first_name`: The golfer's first name (optional).
*   `page`: The page number for pagination (optional, defaults to 1).
*   `per_page`: The number of results per page (optional, defaults to 10).
*   `source`: `GHINcom` (required).

**Example Request:**

```
GET https://api2.ghin.com/api/v1/golfers/search.json?last_name=Smith&first_name=John&page=1&per_page=10&source=GHINcom
```

**Example Response:**

```json
{
  "golfers": [
    {
      "first_name": "John",
      "last_name": "Smith",
      "ghin_number": "1234567",
      "club_name": "Example Golf Club",
      "handicap_index": "10.5"
    }
  ]
}
```
