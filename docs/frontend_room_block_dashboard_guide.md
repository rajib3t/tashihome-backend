# Frontend Integration Guide: Room Block Data in Admin & Vendor Dashboards

This guide provides frontend engineers with the complete architecture, UI wireframes, TypeScript interfaces, API schemas, and component implementation patterns for displaying **Room Block Data** across both the **Admin Dashboard** and **Vendor (Supply) Dashboard**.

---

## 1. Overview & Architecture

### What is Room Blocking?
Room blocking is the platform feature allowing hosts and administrators to temporarily hold room inventory (taking units off the market) for reasons such as:
- **Routine maintenance & renovations**
- **Host / family personal stay**
- **VIP reservation holds**
- **Emergency property repairs**

### Why is Room Block Data on Dashboards?
Surfacing room block metrics directly on Admin and Vendor dashboards ensures:
1. **Real-Time Operational Awareness**: Operators and hosts immediately know how many room units are locked today and unavailable for booking.
2. **True Inventory Visibility**: Avoids confusion when occupancy is low but properties appear "sold out" on the consumer portal.
3. **Streamlined Navigation**: Hosts can quickly review recent holds and access the dedicated `/room-blocks` management interface in one click.

---

## 2. API Endpoints & Payloads

### 2.1 Admin Dashboard Endpoints

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/v1/admin/dashboard` | `GET` | Bearer (Admin) | Full admin dashboard including all KPIs, room blocks summary, and recent room blocks (limit 5). |
| `/api/v1/admin/dashboard/summary` | `GET` | Bearer (Admin) | Lightweight summary including KPI cards (`room_blocks_summary` and `occupancy_today`). |

#### Query Parameters (`GET /api/v1/admin/dashboard`):
- `months` *(optional, int, default: 12, min: 1, max: 24)*: Number of months for trend charts.

#### Example Admin Response (`GET /api/v1/admin/dashboard`):
```json
{
  "status": "success",
  "message": "Admin dashboard data retrieved successfully.",
  "data": {
    "bookings_summary": {
      "total": 185,
      "pending": 8,
      "confirmed": 42,
      "checked_in": 15,
      "checked_out": 95,
      "cancelled": 12,
      "completed": 13,
      "no_show": 0
    },
    "revenue_summary": {
      "total_revenue": 1425000.0,
      "gross_revenue": 1550000.0,
      "net_revenue": 1425000.0,
      "pending_revenue": 85000.0,
      "refunded_amount": 40000.0,
      "total_refunded": 40000.0,
      "currency": "INR"
    },
    "properties_summary": {
      "total": 48,
      "active": 42,
      "draft": 4,
      "inactive": 2,
      "archived": 0,
      "featured": 12,
      "by_type": { "homestay": 38, "resort": 10 }
    },
    "users_summary": {
      "total": 1240,
      "active": 1180,
      "inactive": 50,
      "suspended": 10,
      "by_role": { "user": 1180, "vendor": 48, "admin": 8, "staff": 4 },
      "pending_hosts": 6
    },
    "refunds_summary": {
      "total_requests": 14,
      "pending": 2,
      "approved": 4,
      "processed": 8,
      "rejected": 0,
      "total_amount_refunded": 40000.0
    },
    "payouts_summary": {
      "total_payouts": 52,
      "total_paid_amount": 1240000.0,
      "pending_payout_amount": 85000.0,
      "processing_payout_amount": 65000.0,
      "failed_payout_amount": 0.0,
      "pending_count": 2,
      "processing_count": 3,
      "paid_count": 47,
      "failed_count": 0,
      "last_payout_date": "2026-08-30T10:00:00Z",
      "last_payout_amount": 50000.0,
      "currency": "INR"
    },
    "room_blocks_summary": {
      "total": 34,
      "active": 5,
      "upcoming": 18,
      "past": 11,
      "total_units_blocked_today": 8
    },
    "occupancy_today": {
      "today_check_ins": 6,
      "today_check_outs": 4,
      "active_guests": 28,
      "blocked_units_today": 8
    },
    "revenue_trends": [],
    "recent_bookings": [],
    "recent_host_requests": [],
    "recent_users": [],
    "recent_refund_requests": [],
    "recent_payouts": [],
    "recent_room_blocks": [
      {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "property_name": "Tashi Homestay & Heritage",
        "property_slug": "tashi-homestay-heritage",
        "room_type_name": "Deluxe Valley Suite",
        "block_start_date": "2026-09-02",
        "block_end_date": "2026-09-06",
        "units_blocked": 2,
        "reason": "Scheduled bathroom renovation",
        "created_by_name": "Tashi Dorji",
        "created_at": "2026-09-01T08:30:00Z"
      },
      {
        "id": "1b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
        "property_name": "Riverfront Villa",
        "property_slug": "riverfront-villa",
        "room_type_name": "Standard Mountain Room",
        "block_start_date": "2026-09-10",
        "block_end_date": "2026-09-15",
        "units_blocked": 1,
        "reason": "Host family visit",
        "created_by_name": "Kinley Tshering",
        "created_at": "2026-08-30T14:15:00Z"
      }
    ],
    "top_properties": []
  }
}
```

---

### 2.2 Vendor (Supply) Dashboard Endpoints

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/v1/vendor/dashboard` | `GET` | Bearer (Vendor) | Full vendor dashboard scoped strictly to vendor's properties, with `room_blocks_summary` and `recent_room_blocks`. |
| `/api/v1/vendor/dashboard/summary` | `GET` | Bearer (Vendor) | Lightweight vendor summary with `room_blocks_summary` and `occupancy_today`. |

#### Example Vendor Response (`GET /api/v1/vendor/dashboard`):
```json
{
  "status": "success",
  "message": "Vendor dashboard data retrieved successfully.",
  "data": {
    "bookings_summary": {
      "total": 35,
      "pending": 2,
      "confirmed": 14,
      "checked_in": 4,
      "checked_out": 12,
      "cancelled": 2,
      "completed": 1,
      "no_show": 0
    },
    "revenue_summary": {
      "total_revenue": 145000.0,
      "gross_revenue": 145000.0,
      "net_revenue": 145000.0,
      "pending_revenue": 18000.0,
      "refunded_amount": 0.0,
      "total_refunded": 0.0,
      "currency": "INR"
    },
    "properties_summary": {
      "total": 3,
      "active": 3,
      "draft": 0,
      "inactive": 0,
      "archived": 0,
      "featured": 1,
      "by_type": { "homestay": 3 }
    },
    "payouts_summary": {
      "total_payouts": 8,
      "total_paid_amount": 98000.0,
      "pending_payout_amount": 16000.0,
      "processing_payout_amount": 0.0,
      "failed_payout_amount": 0.0,
      "pending_count": 1,
      "processing_count": 0,
      "paid_count": 7,
      "failed_count": 0,
      "last_payout_date": "2026-08-31T09:00:00Z",
      "last_payout_amount": 24000.0,
      "currency": "INR"
    },
    "reviews_summary": {
      "total_reviews": 24,
      "average_rating": 4.9
    },
    "room_blocks_summary": {
      "total": 6,
      "active": 1,
      "upcoming": 3,
      "past": 2,
      "total_units_blocked_today": 2
    },
    "occupancy_today": {
      "today_check_ins": 1,
      "today_check_outs": 2,
      "active_guests": 8,
      "blocked_units_today": 2
    },
    "revenue_trends": [],
    "recent_bookings": [],
    "upcoming_bookings": [],
    "recent_payouts": [],
    "recent_room_blocks": [
      {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "property_name": "Tashi Homestay & Heritage",
        "property_slug": "tashi-homestay-heritage",
        "room_type_name": "Deluxe Valley Suite",
        "block_start_date": "2026-09-02",
        "block_end_date": "2026-09-06",
        "units_blocked": 2,
        "reason": "Scheduled bathroom renovation",
        "created_by_name": "Tashi Dorji",
        "created_at": "2026-09-01T08:30:00Z"
      }
    ],
    "top_properties": []
  }
}
```

---

## 3. UI/UX Wireframes & Component Layouts

### 3.1 Top KPI Ribbon & Occupancy Strip
Add the **Blocked Today** card to the occupancy strip or top metric cards:

```
+---------------------------------------------------------------------------------------------------------------+
|  TODAY'S PROPERTY PULSE                                                                                       |
|  +---------------------+  +---------------------+  +---------------------+  +-------------------------------+ |
|  | 📥 CHECK-INS        |  | 📤 CHECK-OUTS       |  | 👥 IN-HOUSE GUESTS  |  | 🚫 BLOCKED ROOM UNITS         | |
|  | 6 Arrivals Today    |  | 4 Departures Today  |  | 28 Active Guests    |  | 8 Units Blocked (5 active)   | |
|  | [ View Guests ➔ ]   |  | [ Room Turnovers ]  |  | Occupancy: 82%      |  | [ Manage Blocks ➔ ]          | |
|  +---------------------+  +---------------------+  +---------------------+  +-------------------------------+ |
+---------------------------------------------------------------------------------------------------------------+
```

### 3.2 Recent Room Blocks Widget / Card Layout
Display directly alongside Recent Bookings or under Property Operations:

```
+---------------------------------------------------------------------------------------------------------------+
|  🔒 Recent Room Blocks                                                 [ + Block Dates ] [ View All Blocks ➔ ]|
+---------------------------------------------------------------------------------------------------------------+
|  Property / Room Type         | Dates                  | Units | Reason               | Status       | Action |
|-------------------------------|------------------------|-------|----------------------|--------------|--------|
|  Tashi Homestay & Heritage    | Sep 02, 26 - Sep 06, 26| 2     | Bathroom renovation  | 🟢 ACTIVE NOW| [View] |
|  Deluxe Valley Suite          | (4 nights)             |       | By: Tashi Dorji      |              |        |
|-------------------------------|------------------------|-------|----------------------|--------------|--------|
|  Riverfront Villa             | Sep 10, 26 - Sep 15, 26| 1     | Host family visit    | 🔵 UPCOMING  | [View] |
|  Standard Mountain Room       | (5 nights)             |       | By: Kinley Tshering  |              |        |
|-------------------------------|------------------------|-------|----------------------|--------------|--------|
|  Alpine Ridge Cabin           | Aug 20, 26 - Aug 25, 26| 1     | Deep cleaning        | ⚪ EXPIRED   | [View] |
|  Attic Suite                  | (5 nights)             |       | By: Staff Sonam      |              |        |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 4. TypeScript Type Definitions

Save in `src/types/dashboard.ts`:

```typescript
export interface RoomBlockStats {
  total: number;
  active: number;
  upcoming: number;
  past: number;
  total_units_blocked_today: number;
}

export interface OccupancyToday {
  today_check_ins: number;
  today_check_outs: number;
  active_guests: number;
  blocked_units_today: number;
}

export interface RecentRoomBlock {
  id: string;
  property_name: string | null;
  property_slug: string | null;
  room_type_name: string | null;
  block_start_date: string; // YYYY-MM-DD
  block_end_date: string;   // YYYY-MM-DD
  units_blocked: number;
  reason: string | null;
  created_by_name: string | null;
  created_at: string | null;
}

// Updated Admin Dashboard Data
export interface AdminDashboardData {
  bookings_summary: BookingStats;
  revenue_summary: RevenueStats;
  properties_summary: PropertyStats;
  users_summary: UserStats;
  refunds_summary: RefundStats;
  payouts_summary: PayoutStats;
  room_blocks_summary: RoomBlockStats;
  occupancy_today: OccupancyToday;
  revenue_trends: RevenueTrendItem[];
  recent_bookings: RecentBooking[];
  recent_host_requests: RecentHostRequest[];
  recent_users: RecentUser[];
  recent_refund_requests: RecentRefundRequest[];
  recent_payouts: RecentPayout[];
  recent_room_blocks: RecentRoomBlock[];
  top_properties: TopProperty[];
}

// Updated Vendor Dashboard Data
export interface VendorDashboardData {
  bookings_summary: BookingStats;
  revenue_summary: RevenueStats;
  properties_summary: PropertyStats;
  payouts_summary: PayoutStats;
  reviews_summary: ReviewStats;
  room_blocks_summary: RoomBlockStats;
  occupancy_today: OccupancyToday;
  revenue_trends: RevenueTrendItem[];
  recent_bookings: RecentBooking[];
  upcoming_bookings: RecentBooking[];
  recent_payouts: RecentPayout[];
  recent_room_blocks: RecentRoomBlock[];
  top_properties: TopProperty[];
}
```

---

## 5. Status Computation & Badges Guide

Frontend components should compute the block lifecycle status dynamically to guarantee consistent display regardless of client timezone:

```typescript
export type RoomBlockStatus = 'active' | 'upcoming' | 'past';

export function getRoomBlockStatus(startDate: string, endDate: string): RoomBlockStatus {
  const today = new Date().toISOString().split('T')[0]; // Current date YYYY-MM-DD
  
  if (endDate < today) {
    return 'past';
  }
  if (startDate <= today && endDate >= today) {
    return 'active';
  }
  return 'upcoming';
}
```

### Visual Badge Indicator Matrix

| Status | Condition | Badge Text | Tailwind Styling |
|---|---|---|---|
| **Active Now** | `start_date <= today <= end_date` | `Active Now` | `bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300` |
| **Upcoming** | `start_date > today` | `Upcoming` | `bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-950/40 dark:text-blue-300` |
| **Expired** | `end_date < today` | `Expired` | `bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-400` |

---

## 6. React / Next.js Component Example

```tsx
import React from 'react';
import Link from 'next/link';
import { format, parseISO } from 'date-fns';
import { RecentRoomBlock, RoomBlockStats } from '@/types/dashboard';

interface RoomBlocksCardProps {
  stats: RoomBlockStats;
  blocks: RecentRoomBlock[];
  viewAllHref: string; // e.g., '/admin/room-blocks' or '/vendor/room-blocks'
}

export const DashboardRoomBlocksWidget: React.FC<RoomBlocksCardProps> = ({
  stats,
  blocks,
  viewAllHref,
}) => {
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-4 mb-4">
        <div>
          <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-base flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
            Room Holds & Blocks
          </h3>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            {stats.total_units_blocked_today} unit{stats.total_units_blocked_today === 1 ? '' : 's'} blocked today across {stats.active} active hold{stats.active === 1 ? '' : 's'}
          </p>
        </div>
        <Link
          href={viewAllHref}
          className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
        >
          Manage Blocks ➔
        </Link>
      </div>

      {/* Mini KPI Chips */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-lg p-2.5 text-center">
          <div className="text-xs text-amber-700 dark:text-amber-400 font-medium">Active Today</div>
          <div className="text-lg font-bold text-amber-900 dark:text-amber-200">{stats.active}</div>
        </div>
        <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/40 rounded-lg p-2.5 text-center">
          <div className="text-xs text-blue-700 dark:text-blue-400 font-medium">Upcoming</div>
          <div className="text-lg font-bold text-blue-900 dark:text-blue-200">{stats.upcoming}</div>
        </div>
        <div className="bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-700 rounded-lg p-2.5 text-center">
          <div className="text-xs text-zinc-600 dark:text-zinc-400 font-medium">Total Holds</div>
          <div className="text-lg font-bold text-zinc-900 dark:text-zinc-200">{stats.total}</div>
        </div>
      </div>

      {/* Recent Blocks List */}
      {blocks.length === 0 ? (
        <div className="text-center py-6 text-sm text-zinc-400">No recent room blocks found.</div>
      ) : (
        <div className="space-y-2.5">
          {blocks.map((block) => {
            const isActive = block.block_start_date <= today && block.block_end_date >= today;
            const isUpcoming = block.block_start_date > today;

            return (
              <div
                key={block.id}
                className="flex items-center justify-between p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <div>
                  <div className="font-medium text-sm text-zinc-900 dark:text-zinc-100">
                    {block.property_name || 'Property'}
                    <span className="text-xs text-zinc-400 ml-1.5">({block.room_type_name})</span>
                  </div>
                  <div className="text-xs text-zinc-500 mt-0.5">
                    {format(parseISO(block.block_start_date), 'MMM d')} – {format(parseISO(block.block_end_date), 'MMM d, yyyy')} • {block.units_blocked} unit{block.units_blocked > 1 ? 's' : ''}
                    {block.reason && <span className="italic ml-1">({block.reason})</span>}
                  </div>
                </div>
                <div>
                  {isActive && (
                    <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                      Active Now
                    </span>
                  )}
                  {isUpcoming && (
                    <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300">
                      Upcoming
                    </span>
                  )}
                  {!isActive && !isUpcoming && (
                    <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-zinc-200 text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300">
                      Expired
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
```

