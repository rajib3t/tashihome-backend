# Frontend Integration & UI Layout Guide: Admin Payout Management

This document provides the frontend engineering team with the complete **UI/UX Component Layouts, Screen Wireframes, TypeScript Interfaces, API Payloads, and State Management Rules** for building the **Admin Payout Management** module.

> **Last Updated**: 2026-09-06  
> **Base URL**: `/api/v1/admin/payouts`  
> **Auth**: `Authorization: Bearer <ADMIN_ACCESS_TOKEN>`

---

## Table of Contents
1. [Module Architecture & Navigation](#1-module-architecture--navigation)
2. [Overall Flow Diagram](#2-overall-flow-diagram)
3. [Screen Layouts & UI Wireframes](#3-screen-layouts--ui-wireframes)
   - [3.1 Payouts Dashboard & Table View](#31-payouts-dashboard--table-view)
   - [3.2 Create Payout / Dues Calculator Modal](#32-create-payout--dues-calculator-modal)
   - [3.3 Payout Details & Timeline Drawer](#33-payout-details--timeline-drawer)
   - [3.4 Vendor Bank Account Management Modal](#34-vendor-bank-account-management-modal)
4. [TypeScript Type Definitions](#4-typescript-type-definitions)
5. [API Endpoints & Integration Specs](#5-api-endpoints--integration-specs)
   - [5.1 Bank Account Management](#51-bank-account-management)
   - [5.2 Payout Lifecycle](#52-payout-lifecycle)
6. [Status Badges & Action Matrix](#6-status-badges--action-matrix)
7. [Error Handling & Edge Cases](#7-error-handling--edge-cases)

---

## 1. Module Architecture & Navigation

The Payout Management module resides under the **Admin Portal** navigation menu:
```
Admin Navigation
└── Finance & Settlements
    ├── 💰 Payouts (Active Route: /admin/finance/payouts)
    └── 🔄 Refunds (/admin/finance/refunds)
```

---

## 2. Overall Flow Diagram

```
Admin Opens Vendor Page
        │
        ▼
┌─────────────────────────┐
│  List Bank Accounts      │  GET /vendors/{id}/bank-accounts
│  (does vendor have any?) │
└─────────────┬───────────┘
              │
       No ───►│◄─── Yes
              │              │
              ▼              ▼
   ┌──────────────────┐   ┌─────────────────────────┐
   │  Add Bank Account │   │  Calculate Vendor Earnings│
   │  (Bank / UPI VPA) │   │  GET /eligible?vendor_id  │
   └──────────┬───────┘   └────────────┬────────────┘
              │                        │
              ▼                        ▼
   POST /vendors/{id}/            ┌──────────────────────┐
   bank-accounts                  │  Create Payout Record  │
   ┌──────────────────┐           │  POST /               │
   │ Auto-creates:     │           └──────────┬───────────┘
   │  • Razorpay       │                      │
   │    Contact        │                      ▼
   │  • Fund Account   │           ┌──────────────────────┐
   └──────────────────┘           │  Process via Razorpay  │
                                  │  POST /{id}/process    │
                                  └──────────┬───────────┘
                                             │
                               ┌─────────────┼─────────────┐
                               ▼             ▼             ▼
                          [processing]   [queued]      [failed]
                               │             │             │
                          POST /{id}/   POST /{id}/   [Show error +
                            sync         cancel         Retry]
                               │
                          [paid] → Show UTR
```

---

## 3. Screen Layouts & UI Wireframes

### 3.1 Payouts Dashboard & Table View
**Route**: `/admin/finance/payouts`

```
+---------------------------------------------------------------------------------------------------------+
| [ Finance ] / Payouts                                              [ + Create Payout ]  [ 🔄 Refresh ]   |
+---------------------------------------------------------------------------------------------------------+
| [ METRIC CARDS ]                                                                                        |
| +---------------------+  +---------------------+  +---------------------+  +---------------------+      |
| | Total Disbursed     |  | Pending Payouts     |  | In Processing       |  | Failed / Action Req |      |
| | ₹ 14,25,000         |  | ₹ 1,45,200 (12)     |  | ₹ 48,000 (3)        |  | ₹ 12,500 (1)        |      |
| +---------------------+  +---------------------+  +---------------------+  +---------------------+      |
+---------------------------------------------------------------------------------------------------------+
| [ FILTERS & SEARCH BAR ]                                                                                |
| [🔍 Search by Vendor / Ref ID... ]  [ Status: All ▼ ]  [ Date Range: 01 Aug - 31 Aug 2026 ▼ ] [ Clear ] |
+---------------------------------------------------------------------------------------------------------+
| VENDOR              | PERIOD            | GROSS (₹)  | COMM (₹) | NET AMOUNT | STATUS    | ACTIONS      |
+---------------------+-------------------+------------+----------+------------+-----------+--------------+
| Tashi Homestay      | 01 Aug - 15 Aug   | 50,000.00  | 5,000.00 | 45,000.00  | [PAID]    | [View]       |
| Mountain View Villa | 15 Aug - 31 Aug   | 24,000.00  | 2,400.00 | 21,600.00  | [PROCESS] | [Sync][View] |
| Himalayan Haven     | 01 Aug - 31 Aug   | 18,500.00  | 1,850.00 | 16,650.00  | [PENDING] | [Pay] [View] |
| Riverside Retreat   | 01 Jul - 15 Jul   | 12,000.00  | 1,200.00 | 10,800.00  | [FAILED]  | [Retry][View]|
+---------------------------------------------------------------------------------------------------------+
| Showing 1 - 4 of 48 payouts                                               [ < Prev ] [ 1 ] 2 3 [ Next >]|
+---------------------------------------------------------------------------------------------------------+
```

---

### 3.2 Create Payout / Dues Calculator Modal
**Triggered by**: Clicking `+ Create Payout` button on the top right.

```
+---------------------------------------------------------------------------------------+
|  Generate Vendor Payout                                                           [X] |
+---------------------------------------------------------------------------------------+
|  Step 1: Select Vendor & Settlement Period                                            |
|  Vendor:              [ Select Vendor (Search by Name / Email)                  ▼ ]   |
|  Period Start Date:   [ 2026-08-01 📅 ]      Period End Date: [ 2026-08-31 📅 ]       |
|  Commission Rate (%): [ 10.0 % ]             [ ⚡ Calculate Eligible Dues ]            |
+---------------------------------------------------------------------------------------+
|  [ EARNINGS CALCULATION PREVIEW ]                                                     |
|  +---------------------------------------------------------------------------------+  |
|  | Completed Bookings Count:   14 Bookings                                         |  |
|  | Gross Booking Volume:       ₹ 1,50,000.00                                       |  |
|  | Platform Commission (10%): -₹  15,000.00                                        |  |
|  | Already Disbursed Amount:  -₹        0.00                                       |  |
|  | ------------------------------------------------------------------------------- |  |
|  | Net Payable Amount:        ₹ 1,35,000.00                                        |  |
|  +---------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------+
|  Step 2: Payout Details                                                               |
|  Disbursement Amount (₹): [ 135000.00 ]                                               |
|  Destination Account:     [ HDFC Bank (A/C: ****5678, IFSC: HDFC0001234) [Primary] ▼] |
|                           (+ Add / Change Bank Account)                               |
|  Payment Mode:            [🔘 NEFT ]   [⚪ IMPS ]   [⚪ RTGS ]   [⚪ UPI ]               |
|  Notes / Reference:       [ August 2026 Regular Settlement                        ]   |
+---------------------------------------------------------------------------------------+
|  [ Cancel ]                                  [ Save as Pending ]  [ ⚡ Disburse Now ] |
+---------------------------------------------------------------------------------------+
```

> **Note**: `Save as Pending` calls `POST /` only. `Disburse Now` calls `POST /` then immediately `POST /{id}/process`.

---

### 3.3 Payout Details & Timeline Drawer
**Triggered by**: Clicking `[View]` on any row in the payouts table.

```
+-----------------------------------------------------------------------------------+
| Payout Details: #PO-98234-A                                                   [X] |
+-----------------------------------------------------------------------------------+
| STATUS: [ ✅ PAID ]   (Paid at: 2026-08-16 10:45 AM)          [ 🔄 Sync with Gateway ] |
+-----------------------------------------------------------------------------------+
| 👤 VENDOR DETAILS                                                                 |
| Name:  Tashi Dorjee                                                               |
| Email: tashi.dorjee@example.com      Phone: +91 98765 43210                       |
| Property: Tashi Homestay & Villa (Sikkim)                                         |
+-----------------------------------------------------------------------------------+
| 🏦 DESTINATION BANK ACCOUNT                                                       |
| Account Holder: Tashi Dorjee                                                      |
| Bank Name:      HDFC Bank (Gangtok Branch)                                        |
| Account Number: XXXXXXXX5678                                                      |
| IFSC Code:      HDFC0001234                                                       |
| Razorpay Contact: cont_N827364823     Razorpay Fund A/C: fa_Nq98xK198d            |
| Verified on Razorpay: ✅ Yes                                                       |
+-----------------------------------------------------------------------------------+
| 💳 TRANSACTION & GATEWAY TRACKING                                                 |
| Razorpay Payout ID: pout_872938472938                                             |
| Bank UTR Number:    HDFCN26228392182 (Proof of Bank Transfer)                     |
| Payment Mode:       NEFT                                                          |
| Currency:           INR (₹)                                                       |
+-----------------------------------------------------------------------------------+
| 📊 FINANCIAL BREAKDOWN                                                             |
| Settlement Period:  01 Aug 2026  ➔  15 Aug 2026                                   |
| Gross Bookings:     ₹ 50,000.00                                                   |
| Platform Fee (10%): -₹  5,000.00                                                  |
| --------------------------------------------------------------------------------- |
| Total Disbursed:    ₹ 45,000.00                                                   |
+-----------------------------------------------------------------------------------+
| 📝 NOTES                                                                          |
| "Settlement for 1st fortnight of August 2026"                                     |
+-----------------------------------------------------------------------------------+
| [ Close ]                                              [ 🖨️ Download Receipt PDF ] |
+-----------------------------------------------------------------------------------+
```

---

### 3.4 Vendor Bank Account Management Modal
**Triggered by**: Clicking `(+ Add / Change Bank Account)` inside the payout modal or from vendor profile page.

```
+--------------------------------------------------------------------+
|  Add Vendor Payout Account                                     [X] |
+--------------------------------------------------------------------+
|  Account Type:   (●) Bank Account (NEFT/IMPS/RTGS)                |
|                  ( ) UPI VPA                                       |
|                                                                    |
|  ── When "Bank Account" is selected ──────────────────────────     |
|  Account Holder Name: [ Tashi Dorjee                            ]  |
|  Bank Name:           [ HDFC Bank                               ]  |
|  Account Number:      [ 50100234567890                          ]  |
|  Confirm A/C Number:  [ 50100234567890                          ]  |
|  IFSC Code:           [ HDFC0001234  ] (auto-uppercased)           |
|  Branch Name:         [ Gangtok MG Marg                         ]  |
|                                                                    |
|  ── When "UPI VPA" is selected ────────────────────────────────    |
|  Account Holder Name: [ Tashi Dorjee                            ]  |
|  UPI ID:              [ tashidorjee@okaxis                      ]  |
|                                                                    |
|  [x] Set as Primary Payout Account                                 |
+--------------------------------------------------------------------+
|  ℹ️  Saving will register this account on Razorpay automatically.  |
|  [ Cancel ]                                       [ Save Account ] |
+--------------------------------------------------------------------+
```

**Existing accounts list** (shown above the form):
```
+-----------------------------------------------------------+
| Saved Accounts                                            |
+-----------------------------------------------------------+
| ✅ HDFC Bank — ****5678 — NEFT [Primary] [Set Primary ✓]  |
|    Razorpay Verified ✅   [Delete]                         |
| ○  Axis UPI — tashi@okaxis [Set Primary] [Delete]         |
|    Razorpay Verified ✅                                    |
+-----------------------------------------------------------+
```

---

## 4. TypeScript Type Definitions

Save in `src/types/payout.ts`:

```typescript
// ─── Enums ────────────────────────────────────────────────────────────────────

export type PayoutStatus =
  | 'pending'
  | 'processing'
  | 'queued'
  | 'paid'
  | 'failed'
  | 'reversed'
  | 'rejected'
  | 'cancelled';

export type PayoutMode = 'NEFT' | 'IMPS' | 'RTGS' | 'UPI';

export type BankAccountType = 'bank_account' | 'vpa';

// ─── Entities ─────────────────────────────────────────────────────────────────

export interface PayoutVendor {
  id: string;              // public_id (UUID string)
  email: string;
  phone: string | null;
  full_name: string | null;
}

export interface VendorBankAccount {
  id: string;              // public_id (UUID string)
  account_type: BankAccountType;
  account_holder_name: string;
  account_number: string | null;    // null for VPA
  ifsc_code: string | null;         // null for VPA
  bank_name: string | null;
  branch_name: string | null;
  upi_id: string | null;            // null for bank_account
  is_primary: boolean;
  is_verified: boolean;             // true = Razorpay Fund Account created
  razorpay_contact_id: string | null;      // e.g. "cont_ABC123"
  razorpay_fund_account_id: string | null; // e.g. "fa_XYZ789"
  created_at: string;               // ISO 8601
  updated_at: string;
}

export interface Payout {
  id: string;              // public_id (UUID string)
  amount: number;          // Net disbursement amount (INR)
  gross_amount: number | null;
  commission_amount: number | null;
  currency: string;        // e.g. "INR"
  period_start: string;    // YYYY-MM-DD
  period_end: string;      // YYYY-MM-DD
  status: PayoutStatus;
  mode: PayoutMode | null;
  transaction_id: string | null;
  razorpay_payout_id: string | null;
  razorpay_fund_account_id: string | null;
  utr: string | null;           // Bank UTR after successful transfer
  failure_reason: string | null;
  notes: string | null;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
  vendor?: PayoutVendor;
  bank_account?: VendorBankAccount;
}

export interface VendorEarningsSummary {
  vendor_public_id: string;
  vendor_name: string | null;
  vendor_email: string;
  period_start: string | null;
  period_end: string | null;
  completed_bookings_count: number;
  gross_booking_amount: number;
  commission_percentage: number;
  commission_amount: number;
  net_earned_amount: number;
  already_disbursed_amount: number;
  pending_payable_amount: number;   // Use this as default "amount" in Create Payout form
}

export interface RazorpayContactResponse {
  id: string;             // e.g. "cont_ABC123"
  entity: string;         // "contact"
  name: string;
  contact: string | null;
  email: string | null;
  type: string;           // "vendor"
  reference_id: string;
  active: boolean;
  already_exists?: boolean; // true = contact was already registered on Razorpay
}

// ─── Request Payloads ─────────────────────────────────────────────────────────

export interface PayoutQueryParams {
  page?: number;
  size?: number;
  vendor_id?: string;
  status?: PayoutStatus;
  period_start?: string;   // YYYY-MM-DD
  period_end?: string;     // YYYY-MM-DD
  sort_order?: 'asc' | 'desc';
}

export interface CalculateEarningsParams {
  vendor_id: string;
  period_start?: string;
  period_end?: string;
  commission_percentage?: number;
}

export interface CreatePayoutPayload {
  vendor_id: string;
  bank_account_id?: string;   // If omitted, uses vendor's primary account
  gross_amount?: number;
  commission_amount?: number;
  amount: number;             // > 0, required
  currency?: string;          // Default "INR"
  period_start: string;       // YYYY-MM-DD, required
  period_end: string;         // YYYY-MM-DD, required
  mode?: PayoutMode;          // Default "NEFT"
  notes?: string;
}

export interface ProcessPayoutPayload {
  mode?: PayoutMode;          // Override payout mode
  purpose?: string;           // Default "payout"
  narration?: string;         // Max 30 chars, appears on bank statement
  notes?: Record<string, string>;
}

export interface CreateBankAccountPayload {
  account_type: BankAccountType;
  account_holder_name: string;
  // Required for bank_account:
  account_number?: string;
  ifsc_code?: string;
  bank_name?: string;
  branch_name?: string;
  // Required for vpa:
  upi_id?: string;
  is_primary?: boolean;       // Default true
  notes?: string;
}

// ─── API Response Wrappers ────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  status_code: number;
  message: string;
  data: T;
}

export interface PaginatedApiResponse<T> extends ApiResponse<T[]> {
  meta: {
    total: number;
    page: number;
    size: number;
    pages: number;
  };
}
```

---

## 5. API Endpoints & Integration Specs

### 5.1 Bank Account Management

#### `GET /api/v1/admin/payouts/vendors/{vendor_id}/bank-accounts`
**List all bank accounts for a vendor.**

- `vendor_id`: Vendor's `public_id` (UUID string)

**Response `200`**:
```json
{
  "success": true,
  "message": "Vendor bank accounts retrieved successfully.",
  "data": [
    {
      "id": "83748291-bb21-42ab-9102-123456789abc",
      "account_type": "bank_account",
      "account_holder_name": "Tashi Dorjee",
      "account_number": "50100234567890",
      "ifsc_code": "HDFC0001234",
      "bank_name": "HDFC Bank",
      "branch_name": "Gangtok",
      "upi_id": null,
      "is_primary": true,
      "is_verified": true,
      "razorpay_contact_id": "cont_N827364823",
      "razorpay_fund_account_id": "fa_9823749283",
      "created_at": "2026-07-01T12:00:00Z",
      "updated_at": "2026-07-01T12:00:00Z"
    }
  ]
}
```

> `is_verified: true` = Fund Account registered on Razorpay. Payouts can be processed automatically.  
> `is_verified: false` = Saved locally only. Payout requires manual processing.

---

#### `POST /api/v1/admin/payouts/vendors/{vendor_id}/bank-accounts`
**Add a new bank account or UPI VPA for a vendor.**

Automatically creates (or reuses) the vendor's Razorpay Contact and registers a Fund Account on RazorpayX.

**Request (Bank Account)**:
```json
{
  "account_type": "bank_account",
  "account_holder_name": "Tashi Dorjee",
  "account_number": "50100234567890",
  "ifsc_code": "HDFC0001234",
  "bank_name": "HDFC Bank",
  "branch_name": "Gangtok MG Marg",
  "is_primary": true
}
```

**Request (UPI VPA)**:
```json
{
  "account_type": "vpa",
  "account_holder_name": "Tashi Dorjee",
  "upi_id": "tashidorjee@okaxis",
  "is_primary": true
}
```

**Validation Rules**:
| account_type | Required Fields |
|---|---|
| `bank_account` | `account_holder_name`, `account_number`, `ifsc_code` |
| `vpa` | `account_holder_name`, `upi_id` |

**Response `201`**: Returns the created `VendorBankAccount` object.

---

#### `PATCH /api/v1/admin/payouts/vendors/{vendor_id}/bank-accounts/{bank_account_id}/primary`
**Set an account as the primary payout destination.**

No request body required. Resets all other accounts for this vendor to non-primary.

**Response `200`**: Updated `VendorBankAccount` object.

---

#### `DELETE /api/v1/admin/payouts/vendors/{vendor_id}/bank-accounts/{bank_account_id}`
**Remove a bank account from a vendor's profile.**

**Response `200`**:
```json
{ "success": true, "message": "Vendor bank account removed successfully.", "data": {} }
```

---

#### `POST /api/v1/admin/payouts/vendors/{vendor_id}/razorpay-contact`
**Manually create or sync a vendor's Razorpay Contact.**

No request body. Uses vendor's stored name, email, and phone.

**Response `201`**:
```json
{
  "success": true,
  "message": "Vendor Razorpay contact processed successfully.",
  "data": {
    "id": "cont_N827364823",
    "name": "Tashi Dorjee",
    "email": "tashi@example.com",
    "contact": "+919876543210",
    "type": "vendor",
    "reference_id": "9938b812-...",
    "already_exists": false
  }
}
```

> `already_exists: true` → Contact already existed on Razorpay; existing ID returned. No duplicate created.

---

### 5.2 Payout Lifecycle

#### `GET /api/v1/admin/payouts/eligible`
**Calculate vendor earnings and pending dues before creating a payout.**

**Query Params**:
| Param | Type | Required | Example |
|---|---|---|---|
| `vendor_id` | `string` | ✅ | UUID |
| `period_start` | `date` | ❌ | `2026-08-01` |
| `period_end` | `date` | ❌ | `2026-08-31` |
| `commission_percentage` | `float` | ❌ | `10.0` |

**Response `200`**:
```json
{
  "success": true,
  "message": "Vendor earnings summary calculated successfully.",
  "data": {
    "vendor_public_id": "9938b812-...",
    "vendor_name": "Tashi Dorjee",
    "vendor_email": "tashi@example.com",
    "period_start": "2026-08-01",
    "period_end": "2026-08-31",
    "completed_bookings_count": 14,
    "gross_booking_amount": 150000.0,
    "commission_percentage": 10.0,
    "commission_amount": 15000.0,
    "net_earned_amount": 135000.0,
    "already_disbursed_amount": 0.0,
    "pending_payable_amount": 135000.0
  }
}
```

> Pre-fill `amount` in the Create Payout form with `pending_payable_amount`.

---

#### `POST /api/v1/admin/payouts/`
**Create a payout record (does NOT send money).**

**Request Body**:
```json
{
  "vendor_id": "9938b812-4211-4fa3-8761-123456789abc",
  "bank_account_id": "83748291-bb21-42ab-9102-123456789abc",
  "gross_amount": 150000.0,
  "commission_amount": 15000.0,
  "amount": 135000.0,
  "currency": "INR",
  "period_start": "2026-08-01",
  "period_end": "2026-08-31",
  "mode": "NEFT",
  "notes": "August 2026 regular settlement"
}
```

**Status Code**: `201 Created`  
**Response**: Returns the payout object with `status: "pending"`.

---

#### `GET /api/v1/admin/payouts/`
**List all payouts with filters.**

**Query Params**:
| Param | Type | Default | Values |
|---|---|---|---|
| `page` | `int` | `1` | |
| `size` | `int` | `10` | |
| `vendor_id` | `string` | — | Vendor UUID |
| `status` | `string` | — | `pending`, `processing`, `queued`, `paid`, `failed`, `reversed`, `rejected`, `cancelled` |
| `period_start` | `date` | — | `YYYY-MM-DD` |
| `period_end` | `date` | — | `YYYY-MM-DD` |
| `sort_order` | `string` | `desc` | `asc`, `desc` |

**Response `200`**: Paginated list with `meta.total`, `meta.page`, `meta.pages`.

---

#### `GET /api/v1/admin/payouts/{payout_id}`
**Get a single payout by its `public_id`.**

**Response `200`**:
```json
{
  "success": true,
  "data": {
    "id": "c1f72922-...",
    "amount": 135000.0,
    "gross_amount": 150000.0,
    "commission_amount": 15000.0,
    "currency": "INR",
    "period_start": "2026-08-01",
    "period_end": "2026-08-31",
    "status": "paid",
    "mode": "NEFT",
    "razorpay_payout_id": "pout_M2983749823",
    "utr": "HDFCN26228392182",
    "failure_reason": null,
    "paid_at": "2026-08-16T10:45:00Z",
    "vendor": { "id": "...", "email": "...", "full_name": "..." },
    "bank_account": { "id": "...", "account_type": "bank_account", "is_verified": true, ... }
  }
}
```

---

#### `POST /api/v1/admin/payouts/{payout_id}/process`
**Submit payout to RazorpayX — SENDS REAL MONEY.**

**Request Body (all optional)**:
```json
{
  "mode": "NEFT",
  "narration": "August Vendor Payout",
  "notes": { "batch_ref": "BATCH-2026-08" }
}
```

> `narration` is truncated to **30 characters** — it appears on the vendor's bank statement.

**Response `200`**: Updated payout with `status: "processing"` or `"queued"` and `razorpay_payout_id` set.

---

#### `POST /api/v1/admin/payouts/{payout_id}/sync`
**Fetch latest status from Razorpay and update local record.**

No request body. Call this to transition payout from `processing` → `paid` / `failed`.

**Response `200`**: Updated payout with latest `status`, `utr`, and `failure_reason`.

---

#### `POST /api/v1/admin/payouts/{payout_id}/cancel`
**Cancel a queued payout on Razorpay.**

Only works for payouts in `queued` status. No request body.

**Response `200`**: Updated payout with `status: "cancelled"`.

---

## 6. Status Badges & Action Matrix

### 6.1 Status Color Palette

| Status | Badge Style (Tailwind) | Description |
|:---|:---|:---|
| `pending` | `bg-amber-100 text-amber-800 border-amber-300` | Created, not yet processed |
| `processing` | `bg-blue-100 text-blue-800 border-blue-300 animate-pulse` | Submitted to Razorpay |
| `queued` | `bg-orange-100 text-orange-800 border-orange-300` | Queued by Razorpay (low balance) |
| `paid` | `bg-emerald-100 text-emerald-800 border-emerald-300` | Settled — show UTR number |
| `failed` | `bg-rose-100 text-rose-800 border-rose-300` | Bank rejected / transfer failed |
| `rejected` | `bg-red-100 text-red-800 border-red-300` | Razorpay risk rejection |
| `reversed` | `bg-purple-100 text-purple-800 border-purple-300` | Reversed by bank |
| `cancelled` | `bg-slate-100 text-slate-700 border-slate-300` | Cancelled by admin |

### 6.2 Action Button Availability by Status

| Status | Process / Disburse | Sync Status | Cancel | View Details |
|:---|:---:|:---:|:---:|:---:|
| **`pending`** | ✅ Enabled | ❌ | ✅ Enabled | ✅ |
| **`processing`** | ❌ | ✅ Enabled | ❌ | ✅ |
| **`queued`** | ❌ | ✅ Enabled | ✅ Enabled | ✅ |
| **`paid`** | ❌ | ❌ | ❌ | ✅ |
| **`failed`** | ✅ Retry | ✅ Enabled | ✅ Enabled | ✅ |
| **`reversed`** | ❌ | ❌ | ❌ | ✅ |
| **`rejected`** | ❌ | ❌ | ❌ | ✅ |
| **`cancelled`** | ❌ | ❌ | ❌ | ✅ |

---

## 7. Error Handling & Edge Cases

| `error_code` | HTTP | Frontend Action |
|:---|:---:|:---|
| `VENDOR_NOT_FOUND` | 404 | Toast: *"The specified vendor was not found."* |
| `BANK_ACCOUNT_NOT_FOUND` | 404 | Toast: *"The specified bank account was not found."* |
| `BANK_DETAILS_REQUIRED` | 422 | Highlight `account_number` + `ifsc_code` fields with inline error |
| `UPI_ID_REQUIRED` | 422 | Highlight `upi_id` field with inline error |
| `INVALID_ACCOUNT_TYPE` | 422 | Show: *"Account type must be 'bank_account' or 'vpa'."* |
| `INVALID_AMOUNT` | 422 | Highlight `amount` field: *"Amount must be greater than 0."* |
| `INVALID_MODE` | 422 | Reset mode selector: *"Mode must be NEFT, IMPS, RTGS, or UPI."* |
| `INVALID_STATUS` | 422 | Reset filter to "All" |
| `RAZORPAY_NOT_CONFIGURED` | 500 | Banner: *"Payment gateway is not configured. Contact system admin."* |
| `RAZORPAYX_ACCOUNT_NOT_CONFIGURED` | 500 | Banner: *"RazorpayX source account number is not configured."* |
| `RAZORPAY_CONTACT_CREATION_FAILED` | varies | Toast warning: *"Razorpay contact could not be created. Account saved locally."* |
| `RAZORPAY_FUND_ACCOUNT_FAILED` | varies | Toast warning: *"Razorpay fund account creation failed. Account saved locally — manual processing required."* |
| `RAZORPAY_PAYOUT_FAILED` | varies | Show inline error with Razorpay error message. Allow retry. |
| `RAZORPAY_PAYOUT_CANCEL_FAILED` | varies | Toast: *"Payout could not be cancelled — it may have already been processed."* |

### Special Cases

- **`is_verified: false` bank account**: Show a yellow warning badge on the account in the dropdown. Add tooltip: *"Not verified on Razorpay — payout will require manual processing."*
- **`already_exists: true` from Razorpay contact endpoint**: Show info toast: *"Razorpay contact already exists — using existing contact."*
- **Narration truncation**: Add a character counter (x/30) to the narration input in the Process modal.
- **Idempotency**: The backend uses `X-Payout-Idempotency` internally. Do not retry `POST /{id}/process` unless the payout `status` is still `pending` or `failed`.

