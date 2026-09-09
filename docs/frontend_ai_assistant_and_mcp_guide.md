# Frontend Integration Guide: AI Assistant & Model Context Protocol (MCP)

This document provides complete instructions, endpoint specifications, TypeScript models, security details, and ready-to-use Angular components for integrating the **TashiHome AI Concierge & MCP API** into the frontend application.

---

## 1. API Endpoints Overview

All assistant and MCP endpoints are served under `/api/v1/public/assistant` and `/api/v1/public/mcp`:

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/public/assistant/chat` | Main conversational assistant endpoint with multi-tool calling | Optional (Guest or Logged In) |
| `POST` | `/api/v1/public/assistant/chat/stream` | **Streaming** chat endpoint — same as `/chat` but returns Server-Sent Events (SSE) for progressive, token-by-token reply rendering | Optional (Guest or Logged In) |
| `POST` | `/api/v1/public/assistant/search` | Direct homestay search via assistant engine | No |
| `POST` | `/api/v1/public/assistant/semantic-search` | Natural language / vibe-based vector semantic search | No |
| `POST` | `/api/v1/public/assistant/checkout` | Direct AI checkout with auto-registration for unregistered guests | Optional (Auto-registers if guest) |
| `GET` | `/api/v1/public/assistant/suggestions` | Fetch suggested inquiry prompts & action chips | No |
| `POST` | `/api/v1/public/assistant/sync-embeddings` | Index/sync homestay embeddings into the vector store | Admin / Internal |
| `POST` | `/api/v1/public/mcp/rpc` | Direct JSON-RPC 2.0 endpoint for MCP client integrations | Optional |
| `GET` | `/api/v1/public/mcp/sse` | Server-Sent Events stream for persistent MCP connections | Optional |
| `GET` | `/api/v1/public/mcp/tools` | List all supported MCP tool schemas | No |

---

## 2. Security & Identifier Standards

> [!IMPORTANT]
> **Zero Database Integer ID Exposure**: All entity identifiers exposed by the AI Concierge and MCP tools are secure **UUID strings** (`public_id`) named simply `"id"`. The frontend should treat all entity IDs (`homestay id`, `booking id`, `guest id`, `room type id`) as opaque UUID strings.

---

## 3. Request & Response Specifications

### A. Conversational Chat (`POST /api/v1/public/assistant/chat`)

Processes conversational inquiries, detects intent, and executes relevant MCP tools (e.g. searching stays, checking real-time availability, booking, retrieving policies).

#### Request Body
```json
{
  "message": "Find homestays in Thimphu for 2 guests from 2026-10-10 to 2026-10-15",
  "session_id": "c62b5d4a-39b1-4f93-b6d8-11f26792348a",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hi, I am planning a vacation to Bhutan."
    },
    {
      "role": "assistant",
      "content": "Kuzu Zangpo La! I would love to help you find authentic homestays in Bhutan."
    }
  ],
  "guest_name": "Karma Dorji",
  "guest_email": "karma@example.com",
  "guest_phone": "+97517123456"
}
```

#### Response Body
```json
{
  "status": "success",
  "message": "Assistant response generated successfully.",
  "data": {
    "reply": "Kuzu Zangpo La! I found 3 beautiful homestays in Thimphu for your dates:\n\n1. **Bhutan Heritage Homestay** (Thimphu) - BTN 3,500/night ⭐ 4.9 (12 reviews)\n2. **Valley Pine Retreat** (Thimphu) - BTN 2,800/night ⭐ 4.7 (8 reviews)\n\nWould you like me to check live availability or proceed with a reservation?",
    "session_id": "c62b5d4a-39b1-4f93-b6d8-11f26792348a",
    "intent": "search_homestays",
    "action_taken": "Executed search_homestays",
    "tool_calls": [
      {
        "tool": "search_homestays",
        "arguments": {
          "query": "Thimphu",
          "check_in_date": "2026-10-10",
          "check_out_date": "2026-10-15",
          "guests": 2
        },
        "result": {
          "total": 2,
          "properties": []
        },
        "is_error": false
      }
    ],
    "search_results": [
      {
        "id": "f5a892b1-6b43-4f24-9b22-4a00bc714f3b",
        "name": "Bhutan Heritage Homestay",
        "slug": "bhutan-heritage-homestay",
        "city": "Thimphu",
        "location": "Motithang",
        "base_price": 3500.0,
        "currency": "BTN",
        "max_guests": 4,
        "bedrooms": 2,
        "bathrooms": 1,
        "rating": 4.9,
        "review_count": 12,
        "cover_image": "https://cdn.tashihomes.in/properties/cover1.webp",
        "property_type": "HOME_STAY"
      }
    ],
    "suggested_actions": [
      "Check availability for Bhutan Heritage Homestay",
      "Filter by price under BTN 3000",
      "Explore homestays in Paro"
    ]
  }
}
```

---

### A.2. Streaming Conversational Chat (`POST /api/v1/public/assistant/chat/stream`)

Identical request body to `/chat`, but responds with a **`text/event-stream`** (SSE) stream instead of a single JSON payload. Use this endpoint to render the AI reply progressively — token-by-token — for a real-time typing experience.

> [!IMPORTANT]
> **Do NOT set `response_model` or parse this as JSON directly.** Read it as an SSE stream using `EventSource`, `fetch` with a `ReadableStream`, or the Angular SSE helper shown in Section 5.

#### Request Body
Same as `/chat` — see above.

#### Response Headers
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

#### SSE Event Format

Each line is:
```
data: <JSON object>\n\n
```

| `type` | Description | Key fields |
| :--- | :--- | :--- |
| `start` | Stream opened; emitted immediately before AI processing | `session_id` |
| `token` | A chunk of the reply text (4 words per event by default) | `text` |
| `metadata` | Full structured payload once reply is complete | `intent`, `search_results`, `pagination`, `availability`, `booking`, `tool_calls`, `suggested_actions` |
| `done` | Stream ended successfully | — |
| `error` | An error occurred mid-stream | `message` |

#### Full Event Sequence Example

```
data: {"type":"start","session_id":"c62b5d4a-39b1-4f93-b6d8-11f26792348a"}

data: {"type":"token","text":"Hello! 🙏 I found "}
data: {"type":"token","text":"**3 homestays** in Thimphu "}
data: {"type":"token","text":"for your dates:\n\n1. "}
data: {"type":"token","text":"**Bhutan Heritage Homestay** "}
data: {"type":"token","text":"(Motithang) — ₹3,500/night\n"}

data: {"type":"metadata","intent":"search_homestays","action_taken":"Executed search_homestays","search_results":[{"id":"f5a892b1...","name":"Bhutan Heritage Homestay","city":"Thimphu","base_price":3500.0}],"pagination":{"page":1,"page_size":5,"total":3,"total_pages":1,"has_next":false,"has_prev":false},"suggested_actions":["Check availability","Show next page","Filter by price"]}

data: {"type":"done"}
```

#### Error Event Example

```
data: {"type":"error","message":"Chat message cannot be empty."}
```

#### Quick Test with `curl`

```bash
curl -N -X POST http://localhost:8020/api/v1/public/assistant/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Show homestays in Darjeeling","session_id":"test-001"}'
```

> [!NOTE]
> If the connection is interrupted (network loss, server restart), reconnect by re-sending the same request with the same `session_id`. The session context is preserved in-memory by the server during the session lifetime.

---

### B. Vector Semantic Search (`POST /api/v1/public/assistant/semantic-search`)


Enables natural language, atmosphere, and vibe-based search queries (e.g. *"peaceful wooden cottage with traditional bukhari fireplace and mountain view"*).

#### Request Body
```json
{
  "query": "cozy wooden cottage with fireplace and mountain view",
  "city_name": "Paro",
  "min_price": 2000,
  "max_price": 6000,
  "limit": 6
}
```

#### Response Body
```json
{
  "status": "success",
  "message": "Found 2 matching homestay(s).",
  "data": {
    "query": "cozy wooden cottage with fireplace and mountain view",
    "total_matches": 2,
    "results": [
      {
        "id": "345714b6-b877-49df-8832-03755ad485ce",
        "name": "Paro Pine Wood Sanctuary",
        "slug": "paro-pine-wood",
        "city_name": "Paro",
        "price_per_night": 3500.0,
        "type": "cottage",
        "similarity_score": 0.892,
        "match_percentage": 94.6,
        "description": "A traditional wooden cottage in Paro valley with heated bukhari fireplace and majestic Himalayan mountain views.",
        "amenities": ["Bukhari Fireplace", "Mountain View", "Wooden Bath"]
      }
    ]
  }
}
```

```

---

### C. Vector Embeddings Synchronization & S3 Vector Storage (`tashihome-vector`)

Embeddings are precomputed and cached in-memory and persistently stored in Amazon S3 / MinIO (`VECTOR_S3_BUCKET=tashihome-vector` by default).

#### 1. Sync & Persist Embeddings to S3 (`POST /api/v1/public/assistant/sync-embeddings`)
```json
{
  "status": "success",
  "message": "Successfully indexed 12 active homestay(s) into vector search engine.",
  "data": {
    "indexed_count": 12,
    "total_indexed": 12,
    "last_synced_at": "2026-09-09T02:18:00.000000",
    "s3_persisted": true,
    "s3_bucket": "tashihome-vector",
    "s3_key": "vectors/homestays_vector_index.json"
  }
}
```

#### 2. Manual Save to S3 (`POST /api/v1/public/assistant/vector-save-s3`)
```json
{
  "status": "success",
  "message": "Vector embeddings saved to S3 bucket 'tashihome-vector'.",
  "data": {
    "success": true,
    "persisted": true,
    "bucket": "tashihome-vector",
    "key": "vectors/homestays_vector_index.json",
    "total_saved": 12,
    "last_synced_at": "2026-09-09T02:18:00.000000"
  }
}
```

#### 3. Manual Load from S3 (`POST /api/v1/public/assistant/vector-load-s3`)
```json
{
  "status": "success",
  "message": "Loaded 12 vector embedding(s) from S3 bucket 'tashihome-vector'.",
  "data": {
    "success": true,
    "loaded_count": 12,
    "total_indexed": 12,
    "bucket": "tashihome-vector",
    "key": "vectors/homestays_vector_index.json",
    "last_synced_at": "2026-09-09T02:18:00.000000"
  }
}
```

---

### D. Live Availability & Pricing Quote (With Room-Wise Pricing)

When a user asks for availability or pricing for a stay, the assistant calculates the room-wise price for the chosen or available room types:

#### Response Data Structure (`AvailabilityQuoteData`)
```json
{
  "property_name": "Bhutan Heritage Homestay",
  "property_slug": "bhutan-heritage-homestay",
  "selected_room_type": "Deluxe Mountain Room",
  "room_types": [
    {
      "id": "7b134a62-97bb-41a4-9bdf-8798151240ea",
      "property_room_type_id": "f5193c71-2b0e-473d-9d41-3b7c89fca671",
      "name": "Deluxe Mountain Room",
      "price_per_night": 4500.0,
      "total_units": 2,
      "capacity": 3,
      "is_selected": true
    },
    {
      "id": "e4299b41-5a91-4cf1-88f6-22485fa198cb",
      "property_room_type_id": "018fbc89-9941-479a-bc3e-a1789c671b40",
      "name": "Standard Cozy Room",
      "price_per_night": 3000.0,
      "total_units": 4,
      "capacity": 2,
      "is_selected": false
    }
  ],
  "is_available": true,
  "available_units": 2,
  "requested_rooms": 1,
  "check_in_date": "2026-10-10",
  "check_out_date": "2026-10-15",
  "nights": 5,
  "num_nights": 5,
  "price_per_night": 4500.0,
  "base_amount": 22500.0,
  "subtotal": 22500.0,
  "discount_amount": 0.0,
  "tax_amount": 1125.0,
  "total_amount": 23625.0,
  "currency": "BTN"
}
```

> [!NOTE]
> **Prompting for Missing Dates & Room Types**: If the user asks to checkout or check availability without providing check-in/out dates or room type, the assistant will resolve the property, present the available room types with their specific room-wise nightly prices, and request the dates and preferred room type.

---

### D. Direct Checkout & Auto-Registration (`POST /api/v1/public/assistant/checkout`)

If an unauthenticated guest requests a booking, supplying their details (`guest_name`, `guest_email`, `guest_phone`) along with property and room type will automatically register their guest account and finalize their reservation with the room-wise price.

#### Request Body
```json
{
  "property_id": "bhutan-heritage-homestay",
  "room_type_id": "7b134a62-97bb-41a4-9bdf-8798151240ea",
  "check_in_date": "2026-10-10",
  "check_out_date": "2026-10-15",
  "num_guests": 2,
  "num_rooms": 1,
  "special_requests": "Vegetarian meals, late check-in",
  "guest_name": "Sonam Wangchuk",
  "guest_email": "sonam.wangchuk@example.com",
  "guest_phone": "+97517998877",
  "guest_password": "OptionalSecurePassword123!"
}
```

#### Response Body
```json
{
  "status": "success",
  "message": "Checkout completed and booking confirmed.",
  "data": {
    "reply": "🎉 **Reservation Successfully Created!**\n\n• **Booking Reference**: `BK-20261010-9842`\n• **Homestay**: Bhutan Heritage Homestay (Deluxe Mountain Room)\n• **Stay Dates**: 2026-10-10 to 2026-10-15\n• **Rate**: BTN 4500.0/night\n• **Total Amount**: BTN 23625.0\n\n💳 **Payment Gateway & Checkout**:\n• **Gateway Order ID**: `order_01928374abcd`\n• **Amount Due**: BTN 23625.0\n• **Payment Link**: [Complete Payment Online](http://localhost:4200/bookings/BK-20261010-9842/pay)",
    "intent": "checkout_and_book",
    "action_taken": "Created booking, registered guest user, and initiated payment gateway session",
    "booking": {
      "booking_reference": "BK-20261010-9842",
      "id": "c138b14a-89a0-4cfd-872f-53744655ad1e",
      "status": "PENDING",
      "payment_status": "PENDING",
      "property_name": "Bhutan Heritage Homestay",
      "room_type_name": "Deluxe Mountain Room",
      "price_per_night": 4500.0,
      "check_in_date": "2026-10-10",
      "check_out_date": "2026-10-15",
      "num_guests": 2,
      "num_rooms": 1,
      "total_amount": 23625.0,
      "currency": "BTN",
      "guest": {
        "id": "03b25a40-1bad-47a2-82a7-6de98cdf7a83",
        "full_name": "Sonam Wangchuk",
        "email": "sonam.wangchuk@example.com"
      },
      "payment_gateway": {
        "gateway": "razorpay",
        "order_id": "order_01928374abcd",
        "key_id": "rzp_test_xxxx",
        "amount": 23625.0,
        "currency": "BTN",
        "payment_url": "http://localhost:4200/bookings/BK-20261010-9842/pay",
        "status": "initiated"
      }
    },
    "suggested_actions": [
      "Complete payment online",
      "Track booking BK-20261010-9842",
      "View cancellation policy",
      "Popular places in Thimphu"
    ]
  }
}
```

---

### E. Initiate Booking Payment Gateway Session

If a guest needs to complete payment for an existing reservation, ask the AI Concierge (e.g., *"Pay for booking BK-20261010-9842"*) or invoke the `initiate_booking_payment` MCP tool:

#### Response Data Structure
```json
{
  "booking_reference": "BK-20261010-9842",
  "id": "c138b14a-89a0-4cfd-872f-53744655ad1e",
  "property_name": "Bhutan Heritage Homestay",
  "status": "PENDING",
  "payment_status": "PENDING",
  "total_amount": 18375.0,
  "remaining_balance": 18375.0,
  "payment_gateway": {
    "gateway": "razorpay",
    "order_id": "order_01928374abcd",
    "key_id": "rzp_test_xxxx",
    "amount": 18375.0,
    "currency": "BTN",
    "payment_url": "http://localhost:4200/bookings/BK-20261010-9842/pay",
    "status": "initiated"
  }
}
```

#### Frontend Payment Integration (Razorpay Checkout)
When `payment_gateway` is returned:
1. If using Razorpay JS SDK in Angular:
   ```typescript
   const options = {
     key: data.booking.payment_gateway.key_id,
     amount: data.booking.payment_gateway.amount * 100, // in paise/cents
     currency: data.booking.payment_gateway.currency,
     name: "TashiHome",
     description: `Payment for ${data.booking.property_name} (${data.booking.booking_reference})`,
     order_id: data.booking.payment_gateway.order_id,
     handler: (response: any) => {
       // Verify payment signature via backend
       this.verifyPayment(response);
     },
     prefill: {
       name: data.booking.guest.full_name,
       email: data.booking.guest.email
     },
     theme: { color: "#2563eb" }
   };
   const rzp = new (window as any).Razorpay(options);
   rzp.open();
   ```
2. Alternatively, navigate the user to `payment_gateway.payment_url`.

> **Note on `PAYMENT_ENABLED` Configuration**:
> When `PAYMENT_ENABLED=false` in the backend configuration:
> - Online gateway order creation is disabled (`payment_gateway: null`).
> - The booking is created with Payment on Arrival.
> - The assistant automatically informs the user to settle payment upon arrival and suppresses online payment action chips.

---

## 4. TypeScript Models (`src/app/core/models/assistant.model.ts`)

```typescript
export interface AssistantMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface AssistantChatRequest {
  message: string;
  conversation_history?: AssistantMessage[];
  session_id?: string;
  guest_name?: string;
  guest_email?: string;
  guest_phone?: string;
  guest_password?: string;
}

export interface HomestayCardData {
  id: string; // Public UUID
  name: string;
  slug: string;
  city?: string;
  location?: string;
  address?: string;
  base_price: number;
  currency: string;
  currency_symbol: string; // Setting-driven symbol e.g. "Nu.", "₹", "$"
  max_guests: number;
  bedrooms: number;
  bathrooms: number;
  rating: number; // Real database average rating (0.0 if no reviews yet)
  review_count: number; // Real database published review count
  cover_image?: string;
  property_type: string;
}

export interface SemanticSearchResult {
  id: string; // Public UUID
  name: string;
  slug: string;
  city_name?: string;
  price_per_night: number;
  currency?: string;
  currency_symbol?: string;
  type?: string;
  similarity_score?: number;
  match_percentage?: number;
  description?: string;
  amenities?: string[];
  cover_image?: string;
}

export interface PropertyRoomTypePriceTier {
  id?: string;
  occupancy: number; // e.g. 1, 2, 3, 4 guests
  price_per_night: number; // e.g. 1500.0, 1550.0, 1600.0
  base_price?: number;
  sale_per_night?: number;
}

export interface PropertyRoomTypeOption {
  id: string; // Public UUID
  property_room_type_id: string;
  name: string;
  price_per_night: number;
  total_units: number;
  max_rooms?: number; // Upper bound for room selector
  capacity: number; // Max capacity per room
  max_guests?: number; // Upper bound for guest count
  pricing_tiers?: PropertyRoomTypePriceTier[]; // Capacity-wise rates (e.g. 2 Guests: ₹1,500, 3 Guests: ₹1,550, 4 Guests: ₹1,600)
  is_selected?: boolean;
}

export interface ReviewItem {
  id: string; // Public UUID
  rating: number;
  comment?: string;
  guest_name?: string;
  guest_avatar?: string;
  created_at?: string; // Formatted per setting date format
}

export interface HomestayDetailData {
  id: string; // Public UUID
  name: string;
  slug: string;
  description?: string;
  city?: string;
  location?: string;
  address?: string;
  base_price: number;
  currency: string;
  currency_symbol: string;
  max_guests: number; // Upper bound for guest selection across room types
  max_rooms: number; // Upper bound for total room selection
  total_units: number;
  bedrooms: number;
  bathrooms: number;
  rating: number; // Calculated from database published reviews (0.0 if 0 reviews)
  review_count: number;
  rating_distribution: Record<string, number>; // e.g. {"1": 0, "2": 0, "3": 1, "4": 4, "5": 8}
  recent_reviews: ReviewItem[];
  check_in_time: string;
  check_out_time: string;
  room_types: PropertyRoomTypeOption[];
  amenities: string[];
  facilities: string[];
  cancellation_policy?: {
    name: string;
    description?: string;
    refund_percentage?: number;
    days_before_checkin?: number;
  };
}

export interface AvailabilityQuoteData {
  property_name: string;
  property_slug?: string;
  selected_room_type?: string;
  room_types?: PropertyRoomTypeOption[];
  applied_tier?: {
    occupancy: number;
    price_per_night: number;
    sale_per_night?: number;
  };
  is_available?: boolean;
  available_units?: number;
  max_rooms?: number; // Upper bound for room selector
  max_guests?: number; // Upper bound for guest selector
  capacity?: number; // Per-room max capacity
  max_capacity_per_room?: number;
  total_units?: number;
  requires_dates?: boolean; // True when prompting user to select dates, rooms, and room type
  requested_rooms?: number;
  check_in_date?: string; // ISO format (YYYY-MM-DD)
  check_out_date?: string; // ISO format (YYYY-MM-DD)
  formatted_check_in_date?: string; // Setting-driven display format e.g. "10 Oct 2026" or "10/10/2026"
  formatted_check_out_date?: string;
  nights?: number;
  num_nights?: number;
  price_per_night?: number;
  base_amount?: number;
  subtotal?: number;
  discount_amount?: number;
  tax_amount?: number;
  total_amount?: number;
  currency?: string;
  currency_symbol?: string; // Setting-driven symbol e.g. "Nu.", "₹", "$"
}

export interface PaymentGatewayInfo {
  gateway: string; // "razorpay"
  order_id: string; // Razorpay Order ID (e.g. "order_xxxx")
  key_id?: string; // Razorpay Key ID for frontend Checkout SDK
  amount: number;
  currency: string;
  currency_symbol: string;
  payment_url: string; // e.g. "http://localhost:4200/bookings/BK-XXXX/pay"
  status: "initiated" | "pending" | "success" | "failed";
}

export interface BookingConfirmationData {
  booking_reference: string;
  id: string; // Public UUID
  status: string;
  payment_status: string;
  property_name: string;
  room_type_name?: string;
  applied_tier?: {
    occupancy: number;
    price_per_night: number;
    sale_per_night?: number;
  };
  price_per_night?: number;
  check_in_date: string; // ISO format (YYYY-MM-DD)
  check_out_date: string; // ISO format (YYYY-MM-DD)
  formatted_check_in_date?: string; // Setting-driven display format
  formatted_check_out_date?: string;
  num_guests: number;
  num_rooms: number;
  total_amount: number;
  currency: string;
  currency_symbol: string; // Setting-driven symbol e.g. "Nu.", "₹", "$"
  guest: {
    id: string; // Public UUID
    full_name: string;
    email: string;
  };
  payment_gateway?: PaymentGatewayInfo;
}

export interface AssistantChatData {
  reply: string;
  session_id?: string;
  intent?: string;
  action_taken?: string;
  tool_calls?: Array<{
    tool: string;
    arguments: Record<string, any>;
    result?: any;
    is_error?: boolean;
  }>;
  search_results?: HomestayCardData[];
  pagination?: PaginationMeta;
  availability?: AvailabilityQuoteData;
  booking?: BookingConfirmationData;
  payment?: {
    booking_reference: string;
    id: string;
    property_name?: string;
    status: string;
    payment_status: string;
    total_amount: number;
    remaining_balance: number;
    currency: string;
    currency_symbol: string;
    payment_gateway: PaymentGatewayInfo;
  };
  user?: any;
  suggested_actions?: string[];
}

/**
 * Pagination metadata returned in search results.
 * Present in both the regular `/chat` response (data.pagination) and the `/chat/stream` metadata event.
 */
export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * A single Server-Sent Event emitted by `POST /api/v1/public/assistant/chat/stream`.
 *
 * Listen to events in order: start → token(s) → metadata → done
 */
export interface AssistantStreamEvent {
  /** Event type discriminator */
  type: 'start' | 'token' | 'metadata' | 'done' | 'error';
  /** Session ID — present only on `start` events */
  session_id?: string;
  /** Reply text chunk — present only on `token` events */
  text?: string;
  /** Detected intent — present only on `metadata` events */
  intent?: string;
  /** Action summary — present only on `metadata` events */
  action_taken?: string;
  /** MCP tool call list — present only on `metadata` events */
  tool_calls?: Array<{ tool: string; arguments: any; result?: any; is_error?: boolean }>;
  /** Homestay list from search — present only on `metadata` events */
  search_results?: HomestayCardData[];
  /** Pagination details — present only on `metadata` events */
  pagination?: PaginationMeta;
  /** Availability quote — present only on `metadata` events */
  availability?: AvailabilityQuoteData;
  /** Booking confirmation — present only on `metadata` events */
  booking?: BookingConfirmationData;
  /** Registered guest/user info — present only on `metadata` events */
  user?: any;
  /** Next-action chip labels — present only on `metadata` events */
  suggested_actions?: string[];
  /** Error message — present only on `error` events */
  message?: string;
}

export interface AssistantApiResponse<T> {
  status: string | boolean;
  message: string;
  data: T;
}

export interface SuggestionItem {
  title: string;
  prompt: string;
  category: string;
}
```

---

## 5. Angular Service (`src/app/core/services/ai-assistant.service.ts`)

```typescript
import { Injectable, signal } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable, tap } from "rxjs";
import {
  AssistantChatRequest,
  AssistantApiResponse,
  AssistantChatData,
  AssistantMessage,
  AssistantStreamEvent,
  SuggestionItem,
  SemanticSearchResult
} from "../models/assistant.model";

@Injectable({
  providedIn: "root"
})
export class AiAssistantService {
  private readonly baseUrl = "http://localhost:8020/api/v1/public/assistant";

  // Reactive state using Angular Signals
  public messages = signal<Array<{
    sender: "user" | "assistant";
    text: string;
    timestamp: Date;
    data?: AssistantChatData;
    isStreaming?: boolean;
  }>>([]);

  public isLoading = signal<boolean>(false);
  public sessionId = signal<string>(crypto.randomUUID());

  constructor(private http: HttpClient) {}

  sendMessage(
    text: string,
    guestInfo?: { name?: string; email?: string; phone?: string; password?: string }
  ): Observable<AssistantApiResponse<AssistantChatData>> {
    this.isLoading.set(true);

    this.messages.update(prev => [
      ...prev,
      { sender: "user", text, timestamp: new Date() }
    ]);

    const history: AssistantMessage[] = this.messages().map(m => ({
      role: m.sender === "user" ? "user" : "assistant",
      content: m.text
    }));

    const payload: AssistantChatRequest = {
      message: text,
      conversation_history: history,
      session_id: this.sessionId(),
      guest_name: guestInfo?.name,
      guest_email: guestInfo?.email,
      guest_phone: guestInfo?.phone,
      guest_password: guestInfo?.password
    };

    return this.http.post<AssistantApiResponse<AssistantChatData>>(
      `${this.baseUrl}/chat`,
      payload,
      { withCredentials: true }
    ).pipe(
      tap({
        next: (res) => {
          this.isLoading.set(false);

          if (res.data) {
            this.messages.update(prev => [
              ...prev,
              {
                sender: "assistant",
                text: res.data.reply,
                timestamp: new Date(),
                data: res.data
              }
            ]);
          }
        },
        error: () => {
          this.isLoading.set(false);
          this.messages.update(prev => [
            ...prev,
            {
              sender: "assistant",
              text: "I encountered a temporary network issue. Please try again.",
              timestamp: new Date()
            }
          ]);
        }
      })
    );
  }

  /**
   * Stream the assistant reply via Server-Sent Events.
   *
   * Tokens arrive progressively and update the last message in-place.
   * Structured metadata (search_results, booking, etc.) is applied once the
   * `metadata` event is received.
   *
   * @example
   * await this.assistantService.sendMessageStream("Show homestays in Thimphu");
   */
  async sendMessageStream(
    text: string,
    guestInfo?: { name?: string; email?: string; phone?: string; password?: string }
  ): Promise<void> {
    this.isLoading.set(true);

    // Add user message to history
    this.messages.update(prev => [
      ...prev,
      { sender: "user", text, timestamp: new Date() }
    ]);

    const history: AssistantMessage[] = this.messages().map(m => ({
      role: m.sender === "user" ? "user" : "assistant",
      content: m.text
    }));

    const payload: AssistantChatRequest = {
      message: text,
      conversation_history: history,
      session_id: this.sessionId(),
      guest_name: guestInfo?.name,
      guest_email: guestInfo?.email,
      guest_phone: guestInfo?.phone,
      guest_password: guestInfo?.password
    };

    // Reserve a streaming placeholder in the message list
    this.messages.update(prev => [
      ...prev,
      { sender: "assistant", text: "", timestamp: new Date(), isStreaming: true }
    ]);

    try {
      const response = await fetch(`${this.baseUrl}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload)
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let streamedData: Partial<AssistantChatData> = {};

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? ""; // keep incomplete line for next chunk

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          let event: AssistantStreamEvent;
          try {
            event = JSON.parse(raw);
          } catch {
            continue;
          }

          if (event.type === "token" && event.text) {
            // Append token text to the last (streaming) message
            this.messages.update(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.isStreaming) {
                msgs[msgs.length - 1] = { ...last, text: last.text + event.text };
              }
              return msgs;
            });
          } else if (event.type === "metadata") {
            // Collect all structured fields for final update
            streamedData = {
              intent: event.intent,
              action_taken: event.action_taken,
              tool_calls: event.tool_calls as any,
              search_results: event.search_results,
              pagination: event.pagination,
              availability: event.availability,
              booking: event.booking,
              user: event.user,
              suggested_actions: event.suggested_actions
            };
          } else if (event.type === "start" && event.session_id) {
            this.sessionId.set(event.session_id);
          } else if (event.type === "done") {
            // Finalise the streaming message with full structured data
            this.messages.update(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.isStreaming) {
                msgs[msgs.length - 1] = {
                  ...last,
                  isStreaming: false,
                  data: { reply: last.text, ...streamedData } as AssistantChatData
                };
              }
              return msgs;
            });
          } else if (event.type === "error") {
            this.messages.update(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.isStreaming) {
                msgs[msgs.length - 1] = {
                  ...last,
                  isStreaming: false,
                  text: event.message ?? "An error occurred. Please try again."
                };
              }
              return msgs;
            });
          }
        }
      }
    } catch (err) {
      this.messages.update(prev => {
        const msgs = [...prev];
        const last = msgs[msgs.length - 1];
        if (last?.isStreaming) {
          msgs[msgs.length - 1] = {
            ...last,
            isStreaming: false,
            text: "I encountered a network issue. Please try again."
          };
        }
        return msgs;
      });
    } finally {
      this.isLoading.set(false);
    }
  }

  semanticSearch(
    query: string,
    cityName?: string,
    minPrice?: number,
    maxPrice?: number,
    limit = 8
  ): Observable<AssistantApiResponse<{ query: string; total_matches: number; results: SemanticSearchResult[] }>> {
    return this.http.post<AssistantApiResponse<{ query: string; total_matches: number; results: SemanticSearchResult[] }>>(
      `${this.baseUrl}/semantic-search`,
      { query, city_name: cityName, min_price: minPrice, max_price: maxPrice, limit },
      { withCredentials: true }
    );
  }

  getSuggestions(): Observable<AssistantApiResponse<{ suggestions: SuggestionItem[] }>> {
    return this.http.get<AssistantApiResponse<{ suggestions: SuggestionItem[] }>>(
      `${this.baseUrl}/suggestions`
    );
  }

  checkout(checkoutData: any): Observable<AssistantApiResponse<AssistantChatData>> {
    return this.http.post<AssistantApiResponse<AssistantChatData>>(
      `${this.baseUrl}/checkout`,
      checkoutData,
      { withCredentials: true }
    );
  }
}
```

---

## 6. Angular UI Component Template & Cards

### Template (`src/app/components/ai-assistant/ai-assistant.component.html`)

```html
<div class="ai-assistant-widget" [class.open]="isOpen">
  <!-- Trigger Button -->
  <button class="assistant-bubble" (click)="toggleChat()" aria-label="Open AI Assistant">
    <span class="bubble-icon">✨</span>
    <span class="bubble-text">Ask Tashi Concierge</span>
  </button>

  <!-- Chat Drawer / Window -->
  <div class="assistant-window" *ngIf="isOpen">
    <div class="window-header">
      <div class="header-info">
        <span class="avatar">🙏</span>
        <div>
          <h4>Tashi AI Concierge</h4>
          <span class="status-online">Online • Bhutan Travel Guide</span>
        </div>
      </div>
      <button class="close-btn" (click)="toggleChat()">✕</button>
    </div>

    <!-- Messages Container -->
    <div class="messages-container" #scrollContainer>
      <div *ngFor="let msg of assistantService.messages()" class="message-row" [class.user]="msg.sender === 'user'">
        <div class="message-bubble" [class.user-bubble]="msg.sender === 'user'">
          <div class="message-text" [innerHTML]="msg.text"></div>

          <!-- Typing cursor for active SSE stream -->
          <span class="typing-cursor" *ngIf="msg.isStreaming">▋</span>

          <!-- Rich Homestay Search Cards -->
          <div class="rich-cards" *ngIf="msg.data?.search_results?.length">
            <div class="homestay-card" *ngFor="let stay of msg.data?.search_results">
              <img [src]="stay.cover_image || '/assets/images/default-stay.webp'" [alt]="stay.name" class="card-img" />
              <div class="card-body">
                <h5>{{ stay.name }}</h5>
                <p class="location">📍 {{ stay.city }}</p>
                <div class="card-footer">
                  <span class="price">{{ stay.currency }} {{ stay.base_price }}/night</span>
                  <button class="btn-sm" (click)="selectProperty(stay.slug)">Check Dates</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Availability & Price Breakdown Card -->
          <div class="availability-card" *ngIf="msg.data?.availability">
            <h5>Pricing Quote: {{ msg.data?.availability?.property_name }}</h5>
            <div class="quote-details">
              <div>Stay: {{ msg.data?.availability?.check_in_date }} to {{ msg.data?.availability?.check_out_date }}</div>
              <div>Duration: {{ msg.data?.availability?.nights }} night(s)</div>
              <div>Nightly Rate: {{ msg.data?.availability?.currency }} {{ msg.data?.availability?.price_per_night }}</div>
              <div>Taxes & Fees: {{ msg.data?.availability?.currency }} {{ msg.data?.availability?.tax_amount }}</div>
              <div class="total">Total: {{ msg.data?.availability?.currency }} {{ msg.data?.availability?.total_amount }}</div>
            </div>
            <button class="btn-primary" (click)="initiateBooking(msg.data?.availability)">Instant Book</button>
          </div>

          <!-- Booking Confirmation Card -->
          <div class="booking-card" *ngIf="msg.data?.booking">
            <div class="badge-success">Reservation Created</div>
            <h4>Reference: {{ msg.data?.booking?.booking_reference }}</h4>
            <p>{{ msg.data?.booking?.property_name }}</p>
            <p>{{ msg.data?.booking?.check_in_date }} to {{ msg.data?.booking?.check_out_date }}</p>
            <p class="total-paid">Total: {{ msg.data?.booking?.currency }} {{ msg.data?.booking?.total_amount }}</p>
          </div>
        </div>
      </div>

      <!-- Typing dots — only shown when not streaming (waiting for first token) -->
      <div class="typing-indicator" *ngIf="assistantService.isLoading() && !hasStreamingMessage()">
        <span></span><span></span><span></span>
      </div>
    </div>

    <!-- Suggested Action Chips -->
    <div class="suggestions-bar" *ngIf="suggestions.length">
      <button *ngFor="let s of suggestions" class="suggestion-chip" (click)="useSuggestion(s.prompt)">
        {{ s.title }}
      </button>
    </div>

    <!-- Input Bar -->
    <div class="input-container">
      <input
        type="text"
        [(ngModel)]="userInput"
        (keyup.enter)="sendMessage()"
        placeholder="Ask about homestays, dates, prices..."
      />
      <button class="send-btn" (click)="sendMessage()" [disabled]="!userInput.trim()">
        ➔
      </button>
    </div>
  </div>
</div>
```

#### Component Class (key methods)

```typescript
// ai-assistant.component.ts

async sendMessage(): Promise<void> {
  const text = this.userInput.trim();
  if (!text) return;
  this.userInput = "";

  // Use streaming endpoint by default for a typing-effect UX
  await this.assistantService.sendMessageStream(text);
}

/** Returns true when the last assistant message is still streaming. */
hasStreamingMessage(): boolean {
  const msgs = this.assistantService.messages();
  return msgs.length > 0 && !!msgs[msgs.length - 1].isStreaming;
}
```

---

## 7. Natural Language Vibe Search Bar Example

Add a smart semantic search bar anywhere in your web app:

```html
<div class="vibe-search-bar">
  <input
    type="text"
    [(ngModel)]="vibeQuery"
    (keyup.enter)="onVibeSearch()"
    placeholder="✨ Try: 'Cozy wooden cottage with traditional bukhari fireplace & mountain view'"
  />
  <button (click)="onVibeSearch()">Search</button>
</div>

<!-- Results with Match Badges -->
<div class="results-grid" *ngIf="vibeResults.length">
  <div class="stay-card" *ngFor="let item of vibeResults">
    <div class="vibe-badge" *ngIf="item.match_percentage">
      ✨ {{ item.match_percentage }}% Match
    </div>
    <h4>{{ item.name }}</h4>
    <p>{{ item.city_name }} • {{ item.price_per_night }} BTN/night</p>
  </div>
</div>

---

## 8. MCP Resources Protocol (`/api/v1/public/mcp/rpc`)

MCP clients can query registered resources via standard JSON-RPC 2.0:

### List Resources (`resources/list`)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {}
}
```

### Read Featured Cities Resource (`resources/read`)
Fetches live featured destinations directly from the PostgreSQL database:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/read",
  "params": {
    "uri": "tashihome://featured-cities"
  }
}
```

#### Response:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "contents": [
      {
        "uri": "tashihome://featured-cities",
        "mimeType": "application/json",
        "text": "[\n  {\n    \"id\": \"01928374-abcd-7000-8000-000000000001\",\n    \"name\": \"Thimphu\",\n    \"slug\": \"thimphu\",\n    \"tag_line\": \"The Kingdom's Capital\",\n    \"short_description\": \"A bustling blend of tradition and modernity.\",\n    \"image_url\": \"https://cdn.tashihomes.in/cities/thimphu.webp\",\n    \"is_featured\": true,\n    \"country\": \"Bhutan\"\n  }\n]"
      }
    ]
  }
}
```

---

## 9. Dynamic Country, City & Location Resolution

The AI Assistant and MCP system operates with **zero static country or city assumptions**:

1. **Multi-Region & Non-Bhutan Deployments**:
   - The platform dynamically resolves the active country from database platform settings (`country` / `default_country`) or the first active country record in `CountryService`.
   - All destination lists (`tashihome://destinations`, `tashihome://featured-cities`, `get_popular_destinations`) query live database cities via `CityService` and locations via `LocationService`.
   - Zero hardcoded fallback lists of cities (such as `"Thimphu, Paro, Punakha"`) remain; the assistant queries the database dynamically and renders destination chips based on real database records.

2. **Suggested Prompt Chips (`GET /api/v1/public/assistant/suggestions`)**:
   - Suggested prompts adapt in real time to the database's active featured cities, popular homestays, and platform settings.

3. **Dynamic Zero-Match Search Enrichment**:
   - If a guest searches for an unknown or unlisted location, the assistant intelligently lists the top active cities from the database rather than a static list.

