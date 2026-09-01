# Frontend Integration Guide: Idempotency Keys

This document provides the frontend engineering team with the complete **Idempotency Key Specification, Lifecycle Rules, Axios / Fetch Interceptors, React Hooks, and Error Handling Patterns** to prevent duplicate bookings, double payment transactions, and accidental multi-submissions across TashiHome web and mobile clients.

---

## Table of Contents
1. [Overview & Core Concepts](#1-overview--core-concepts)
2. [HTTP Headers Specification](#2-http-headers-specification)
3. [Protected Endpoints](#3-protected-endpoints)
4. [Backend Response Codes & Replay Behavior](#4-backend-response-codes--replay-behavior)
5. [Idempotency Key Lifecycle & Rules](#5-idempotency-key-lifecycle--rules)
6. [Frontend Implementation Examples](#6-frontend-implementation-examples)
   - [6.1 Key Generator Utility](#61-key-generator-utility)
   - [6.2 Axios Interceptor / Instance](#62-axios-interceptor--instance)
   - [6.3 Native `fetch` Wrapper](#63-native-fetch-wrapper)
   - [6.4 React Custom Hook (`useIdempotentBooking`)](#64-react-custom-hook-useidempotentbooking)
   - [6.5 Vue 3 Composable (`useIdempotency`)](#65-vue-3-composable-useidempotency)
7. [Error Handling & Retry Strategies](#7-error-handling--retry-strategies)
8. [Frontend QA & Testing Checklist](#8-frontend-qa--testing-checklist)

---

## 1. Overview & Core Concepts

### What Problem Are We Solving?
When a user clicks **"Book Now"** or **"Pay ₹5,000"**, transient network failures, slow mobile connections, or multiple rapid button clicks can result in:
- Duplicate booking reservations created in the database.
- Multiple Razorpay orders initiated for the same stay.
- Double charges if payment verification requests are retried.

### How Idempotency Works
```
+-----------------------------------------------------------------------------------------+
|                                    IDEMPOTENCY FLOW                                     |
+-----------------------------------------------------------------------------------------+

  [ Frontend Client ]                                      [ Backend & Redis ]
          |                                                         |
          | --- 1. POST /bookings (Idempotency-Key: UUID-1) ------> |
          |                                                         |-- Check Redis for UUID-1
          |                                                         |-- Not found: Lock key
          |                                                         |-- Process Booking in DB
          |                                                         |-- Cache response in Redis
          | <--- 2. 201 Created (X-Idempotency-Key: UUID-1) ------- |
          |                                                         |
          | [ Network glitch / User clicks Retry / Re-render ]      |
          |                                                         |
          | --- 3. POST /bookings (Idempotency-Key: UUID-1) ------> |
          |                                                         |-- Found completed response
          | <--- 4. 201 Created (Idempotent-Replay: true) --------- | (No DB write, identical result)
          |                                                         |
```

---

## 2. HTTP Headers Specification

When sending state-changing requests (`POST`, `PUT`, `PATCH`), the client sends an idempotency key in the request header:

| Header Name | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `Idempotency-Key` *(Recommended)* | `string` (UUID v4) | `9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d` | Standard RFC header for idempotent execution. |
| `X-Idempotency-Key` *(Supported)* | `string` (UUID v4) | `9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d` | Alternative custom header name (case-insensitive). |

### Backend Response Headers
| Header Name | Value | Description |
| :--- | :--- | :--- |
| `X-Idempotency-Key` | `<uuid>` | Echoes back the idempotency key processed. |
| `Idempotent-Replay` | `"true"` | **Present only on replayed requests.** Indicates the response was served from cache and no new resource was created. |

---

## 3. Protected Endpoints

### ⚠️ Mandatory Idempotency Keys (Required by Backend)
The backend **enforces** `Idempotency-Key` on the following endpoints. Requests without the header will be rejected with HTTP `400 Bad Request`.

| Endpoint | Method | Action |
| :--- | :--- | :--- |
| `/api/v1/user/bookings/` | `POST` | Create a new booking |
| `/api/v1/user/bookings/{id}/payments` | `POST` | Record / process a booking payment |
| `/api/v1/user/bookings/{id}/razorpay/order` | `POST` | Create Razorpay payment gateway order |
| `/api/v1/user/bookings/{id}/razorpay/verify` | `POST` | Verify Razorpay payment signature |

### 💡 Globally Supported Endpoints (Optional but Recommended)
Every other `POST`, `PUT`, `PATCH`, and `DELETE` endpoint (e.g. creating properties, submitting host onboarding requests, processing admin payouts/refunds) automatically supports `Idempotency-Key` if provided.

---

## 4. Backend Response Codes & Replay Behavior

| Status Code | Error Code | Reason | Frontend Action |
| :--- | :--- | :--- | :--- |
| **`200 OK` / `201 Created`** | `None` | Request processed successfully (or replayed from cache). | Treat as normal success. If `Idempotent-Replay: true` header is present, UI can safely navigate to confirmation screen. |
| **`400 Bad Request`** | `IDEMPOTENCY_KEY_REQUIRED` | Missing `Idempotency-Key` header on an endpoint where it is mandatory. | Attach a valid UUID v4 `Idempotency-Key` header and retry. |
| **`409 Conflict`** | `IDEMPOTENCY_CONFLICT` | A request with this key is currently being executed in the backend (in-flight). | Do **NOT** generate a new key. Wait 1–2 seconds and retry with the **same** key. |
| **`422 Unprocessable Entity`** | `IDEMPOTENCY_PAYLOAD_MISMATCH` | The same idempotency key was previously sent with different parameters/body. | Generate a **brand new** UUID v4 key and submit. |
| **`5xx Server Error`** | Various | Backend crash or gateway error. | Backend automatically unlocks the key. Frontend can safely retry using the **same** key. |

---

## 5. Idempotency Key Lifecycle & Rules

To ensure correct behavior, follow these two golden rules:

### Rule 1: Re-use the SAME key for retries of the SAME user intent
- **User clicked "Submit" → Network timeout / Error 500 / Error 409:** Keep the same key and retry.
- **Component re-renders while payment order is processing:** Keep the same key.

### Rule 2: Generate a NEW key when the user changes form input or starts a new intent
- **User edits check-in/check-out dates or guest count:** Generate a new key.
- **User changes property or selects a different room:** Generate a new key.
- **User cancelled previous checkout and starts fresh:** Generate a new key.

```
       +------------------------------------+
       |  User enters Checkout / Pay Screen |
       +------------------------------------+
                         |
           [ Generate UUID v4: key_1 ]
                         |
      +------------------v-------------------+
+---> | User clicks "Confirm & Pay"          |
|     +--------------------------------------+
|                        |
|       (POST with Idempotency-Key: key_1)
|                        |
|       +----------------+----------------+
|       |                                 |
|   [ Success 200/201 ]           [ Network Error / 409 / 5xx ]
|       |                                 |
|   Redirect to Success Page      Retry with SAME key_1 (Up to 3 times)
|
|
+--- [ User modifies Dates/Rooms/Amount ] ---> [ Generate NEW key_2 ]
```

---

## 6. Frontend Implementation Examples

### 6.1 Key Generator Utility

Create `src/utils/idempotency.ts`:

```typescript
/**
 * Generates a standard UUID v4 idempotency key.
 * Uses native Web Crypto API with fallback for older browsers.
 */
export function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  // Fallback RFC4122 UUID v4
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
```

---

### 6.2 Axios Interceptor / Instance

Create `src/api/httpClient.ts`:

```typescript
import axios, { AxiosRequestConfig, InternalAxiosRequestConfig } from "axios";
import { generateIdempotencyKey } from "../utils/idempotency";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8020",
  withCredentials: true, // For HTTP-only cookie auth & CSRF
});

// Attach CSRF Token from cookie if available
function getCsrfToken(): string | null {
  const match = document.cookie.match(new RegExp("(^| )csrf_token=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

// Request Interceptor
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const method = config.method?.toUpperCase();

  // Attach CSRF token on state-changing requests
  if (method && ["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf) {
      config.headers.set("X-CSRF-Token", csrf);
    }
  }

  // If request config already specifies an Idempotency-Key, ensure it is set
  // Otherwise, if config.autoIdempotency is enabled for POST requests:
  if (config.headers && !config.headers.get("Idempotency-Key")) {
    if ((config as any).useIdempotency) {
      config.headers.set("Idempotency-Key", generateIdempotencyKey());
    }
  }

  return config;
});

// Response Interceptor for handling 409 Concurrency Retries
api.interceptors.response.use(
  (response) => {
    // Check if response was replayed
    if (response.headers["idempotent-replay"] === "true") {
      console.info("[API] Response replayed from idempotent cache");
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Auto-retry on 409 IDEMPOTENCY_CONFLICT (max 2 retries with 1.5s delay)
    if (
      error.response?.status === 409 &&
      error.response?.data?.error_code === "IDEMPOTENCY_CONFLICT" &&
      !originalRequest._retryCount
    ) {
      originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
      if (originalRequest._retryCount <= 2) {
        console.warn("[API] Idempotency conflict. Retrying in 1.5s...");
        await new Promise((resolve) => setTimeout(resolve, 1500));
        return api(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);
```

---

### 6.3 Native `fetch` Wrapper

Create `src/api/fetchClient.ts`:

```typescript
import { generateIdempotencyKey } from "../utils/idempotency";

interface FetchOptions extends RequestInit {
  idempotencyKey?: string;
  autoIdempotency?: boolean;
}

export async function fetchWithIdempotency(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { idempotencyKey, autoIdempotency, headers = {}, ...rest } = options;
  const method = (options.method || "GET").toUpperCase();

  const reqHeaders = new Headers(headers);

  // Set CSRF token
  const csrfMatch = document.cookie.match(new RegExp("(^| )csrf_token=([^;]+)"));
  if (csrfMatch) {
    reqHeaders.set("X-CSRF-Token", decodeURIComponent(csrfMatch[2]));
  }

  // Set Idempotency-Key
  if (["POST", "PUT", "PATCH"].includes(method)) {
    if (idempotencyKey) {
      reqHeaders.set("Idempotency-Key", idempotencyKey);
    } else if (autoIdempotency) {
      reqHeaders.set("Idempotency-Key", generateIdempotencyKey());
    }
  }

  const response = await fetch(url, {
    ...rest,
    method,
    headers: reqHeaders,
    credentials: "include",
  });

  return response;
}
```

---

### 6.4 React Custom Hook (`useIdempotentBooking`)

Create `src/hooks/useIdempotentBooking.ts`:

```tsx
import { useState, useRef, useCallback } from "react";
import { api } from "../api/httpClient";
import { generateIdempotencyKey } from "../utils/idempotency";

export interface BookingPayload {
  property_id: string;
  room_type_id?: string;
  check_in_date: string;
  check_out_date: string;
  guests_count: number;
  total_amount: number;
}

export function useIdempotentBooking() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Store idempotency keys in ref to persist across component re-renders
  const bookingKeyRef = useRef<string>(generateIdempotencyKey());
  const paymentKeyRef = useRef<string>(generateIdempotencyKey());

  // Call this if user modifies checkout form data
  const resetKeys = useCallback(() => {
    bookingKeyRef.current = generateIdempotencyKey();
    paymentKeyRef.current = generateIdempotencyKey();
  }, []);

  const createBooking = async (payload: BookingPayload) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post("/api/v1/user/bookings/", payload, {
        headers: {
          "Idempotency-Key": bookingKeyRef.current,
        },
      });

      return response.data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || "Failed to create booking";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createRazorpayOrder = async (bookingId: string, amount: number) => {
    setLoading(true);
    try {
      const response = await api.post(
        `/api/v1/user/bookings/${bookingId}/razorpay/order`,
        { amount },
        {
          headers: {
            "Idempotency-Key": paymentKeyRef.current,
          },
        }
      );
      return response.data;
    } finally {
      setLoading(false);
    }
  };

  return {
    createBooking,
    createRazorpayOrder,
    resetKeys,
    loading,
    error,
  };
}
```

#### Usage in Checkout Component:

```tsx
import React, { useState } from "react";
import { useIdempotentBooking } from "../hooks/useIdempotentBooking";

export const CheckoutModal = ({ property, dates, guests }: any) => {
  const { createBooking, createRazorpayOrder, resetKeys, loading, error } = useIdempotentBooking();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleBookingSubmit = async () => {
    if (isSubmitting) return; // Prevent local double click
    setIsSubmitting(true);

    try {
      // 1. Create Booking (Protected with Idempotency-Key)
      const bookingRes = await createBooking({
        property_id: property.id,
        check_in_date: dates.checkIn,
        check_out_date: dates.checkOut,
        guests_count: guests,
        total_amount: property.price,
      });

      const booking = bookingRes.data;

      // 2. Create Razorpay Order (Protected with Idempotency-Key)
      const orderRes = await createRazorpayOrder(booking.public_id, property.price);
      const { order_id, key_id, amount, currency } = orderRes.data;

      // 3. Open Razorpay Checkout Modal
      const rzp = new (window as any).Razorpay({
        key: key_id,
        amount: amount * 100,
        currency,
        order_id,
        name: "TashiHome",
        description: `Booking #${booking.booking_reference}`,
        handler: async function (paymentResponse: any) {
          // Verify Payment
          await api.post(
            `/api/v1/user/bookings/${booking.public_id}/razorpay/verify`,
            {
              razorpay_order_id: paymentResponse.razorpay_order_id,
              razorpay_payment_id: paymentResponse.razorpay_payment_id,
              razorpay_signature: paymentResponse.razorpay_signature,
            },
            {
              headers: {
                // Use a key derived from payment_id for verification idempotency
                "Idempotency-Key": `verify-${paymentResponse.razorpay_payment_id}`,
              },
            }
          );
          window.location.href = `/bookings/${booking.public_id}/confirmation`;
        },
      });

      rzp.open();
    } catch (e) {
      console.error("Booking error:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="checkout-card">
      <h3>Complete Reservation</h3>
      {error && <div className="error-banner">{error}</div>}
      <button
        onClick={handleBookingSubmit}
        disabled={loading || isSubmitting}
        className="btn-primary"
      >
        {loading ? "Processing..." : "Confirm & Pay"}
      </button>
    </div>
  );
};
```

---

### 6.5 Vue 3 Composable (`useIdempotency`)

Create `src/composables/useIdempotency.ts`:

```typescript
import { ref } from "vue";
import { generateIdempotencyKey } from "@/utils/idempotency";
import { api } from "@/api/httpClient";

export function useIdempotency() {
  const currentKey = ref(generateIdempotencyKey());

  const refreshKey = () => {
    currentKey.value = generateIdempotencyKey();
  };

  const idempotentPost = async <T = any>(url: string, data: any): Promise<T> => {
    const response = await api.post<T>(url, data, {
      headers: {
        "Idempotency-Key": currentKey.value,
      },
    });
    return response.data;
  };

  return {
    currentKey,
    refreshKey,
    idempotentPost,
  };
}
```

---

## 7. Error Handling & Retry Strategies

### Handling `409 IDEMPOTENCY_CONFLICT`
```typescript
try {
  await api.post("/api/v1/user/bookings/", payload, { headers: { "Idempotency-Key": key } });
} catch (err: any) {
  if (err.response?.data?.error_code === "IDEMPOTENCY_CONFLICT") {
    // Show polite toast: "Your booking is currently being confirmed..."
    // Wait and poll booking status or re-request with SAME key
  }
}
```

### Handling `422 IDEMPOTENCY_PAYLOAD_MISMATCH`
```typescript
try {
  await api.post("/api/v1/user/bookings/", payload, { headers: { "Idempotency-Key": key } });
} catch (err: any) {
  if (err.response?.data?.error_code === "IDEMPOTENCY_PAYLOAD_MISMATCH") {
    // Key was corrupted or reused for different params. Regenerate fresh key!
    const newKey = generateIdempotencyKey();
    await api.post("/api/v1/user/bookings/", payload, { headers: { "Idempotency-Key": newKey } });
  }
}
```

---

## 8. Frontend QA & Testing Checklist

- [ ] **Double Click Protection**: Rapidly double-clicking "Confirm & Pay" sends identical `Idempotency-Key`; only 1 booking and 1 Razorpay order are created.
- [ ] **Page Refresh / Offline Replay**: Submitting a booking, dropping network connection, and resubmitting returns `201 Created` with `Idempotent-Replay: true` header without throwing validation/duplicate errors.
- [ ] **Form Modification**: Changing the booking date or room type generates a fresh `Idempotency-Key`.
- [ ] **Headers Inspected**: Inspecting network tab in browser DevTools displays `Idempotency-Key: <uuid-v4>` in request headers and `X-Idempotency-Key` in response headers.
- [ ] **Payment Verification**: `POST /bookings/{id}/razorpay/verify` uses idempotent execution so re-triggering webhook or verification does not duplicate transaction logs.

