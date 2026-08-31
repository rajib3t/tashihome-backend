# Frontend Integration & UI Layout Guide: Admin Payout Management

This document provides the frontend engineering team with the complete **UI/UX Component Layouts, Screen Wireframes, TypeScript Interfaces, API Payloads, and State Management Rules** for building the **Admin Payout Management** module.

---

## Table of Contents
1. [Module Architecture & Navigation](#1-module-architecture--navigation)
2. [Screen Layouts & UI Wireframes](#2-screen-layouts--ui-wireframes)
   - [2.1 Payouts Dashboard & Table View](#21-payouts-dashboard--table-view)
   - [2.2 Create Payout / Dues Calculator Modal](#22-create-payout--dues-calculator-modal)
   - [2.3 Payout Details & Timeline Drawer](#23-payout-details--timeline-drawer)
   - [2.4 Vendor Bank Account Management Modal](#24-vendor-bank-account-management-modal)
3. [TypeScript Type Definitions](#3-typescript-type-definitions)
4. [API Endpoints & Integration Specs](#4-api-endpoints--integration-specs)
5. [Status Badges & Action Matrix](#5-status-badges--action-matrix)
6. [Error Handling & Edge Cases](#6-error-handling--edge-cases)

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

## 2. Screen Layouts & UI Wireframes

### 2.1 Payouts Dashboard & Table View
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

### 2.2 Create Payout / Dues Calculator Modal
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
|  | Already Disbursed Amount:  -₹        0.00                                        |  |
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

---

### 2.3 Payout Details & Timeline Drawer
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
| Razorpay Fund A/C: fa_Nq98xK198d                                                  |
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

### 2.4 Vendor Bank Account Management Modal
**Triggered by**: Clicking `(+ Add / Change Bank Account)` or managing host settings.

```
+--------------------------------------------------------------------+
|  Add Vendor Payout Account                                     [X] |
+--------------------------------------------------------------------+
|  Account Type:        (●) Bank Account       ( ) UPI VPA           |
|                                                                    |
|  Account Holder Name: [ Tashi Dorjee                             ] |
|  Bank Name:           [ HDFC Bank                                ] |
|  Account Number:      [ 50100234567890                           ] |
|  Confirm A/C Number:  [ 50100234567890                           ] |
|  IFSC Code:           [ HDFC0001234                              ] |
|  Branch Name:         [ Gangtok MG Marg                          ] |
|                                                                    |
|  [x] Set as Primary Payout Account                                 |
+--------------------------------------------------------------------+
|  [ Cancel ]                                       [ Save Account ] |
+--------------------------------------------------------------------+
```

---

## 3. TypeScript Type Definitions

Save in `types/payout.ts` or `src/api/types/payout.ts`:

```typescript
export type PayoutStatus =
  | 'pending'
  | 'processing'
  | 'paid'
  | 'failed'
  | 'reversed'
  | 'rejected'
  | 'cancelled';

export type PayoutMode = 'NEFT' | 'IMPS' | 'RTGS' | 'UPI';

export type BankAccountType = 'bank_account' | 'vpa';

export interface PayoutVendor {
  public_id: string;
  email: string;
  phone: string | null;
  full_name: string | null;
}

export interface VendorBankAccount {
  public_id: string;
  account_type: BankAccountType;
  account_holder_name: string;
  account_number: string | null;
  ifsc_code: string | null;
  bank_name: string | null;
  branch_name: string | null;
  upi_id: string | null;
  is_primary: boolean;
  is_verified: boolean;
  razorpay_contact_id: string | null;
  razorpay_fund_account_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Payout {
  public_id: string;
  amount: number; // Net amount in INR
  gross_amount: number | null;
  commission_amount: number | null;
  currency: string;
  period_start: string; // YYYY-MM-DD
  period_end: string;   // YYYY-MM-DD
  status: PayoutStatus;
  mode: PayoutMode;
  transaction_id: string | null;
  razorpay_payout_id: string | null;
  razorpay_fund_account_id: string | null;
  utr: string | null;
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
  pending_payable_amount: number;
}

export interface PayoutQueryParams {
  page?: number;
  size?: number;
  vendor_id?: string;
  status?: PayoutStatus;
  period_start?: string;
  period_end?: string;
  sort_order?: 'asc' | 'desc';
}

export interface CreatePayoutPayload {
  vendor_id: string;
  bank_account_id?: string;
  gross_amount?: number;
  commission_amount?: number;
  amount: number;
  currency?: string;
  period_start: string;
  period_end: string;
  mode?: PayoutMode;
  notes?: string;
}

export interface ProcessPayoutPayload {
  mode?: PayoutMode;
  narration?: string;
  notes?: Record<string, string>;
}

export interface CreateBankAccountPayload {
  account_type: BankAccountType;
  account_holder_name: string;
  account_number?: string;
  ifsc_code?: string;
  bank_name?: string;
  branch_name?: string;
  upi_id?: string;
  is_primary?: boolean;
  notes?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  status_code: number;
  message: string;
  data: T;
  meta?: {
    total: number;
    page: number;
    page_size: number;
    pages: number;
  };
}
```

---

## 4. API Endpoints & Integration Specs

Base URL: `/api/v1/admin/payouts`  
Headers: `Authorization: Bearer <ADMIN_ACCESS_TOKEN>`

### 4.1 List All Payouts
- **Method / Endpoint**: `GET /api/v1/admin/payouts`
- **Query Params**: `page=1&size=10&status=paid&sort_order=desc`
- **Response Sample**:
```json
{
  "success": true,
  "status_code": 200,
  "message": "Payouts retrieved successfully.",
  "data": [
    {
      "public_id": "c1f72922-38b2-4d2c-9a43-982736172831",
      "amount": 45000.0,
      "gross_amount": 50000.0,
      "commission_amount": 5000.0,
      "currency": "INR",
      "period_start": "2026-08-01",
      "period_end": "2026-08-15",
      "status": "paid",
      "mode": "NEFT",
      "transaction_id": "pout_M2983749823",
      "razorpay_payout_id": "pout_M2983749823",
      "razorpay_fund_account_id": "fa_9823749283",
      "utr": "HDFCN26228392182",
      "failure_reason": null,
      "notes": "Settlement for August 1st half",
      "paid_at": "2026-08-16T10:45:00Z",
      "created_at": "2026-08-16T10:40:00Z",
      "updated_at": "2026-08-16T10:45:00Z",
      "vendor": {
        "public_id": "9938b812-4211-4fa3-8761-123456789abc",
        "email": "tashi.dorjee@example.com",
        "phone": "+919876543210",
        "full_name": "Tashi Dorjee"
      },
      "bank_account": {
        "public_id": "83748291-bb21-42ab-9102-123456789abc",
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
    }
  ],
  "meta": {
    "total": 48,
    "page": 1,
    "page_size": 10,
    "pages": 5
  }
}
```

---

### 4.2 Calculate Eligible Dues & Earnings for a Vendor
- **Method / Endpoint**: `GET /api/v1/admin/payouts/eligible`
- **Query Params**:
  - `vendor_id`: UUID (Required)
  - `period_start`: `2026-08-01` (Optional)
  - `period_end`: `2026-08-31` (Optional)
  - `commission_percentage`: `10.0` (Optional, defaults to backend setting `10%`)
- **Response Sample**:
```json
{
  "success": true,
  "status_code": 200,
  "message": "Vendor earnings summary calculated successfully.",
  "data": {
    "vendor_public_id": "9938b812-4211-4fa3-8761-123456789abc",
    "vendor_name": "Tashi Dorjee",
    "vendor_email": "tashi.dorjee@example.com",
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

---

### 4.3 Create Payout Record
- **Method / Endpoint**: `POST /api/v1/admin/payouts`
- **Request Body**:
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
- **Status Code**: `201 Created`

---

### 4.4 Process Payout (Disburse via RazorpayX)
- **Method / Endpoint**: `POST /api/v1/admin/payouts/{payout_id}/process`
- **Request Body (Optional)**:
```json
{
  "mode": "NEFT",
  "narration": "August Payout",
  "notes": {
    "internal_batch": "BATCH-2026-08"
  }
}
```
- **Response Sample**:
```json
{
  "success": true,
  "status_code": 200,
  "message": "Payout submitted to Razorpay successfully.",
  "data": {
    "public_id": "c1f72922-38b2-4d2c-9a43-982736172831",
    "amount": 135000.0,
    "status": "processing",
    "razorpay_payout_id": "pout_M2983749823",
    "mode": "NEFT",
    "utr": null,
    "paid_at": null
  }
}
```

---

### 4.5 Sync Payout Live Status from Razorpay
- **Method / Endpoint**: `POST /api/v1/admin/payouts/{payout_id}/sync`
- **Response Sample**: Returns updated payout with latest status and `utr` populated when processed by bank.

---

### 4.6 Cancel Payout
- **Method / Endpoint**: `POST /api/v1/admin/payouts/{payout_id}/cancel`

---

### 4.7 Manage Vendor Bank Accounts
- **List Accounts**: `GET /api/v1/admin/payouts/vendors/{vendor_id}/bank-accounts`
- **Add Account**: `POST /api/v1/admin/payouts/vendors/{vendor_id}/bank-accounts`
  - **Body (Bank Account)**:
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
  - **Body (UPI VPA)**:
    ```json
    {
      "account_type": "vpa",
      "account_holder_name": "Tashi Dorjee",
      "upi_id": "tashidorjee@okaxis",
      "is_primary": true
    }
    ```

---

## 5. Status Badges & Action Matrix

### 5.1 Status Color Palette

| Status | Badge Color (Tailwind) | Description |
| :--- | :--- | :--- |
| `pending` | `bg-amber-100 text-amber-800 border-amber-300` | Payout created in system, not yet sent to bank |
| `processing` | `bg-blue-100 text-blue-800 border-blue-300 animate-pulse` | In-flight in Razorpay / Banking queue |
| `paid` | `bg-emerald-100 text-emerald-800 border-emerald-300` | Successfully settled in vendor bank account with UTR |
| `failed` | `bg-rose-100 text-rose-800 border-rose-300` | Bank rejected / invalid IFSC / transfer failed |
| `rejected` | `bg-red-100 text-red-800 border-red-300` | Razorpay risk rejection |
| `reversed` | `bg-purple-100 text-purple-800 border-purple-300` | Debited but reversed back to platform account |
| `cancelled` | `bg-slate-100 text-slate-700 border-slate-300` | Cancelled by admin before transfer |

---

### 5.2 Action Button Availability by Status

| Status | [ Process / Disburse ] | [ Sync Status ] | [ Cancel ] | [ View Details ] |
| :--- | :---: | :---: | :---: | :---: |
| **`pending`** | ✅ Enabled | ❌ Disabled | ✅ Enabled | ✅ Enabled |
| **`processing`** | ❌ Disabled | ✅ Enabled | ⚠️ If queued | ✅ Enabled |
| **`paid`** | ❌ Disabled | ❌ Disabled | ❌ Disabled | ✅ Enabled |
| **`failed`** | ✅ Retry | ✅ Enabled | ✅ Enabled | ✅ Enabled |
| **`cancelled`**| ❌ Disabled | ❌ Disabled | ❌ Disabled | ✅ Enabled |

---

## 6. Error Handling & Edge Cases

| Error Code | HTTP Status | Frontend Action / Message to User |
| :--- | :---: | :--- |
| `VENDOR_BANK_ACCOUNT_MISSING` | `400` | Open "Add Bank Account" modal with prompt: *"Vendor has no bank account configured. Please add bank details first."* |
| `PAYMENT_DISABLED` | `400` | Show warning banner: *"Payment processing is temporarily disabled in system settings."* |
| `PAYOUT_ALREADY_PROCESSED` | `400` | Toast error: *"This payout has already been processed or is currently in-flight."* |
| `RAZORPAYX_ACCOUNT_NOT_CONFIGURED` | `500` | Toast error: *"Platform RazorpayX account number is not configured in backend."* |
| `INVALID_BANK_DETAILS` | `400` | Highlight IFSC / Account Number input fields with error message. |

