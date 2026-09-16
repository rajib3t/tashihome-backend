# Frontend Integration & UI Layout Guide: Taxes & System Settings

This document provides the frontend engineering team with the complete **UI/UX Component Layouts, Screen Wireframes, TypeScript Interfaces, API Payloads, Validation Rules, and Integration Specifications** for building the **Tax & GST Management** and **System Settings** modules.

> **Last Updated**: 2026-09-06  
> **Base URL (Admin Taxes)**: `/api/v1/admin/taxes`  
> **Base URL (Public Taxes)**: `/api/v1/public/taxes`  
> **Base URL (Admin Settings)**: `/api/v1/admin/settings`  
> **Base URL (Public Settings)**: `/api/v1/public/settings`  
> **Auth**: `Authorization: Bearer <ADMIN_ACCESS_TOKEN>` for `/admin/*` routes; Public routes are unauthenticated.

---

## Table of Contents
1. [Module Architecture & Navigation](#1-module-architecture--navigation)
2. [Data Flow Diagrams](#2-data-flow-diagrams)
3. [Screen Layouts & UI Wireframes](#3-screen-layouts--ui-wireframes)
   - [3.1 Admin Tax & GST Dashboard](#31-admin-tax--gst-dashboard)
   - [3.2 Create / Edit Tax Modal](#32-create--edit-tax-modal)
   - [3.3 Admin System Settings Page (Tabbed)](#33-admin-system-settings-page-tabbed)
   - [3.4 Guest Checkout Price Summary Component](#34-guest-checkout-price-summary-component)
4. [TypeScript Type Definitions](#4-typescript-type-definitions)
5. [API Endpoints & Integration Specs](#5-api-endpoints--integration-specs)
   - [5.1 Tax Management APIs](#51-tax-management-apis)
   - [5.2 System Settings APIs](#52-system-settings-apis)
6. [Tax Calculation Formulas](#6-tax-calculation-formulas)
7. [Validation & Input Guidelines](#7-validation--input-guidelines)
8. [State Management & Integration Hooks](#8-state-management--integration-hooks)

---

## 1. Module Architecture & Navigation

The settings and tax modules reside under the **Admin Portal** and **Public / Guest Web App**:

```
Admin Navigation
└── ⚙️ System Settings
    ├── 🏢 General & Platform Settings (/admin/settings)
    ├── 🧾 Tax & GST Rates (/admin/settings/taxes)
    └── ⏳ Maintenance & Coming Soon (/admin/settings?tab=coming-soon)

Public Web App / Mobile Web
├── 🌐 App Bootloader: Fetches GET /api/v1/public/settings (App Name, Currency, Logos, SEO)
├── 🏨 Property Listing & Detail: Fetches GET /api/v1/public/taxes/default for tax badges
└── 💳 Booking Checkout: Dynamic price breakdown using active tax configuration
```

---

## 2. Data Flow Diagrams

### Tax & GST Configuration & Booking Flow
```
┌─────────────────────────────────┐
│ Admin Tax Management            │
│ POST /api/v1/admin/taxes        │ (Sets GST Rate, GSTIN, SAC, Inclusive/Exclusive)
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Database (taxes table)          │
└──────────────┬──────────────────┘
               │
               ├──────────────────────────────────────────┐
               ▼                                          ▼
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│ Public Web App                  │     │ Backend Booking Service          │
│ GET /api/v1/public/taxes        │     │ Quote calculation & Invoicing    │
│ Displays itemized GST breakdown │     │ Applies default active GST rate  │
└─────────────────────────────────┘     └──────────────────────────────────┘
```

---

## 3. Screen Layouts & UI Wireframes

### 3.1 Admin Tax & GST Dashboard
**Route**: `/admin/settings/taxes`

```
+---------------------------------------------------------------------------------------------------------+
| [ Settings ] / Taxes & GST                                               [ + Add New Tax ]  [ 🔄 Refresh ]|
+---------------------------------------------------------------------------------------------------------+
| [ STATS / OVERVIEW CARDS ]                                                                              |
| +---------------------+  +---------------------+  +---------------------+  +---------------------+      |
| | Default Tax Rate    |  | Active Tax Rules    |  | Business GSTIN      |  | SAC Code            |      |
| | 12.00% (GST_12)     |  | 2 Active Rules      |  | 27ABCDE1234F1Z5     |  | 996311 (Lodging)    |      |
| +---------------------+  +---------------------+  +---------------------+  +---------------------+      |
+---------------------------------------------------------------------------------------------------------+
| [ FILTERS & SEARCH ]                                                                                    |
| [🔍 Search by Name, Code, GSTIN... ]  [ Status: All ▼ ]  [ Type: All ▼ ]  [ Clear Filters ]              |
+---------------------------------------------------------------------------------------------------------+
| [ TAX RULES TABLE ]                                                                                     |
| Code     | Name           | Rate (%) | Type        | Inclusive? | Default | Status   | Actions           |
|----------+----------------+----------+-------------+------------+---------+----------+-------------------|
| GST_12   | Standard GST   | 12.00%   | Percentage  | No (Add-on)| [★ YES] | [Active] | [✏️] [⚙️] [🗑️]    |
| GST_18   | Luxury GST     | 18.00%   | Percentage  | No (Add-on)| [  NO ] | [Active] | [✏️] [⚙️] [🗑️]    |
| GST_EX   | Exempted / Nil | 0.00%    | Percentage  | Yes        | [  NO ] | [Inactive| [✏️] [⚙️] [🗑️]    |
+---------------------------------------------------------------------------------------------------------+
| Showing 1-3 of 3 tax rules                                                       [ < Previous ] [ Next > ]|
+---------------------------------------------------------------------------------------------------------+
```

---

### 3.2 Create / Edit Tax Modal
**Triggered by**: `[ + Add New Tax ]` or `[ ✏️ Edit ]`

```
+-----------------------------------------------------------------------------------+
| Create Tax / GST Rule                                                         [X] |
+-----------------------------------------------------------------------------------+
|  Tax Name *                          Tax Code * (Uppercase, e.g. GST_12)           |
|  [ Standard GST 12%            ]     [ GST_12                         ]           |
|                                                                                   |
|  Tax Rate (%) *                      Tax Type *                                   |
|  [ 12.00                       ]     (•) Percentage (%)    ( ) Fixed Amount       |
|                                                                                   |
|  [ ] Price is inclusive of tax       [X] Set as system default tax rate           |
|                                                                                   |
| ── GST Compliance Details (Optional) ─────────────────────────────────────────── |
|  Business GSTIN                      SAC / HSN Code                               |
|  [ 27ABCDE1234F1Z5             ]     [ 996311                         ]           |
|                                                                                   |
|  Registered Legal Business Name                                                   |
|  [ Tashi Homes Hospitality Private Limited                     ]                  |
|                                                                                   |
|  Registered Tax Address                                                           |
|  [ Plot 42, Green Valley Hills, Gangtok, Sikkim - 737101        ]                 |
|                                                                                   |
| ── Component Breakdown (For Itemized Invoices) ────────────────────────────────── |
|  CGST Rate (%)        SGST Rate (%)        IGST Rate (%)                          |
|  [ 6.00            ]  [ 6.00            ]  [ 12.00           ]                    |
|                                                                                   |
|  Description / Notes                                                              |
|  [ Standard GST applied on homestay rooms under ₹7,500/night   ]                  |
|                                                                                   |
|  Status                                                                           |
|  [ Active                    ▼ ]                                                  |
|                                                                                   |
|                                                   [ Cancel ]    [ Save Tax Rule ] |
+-----------------------------------------------------------------------------------+
```

---

### 3.3 Admin System Settings Page (Tabbed)
**Route**: `/admin/settings`

```
+---------------------------------------------------------------------------------------------------------+
| System Settings                                                                       [ Save Changes 💾 ]|
+---------------------------------------------------------------------------------------------------------+
|  [🏢 General & Brand]  |  [📞 Contact & Support]  |  [🏡 Homestay & Booking]  |  [🌐 Social & SEO]  |  [⏳ Coming Soon] |
+---------------------------------------------------------------------------------------------------------+
| TAB 1: General & Brand                                                                                  |
|  App Display Name *                                  Default Currency        Currency Symbol            |
|  [ Tashi Homes                               ]       [ INR                ]  [ ₹              ]         |
|                                                                                                         |
|  Timezone                                            Date Format             Time Format                |
|  [ Asia/Kolkata (UTC+05:30)                ▼ ]       [ DD/MM/YYYY       ▼ ]  [ 12 Hours (AM/PM) ▼ ]     |
|                                                                                                         |
|  Primary Brand Logo                                  White / Dark Background Logo                       |
|  +---------------------------+  [ Choose File ]      +---------------------------+  [ Choose File ]     |
|  | [ Current Logo Preview ]  |                       | [ White Logo Preview ]    |                      |
|  +---------------------------+                       +---------------------------+                      |
|                                                                                                         |
|  Browser Favicon (.ico, .png)                                                                           |
|  +-------------+  [ Choose File ]                                                                       |
|  | [ Favicon ] |                                                                                        |
|  +-------------+                                                                                        |
+---------------------------------------------------------------------------------------------------------+
| TAB 2: Contact & Support                                                                                |
|  Support Email                                       Support Phone                                      |
|  [ support@tashihomes.in                     ]       [ +91 9876543210                 ]                 |
|                                                                                                         |
|  Office / Contact Address                                                                               |
|  [ MG Marg, Gangtok, Sikkim - 737101, India                                   ]                         |
+---------------------------------------------------------------------------------------------------------+
| TAB 3: Homestay & Booking Financials                                                                    |
|  Platform Commission (%)                             Guest Service Fee (%)                              |
|  [ 10.00                       ]                     [ 0.00                           ]                 |
|                                                                                                         |
|  Standard Check-in Time                              Standard Check-out Time                            |
|  [ 14:00 (2:00 PM)             ]                     [ 11:00 (11:00 AM)               ]                 |
|                                                                                                         |
|  Minimum Stay (Days)                                 Maximum Stay (Days)                                |
|  [ 1                           ]                     [ 30                             ]                 |
|                                                                                                         |
|  Cancellation Grace Period (Hours)                                                                      |
|  [ 24                          ]                                                                        |
+---------------------------------------------------------------------------------------------------------+
| TAB 4: Social & SEO                                                                                     |
|  Facebook URL               Instagram URL               Twitter / X URL                                 |
|  [ https://facebook.com/... ] [ https://instagram.com/.. ] [ https://x.com/tashihomes... ]             |
|                                                                                                         |
|  Meta Title                                          Meta Keywords                                      |
|  [ Tashi Homes - Premium Homestays & Stays  ]        [ homestay, sikkim, luxury stays ]                 |
|                                                                                                         |
|  Meta Description                                                                                       |
|  [ Discover handpicked homestays and heritage retreats across Northeast India. ]                        |
|                                                                                                         |
|  OG / Social Preview Image (Max 3MB, 1200x630px recommended)                                            |
|  +---------------------------------------------+  [ Upload OG Image ]                                    |
|  | [ OG Social Preview Image Banner ]           |                                                        |
|  +---------------------------------------------+                                                        |
+---------------------------------------------------------------------------------------------------------+
```

---

### 3.4 Guest Checkout Price Summary Component

```
+-------------------------------------------------------+
| Price Summary                                         |
+-------------------------------------------------------+
| ₹ 2,500.00 × 2 Nights × 1 Room            ₹ 5,000.00  |
| Discount                                    − ₹ 0.00  |
| GST / Tax (12% Standard GST)                + ₹ 600.00|
|   ├ CGST (6%): ₹ 300.00                               |
|   └ SGST (6%): ₹ 300.00                               |
|-------------------------------------------------------|
| Total Payable (INR)                       ₹ 5,600.00  |
| [✓] Includes all mandatory taxes & local levies       |
+-------------------------------------------------------+
| [ Proceed to Secure Payment ]                         |
+-------------------------------------------------------+
```

---

## 4. TypeScript Type Definitions

Save in `src/types/settings.ts` & `src/types/tax.ts`:

```typescript
// ==========================================
// Tax & GST Type Definitions
// ==========================================

export type TaxStatus = 'active' | 'inactive';
export type TaxType = 'percentage' | 'fixed';

export interface TaxItem {
  id: string; // UUID (public_id)
  name: string;
  code: string;
  rate: number;
  tax_type: TaxType;
  is_inclusive: boolean;
  is_default: boolean;
  gst_number?: string | null;
  legal_name?: string | null;
  address?: string | null;
  hsn_sac_code?: string | null;
  cgst_rate?: number | null;
  sgst_rate?: number | null;
  igst_rate?: number | null;
  description?: string | null;
  status: TaxStatus;
  created_at?: string;
  updated_at?: string;
}

export interface TaxCreatePayload {
  name: string;
  code: string;
  rate: number;
  tax_type?: TaxType;
  is_inclusive?: boolean;
  is_default?: boolean;
  gst_number?: string;
  legal_name?: string;
  address?: string;
  hsn_sac_code?: string;
  cgst_rate?: number;
  sgst_rate?: number;
  igst_rate?: number;
  description?: string;
  status?: TaxStatus;
}

export type TaxUpdatePayload = Partial<TaxCreatePayload>;

export interface TaxQueryFilters {
  page?: number;
  size?: number;
  search?: string;
  status?: TaxStatus;
  is_default?: boolean;
}

// ==========================================
// System Settings Type Definitions
// ==========================================

export interface SettingItem {
  name: string;
  value: string | null;
}

export interface SystemSettingsMap {
  // Branding & General
  app_name?: string;
  app_logo?: string;
  white_logo?: string;
  app_favicon?: string;
  app_timezone?: string;
  app_date_format?: string;
  app_time_format?: string;
  default_currency?: string;
  currency_symbol?: string;

  // Contact & Support
  contact_email?: string;
  contact_phone?: string;
  contact_address?: string;
  contact_whatsapp?: string;

  // Homestay & Booking Financials
  default_commission_percentage?: string | number;
  service_fee_percentage?: string | number;
  check_in_time?: string;
  check_out_time?: string;
  min_booking_days?: string | number;
  max_booking_days?: string | number;
  cancellation_grace_period_hours?: string | number;

  // Social Links
  facebook_url?: string;
  instagram_url?: string;
  twitter_url?: string;
  linkedin_url?: string;
  youtube_url?: string;

  // SEO & Policies
  meta_title?: string;
  meta_description?: string;
  meta_keywords?: string;
  meta_image?: string;
  og_image?: string;
  terms_and_conditions_url?: string;
  privacy_policy_url?: string;
  refund_policy_url?: string;

  // Coming Soon
  is_enabled_coming_soon?: string | boolean;
  launch_date?: string;
  coming_soon_message?: string;
  coming_background_image?: string;
  coming_soon_video?: string;
}
```

---

## 5. API Endpoints & Integration Specs

### 5.1 Tax Management APIs

#### 1. List All Taxes (Admin)
- **Endpoint**: `GET /api/v1/admin/taxes`
- **Query Params**: `page=1`, `size=20`, `search=GST`, `status=active`, `is_default=true`
- **Response**:
```json
{
  "success": true,
  "message": "Taxes retrieved successfully.",
  "data": [
    {
      "id": "7b08e2d4-1a9c-4e89-8d7b-9c3f81e05d21",
      "name": "Standard GST",
      "code": "GST_12",
      "rate": 12.0,
      "tax_type": "percentage",
      "is_inclusive": false,
      "is_default": true,
      "gst_number": "27ABCDE1234F1Z5",
      "legal_name": "Tashi Homes Hospitality",
      "address": "MG Marg, Gangtok",
      "hsn_sac_code": "996311",
      "cgst_rate": 6.0,
      "sgst_rate": 6.0,
      "igst_rate": 12.0,
      "description": "Standard 12% GST on room stays",
      "status": "active",
      "created_at": "2026-09-06T18:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "size": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

#### 2. Create Tax (Admin)
- **Endpoint**: `POST /api/v1/admin/taxes`
- **Headers**: `Content-Type: application/json`
- **Request Body**: `TaxCreatePayload`
- **Response**: `201 Created` with `TaxItem` in `data`.

#### 3. Update Tax (Admin)
- **Endpoint**: `PUT /api/v1/admin/taxes/{tax_id}`
- **Request Body**: `TaxUpdatePayload`

#### 4. Update Status (Admin)
- **Endpoint**: `PATCH /api/v1/admin/taxes/{tax_id}/status`
- **Request Body**:
```json
{
  "status": "inactive"
}
```

#### 5. Delete Tax (Admin)
- **Endpoint**: `DELETE /api/v1/admin/taxes/{tax_id}?hard=false`
- `hard=false` (default): Sets status to `inactive` (soft delete).
- `hard=true`: Permanently deletes record.

#### 6. Get Public Taxes (Public)
- **Endpoint**: `GET /api/v1/public/taxes`
- Returns all active taxes for public use.

#### 7. Get Default Tax (Public)
- **Endpoint**: `GET /api/v1/public/taxes/default`
- Returns the current default system tax rate.

---

### 5.2 System Settings APIs

#### 1. Save / Update System Settings (Admin)
- **Endpoint**: `POST /api/v1/admin/settings`
- **Content-Type**: `multipart/form-data` (due to optional file uploads)
- **Form Fields**: Any or all keys from `SystemSettingsUpdatePayload`, plus file fields (`app_logo`, `white_logo`, `app_favicon`, `og_image` / `meta_image`, `coming_background_image`, `coming_soon_video`).
- **Tab URL Synchronization**: Tab state persists in the browser address bar query string: `/admin/setting?tab=general|contact|financials|seo|coming-soon`. Deep-linking and refreshing retains the active tab.
- **Response**:
```json
{
  "success": true,
  "message": "Settings saved successfully",
  "data": [
    { "name": "app_name", "value": "Tashi Homes" },
    { "name": "default_currency", "value": "INR" },
    { "name": "currency_symbol", "value": "₹" },
    { "name": "app_logo", "value": "https://cdn.tashihomes.in/settings/app_logo_abc.webp" }
  ]
}
```

#### 2. Fetch System Settings (Admin)
- **Endpoint**: `GET /api/v1/admin/settings/fetch`
- **Response**: Returns array of `{ name: string, value: string }` settings.

#### 3. Fetch Public System Settings (Public)
- **Endpoint**: `GET /api/v1/public/settings`
- **Usage**: Call on app load to initialize theme, branding, contact links, currency symbol, and check coming soon status.

---

## 6. Tax Calculation Formulas

Use these client-side helpers to mirror the backend calculation:

```typescript
export interface PriceCalculationResult {
  baseAmount: number;
  discountAmount: number;
  taxAmount: number;
  totalAmount: number;
  cgstAmount?: number;
  sgstAmount?: number;
}

export function calculateBookingPrice(
  pricePerNight: number,
  nights: number,
  numRooms: number = 1,
  discount: number = 0,
  tax?: {
    rate: number;
    isInclusive: boolean;
    cgstRate?: number | null;
    sgstRate?: number | null;
  }
): PriceCalculationResult {
  const baseAmount = Math.round(pricePerNight * numRooms * nights * 100) / 100;
  const taxableBase = Math.max(0, baseAmount - discount);

  if (!tax || tax.rate <= 0) {
    return {
      baseAmount,
      discountAmount: discount,
      taxAmount: 0,
      totalAmount: taxableBase,
    };
  }

  if (tax.isInclusive) {
    // Net base before tax = Total / (1 + Rate/100)
    const netBase = taxableBase / (1 + tax.rate / 100);
    const taxAmount = Math.round((taxableBase - netBase) * 100) / 100;
    return {
      baseAmount,
      discountAmount: discount,
      taxAmount,
      totalAmount: taxableBase,
    };
  } else {
    // Exclusive: Tax = TaxableBase * (Rate / 100)
    const taxAmount = Math.round(taxableBase * (tax.rate / 100) * 100) / 100;
    const cgstAmount = tax.cgstRate
      ? Math.round(taxableBase * (tax.cgstRate / 100) * 100) / 100
      : undefined;
    const sgstAmount = tax.sgstRate
      ? Math.round(taxableBase * (tax.sgstRate / 100) * 100) / 100
      : undefined;

    return {
      baseAmount,
      discountAmount: discount,
      taxAmount,
      totalAmount: Math.round((taxableBase + taxAmount) * 100) / 100,
      cgstAmount,
      sgstAmount,
    };
  }
}
```

---

## 7. Validation & Input Guidelines

1. **GSTIN Format**:
   - Regex: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`
   - Example: `27ABCDE1234F1Z5`
2. **SAC / HSN Code**:
   - Standard Indian SAC code for hotel/homestay accommodation is `996311`.
3. **Tax Code**:
   - Always uppercase alphanumeric with underscores (e.g., `GST_12`, `GST_18`, `LUXURY_5`).
4. **Settings Multipart Uploads**:
   - Images (`app_logo`, `white_logo`, `app_favicon`): Max 2MB (Favicon 1MB), WebP/PNG/JPG/SVG.
   - Social / SEO Share Image (`og_image` / `meta_image`): Max 3MB, WebP/PNG/JPG (1200×630px recommended).
   - Splash Image (`coming_background_image`): Max 4MB, WebP/PNG/JPG.
   - Video (`coming_soon_video`): Max 10MB, MP4/WebM.

---

## 8. State Management & Integration Hooks

### React Query / SWR Helper Hook Example

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { SystemSettingsMap, SettingItem } from '@/types/settings';
import { TaxItem, TaxQueryFilters } from '@/types/tax';

// Convert SettingItem[] array to key-value object map
export function toSettingsMap(settingsList: SettingItem[]): SystemSettingsMap {
  return (settingsList || []).reduce((acc, item) => {
    acc[item.name as keyof SystemSettingsMap] = item.value as any;
    return acc;
  }, {} as SystemSettingsMap);
}

// Hook: Fetch Public System Settings
export function usePublicSettings() {
  return useQuery({
    queryKey: ['public-settings'],
    queryFn: async () => {
      const { data } = await axios.get('/api/v1/public/settings');
      return toSettingsMap(data.data);
    },
    staleTime: 1000 * 60 * 15, // 15 minutes cache
  });
}

// Hook: Fetch Admin Taxes
export function useAdminTaxes(filters?: TaxQueryFilters) {
  return useQuery({
    queryKey: ['admin-taxes', filters],
    queryFn: async () => {
      const { data } = await axios.get('/api/v1/admin/taxes', { params: filters });
      return data;
    },
  });
}
```

---

## 9. Setting-Driven UI Components & Implementation Guide

Below are complete, production-ready React / Next.js implementation patterns showing how to dynamically render settings across the application.

### 9.1 Global Settings Context / Provider

```tsx
// src/context/SettingsContext.tsx
import React, { createContext, useContext, ReactNode } from 'react';
import { usePublicSettings } from '@/hooks/usePublicSettings';
import { SystemSettingsMap } from '@/types/settings';

const defaultSettings: SystemSettingsMap = {
  app_name: 'Tashi Homestay',
  default_currency: 'INR',
  currency_symbol: '₹',
  contact_email: 'support@tashihome.in',
  contact_phone: '+91 9876543210',
  contact_whatsapp: '+91 9876543210',
  contact_address: 'MG Marg, Gangtok, Sikkim - 737101, India',
  check_in_time: '14:00',
  check_out_time: '11:00',
  is_enabled_coming_soon: 'false',
};

interface SettingsContextType {
  settings: SystemSettingsMap;
  isLoading: boolean;
  formatPrice: (amount: number) => string;
}

const SettingsContext = createContext<SettingsContextType>({
  settings: defaultSettings,
  isLoading: false,
  formatPrice: (amt) => `₹${amt.toLocaleString('en-IN')}`,
});

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
  const { data: fetchedSettings, isLoading } = usePublicSettings();
  const settings: SystemSettingsMap = { ...defaultSettings, ...(fetchedSettings || {}) };

  const formatPrice = (amount: number): string => {
    const symbol = settings.currency_symbol || '₹';
    return `${symbol} ${Number(amount).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  return (
    <SettingsContext.Provider value={{ settings, isLoading, formatPrice }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => useContext(SettingsContext);
```

---

### 9.2 Dynamic Header / Navbar

```tsx
// src/components/layout/Navbar.tsx
import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useSettings } from '@/context/SettingsContext';
import { Phone, MessageCircle } from 'lucide-react';

export const Navbar = () => {
  const { settings } = useSettings();

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur shadow-sm border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <Link href="/" className="flex items-center gap-3">
          {settings.app_logo ? (
            <img
              src={settings.app_logo}
              alt={settings.app_name || 'Logo'}
              className="h-10 w-auto object-contain"
            />
          ) : (
            <span className="text-xl font-bold text-emerald-800">
              {settings.app_name || 'Tashi Homestay'}
            </span>
          )}
        </Link>

        {/* Quick Contact & Action Buttons */}
        <div className="flex items-center gap-4">
          {settings.contact_phone && (
            <a
              href={`tel:${settings.contact_phone}`}
              className="hidden md:flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:text-emerald-700"
            >
              <Phone className="w-4 h-4 text-emerald-600" />
              <span>{settings.contact_phone}</span>
            </a>
          )}

          {settings.contact_whatsapp && (
            <a
              href={`https://wa.me/${settings.contact_whatsapp.replace(/[^0-9]/g, '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-sm font-semibold hover:bg-emerald-100 transition"
            >
              <MessageCircle className="w-4 h-4 text-emerald-600" />
              <span className="hidden sm:inline">WhatsApp Help</span>
            </a>
          )}

          <Link
            href="/homestays"
            className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 shadow-sm"
          >
            Explore Stays
          </Link>
        </div>
      </div>
    </header>
  );
};
```

---

### 9.3 Dynamic Footer with Contact, Social & Policies

```tsx
// src/components/layout/Footer.tsx
import React from 'react';
import Link from 'next/link';
import { useSettings } from '@/context/SettingsContext';
import {
  Mail,
  Phone,
  MapPin,
  Facebook,
  Instagram,
  Twitter,
  Linkedin,
  Youtube,
} from 'lucide-react';

export const Footer = () => {
  const { settings } = useSettings();

  const socialLinks = [
    { icon: Facebook, url: settings.facebook_url, label: 'Facebook' },
    { icon: Instagram, url: settings.instagram_url, label: 'Instagram' },
    { icon: Twitter, url: settings.twitter_url, label: 'Twitter' },
    { icon: Linkedin, url: settings.linkedin_url, label: 'LinkedIn' },
    { icon: Youtube, url: settings.youtube_url, label: 'YouTube' },
  ].filter((item) => Boolean(item.url));

  return (
    <footer className="bg-gray-900 text-gray-300 pt-12 pb-8 border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
        {/* Brand Info */}
        <div className="md:col-span-1">
          {settings.white_logo || settings.app_logo ? (
            <img
              src={settings.white_logo || settings.app_logo}
              alt={settings.app_name || 'Logo'}
              className="h-10 w-auto mb-4 object-contain brightness-0 invert"
            />
          ) : (
            <h3 className="text-xl font-bold text-white mb-4">{settings.app_name}</h3>
          )}
          <p className="text-sm text-gray-400">
            {settings.meta_description ||
              'Authentic mountain homestays and authentic Himalayan hospitality.'}
          </p>
        </div>

        {/* Contact Info */}
        <div>
          <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">Contact & Support</h4>
          <ul className="space-y-2.5 text-sm">
            {settings.contact_address && (
              <li className="flex items-start gap-2">
                <MapPin className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                <span>{settings.contact_address}</span>
              </li>
            )}
            {settings.contact_phone && (
              <li className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-emerald-400 shrink-0" />
                <a href={`tel:${settings.contact_phone}`} className="hover:text-white">
                  {settings.contact_phone}
                </a>
              </li>
            )}
            {settings.contact_email && (
              <li className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-emerald-400 shrink-0" />
                <a href={`mailto:${settings.contact_email}`} className="hover:text-white">
                  {settings.contact_email}
                </a>
              </li>
            )}
          </ul>
        </div>

        {/* Legal & Policies */}
        <div>
          <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">Policies</h4>
          <ul className="space-y-2 text-sm">
            {settings.terms_and_conditions_url && (
              <li>
                <a href={settings.terms_and_conditions_url} className="hover:text-white">
                  Terms & Conditions
                </a>
              </li>
            )}
            {settings.privacy_policy_url && (
              <li>
                <a href={settings.privacy_policy_url} className="hover:text-white">
                  Privacy Policy
                </a>
              </li>
            )}
            {settings.refund_policy_url && (
              <li>
                <a href={settings.refund_policy_url} className="hover:text-white">
                  Cancellation & Refund Policy
                </a>
              </li>
            )}
          </ul>
        </div>

        {/* Social Media Links */}
        <div>
          <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">Follow Us</h4>
          <div className="flex gap-3">
            {socialLinks.map(({ icon: Icon, url, label }) => (
              <a
                key={label}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={label}
                className="w-9 h-9 rounded-full bg-gray-800 flex items-center justify-center text-gray-400 hover:text-white hover:bg-emerald-600 transition"
              >
                <Icon className="w-4 h-4" />
              </a>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 border-t border-gray-800 pt-6 text-center text-xs text-gray-500">
        © {new Date().getFullYear()} {settings.app_name || 'Tashi Homestay'}. All rights reserved.
      </div>
    </footer>
  );
};
```

---

### 9.4 Next.js App Router SEO & Metadata Integration

In Next.js 13+ / 14+ (`app/layout.tsx` or `app/page.tsx`):

```tsx
// src/app/layout.tsx
import { Metadata } from 'next';
import axios from 'axios';

export async function generateMetadata(): Promise<Metadata> {
  try {
    const res = await axios.get(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/public/settings`);
    const settingsList = res.data?.data || [];
    const settings = settingsList.reduce((acc: any, item: any) => {
      acc[item.name] = item.value;
      return acc;
    }, {});

    return {
      title: {
        default: settings.meta_title || 'Tashi Homestay & Hospitality',
        template: `%s | ${settings.app_name || 'Tashi Homestay'}`,
      },
      description: settings.meta_description || 'Authentic homestays in Northeast India',
      keywords: settings.meta_keywords?.split(',').map((k: string) => k.trim()) || [],
      icons: {
        icon: settings.app_favicon || '/favicon.ico',
      },
      openGraph: {
        title: settings.meta_title,
        description: settings.meta_description,
        images: settings.meta_image ? [{ url: settings.meta_image }] : [],
      },
    };
  } catch (error) {
    return {
      title: 'Tashi Homestay',
      description: 'Authentic mountain homestays',
    };
  }
}
```

---

### 9.5 Property Stay Policy Summary Helper

```tsx
// src/components/homestay/StayPolicyCard.tsx
import React from 'react';
import { useSettings } from '@/context/SettingsContext';
import { Clock, ShieldCheck, Calendar } from 'lucide-react';

export const StayPolicyCard = () => {
  const { settings } = useSettings();

  return (
    <div className="rounded-xl border border-gray-200 bg-emerald-50/50 p-5 space-y-4">
      <h4 className="font-semibold text-gray-900 text-sm">Booking & House Policies</h4>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-gray-700">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Check-in: <strong>{settings.check_in_time || '14:00'}</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Check-out: <strong>{settings.check_out_time || '11:00'}</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Cancellation Grace: <strong>{settings.cancellation_grace_period_hours || '24'} hrs</strong></span>
        </div>
      </div>
    </div>
  );
};
```


