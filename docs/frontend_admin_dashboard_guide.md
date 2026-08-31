# Frontend Integration & UI Layout Guide: Admin Dashboard & Payouts

This document provides the frontend engineering team with the complete **UI/UX Component Layouts, Screen Wireframes, TypeScript Interfaces, API Payloads, and Integration Rules** for integrating the **Admin Dashboard** and its embedded **Platform Payouts & Settlements** tracking.

---

## Table of Contents
1. [Module Architecture & Admin Navigation](#1-module-architecture--admin-navigation)
2. [Screen Layouts & UI Wireframes](#2-screen-layouts--ui-wireframes)
   - [2.1 Admin Overview Dashboard Screen](#21-admin-overview-dashboard-screen)
   - [2.2 Platform Payouts & Settlements Card](#22-platform-payouts--settlements-card)
   - [2.3 Recent Platform Payouts Table](#23-recent-platform-payouts-table)
3. [TypeScript Type Definitions](#3-typescript-type-definitions)
4. [API Endpoints & Integration Specs](#4-api-endpoints--integration-specs)
   - [4.1 Full Admin Dashboard Data (`GET /api/v1/admin/dashboard`)](#41-full-admin-dashboard-data-get-apiv1admindashboard)
   - [4.2 Quick KPI Summary (`GET /api/v1/admin/dashboard/summary`)](#42-quick-kpi-summary-get-apiv1admindashboardsummary)
5. [Field-by-Field Schema Reference](#5-field-by-field-schema-reference)
6. [Status Badges & Visual Indicator Matrix](#6-status-badges--visual-indicator-matrix)

---

## 1. Module Architecture & Admin Navigation

```
Admin Portal
├── 📊 Dashboard (Route: /admin/dashboard)
│   ├── KPI Metric Cards (Gross Volume, Net Revenue, Disbursed Payouts, Total Users & Bookings)
│   ├── Platform Settlements & Payouts Summary
│   ├── Revenue Trends Analytics (Gross vs Net vs Refunds)
│   ├── Recent Platform Bookings & Host Onboarding Requests
│   ├── Recent Payout Disbursements
│   ├── Recent Refund Requests
│   └── Top Performing Homestays / Properties
├── 🏨 Properties (/admin/properties)
├── 👥 User Management (/admin/users)
├── 💰 Finance & Settlements
│   ├── 💸 Payouts (/admin/finance/payouts)
│   └── 🔄 Refunds (/admin/finance/refunds)
└── ⚙️ System Settings (/admin/settings)
```

---

## 2. Screen Layouts & UI Wireframes

### 2.1 Admin Overview Dashboard Screen
**Route**: `/admin/dashboard`

```
+---------------------------------------------------------------------------------------------------------------+
|  🛡️ Admin Command Center                                       [ Trends: Last 12 Months ▼ ]  [ 🔄 Refresh ]   |
+---------------------------------------------------------------------------------------------------------------+
|  [ TOP KPI METRICS STRIP ]                                                                                    |
|  +---------------------+  +---------------------+  +---------------------+  +---------------------+           |
|  | 💵 NET REVENUE      |  | 💸 DISBURSED PAYOUTS|  | 📅 TOTAL BOOKINGS   |  | 👥 ACTIVE USERS     |           |
|  | ₹ 14,25,000.00      |  | ₹ 12,40,000.00      |  | 185 Bookings        |  | 1,240 Users         |           |
|  | Gross: ₹15,50,000   |  | Pending: ₹85,000    |  | 42 Confirmed        |  | 48 Hosts / Vendors  |           |
|  +---------------------+  +---------------------+  +---------------------+  +---------------------+           |
+---------------------------------------------------------------------------------------------------------------+
|  [ SECTION 1: REVENUE TRENDS & PLATFORM SETTLEMENTS ]                                                         |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
|  | 📈 Platform Financial Performance                           |  | 🏦 Host Settlements Summary             | |
|  | [ Bar/Line Chart: Gross Volume vs Net vs Refunds ]         |  | Settled to Hosts:  ₹ 12,40,000 (45 tx)  | |
|  |                                                             |  | In-Flight:         ₹    65,000 (3 tx)   | |
|  |                                                             |  | Pending Approval:  ₹    20,000 (2 tx)   | |
|  |                                                             |  | Failed / Attention:₹         0 (0)      | |
|  |                                                             |  | Last Disbursed:    ₹    50,000 (16 Aug) | |
|  |                                                             |  |                                         | |
|  |                                                             |  | [ Go to Payout Management ➔ ]          | |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
+---------------------------------------------------------------------------------------------------------------+
|  [ SECTION 2: RECENT ACTIVITY GRID (4 PANELS) ]                                                               |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
|  | 💸 Recent Payout Disbursements                              |  | 🔄 Recent Refund Requests               | |
|  | Tashi Homestay    | ₹45,000 | [PAID] | UTR: HDFC262283921   |  | John Doe    | ₹3,500 | [PROCESSED]        | |
|  | Mountain Villa    | ₹21,600 | [PROC] | In-flight via RzpX   |  | Jane Smith  | ₹7,000 | [PENDING]          | |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
|  | 📅 Recent Bookings                                          |  | 📝 Host Applications                    | |
|  | BK-202608-001 | John Doe | Riverfront Villa | ₹14,000 [CONF] |  | Tashi Dorji | Valley Haven | [PENDING]   | |
|  +-------------------------------------------------------------+  +-----------------------------------------+ |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 3. TypeScript Type Definitions

Save in `src/types/admin-dashboard.ts`:

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

export interface UserStats {
  total: number;
  active: number;
  inactive: number;
  suspended: number;
  by_role: Record<string, number>;
  pending_hosts: number;
}

export interface RefundStats {
  total_requests: number;
  pending: number;
  approved: number;
  processed: number;
  rejected: number;
  total_amount_refunded: number;
}

export interface OccupancyToday {
  today_check_ins: number;
  today_check_outs: number;
  active_guests: number;
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
  check_in_date: string;
  check_out_date: string;
  num_guests: number;
  num_rooms: number;
  total_amount: number;
  currency: string;
  status: string;
  payment_status: string;
  created_at: string | null;
}

export interface DashboardPayoutItem {
  id: string;
  vendor_name: string | null;
  vendor_email: string | null;
  amount: number;
  gross_amount: number | null;
  commission_amount: number | null;
  currency: string;
  period_start: string;
  period_end: string;
  status: 'pending' | 'processing' | 'paid' | 'failed' | 'reversed' | 'rejected' | 'cancelled';
  mode: string | null;
  utr: string | null;
  notes: string | null;
  paid_at: string | null;
  created_at: string | null;
}

export interface DashboardRefundItem {
  id: string;
  booking_reference: string | null;
  guest_name: string | null;
  guest_email: string | null;
  property_name: string | null;
  amount: number;
  reason: string | null;
  status: string;
  razorpay_refund_id: string | null;
  approved_at: string | null;
  created_at: string | null;
}

export interface DashboardHostRequestItem {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  property_name: string | null;
  property_type: string | null;
  city: string | null;
  status: string;
  created_at: string | null;
}

export interface DashboardUserItem {
  id: string;
  full_name: string | null;
  email: string;
  role: string;
  status: string;
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

export interface AdminDashboardData {
  bookings_summary: BookingStats;
  revenue_summary: RevenueStats;
  properties_summary: PropertyStats;
  users_summary: UserStats;
  refunds_summary: RefundStats;
  payouts_summary: PayoutStats;
  occupancy_today: OccupancyToday;
  revenue_trends: RevenueTrendItem[];
  recent_bookings: DashboardBookingItem[];
  recent_host_requests: DashboardHostRequestItem[];
  recent_users: DashboardUserItem[];
  recent_refund_requests: DashboardRefundItem[];
  recent_payouts: DashboardPayoutItem[];
  top_properties: TopPropertyItem[];
}

export interface AdminSummaryData {
  bookings_summary: BookingStats;
  revenue_summary: RevenueStats;
  properties_summary: PropertyStats;
  users_summary: UserStats;
  refunds_summary: RefundStats;
  payouts_summary: PayoutStats;
  occupancy_today: OccupancyToday;
}

export interface AdminDashboardResponse {
  status: string;
  message: string;
  data: AdminDashboardData;
}

export interface AdminSummaryResponse {
  status: string;
  message: string;
  data: AdminSummaryData;
}
```

---

## 4. API Endpoints & Integration Specs

### 4.1 Full Admin Dashboard Data (`GET /api/v1/admin/dashboard`)
- **URL**: `/api/v1/admin/dashboard`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <ADMIN_ACCESS_TOKEN>`
- **Query Parameters**:
  - `months` (optional integer, `1` to `24`, default = `12`): Trend period for `revenue_trends`.

#### Response Sample (`200 OK`):
```json
{
  "status": "success",
  "message": "Admin dashboard data retrieved successfully.",
  "data": {
    "bookings_summary": {
      "total": 185,
      "pending": 12,
      "confirmed": 85,
      "checked_in": 25,
      "checked_out": 45,
      "cancelled": 15,
      "completed": 3,
      "no_show": 0
    },
    "revenue_summary": {
      "total_revenue": 1425000.0,
      "gross_revenue": 1550000.0,
      "net_revenue": 1425000.0,
      "pending_revenue": 85000.0,
      "refunded_amount": 125000.0,
      "total_refunded": 125000.0,
      "currency": "INR"
    },
    "properties_summary": {
      "total": 48,
      "active": 40,
      "draft": 5,
      "inactive": 3,
      "archived": 0,
      "featured": 12,
      "by_type": {
        "homestay": 32,
        "villa": 10,
        "resort": 6
      }
    },
    "users_summary": {
      "total": 1240,
      "active": 1180,
      "inactive": 50,
      "suspended": 10,
      "by_role": {
        "user": 1185,
        "vendor": 48,
        "admin": 4,
        "staff": 3
      },
      "pending_hosts": 6
    },
    "refunds_summary": {
      "total_requests": 18,
      "pending": 3,
      "approved": 4,
      "processed": 10,
      "rejected": 1,
      "total_amount_refunded": 125000.0
    },
    "payouts_summary": {
      "total_payouts": 50,
      "total_paid_amount": 1240000.0,
      "pending_payout_amount": 20000.0,
      "processing_payout_amount": 65000.0,
      "failed_payout_amount": 0.0,
      "pending_count": 2,
      "processing_count": 3,
      "paid_count": 45,
      "failed_count": 0,
      "last_payout_date": "2026-08-16T10:45:00Z",
      "last_payout_amount": 50000.0,
      "currency": "INR"
    },
    "occupancy_today": {
      "today_check_ins": 14,
      "today_check_outs": 8,
      "active_guests": 62
    },
    "revenue_trends": [
      {
        "month": "2026-07",
        "revenue": 650000.0,
        "gross_revenue": 700000.0,
        "refunded": 50000.0,
        "bookings_count": 80
      },
      {
        "month": "2026-08",
        "revenue": 775000.0,
        "gross_revenue": 850000.0,
        "refunded": 75000.0,
        "bookings_count": 105
      }
    ],
    "recent_bookings": [
      {
        "id": "e4293810-7212-4211-9122-123456789abc",
        "booking_reference": "BK-202608-001",
        "guest_name": "John Doe",
        "guest_email": "john@example.com",
        "property_name": "Mountain View Homestay",
        "property_slug": "mountain-view-homestay",
        "check_in_date": "2026-09-01",
        "check_out_date": "2026-09-05",
        "num_guests": 2,
        "num_rooms": 1,
        "total_amount": 14000.0,
        "currency": "INR",
        "status": "confirmed",
        "payment_status": "paid",
        "created_at": "2026-08-25T12:00:00Z"
      }
    ],
    "recent_host_requests": [
      {
        "id": "a9834710-1283-4912-8712-123456789abc",
        "full_name": "Tashi Dorji",
        "email": "tashi@example.com",
        "phone": "+97517123456",
        "property_name": "Valley View Haven",
        "property_type": "homestay",
        "city": "Paro",
        "status": "pending",
        "created_at": "2026-08-30T10:00:00Z"
      }
    ],
    "recent_users": [
      {
        "id": "u1827364-9912-4812-b812-123456789abc",
        "full_name": "Alice Wonderland",
        "email": "alice@example.com",
        "role": "user",
        "status": "active",
        "created_at": "2026-08-30T11:00:00Z"
      }
    ],
    "recent_refund_requests": [
      {
        "id": "r8192734-1182-4912-9912-123456789abc",
        "booking_reference": "BK-202608-001",
        "guest_name": "John Doe",
        "guest_email": "john@example.com",
        "property_name": "Mountain View Homestay",
        "amount": 3500.0,
        "reason": "Guest cancelled within free window",
        "status": "processed",
        "razorpay_refund_id": "rfnd_123456",
        "approved_at": "2026-08-26T10:00:00Z",
        "created_at": "2026-08-26T09:30:00Z"
      }
    ],
    "recent_payouts": [
      {
        "id": "c1f72922-38b2-4d2c-9a43-982736172831",
        "vendor_name": "Tashi Dorji",
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
        "notes": "Settlement for August 1st half",
        "paid_at": "2026-08-16T10:45:00Z",
        "created_at": "2026-08-16T10:40:00Z"
      }
    ],
    "top_properties": [
      {
        "id": "9938b812-4211-4fa3-8761-123456789abc",
        "name": "Mountain View Homestay",
        "slug": "mountain-view-homestay",
        "city": "Thimphu",
        "type": "homestay",
        "price_per_night": 3500.0,
        "image_url": "https://cdn.example.com/mountain.jpg",
        "total_bookings": 25,
        "total_revenue": 87500.0,
        "average_rating": 4.8
      }
    ]
  }
}
```

---

### 4.2 Quick KPI Summary (`GET /api/v1/admin/dashboard/summary`)
- **URL**: `/api/v1/admin/dashboard/summary`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <ADMIN_ACCESS_TOKEN>`

#### Response Sample (`200 OK`):
```json
{
  "status": "success",
  "message": "Admin summary data retrieved successfully.",
  "data": {
    "bookings_summary": {
      "total": 185,
      "pending": 12,
      "confirmed": 85,
      "checked_in": 25,
      "checked_out": 45,
      "cancelled": 15,
      "completed": 3,
      "no_show": 0
    },
    "revenue_summary": {
      "total_revenue": 1425000.0,
      "gross_revenue": 1550000.0,
      "net_revenue": 1425000.0,
      "pending_revenue": 85000.0,
      "refunded_amount": 125000.0,
      "total_refunded": 125000.0,
      "currency": "INR"
    },
    "properties_summary": {
      "total": 48,
      "active": 40,
      "draft": 5,
      "inactive": 3,
      "archived": 0,
      "featured": 12,
      "by_type": { "homestay": 32, "villa": 10, "resort": 6 }
    },
    "users_summary": {
      "total": 1240,
      "active": 1180,
      "inactive": 50,
      "suspended": 10,
      "by_role": { "user": 1185, "vendor": 48, "admin": 4, "staff": 3 },
      "pending_hosts": 6
    },
    "refunds_summary": {
      "total_requests": 18,
      "pending": 3,
      "approved": 4,
      "processed": 10,
      "rejected": 1,
      "total_amount_refunded": 125000.0
    },
    "payouts_summary": {
      "total_payouts": 50,
      "total_paid_amount": 1240000.0,
      "pending_payout_amount": 20000.0,
      "processing_payout_amount": 65000.0,
      "failed_payout_amount": 0.0,
      "pending_count": 2,
      "processing_count": 3,
      "paid_count": 45,
      "failed_count": 0,
      "last_payout_date": "2026-08-16T10:45:00Z",
      "last_payout_amount": 50000.0,
      "currency": "INR"
    },
    "occupancy_today": {
      "today_check_ins": 14,
      "today_check_outs": 8,
      "active_guests": 62
    }
  }
}
```

---

## 5. Field-by-Field Schema Reference

### `payouts_summary`
| Field | Type | Description |
| :--- | :--- | :--- |
| `total_payouts` | `number` | Total payout disbursements generated across all vendors |
| `total_paid_amount` | `number` | Total funds successfully transferred to vendor bank accounts (INR) |
| `pending_payout_amount` | `number` | Total pending settlement amount awaiting disbursement |
| `processing_payout_amount`| `number`| Total amount in-flight with RazorpayX / banking networks |
| `failed_payout_amount` | `number` | Total failed transfer volume requiring administrative action |
| `pending_count` | `number` | Count of pending payout batches |
| `processing_count` | `number` | Count of in-flight payout transfers |
| `paid_count` | `number` | Count of successfully settled payouts |
| `failed_count` | `number` | Count of failed, rejected, or reversed transfers |
| `last_payout_date` | `string \| null` | Timestamp of the most recent payout execution |
| `last_payout_amount` | `number \| null` | Amount of the most recent payout execution |

---

## 6. Status Badges & Visual Indicator Matrix

| Payout Status | Tailwind CSS Badge Classes | Action Required |
| :--- | :--- | :--- |
| `paid` | `bg-emerald-50 text-emerald-700 border-emerald-200` | Settled |
| `processing` | `bg-blue-50 text-blue-700 border-blue-200 animate-pulse` | In Banking Queue |
| `pending` | `bg-amber-50 text-amber-700 border-amber-200` | Ready for Disbursement |
| `failed` | `bg-rose-50 text-rose-700 border-rose-200` | Review & Retry |
| `cancelled` | `bg-slate-50 text-slate-600 border-slate-200` | Cancelled |

---

