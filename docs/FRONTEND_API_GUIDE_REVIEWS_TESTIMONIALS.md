# Frontend API Guide: Reviews & Testimonials

Comprehensive integration guide for Frontend developers connecting to the TashiHome Homestay Reviews and Testimonials APIs.

---

## 1. General Principles & Headers

### Base URL
```
https://api.tashihome.com/api/v1
```
(Or `http://localhost:8000/api/v1` for local development)

### Headers

| Header | Required For | Description |
| :--- | :--- | :--- |
| `Authorization` | Protected routes | `Bearer <access_token>` (if using Bearer token instead of HttpOnly cookies) |
| `X-CSRF-Token` | State-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) | CSRF token extracted from cookie or `/api/v1/auth/csrf` |
| `X-Idempotency-Key` | Specific create requests (`POST`) | UUIDv4 string (e.g. `crypto.randomUUID()`) to prevent duplicate submits |
| `Content-Type` | JSON bodies | `application/json` |

---

## 2. Review APIs

### 2.1. User Review Endpoints

#### 1. Submit Review for a Booking
- **Method**: `POST`
- **Path**: `/api/v1/user/reviews`
- **Auth**: User token
- **Headers**: `X-CSRF-Token`, `X-Idempotency-Key`
- **Request Body**:
```json
{
  "booking_id": "b3c5a892-71df-4b92-9a3b-2804f329bb62", // Public UUID or Booking Reference like "BK26083186CE96"
  "booking_reference": "BK26083186CE96", // (Optional alternative to booking_id)
  "rating": 5,
  "comment": "Had an incredible stay! The mountain views and home-cooked breakfast were exceptional."
}
```
- **Response** (`201 Created`):
```json
{
  "success": true,
  "message": "Review submitted successfully and is pending approval.",
  "data": {
    "id": "7a94f1c2-3e28-444a-89cf-1234567890ab",
    "rating": 5,
    "comment": "Had an incredible stay! The mountain views and home-cooked breakfast were exceptional.",
    "host_reply": null,
    "host_replied_at": null,
    "status": "pending",
    "created_at": "2026-09-03T19:40:00Z",
    "updated_at": "2026-09-03T19:40:00Z",
    "property": {
      "id": "e4f8c92a-3b1a-4d2f-9812-34567890abcd",
      "name": "Himalayan Sunrise Homestay",
      "slug": "himalayan-sunrise-homestay"
    },
    "booking": {
      "id": "b3c5a892-71df-4b92-9a3b-2804f329bb62",
      "booking_reference": "BK-202609-8921",
      "check_in_date": "2026-08-20",
      "check_out_date": "2026-08-25"
    }
  }
}
```

#### 2. Get User's Reviews
- **Method**: `GET`
- **Path**: `/api/v1/user/reviews?page=1&page_size=10&sort_order=desc`
- **Auth**: User token
- **Response** (`200 OK`):
```json
{
  "success": true,
  "message": "Reviews retrieved successfully.",
  "data": [
    {
      "id": "7a94f1c2-3e28-444a-89cf-1234567890ab",
      "rating": 5,
      "comment": "Had an incredible stay!",
      "host_reply": "Thank you for staying with us!",
      "host_replied_at": "2026-09-04T10:00:00Z",
      "status": "published",
      "created_at": "2026-09-03T19:40:00Z",
      "updated_at": "2026-09-04T10:00:00Z",
      "property": {
        "id": "e4f8c92a-3b1a-4d2f-9812-34567890abcd",
        "name": "Himalayan Sunrise Homestay",
        "slug": "himalayan-sunrise-homestay"
      }
    }
  ],
  "meta": {
    "pagination": {
      "total": 1,
      "page": 1,
      "page_size": 10,
      "pages": 1
    }
  }
}
```

#### 3. Update User's Review
- **Method**: `PUT`
- **Path**: `/api/v1/user/reviews/{review_id}`
- **Auth**: User token
- **Headers**: `X-CSRF-Token`
- **Request Body**:
```json
{
  "rating": 4,
  "comment": "Updated comment: Clean rooms, great hosts, slightly bumpy road to reach."
}
```
*(Note: Editing a review automatically resets its status to `pending` for admin approval.)*

#### 4. Delete User's Review
- **Method**: `DELETE`
- **Path**: `/api/v1/user/reviews/{review_id}`
- **Auth**: User token
- **Headers**: `X-CSRF-Token`
- **Response** (`200 OK`):
```json
{
  "success": true,
  "message": "Review deleted successfully.",
  "data": null
}
```

---

### 2.2. Vendor Review Endpoints

#### 1. Get Reviews on Vendor's Properties
- **Method**: `GET`
- **Path**: `/api/v1/vendor/reviews?page=1&page_size=10&status=published`
- **Auth**: Vendor token
- **Response** (`200 OK`): List of reviews with guest name and booking details.

#### 2. Reply to a Review
- **Method**: `POST`
- **Path**: `/api/v1/vendor/reviews/{review_id}/reply`
- **Auth**: Vendor token
- **Headers**: `X-CSRF-Token`
- **Request Body**:
```json
{
  "host_reply": "Thank you so much for your kind words! We would love to host you again."
}
```

---

### 2.3. Admin Review Moderation Endpoints

#### 1. List All Reviews
- **Method**: `GET`
- **Path**: `/api/v1/admin/reviews?page=1&page_size=10&status=pending&search=sunrise`
- **Query Params**:
  - `status` (`pending` | `published` | `hidden` | `flagged` | `rejected`)
  - `property_id` (Public ID of property)
  - `search` (Search query matching comment, reviewer name, email, property name)
  - `page`, `page_size`, `sort_order` (`asc` | `desc`)
- **Auth**: Admin token

#### 2. Approve Review
- **Method**: `POST`
- **Path**: `/api/v1/admin/reviews/{review_id}/approve`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`
- **Response** (`200 OK`):
```json
{
  "success": true,
  "message": "Review approved successfully.",
  "data": {
    "id": "7a94f1c2-3e28-444a-89cf-1234567890ab",
    "status": "published",
    "rating": 5,
    "comment": "Had an incredible stay!"
  }
}
```

#### 3. Reject Review
- **Method**: `POST`
- **Path**: `/api/v1/admin/reviews/{review_id}/reject`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`

#### 4. Update Review Status (Flexible)
- **Method**: `PATCH`
- **Path**: `/api/v1/admin/reviews/{review_id}/status`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`
- **Request Body**:
```json
{
  "status": "flagged"
}
```

#### 5. Delete Review
- **Method**: `DELETE`
- **Path**: `/api/v1/admin/reviews/{review_id}`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`

---

### 2.4. Public Review Endpoints

#### 1. Get Reviews for a Property
- **Method**: `GET`
- **Path**: `/api/v1/public/reviews/property/{property_id_or_slug}?page=1&page_size=10`
- **Auth**: Public (No auth required)
- **Response** (`200 OK`):
```json
{
  "success": true,
  "message": "Property reviews retrieved successfully.",
  "data": [
    {
      "id": "7a94f1c2-3e28-444a-89cf-1234567890ab",
      "rating": 5,
      "comment": "Had an incredible stay!",
      "host_reply": "Thank you for visiting!",
      "host_replied_at": "2026-09-04T10:00:00Z",
      "status": "published",
      "created_at": "2026-09-03T19:40:00Z",
      "guest": {
        "id": "4d1f2a3c-...",
        "full_name": "Tenzing Norbu",
        "is_profile_image_url": "https://cdn.tashihome.com/avatars/user1.jpg"
      }
    }
  ],
  "meta": {
    "pagination": {
      "total": 12,
      "page": 1,
      "page_size": 10,
      "pages": 2
    },
    "summary": {
      "average_rating": 4.85,
      "total_reviews": 12,
      "rating_distribution": {
        "1": 0,
        "2": 0,
        "3": 1,
        "4": 2,
        "5": 9
      }
    }
  }
}
```

#### 2. Get Property Rating Summary Only
- **Method**: `GET`
- **Path**: `/api/v1/public/reviews/property/{property_id_or_slug}/summary`
- **Response** (`200 OK`):
```json
{
  "success": true,
  "message": "Property rating summary retrieved successfully.",
  "data": {
    "average_rating": 4.85,
    "total_reviews": 12,
    "rating_distribution": {
      "1": 0,
      "2": 0,
      "3": 1,
      "4": 2,
      "5": 9
    }
  }
}
```

---

## 3. Testimonial APIs

### 3.1. User & Vendor Testimonial Endpoints

#### 1. Submit Testimonial (Guest / User)
- **Method**: `POST`
- **Path**: `/api/v1/user/testimonials`
- **Auth**: User token
- **Headers**: `X-CSRF-Token`, `X-Idempotency-Key`
- **Request Body**:
```json
{
  "name": "Rohan Sharma",
  "designation": "Solo Traveler from Delhi",
  "avatar_url": "https://cdn.tashihome.com/avatars/rohan.jpg",
  "rating": 5,
  "content": "TashiHome made finding authentic homestays in Sikkim so easy and trustworthy!"
}
```
*(Note: If `name` or `avatar_url` is omitted, the API automatically uses your logged-in profile name and avatar.)*

#### 2. Submit Testimonial (Host / Vendor)
- **Method**: `POST`
- **Path**: `/api/v1/vendor/testimonials`
- **Auth**: Vendor token
- **Headers**: `X-CSRF-Token`, `X-Idempotency-Key`
- **Request Body**:
```json
{
  "name": "Sonam Lepcha",
  "designation": "Homestay Host in Pelling",
  "rating": 5,
  "content": "Listing our property on TashiHome helped us connect with respectful guests from all over the world."
}
```

#### 3. Get User / Vendor's Submitted Testimonials
- **Method**: `GET`
- **Path**: `/api/v1/user/testimonials` OR `/api/v1/vendor/testimonials`
- **Auth**: Authenticated token

#### 4. Update Submitted Testimonial
- **Method**: `PUT`
- **Path**: `/api/v1/user/testimonials/{testimonial_id}` OR `/api/v1/vendor/testimonials/{testimonial_id}`
- **Auth**: Authenticated token
- **Headers**: `X-CSRF-Token`
- **Request Body**:
```json
{
  "designation": "Frequent Homestay Traveler",
  "rating": 5,
  "content": "Updated testimonial message."
}
```

#### 5. Delete Submitted Testimonial
- **Method**: `DELETE`
- **Path**: `/api/v1/user/testimonials/{testimonial_id}` OR `/api/v1/vendor/testimonials/{testimonial_id}`
- **Auth**: Authenticated token
- **Headers**: `X-CSRF-Token`

---

### 3.2. Admin Testimonial Moderation Endpoints

#### 1. List All Testimonials
- **Method**: `GET`
- **Path**: `/api/v1/admin/testimonials?page=1&page_size=10&status=pending&user_role=vendor`
- **Query Params**:
  - `status` (`pending` | `approved` | `rejected` | `hidden`)
  - `user_role` (`user` | `vendor`)
  - `is_featured` (`true` | `false`)
  - `search` (matches name, designation, user email)
  - `page`, `page_size`, `sort_order` (`asc` | `desc`)
- **Auth**: Admin token

#### 2. Approve Testimonial
- **Method**: `POST`
- **Path**: `/api/v1/admin/testimonials/{testimonial_id}/approve`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`

#### 3. Reject Testimonial
- **Method**: `POST`
- **Path**: `/api/v1/admin/testimonials/{testimonial_id}/reject`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`

#### 4. Toggle / Set Featured on Homepage
- **Method**: `PATCH`
- **Path**: `/api/v1/admin/testimonials/{testimonial_id}/feature`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`
- **Request Body**:
```json
{
  "is_featured": true
}
```

#### 5. Update Status
- **Method**: `PATCH`
- **Path**: `/api/v1/admin/testimonials/{testimonial_id}/status`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`
- **Request Body**:
```json
{
  "status": "approved"
}
```

#### 6. Delete Testimonial
- **Method**: `DELETE`
- **Path**: `/api/v1/admin/testimonials/{testimonial_id}`
- **Auth**: Admin token
- **Headers**: `X-CSRF-Token`

---

### 3.3. Public Testimonial Endpoints

#### 1. Get Approved Testimonials for Landing Page
- **Method**: `GET`
- **Path**: `/api/v1/public/testimonials?is_featured=true&page=1&page_size=6`
- **Query Params**:
  - `is_featured` (`true` or omit for all approved)
  - `user_role` (`user` | `vendor` or omit for both)
  - `page`, `page_size`, `sort_order`
- **Auth**: None (Public)
- **Response** (`200 OK`):
```json
{
  "success": true,
  "message": "Testimonials retrieved successfully.",
  "data": [
    {
      "id": "3c98f12a-8d19-4f76-88ab-1029384756ab",
      "name": "Sonam Lepcha",
      "designation": "Homestay Host in Pelling",
      "avatar_url": "https://cdn.tashihome.com/avatars/sonam.jpg",
      "rating": 5,
      "content": "Listing our property on TashiHome helped us connect with respectful guests.",
      "status": "approved",
      "user_role": "vendor",
      "is_featured": true,
      "created_at": "2026-08-15T12:00:00Z",
      "updated_at": "2026-08-16T10:00:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "total": 6,
      "page": 1,
      "page_size": 6,
      "pages": 1
    }
  }
}
```

---

## 4. Frontend Code Example (Axios + TypeScript)

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "https://api.tashihome.com/api/v1",
  withCredentials: true, // sends cookies automatically
});

// Helper to get CSRF token from cookie or header
const getCsrfToken = () => {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
};

// 1. Submit a Booking Review
export async function submitBookingReview(bookingId: string, rating: number, comment?: string) {
  const response = await api.post(
    "/user/reviews",
    { booking_id: bookingId, rating, comment },
    {
      headers: {
        "X-CSRF-Token": getCsrfToken(),
        "X-Idempotency-Key": crypto.randomUUID(),
      },
    }
  );
  return response.data;
}

// 2. Submit a Testimonial (User or Host)
export async function submitTestimonial(role: "user" | "vendor", content: string, rating?: number, designation?: string) {
  const endpoint = role === "vendor" ? "/vendor/testimonials" : "/user/testimonials";
  const response = await api.post(
    endpoint,
    { content, rating, designation },
    {
      headers: {
        "X-CSRF-Token": getCsrfToken(),
        "X-Idempotency-Key": crypto.randomUUID(),
      },
    }
  );
  return response.data;
}

// 3. Fetch Featured Testimonials for Homepage
export async function fetchFeaturedTestimonials() {
  const response = await api.get("/public/testimonials", {
    params: { is_featured: true, page_size: 6 },
  });
  return response.data;
}

// 4. Admin Approve Review
export async function adminApproveReview(reviewId: string) {
  const response = await api.post(
    `/admin/reviews/${reviewId}/approve`,
    {},
    {
      headers: {
        "X-CSRF-Token": getCsrfToken(),
      },
    }
  );
  return response.data;
}
```

