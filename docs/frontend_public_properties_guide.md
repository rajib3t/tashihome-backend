# Frontend API Guide: Public Properties & Stay Search

Comprehensive integration guide for Frontend developers connecting to the TashiHome Public Property, Stay Search, Slug-based Listing, and Pricing/Sorting APIs.

---

## 1. Overview & Base Configuration

### Base URL
```
https://api.tashihome.com/api/v1
```
*(Or `http://localhost:8000/api/v1` for local development)*

### Headers

| Header | Required For | Description |
| :--- | :--- | :--- |
| `Content-Type` | `POST` requests | `application/json` |
| `Accept` | All requests | `application/json` |

---

## 2. Endpoints Quick Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/properties` | Public listing of properties with slug, price, and sorting filters. |
| `GET` | `/properties/search` | Full stay search with dates, guest count, price, and attributes. |
| `GET` | `/properties/{slug}` | Detailed view of a single property by its unique slug. |
| `POST` | `/properties/check-availability` | Check room availability & dynamic pricing for specified dates. |
| `GET` | `/cities` | List active cities (with slugs and location hierarchies). |

---

## 3. Query Parameters Reference

### 3.1. Main Property Listing: `GET /properties`

Use this endpoint for main property listings, city landing pages, and location/neighborhood listing pages.

| Query Param | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `city_slug` | `string` | No | Match properties by city slug (e.g., `manali`, `darjeeling`, `gangtok`). |
| `location_slug` | `string` | No | Match properties by location slug within a city (e.g., `old-manali`, `mall-road`). |
| `country_slug` | `string` | No | Match properties by country slug (e.g., `india`, `nepal`, `bhutan`). |
| `min_price` | `float` | No | Minimum effective price per night (e.g., `1000.0`). Must be $\ge 0$. |
| `max_price` | `float` | No | Maximum effective price per night (e.g., `5000.0`). Must be $\ge \text{min\_price}$. |
| `is_featured` | `boolean` | No | `true` or `false` to filter exclusively by featured status. |
| `sort_by` | `string` | No | Sort field: `"created_at"` *(default)*, `"name"`, `"price"`. |
| `sort_order` | `string` | No | Direction: `"desc"` *(default)* or `"asc"`. |
| `page` | `integer` | No | Page number (default: `1`, minimum: `1`). |
| `size` | `integer` | No | Items per page (default: `10`, maximum: `100`). |
| `city_id` | `UUID` | No | *(Legacy/Alternative)* Direct City UUID. |
| `location_id`| `UUID` | No | *(Legacy/Alternative)* Direct Location UUID. |
| `country_id` | `UUID` | No | *(Legacy/Alternative)* Direct Country UUID. |

> [!IMPORTANT]
> ### 🏆 Guaranteed Featured-First Ordering
> Regardless of the selected `sort_by` (`name`, `price`, or `created_at`) and `sort_order`, **Featured Properties (`is_featured: true`) always appear at the top** of the results list.
> Within the featured group, your selected sorting criteria is applied, followed by the non-featured group sorted by the same criteria.

> [!NOTE]
> ### 🏷️ Effective Pricing Logic
> Price filtering (`min_price`, `max_price`) and price sorting (`sort_by="price"`) calculate the **effective price**:
> - If `sale_per_night` exists and is $> 0$, the discounted `sale_per_night` is used.
> - Otherwise, `price_per_night` is used.

---

### 3.2. Advanced Stay Search: `GET /properties/search`

Use this endpoint for the global stay search bar where users provide dates, guest counts, and amenity/facility filters.

| Query Param | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `city_slug` | `string` | No | Filter by city slug (e.g., `manali`). |
| `location_slug` | `string` | No | Filter by location slug (e.g., `old-manali`). |
| `country_slug` | `string` | No | Filter by country slug (e.g., `india`). |
| `check_in_date` | `string (YYYY-MM-DD)` | No* | Check-in date *(Required if `check_out_date` is supplied)*. |
| `check_out_date` | `string (YYYY-MM-DD)` | No* | Check-out date *(Must be after `check_in_date`)*. |
| `guests` | `integer` | No | Total guest count (or specify `adults` + `children`). |
| `adults` | `integer` | No | Adult count. |
| `children` | `integer` | No | Children count. |
| `rooms` | `integer` | No | Minimum required rooms count. |
| `min_price` | `float` | No | Minimum effective price per night. |
| `max_price` | `float` | No | Maximum effective price per night. |
| `amenities` | `array[UUID] / string` | No | List of required Amenity IDs (repeat param or comma-separated). |
| `facilities` | `array[UUID] / string` | No | List of required Facility IDs. |
| `room_types` | `array[UUID] / string` | No | List of required Room Type IDs. |
| `property_categories`| `array[UUID]` | No | List of Property Category IDs. |
| `page` | `integer` | No | Page number (default: `1`). |
| `size` | `integer` | No | Page size (default: `10`). |

---

## 4. Frontend Route & URL Design Patterns

### 4.1. URL Structure Recommendations for Next.js / React

| Page | Frontend Route | Backend API Call |
| :--- | :--- | :--- |
| All Homestays | `/homestays` | `GET /properties?page=1&size=12` |
| City Stays | `/homestays/[city_slug]` | `GET /properties?city_slug={city_slug}&page=1&size=12` |
| Location Stays | `/homestays/[city_slug]/[location_slug]` | `GET /properties?city_slug={city_slug}&location_slug={location_slug}&page=1&size=12` |
| Property Details | `/homestay/[slug]` | `GET /properties/{slug}` |

---

### 4.2. Example Request Scenarios

#### Scenario 1: City Landing Page (`/homestays/manali`)
```http
GET /api/v1/properties?city_slug=manali&page=1&size=12
```

#### Scenario 2: Location Page with Price Filter (₹2,000 – ₹6,000)
```http
GET /api/v1/properties?city_slug=manali&location_slug=old-manali&min_price=2000&max_price=6000&page=1&size=12
```

#### Scenario 3: Sorting Alphabetically by Name (A to Z)
```http
GET /api/v1/properties?city_slug=manali&sort_by=name&sort_order=asc&page=1&size=12
```

#### Scenario 4: Sorting by Price (Lowest to Highest)
```http
GET /api/v1/properties?city_slug=manali&sort_by=price&sort_order=asc&page=1&size=12
```

#### Scenario 5: Search Bar with Check-in / Check-out & Guests
```http
GET /api/v1/properties/search?city_slug=manali&check_in_date=2026-10-01&check_out_date=2026-10-05&adults=2&children=1&rooms=1
```

---

## 5. Response Schemas & TypeScript Types

### 5.1. TypeScript Definitions

```typescript
export interface LocationNested {
  id: string;
  name: string;
  slug: string;
}

export interface CityNested {
  id: string;
  name: string;
  slug: string;
}

export interface PropertyAsset {
  id: string;
  file_url: string;
}

export interface RatingSummary {
  average_rating: number;
  total_reviews: number;
}

export interface PublicPropertyItem {
  id: string;
  name: string;
  slug: string;
  type?: string;
  price_per_night: number;
  sale_per_night?: number | null;
  currency?: string;
  address?: string;
  is_featured: boolean;
  feature_image?: PropertyAsset | null;
  city?: CityNested | null;
  location?: LocationNested | null;
  rating_summary?: RatingSummary | null;
  average_rating?: number;
  total_reviews?: number;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next?: boolean;
  has_prev?: boolean;
}

export interface PublicPropertyListResponse {
  success: boolean;
  message: string;
  data: PublicPropertyItem[];
  meta: PaginationMeta;
}
```

---

### 5.2. Sample JSON Response (`GET /properties`)

```json
{
  "success": true,
  "message": "Properties retrieved successfully.",
  "data": [
    {
      "id": "7fa12ca3-c21d-40aa-b8db-0e6d6287f3b8",
      "name": "Apple Blossom Heritage Homestay",
      "slug": "apple-blossom-heritage-homestay",
      "type": "homestay",
      "price_per_night": 3500.0,
      "sale_per_night": 2999.0,
      "currency": "INR",
      "address": "Hadimba Temple Road, Old Manali",
      "is_featured": true,
      "feature_image": {
        "id": "e3d9f25c-3a6c-42c4-df5a-057dc05e298c",
        "file_url": "https://cdn.tashihome.com/properties/apple-blossom-cover.jpg"
      },
      "city": {
        "id": "c1f7b03a-1e4a-40a2-bf3e-835ba83c076a",
        "name": "Manali",
        "slug": "manali"
      },
      "location": {
        "id": "d2c8e14b-2f5b-41b3-cf4f-946cb94d187b",
        "name": "Old Manali",
        "slug": "old-manali"
      },
      "rating_summary": {
        "average_rating": 4.9,
        "total_reviews": 42
      },
      "average_rating": 4.9,
      "total_reviews": 42
    },
    {
      "id": "8eb64db4-d32e-41bb-c9ec-1f7e7398f4c9",
      "name": "Cedar Wood Villa",
      "slug": "cedar-wood-villa",
      "type": "villa",
      "price_per_night": 2200.0,
      "sale_per_night": null,
      "currency": "INR",
      "address": "Club House Road",
      "is_featured": false,
      "feature_image": {
        "id": "f4e0a36d-4b7d-53d5-eg6b-168ed16f309d",
        "file_url": "https://cdn.tashihome.com/properties/cedar-wood-cover.jpg"
      },
      "city": {
        "id": "c1f7b03a-1e4a-40a2-bf3e-835ba83c076a",
        "name": "Manali",
        "slug": "manali"
      },
      "location": {
        "id": "d2c8e14b-2f5b-41b3-cf4f-946cb94d187b",
        "name": "Old Manali",
        "slug": "old-manali"
      },
      "rating_summary": {
        "average_rating": 4.6,
        "total_reviews": 18
      },
      "average_rating": 4.6,
      "total_reviews": 18
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 12,
    "total": 28,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 6. Single Property Detail: `GET /properties/{slug}`

Fetch comprehensive details about a homestay, including room types, amenities, facilities, food options, gallery images, and variable pricing.

- **Method**: `GET`
- **Path**: `/api/v1/properties/{slug}`
- **Optional Query Params**:
  - `check_in_date` (`YYYY-MM-DD`)
  - `check_out_date` (`YYYY-MM-DD`)
  *(When dates are provided, room availability and custom date pricing are computed automatically)*

### Sample Request
```http
GET /api/v1/properties/apple-blossom-heritage-homestay?check_in_date=2026-10-01&check_out_date=2026-10-05
```

---

## 7. Availability & Dynamic Price Check: `POST /properties/check-availability`

Check real-time availability and calculate total cost before navigating to checkout.

- **Method**: `POST`
- **Path**: `/api/v1/properties/check-availability`
- **Headers**: `Content-Type: application/json`

### Request Body
```json
{
  "property_id": "7fa12ca3-c21d-40aa-b8db-0e6d6287f3b8",
  "check_in_date": "2026-10-01",
  "check_out_date": "2026-10-05",
  "room_type_id": "9ca12ca3-c21d-40aa-b8db-0e6d6287f3c1",
  "rooms_count": 1,
  "guests": 2
}
```

---

## 8. Frontend Implementation Examples

### 8.1. React / Next.js Fetch Hook Example

```typescript
import { useState, useEffect } from 'react';

interface UsePropertiesFilter {
  citySlug?: string;
  locationSlug?: string;
  minPrice?: number;
  maxPrice?: number;
  sortBy?: 'name' | 'price' | 'created_at';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  size?: number;
}

export function useProperties(filter: UsePropertiesFilter) {
  const [data, setData] = useState<PublicPropertyListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProperties() {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (filter.citySlug) params.set('city_slug', filter.citySlug);
      if (filter.locationSlug) params.set('location_slug', filter.locationSlug);
      if (filter.minPrice !== undefined) params.set('min_price', String(filter.minPrice));
      if (filter.maxPrice !== undefined) params.set('max_price', String(filter.maxPrice));
      if (filter.sortBy) params.set('sort_by', filter.sortBy);
      if (filter.sortOrder) params.set('sort_order', filter.sortOrder);
      if (filter.page) params.set('page', String(filter.page));
      if (filter.size) params.set('size', String(filter.size));

      try {
        const res = await fetch(`/api/v1/properties?${params.toString()}`);
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.message || 'Failed to fetch properties');
        }
        const json: PublicPropertyListResponse = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || 'An unexpected error occurred');
      } finally {
        setLoading(false);
      }
    }

    fetchProperties();
  }, [
    filter.citySlug,
    filter.locationSlug,
    filter.minPrice,
    filter.maxPrice,
    filter.sortBy,
    filter.sortOrder,
    filter.page,
    filter.size,
  ]);

  return { data, loading, error };
}
```

---

## 9. Error Codes & Handling

| HTTP Code | Error Code | Field | Description / Cause |
| :--- | :--- | :--- | :--- |
| `404 Not Found` | `CITY_NOT_FOUND` | `city_slug` | City with the specified slug does not exist. |
| `404 Not Found` | `LOCATION_NOT_FOUND` | `location_slug` | Location with the specified slug does not exist. |
| `404 Not Found` | `PROPERTY_NOT_FOUND` | `slug` | Property with the specified slug does not exist or is inactive. |
| `422 Unprocessable`| `INVALID_SORT_BY` | `sort_by` | Must be one of `created_at`, `name`, `price`. |
| `422 Unprocessable`| `INVALID_PRICE` | `min_price` / `max_price` | Price cannot be negative. |
| `422 Unprocessable`| `INVALID_PRICE_RANGE` | `min_price` | `min_price` cannot exceed `max_price`. |
| `422 Unprocessable`| `DATE_RANGE_REQUIRED` | `check_out_date` | `check_out_date` must be provided if `check_in_date` is specified. |
| `422 Unprocessable`| `INVALID_DATE_RANGE` | `check_out_date` | `check_out_date` must be strictly after `check_in_date`. |

### Error Response Shape
```json
{
  "success": false,
  "message": "City with given slug not found.",
  "error_code": "CITY_NOT_FOUND",
  "field": "city_slug"
}
```

