# Frontend Integration & UI Layout Guide: Supply / Vendor Dashboard & Payouts

This document provides the frontend engineering team with the complete **UI/UX Component Layouts, Screen Wireframes, TypeScript Interfaces, API Payloads, and State Management Rules** for integrating the **Supply (Host / Vendor) Dashboard** and its embedded **Payouts & Financial Settlements** tracking.

---

## Table of Contents
1. [Module Architecture & Host Navigation](#1-module-architecture--host-navigation)
2. [Screen Layouts & UI Wireframes](#2-screen-layouts--ui-wireframes)
   - [2.1 Host Overview Dashboard Screen](#21-host-overview-dashboard-screen)
   - [2.2 Financial & Payouts Settlement Widget](#22-financial--payouts-settlement-widget)
   - [2.3 Recent Payouts Table & Details Modal](#23-recent-payouts-table--details-modal)
   - [2.4 Bookings & Occupancy Widgets](#24-bookings--occupancy-widgets)
3. [TypeScript Type Definitions](#3-typescript-type-definitions)
4. [API Endpoints & Integration Specs](#4-api-endpoints--integration-specs)
   - [4.1 Full Vendor Dashboard Data (`GET /api/v1/vendor/dashboard`)](#41-full-vendor-dashboard-data-get-apiv1vendordashboard)
   - [4.2 Quick KPI Summary (`GET /api/v1/vendor/dashboard/summary`)](#42-quick-kpi-summary-get-apiv1vendordashboardsummary)
5. [Field-by-Field Schema Reference](#5-field-by-field-schema-reference)
6. [Status Badges & Visual Indicator Matrix](#6-status-badges--visual-indicator-matrix)
7. [Frontend State Management & Best Practices](#7-frontend-state-management--best-practices)

---

## 1. Module Architecture & Host Navigation

In the **Host / Supply Portal**, the dashboard serves as the central command center for property performance, upcoming reservations, guest occupancy, and financial settlements:

```
Supply / Host Portal
├── 📊 Dashboard (Route: /host/dashboard)
│   ├── KPI Metric Cards (Bookings, Net Earnings, Disbursed Payouts, Today's Occupancy)
│   ├── Financial Settlements & Payouts Summary
│   ├── Revenue Trends Chart (Monthly Net Earnings)
│   ├── Upcoming & Recent Guest Check-ins
│   ├── Recent Payout Transfers
│   └── Top Performing Properties
├── 🏠 My Properties (/host/properties)
├── 📅 Bookings & Calendar (/host/bookings)
└── 💳 Earnings & Payouts (/host/payouts)
```

---

## 2. Screen Layouts & UI Wireframes

### 2.1 Host Overview Dashboard Screen
**Route**: `/host/dashboard`

```
+---------------------------------------------------------------------------------------------------------------+
|  👋 Welcome back, Tashi Homestay!                              [ Trends: Last 12 Months ▼ ]  [ 🔄 Refresh ]   |
+---------------------------------------------------------------------------------------------------------------+
|  [ TOP KPI METRICS STRIP ]                                                                                    |
|  +---------------------+  +---------------------+  +---------------------+  +---------------------+           |
|  | 💵 NET EARNINGS     |  | 💰 SETTLED PAYOUTS  |  | 📅 TOTAL BOOKINGS   |  | 🛎️ TODAY'S GUESTS   |           |
|  | ₹ 3,45,000.00       |  | ₹ 3,10,000.00       |  | 48 Bookings         |  | 14 Active Guests    |           |
|  | Gross: ₹3,85,000    |  | Pending: ₹35,000    |  | 8 Confirmed         |  | 3 In / 2 Out Today  |           |
|  +---------------------+  +---------------------+  +---------------------+  +---------------------+           |
+---------------------------------------------------------------------------------------------------------------+
|  [ SECTION 1: REVENUE TRENDS & EARNINGS OVERVIEW ]                                                            |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
|  | 📈 Monthly Revenue vs Payouts                               |  | 🏦 Payout Settlement Status             | |
|  | [ Bar/Line Chart showing Net Revenue over Selected Months] |  | Total Paid:        ₹ 3,10,000 (12 tx)   | |
|  |                                                             |  | In Processing:     ₹   25,000 (1 tx)    | |
|  |                                                             |  | Pending Approval:  ₹   10,000 (1 tx)    | |
|  |                                                             |  | Last Disbursed:    ₹   45,000 (15 Aug)  | |
|  |                                                             |  |                                         | |
|  |                                                             |  | [ View All Payout Statements ➔ ]        | |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
+---------------------------------------------------------------------------------------------------------------+
|  [ SECTION 2: BOOKINGS MANAGEMENT TABS ]                                                                      |
|  [ (●) Upcoming Check-ins (5) ]      [ ( ) Recent Bookings (5) ]                                              |
|  +---------------------------------------------------------------------------------------------------------+  |
|  | GUEST              | PROPERTY               | DATES             | GUESTS | AMOUNT     | STATUS  | ACTION  |  |
|  +--------------------+------------------------+-------------------+--------+------------+---------+---------+  |
|  | Bob Smith          | Riverfront Villa       | 10 Sep - 12 Sep   | 4 (2R) | ₹ 16,000   | [CONF]  | [View]  |  |
|  | Carol Davis        | Mountain View Homestay | 15 Sep - 18 Sep   | 2 (1R) | ₹ 10,500   | [CONF]  | [View]  |  |
|  +---------------------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------------------+
|  [ SECTION 3: RECENT PAYOUT TRANSFERS & TOP PROPERTIES ]                                                      |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
|  | 💸 Recent Payout Transfers                                  |  | 🏆 Top Performing Properties            | |
|  | 01 Aug - 15 Aug | ₹ 45,000.00 | [PAID] | UTR: HDFC...       |  | 1. Riverfront Villa                     | |
|  | 15 Jul - 31 Jul | ₹ 32,500.00 | [PAID] | UTR: ICIC...       |  |    ₹ 1,50,000 (22 bookings) ⭐ 4.9     | |
|  | 01 Jul - 15 Jul | ₹ 28,000.00 | [PAID] | UTR: AXIS...       |  | 2. Mountain View Retreat                | |
|  |                                                             |  |    ₹ 95,000 (14 bookings) ⭐ 4.7       | |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
+---------------------------------------------------------------------------------------------------------------+
```

---

### 2.2 Financial & Payouts Settlement Widget
The Payouts Card summarizes funds disbursed vs pending settlement:

```
+-----------------------------------------------------------+
| 🏦 Payout Settlement Breakdown                            |
+-----------------------------------------------------------+
| Total Transferred to Bank:    ₹ 3,10,000.00  (12 Payouts) |
| In-Flight / Processing:       ₹   25,000.00  (1 Transfer) |
| Pending Settlement:           ₹   10,000.00  (1 Transfer) |
| Action Required / Failed:     ₹        0.00  (0)          |
+-----------------------------------------------------------+
| 📅 Last Payout Disbursed:                                 |
| Date: 16 Aug 2026, 10:45 AM     Amount: ₹ 45,000.00       |
+-----------------------------------------------------------+
| [ View Bank Details ]       [ Download Payout History ]   |
+-----------------------------------------------------------+
```

---

### 2.3 Recent Payouts Table & Details Modal

#### Recent Payouts Table
```
+-----------------------------------------------------------------------------------------------+
| PERIOD             | GROSS EARNED | COMMISSION  | NET DISBURSED | STATUS     | UTR / REF      |
+--------------------+--------------+-------------+---------------+------------+----------------+
| 01 Aug - 15 Aug    | ₹ 50,000.00  | ₹ 5,000.00  | ₹ 45,000.00   | [✅ PAID]   | HDFCN262283921 |
| 15 Jul - 31 Jul    | ₹ 36,000.00  | ₹ 3,600.00  | ₹ 32,400.00   | [✅ PAID]   | ICICN892374829 |
| 01 Jul - 15 Jul    | ₹ 12,000.00  | ₹ 1,200.00  | ₹ 10,800.00   | [🔄 PROC]   | pout_923847293 |
+-----------------------------------------------------------------------------------------------+
```

---

## 3. TypeScript Type Definitions

Copy and paste these definitions into `src/types/vendor-dashboard.ts` or `src/api/types/dashboard.ts`:

```typescript
export interface BookingStats {
  total: number;
  pending: number;
  confirmed: number;
  checked_in: number;
  checked_out: number;
  cancelled: number;
  completed: number;
  no_show: number;
}

export interface RevenueStats {
  total_revenue: number;
  gross_revenue: number;
  net_revenue: number;
  pending_revenue: number;
  refunded_amount: number;
  total_refunded: number;
  currency: string;
}

export interface PayoutStats {
  total_payouts: number;
  total_paid_amount: number;
  pending_payout_amount: number;
  processing_payout_amount: number;
  failed_payout_amount: number;
  pending_count: number;
  processing_count: number;
  paid_count: number;
  failed_count: number;
  last_payout_date: string | null;
  last_payout_amount: number | null;
  currency: string;
}

export interface PropertyStats {
  total: number;
  active: number;
  draft: number;
  inactive: number;
  archived: number;
  featured: number;
  by_type: Record<string, number>;
}

export interface ReviewStats {
  total_reviews: number;
  average_rating: number;
}

export interface OccupancyToday {
  today_check_ins: number;
  today_check_outs: number;
  active_guests: number;
  blocked_units_today: number;
}

export interface RoomBlockStats {
  total: number;
  active: number;
  upcoming: number;
  past: number;
  total_units_blocked_today: number;
}

export interface DashboardRoomBlockItem {
  id: string;
  property_name: string | null;
  property_slug: string | null;
  room_type_name: string | null;
  block_start_date: string;
  block_end_date: string;
  units_blocked: number;
  reason: string | null;
  created_by_name: string | null;
  created_at: string | null;
}

export interface RevenueTrendItem {
  month: string; // YYYY-MM
  revenue: number;
  gross_revenue: number;
  refunded: number;
  bookings_count: number;
}

export interface DashboardBookingItem {
  id: string;
  booking_reference: string;
  guest_name: string | null;
  guest_email: string | null;
  property_name: string | null;
  property_slug: string | null;
  check_in_date: string;  // YYYY-MM-DD
  check_out_date: string; // YYYY-MM-DD
  num_guests: number;
  num_rooms: number;
  total_amount: number;
  currency: string;
  status: 'pending' | 'confirmed' | 'checked_in' | 'checked_out' | 'cancelled' | 'completed' | 'no_show';
  payment_status: 'pending' | 'partially_paid' | 'paid' | 'failed' | 'refunded';
  created_at: string | null;
}

export interface DashboardPayoutItem {
  id: string;
  vendor_name?: string | null;
  vendor_email?: string | null;
  amount: number;             // Net payout amount
  gross_amount: number | null;// Total booking gross in period
  commission_amount: number | null; // Platform commission deducted
  currency: string;
  period_start: string;       // YYYY-MM-DD
  period_end: string;         // YYYY-MM-DD
  status: 'pending' | 'processing' | 'paid' | 'failed' | 'reversed' | 'rejected' | 'cancelled';
  mode: string | null;        // NEFT, IMPS, RTGS, UPI
  utr: string | null;         // Bank UTR transfer reference
  notes: string | null;
  paid_at: string | null;
  created_at: string | null;
}

export interface TopPropertyItem {
  id: string;
  name: string;
  slug: string | null;
  city: string | null;
  type: string | null;
  price_per_night: number;
  image_url: string | null;
  total_bookings: number;
  total_revenue: number;
  average_rating: number;
}

export interface VendorDashboardData {
  bookings_summary: BookingStats;
  revenue_summary: RevenueStats;
  properties_summary: PropertyStats;
  payouts_summary: PayoutStats;
  reviews_summary: ReviewStats;
  room_blocks_summary: RoomBlockStats;
  occupancy_today: OccupancyToday;
  revenue_trends: RevenueTrendItem[];
  recent_bookings: DashboardBookingItem[];
  upcoming_bookings: DashboardBookingItem[];
  recent_payouts: DashboardPayoutItem[];
  recent_room_blocks: DashboardRoomBlockItem[];
  top_properties: TopPropertyItem[];
}

export interface VendorSummaryData {
  bookings_summary: BookingStats;
  revenue_summary: RevenueStats;
  properties_summary: PropertyStats;
  payouts_summary: PayoutStats;
  reviews_summary: ReviewStats;
  room_blocks_summary: RoomBlockStats;
  occupancy_today: OccupancyToday;
}

export interface VendorDashboardResponse {
  status: string;
  message: string;
  data: VendorDashboardData;
}

export interface VendorSummaryResponse {
  status: string;
  message: string;
  data: VendorSummaryData;
}
```

---

## 4. API Endpoints & Integration Specs

### 4.1 Full Vendor Dashboard Data (`GET /api/v1/vendor/dashboard`)
Retrieves the comprehensive dashboard payload tailored to the authenticated host/vendor.

- **URL**: `/api/v1/vendor/dashboard`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <VENDOR_ACCESS_TOKEN>`
- **Query Parameters**:
  - `months` (optional integer, `1` to `24`, default = `12`): Number of historical months for `revenue_trends`.

#### Response Example (`200 OK`):
```json
{
  "status": "success",
  "message": "Vendor dashboard data retrieved successfully.",
  "data": {
    "bookings_summary": {
      "total": 35,
      "pending": 3,
      "confirmed": 18,
      "checked_in": 5,
      "checked_out": 7,
      "cancelled": 2,
      "completed": 0,
      "no_show": 0
    },
    "revenue_summary": {
      "total_revenue": 345000.0,
      "gross_revenue": 385000.0,
      "net_revenue": 345000.0,
      "pending_revenue": 14000.0,
      "refunded_amount": 0.0,
      "total_refunded": 0.0,
      "currency": "INR"
    },
    "properties_summary": {
      "total": 4,
      "active": 3,
      "draft": 1,
      "inactive": 0,
      "archived": 0,
      "featured": 2,
      "by_type": {
        "homestay": 3,
        "villa": 1
      }
    },
    "payouts_summary": {
      "total_payouts": 8,
      "total_paid_amount": 310000.0,
      "pending_payout_amount": 10000.0,
      "processing_payout_amount": 25000.0,
      "failed_payout_amount": 0.0,
      "pending_count": 1,
      "processing_count": 1,
      "paid_count": 6,
      "failed_count": 0,
      "last_payout_date": "2026-08-16T10:45:00Z",
      "last_payout_amount": 45000.0,
      "currency": "INR"
    },
    "reviews_summary": {
      "total_reviews": 24,
      "average_rating": 4.8
    },
    "occupancy_today": {
      "today_check_ins": 3,
      "today_check_outs": 2,
      "active_guests": 14
    },
    "revenue_trends": [
      {
        "month": "2026-06",
        "revenue": 95000.0,
        "gross_revenue": 95000.0,
        "refunded": 0.0,
        "bookings_count": 10
      },
      {
        "month": "2026-07",
        "revenue": 115000.0,
        "gross_revenue": 115000.0,
        "refunded": 0.0,
        "bookings_count": 12
      },
      {
        "month": "2026-08",
        "revenue": 135000.0,
        "gross_revenue": 135000.0,
        "refunded": 0.0,
        "bookings_count": 13
      }
    ],
    "recent_bookings": [
      {
        "id": "e4293810-7212-4211-9122-123456789abc",
        "booking_reference": "BK-202608-010",
        "guest_name": "Tashi Wangchuk",
        "guest_email": "tashi.w@example.com",
        "property_name": "Riverfront Villa",
        "property_slug": "riverfront-villa",
        "check_in_date": "2026-08-20",
        "check_out_date": "2026-08-25",
        "num_guests": 4,
        "num_rooms": 2,
        "total_amount": 25000.0,
        "currency": "INR",
        "status": "checked_out",
        "payment_status": "paid",
        "created_at": "2026-08-10T14:30:00Z"
      }
    ],
    "upcoming_bookings": [
      {
        "id": "f8391029-3321-4981-8192-987654321def",
        "booking_reference": "BK-202609-001",
        "guest_name": "Anita Sharma",
        "guest_email": "anita.s@example.com",
        "property_name": "Riverfront Villa",
        "property_slug": "riverfront-villa",
        "check_in_date": "2026-09-10",
        "check_out_date": "2026-09-14",
        "num_guests": 2,
        "num_rooms": 1,
        "total_amount": 16000.0,
        "currency": "INR",
        "status": "confirmed",
        "payment_status": "paid",
        "created_at": "2026-08-28T09:15:00Z"
      }
    ],
    "recent_payouts": [
      {
        "id": "c1f72922-38b2-4d2c-9a43-982736172831",
        "vendor_name": "Tashi Dorjee",
        "vendor_email": "tashi.dorjee@example.com",
        "amount": 45000.0,
        "gross_amount": 50000.0,
        "commission_amount": 5000.0,
        "currency": "INR",
        "period_start": "2026-08-01",
        "period_end": "2026-08-15",
        "status": "paid",
        "mode": "NEFT",
        "utr": "HDFCN26228392182",
        "notes": "Settlement for 1st half of August",
        "paid_at": "2026-08-16T10:45:00Z",
        "created_at": "2026-08-16T10:40:00Z"
      }
    ],
    "top_properties": [
      {
        "id": "9938b812-4211-4fa3-8761-123456789abc",
        "name": "Riverfront Villa",
        "slug": "riverfront-villa",
        "city": "Punakha",
        "type": "villa",
        "price_per_night": 5000.0,
        "image_url": "https://cdn.tashihome.com/properties/riverfront.jpg",
        "total_bookings": 22,
        "total_revenue": 210000.0,
        "average_rating": 4.9
      }
    ]
  }
}
```

---

### 4.2 Quick KPI Summary (`GET /api/v1/vendor/dashboard/summary`)
A lightweight endpoint intended for header widgets, quick mobile refresh, or navigation badges.

- **URL**: `/api/v1/vendor/dashboard/summary`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <VENDOR_ACCESS_TOKEN>`

#### Response Example (`200 OK`):
```json
{
  "status": "success",
  "message": "Vendor summary data retrieved successfully.",
  "data": {
    "bookings_summary": {
      "total": 35,
      "pending": 3,
      "confirmed": 18,
      "checked_in": 5,
      "checked_out": 7,
      "cancelled": 2,
      "completed": 0,
      "no_show": 0
    },
    "revenue_summary": {
      "total_revenue": 345000.0,
      "gross_revenue": 385000.0,
      "net_revenue": 345000.0,
      "pending_revenue": 14000.0,
      "refunded_amount": 0.0,
      "total_refunded": 0.0,
      "currency": "INR"
    },
    "properties_summary": {
      "total": 4,
      "active": 3,
      "draft": 1,
      "inactive": 0,
      "archived": 0,
      "featured": 2,
      "by_type": { "homestay": 3, "villa": 1 }
    },
    "payouts_summary": {
      "total_payouts": 8,
      "total_paid_amount": 310000.0,
      "pending_payout_amount": 10000.0,
      "processing_payout_amount": 25000.0,
      "failed_payout_amount": 0.0,
      "pending_count": 1,
      "processing_count": 1,
      "paid_count": 6,
      "failed_count": 0,
      "last_payout_date": "2026-08-16T10:45:00Z",
      "last_payout_amount": 45000.0,
      "currency": "INR"
    },
    "reviews_summary": {
      "total_reviews": 24,
      "average_rating": 4.8
    },
    "occupancy_today": {
      "today_check_ins": 3,
      "today_check_outs": 2,
      "active_guests": 14
    }
  }
}
```

---

## 5. Field-by-Field Schema Reference

### `payouts_summary`
| Field | Type | Description |
| :--- | :--- | :--- |
| `total_payouts` | `number` | Total number of payout records created for this host |
| `total_paid_amount` | `number` | Total amount successfully transferred to host's bank account (in INR) |
| `pending_payout_amount` | `number` | Sum of payouts currently awaiting platform approval / batching |
| `processing_payout_amount`| `number`| Sum of payouts in-flight with RazorpayX / banking networks |
| `failed_payout_amount` | `number` | Sum of payouts that failed or were rejected (action required) |
| `pending_count` | `number` | Number of payouts in `pending` state |
| `processing_count` | `number` | Number of payouts in `processing` state |
| `paid_count` | `number` | Number of payouts in `paid` state |
| `failed_count` | `number` | Number of payouts in `failed`, `rejected`, or `reversed` states |
| `last_payout_date` | `string \| null` | ISO timestamp of the most recent successful bank transfer |
| `last_payout_amount` | `number \| null` | Net amount of the most recent successful bank transfer |

### `recent_payouts[]`
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Payout Public UUID |
| `amount` | `number` | Net payable amount transferred to host |
| `gross_amount` | `number` | Total booking volume generated during settlement period |
| `commission_amount` | `number` | Platform fee deducted for the period |
| `period_start` | `string` | Settlement period start date (`YYYY-MM-DD`) |
| `period_end` | `string` | Settlement period end date (`YYYY-MM-DD`) |
| `status` | `string` | `pending`, `processing`, `paid`, `failed`, `cancelled`, etc. |
| `mode` | `string` | Transfer mode (`NEFT`, `IMPS`, `RTGS`, `UPI`) |
| `utr` | `string \| null` | Bank UTR / Reference number (proof of transfer) |
| `notes` | `string \| null` | Settlement notes or reference description |
| `paid_at` | `string \| null` | Timestamp when funds cleared in host account |

---

## 6. Status Badges & Visual Indicator Matrix

### Payout Status Badges
| Status | Label | Tailwind CSS Classes | Recommended Icon |
| :--- | :--- | :--- | :--- |
| `paid` | **Settled** | `bg-emerald-50 text-emerald-700 border-emerald-200` | `CheckCircle2` |
| `processing`| **In-Flight** | `bg-blue-50 text-blue-700 border-blue-200 animate-pulse` | `Loader2` |
| `pending` | **Pending** | `bg-amber-50 text-amber-700 border-amber-200` | `Clock` |
| `failed` | **Failed** | `bg-rose-50 text-rose-700 border-rose-200` | `AlertCircle` |
| `cancelled` | **Cancelled**| `bg-gray-50 text-gray-600 border-gray-200` | `XCircle` |

### Booking Status Badges
| Status | Label | Tailwind CSS Classes |
| :--- | :--- | :--- |
| `confirmed` | **Confirmed** | `bg-emerald-50 text-emerald-700 border-emerald-200` |
| `checked_in`| **Checked In** | `bg-indigo-50 text-indigo-700 border-indigo-200` |
| `checked_out`| **Checked Out** | `bg-slate-50 text-slate-700 border-slate-200` |
| `pending` | **Pending** | `bg-amber-50 text-amber-700 border-amber-200` |
| `cancelled` | **Cancelled** | `bg-rose-50 text-rose-700 border-rose-200` |

---

## 7. Frontend State Management & Best Practices

### 1. Data Fetching with TanStack Query (React Query)
```typescript
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { VendorDashboardResponse } from '@/types/vendor-dashboard';

export function useVendorDashboard(months: number = 12) {
  return useQuery({
    queryKey: ['vendor-dashboard', months],
    queryFn: async () => {
      const response = await axios.get<VendorDashboardResponse>(
        `/api/v1/vendor/dashboard?months=${months}`
      );
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes fresh
    refetchOnWindowFocus: true,
  });
}
```

### 2. Formatting Currency & Dates
- Always format currency values with `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })`.
- For dates, use `Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })` for consistency across periods and check-in dates.

### 3. Handling Empty States
- When `recent_payouts` is empty: Render an informative empty card: *"No payout disbursements recorded yet. Payouts will appear here once bookings complete and settlements are generated."*
- When `upcoming_bookings` is empty: Display: *"No upcoming check-ins in the immediate queue. Your calendar is clear."*

---

