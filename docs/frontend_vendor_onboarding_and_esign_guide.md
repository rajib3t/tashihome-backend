# Frontend Integration & UI Layout Guide: Host Onboarding, Consent & E-Sign

This guide provides frontend engineers with the complete **UI/UX wireframes, screen layouts, TypeScript models, API integration specs, and Angular component implementations** for both the **Admin Host Onboarding & Agreement Management** and the **Public Host Consent & E-Sign Portal**.

> **Document Version**: 1.0.0  
> **Base URLs**:  
> - Admin Endpoints: `/api/v1/admin`  
> - Public E-Sign Endpoints: `/api/v1/public/agreements`  
> **Target Framework**: Angular 17+ / Standalone Components & RxJS / Signals

---

## Table of Contents
1. [User Journeys & Flow Diagrams](#1-user-journeys--flow-diagrams)
2. [UI Layouts & Screen Wireframes](#2-ui-layouts--screen-wireframes)
   - [2.1 Admin: Onboard Host Modal (with Agreement Dispatch)](#21-admin-onboard-host-modal)
   - [2.2 Admin: Host Agreements Table & Management](#22-admin-host-agreements-table)
   - [2.3 Public Host Portal: E-Sign & Consent Page (`/agreements/:token`)](#23-public-host-portal-e-sign-page)
   - [2.4 Public Host Portal: Agreement Signed / Confirmation Screen](#24-public-host-portal-confirmation-screen)
3. [TypeScript Models & Interfaces](#3-typescript-models--interfaces)
4. [API Endpoints & Integration Specifications](#4-api-endpoints--integration-specifications)
   - [4.1 Admin Agreement Endpoints](#41-admin-agreement-endpoints)
   - [4.2 Public E-Sign Endpoints](#42-public-e-sign-endpoints)
5. [Angular Implementation Examples](#5-angular-implementation-examples)
   - [5.1 Agreement Service (`agreement.service.ts`)](#51-agreement-service)
   - [5.2 Interactive Signature Pad Component](#52-interactive-signature-pad-component)
   - [5.3 Public E-Sign Page Component](#53-public-e-sign-page-component)
6. [Status Badges & Error Handling Matrix](#6-status-badges--error-handling-matrix)

---

## 1. User Journeys & Flow Diagrams

```
[Admin Flow]
Admin clicks "Onboard Host"
       │
       ▼
Fills Host Info (Name, Email, Phone, Homestay Name, Commission %)
       │
       ▼
Checks [X] "Send Host Partnership Agreement for E-Sign"
       │
       ▼
POST /api/v1/admin/vendors/onboard
       │
       ├──► Host Account Created (Inactive / Pending Signature)
       └──► Agreement Generated & Email Dispatched with Unique Token Link

─────────────────────────────────────────────────────────────────────────

[Host E-Sign Flow]
Host opens invitation link: https://tashihomes.in/agreements/{token}
       │
       ▼
GET /api/v1/public/agreements/{token}
(Backend transitions status: SENT ──► VIEWED)
       │
       ▼
Host reviews terms:
  • Homestay listing rules
  • Platform commission (e.g. 10%)
  • Payout cycle & settlement rules
  • Cancellation & guest refund policies
       │
       ▼
Host checks mandatory consent boxes:
  [X] I accept the TashiHome Host Terms of Service
  [X] I verify that I am the authorized legal owner / representative
       │
       ▼
Host chooses signature format:
  • Type Legal Name (generates stylized signature preview)
  • OR Draw Signature via canvas touch/mouse
       │
       ▼
POST /api/v1/public/agreements/{token}/sign
       │
       ├──► Backend records IP, user-agent, timestamp, SHA-256 hash
       ├──► Dynamic ReportLab PDF generated & saved to S3
       ├──► Agreement status updated to SIGNED
       ├──► Vendor account activated (is_terms_accepted = true)
       └──► Executed PDF emailed to Host & Admin
       │
       ▼
Host views completion screen with instant "Download Signed PDF" button
```

---

## 2. UI Layouts & Screen Wireframes

### 2.1 Admin: Onboard Host Modal
Route: `/admin/vendors` (Triggered via **"+ Onboard New Host"** button)

```
┌────────────────────────────────────────────────────────────────────────┐
│  Onboard New Homestay Host                                         [✕] │
├────────────────────────────────────────────────────────────────────────┤
│  HOST INFORMATION                                                      │
│  Full Name *                  Email Address *                          │
│  ┌──────────────────────────┐ ┌──────────────────────────────────────┐ │
│  │ Karma Tenzin             │ │ karma@gmail.com                      │ │
│  └──────────────────────────┘ └──────────────────────────────────────┘ │
│  Phone Number *               Password (leave blank for default phone) │
│  ┌──────────────────────────┐ ┌──────────────────────────────────────┐ │
│  │ +91 9876543210           │ │ ••••••••••••••                       │ │
│  └──────────────────────────┘ └──────────────────────────────────────┘ │
│                                                                        │
│  PROPERTY / COMPANY DETAILS                                            │
│  Homestay / Company Name *    Property City *                          │
│  ┌──────────────────────────┐ ┌──────────────────────────────────────┐ │
│  │ Tenzin Heritage Homestay │ │ Pelling, West Sikkim                 │ │
│  └──────────────────────────┘ └──────────────────────────────────────┘ │
│  Property Address                                                      │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ Upper Pelling, Near Monastery Road                                │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  PARTNERSHIP AGREEMENT & E-SIGN                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ [✓] Send Host Partnership Agreement for E-Signature via Email     │ │
│  │                                                                   │ │
│  │ Platform Commission Rate (%)     Agreement Valid Duration         │ │
│  │ ┌──────────────────────────────┐ ┌──────────────────────────────┐ │ │
│  │ │ 10.0                         │ │ 7 Days                       │ │ │
│  │ └──────────────────────────────┘ └──────────────────────────────┘ │ │
│  │ Custom Notes / Contract Annexure (Optional)                       │ │
│  │ ┌───────────────────────────────────────────────────────────────┐ │ │
│  │ │ Standard 10% platform commission on confirmed check-outs.     │ │ │
│  │ └───────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│  [ Cancel ]                                 [ Save & Send Agreement ]  │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Admin: Host Agreements Table
Route: `/admin/vendors/agreements` or `/admin/agreements`

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  Host Agreements & E-Sign Records                                      [ Search by Host / Token ]  │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Filters: [ All Statuses ▼ ] [ Date Range ▼ ]                         [ ↻ Refresh ] [ + New Agmt ] │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  HOST / HOMESTAY          TITLE & VERSION     STATUS    SENT DATE      SIGNED DATE    ACTIONS      │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Karma Tenzin             Host Agreement v1.0 [SIGNED]  12 Sep, 10:30  12 Sep, 14:15  [PDF] [View] │
│  Tenzin Heritage Homestay                                                                          │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Dawa Norbu               Host Agreement v1.0 [VIEWED]  14 Sep, 09:00  --             [Resend] [✕] │
│  Kanchenjunga Retreat                                                                              │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Pemba Sherpa             Host Agreement v1.0 [SENT]    15 Sep, 16:20  --             [Resend] [✕] │
│  Sherpa Mountain Lodge                                                                             │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Showing 1 to 3 of 42 agreements                     [ Previous ]  Page 1 of 14  [ Next ]          │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Public Host Portal: E-Sign Page
Route: `/agreements/:token` (Public, no login required)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│  🏡 TASHIHOME                      Host Partnership & Electronic Signature Portal   │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│   ┌────────────────────────────────────────────────────────────────────────────┐   │
│   │ 📄 TASHIHOME HOST PARTNERSHIP AGREEMENT                                    │   │
│   │ Agreement Reference: AGMT-2026-004291        Effective: 16 Sep 2026        │   │
│   ├────────────────────────────────────────────────────────────────────────────┤   │
│   │ PARTIES:                                                                   │   │
│   │ • Platform: TashiHome Technologies Private Limited                         │   │
│   │ • Host / Vendor: Karma Tenzin (Tenzin Heritage Homestay)                   │   │
│   │ • Contact: karma@gmail.com | +91 9876543210                                │   │
│   ├────────────────────────────────────────────────────────────────────────────┤   │
│   │ KEY COMMERCIAL TERMS:                                                      │   │
│   │ • Platform Service Fee: 10.0% of booking subtotal                          │   │
│   │ • Settlement Schedule: Automated payout 24 hours after verified guest      │   │
│   │   check-in via RazorpayX.                                                  │   │
│   │ • Cancellation & Refund Policy: Compliant with TashiHome Standard Policy   │   │
│   ├────────────────────────────────────────────────────────────────────────────┤   │
│   │ CONTRACT TERMS & OBLIGATIONS (Scroll to review)                            │   │
│   │ ┌────────────────────────────────────────────────────────────────────────┐ │   │
│   │ │ 1. Property Standards: The Host guarantees that all listed rooms are   │ │   │
│   │ │    clean, sanitary, and accurately represented.                        │ │   │
│   │ │ 2. Rate Parity: Direct booking rates shall not undercut rates listed   │ │   │
│   │ │    on the TashiHome platform for the same period.                      │ │   │
│   │ │ 3. Payouts & Commission: TashiHome will collect guest payments and     │ │   │
│   │ │    disburse host earnings net of platform fee to the registered bank.  │ │   │
│   │ │ 4. Guest Safety & Compliance: Host must maintain guest check-in logs   │ │   │
│   │ │    and comply with local Sikkimese tourism regulations.                │ │   │
│   │ └────────────────────────────────────────────────────────────────────────┘ │   │
│   └────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                    │
│   LEGAL CONSENT & ACKNOWLEDGMENT                                                   │
│   [✓] I have read and agree to the TashiHome Host Partnership Terms & Policies.    │
│   [✓] I verify that I am authorized to register this homestay and accept payouts.  │
│                                                                                    │
│   EXECUTE ELECTRONIC SIGNATURE                                                     │
│   Signature Mode:  (●) Draw Signature     ( ) Type Legal Name                     │
│   ┌────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                            │   │
│   │      ✍️ [ Drawn signature path rendered on HTML5 Canvas ]                  │   │
│   │                                                                            │   │
│   ├────────────────────────────────────────────────────────────────────────────┤   │
│   │ [ ⟲ Clear Signature Pad ]                                                  │   │
│   └────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                    │
│   Signer Full Legal Name *                                                         │
│   ┌────────────────────────────────────────────────────────────────────────────┐   │
│   │ Karma Tenzin                                                               │   │
│   └────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                    │
│   🔒 By clicking below, you submit a legally binding digital signature under      │
│      the Information Technology Act. Your IP address & timestamp will be logged.   │
│                                                                                    │
│   [ Decline Agreement ]                                [ E-Sign & Accept Terms ➔ ] │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.4 Public Host Portal: Confirmation Screen

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│  🏡 TASHIHOME                      Host Partnership & Electronic Signature Portal   │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│                                  ✅                                                │
│                   Agreement Successfully Executed!                                 │
│                                                                                    │
│   Welcome to the TashiHome Host Community, Karma Tenzin!                           │
│   Your Host Partnership Agreement has been digitally signed, verified, and         │
│   archived. A copy has been emailed to karma@gmail.com.                            │
│                                                                                    │
│   ┌────────────────────────────────────────────────────────────────────────────┐   │
│   │ Verification Summary                                                       │   │
│   │ • Agreement ID:        AGMT-2026-004291                                    │   │
│   │ • Signed Timestamp:    16 Sep 2026, 11:45:12 AM IST                        │   │
│   │ • Signer IP Address:   103.212.144.18                                      │   │
│   │ • Integrity Checksum:  sha256:8f4b1e9d2a3c7...                             │   │
│   └────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                    │
│   [ 📄 Download Executed PDF Contract ]        [ Proceed to Vendor Dashboard ➔ ]   │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.6 Setting-Driven Contract Template & Logo Configuration

Administrators can dynamically control the agreement branding, logo, legal entities, and default clauses via the **Platform Settings API** (`PUT /api/v1/admin/settings`):

| Setting Key | Type | Description | Default Fallback |
| :--- | :--- | :--- | :--- |
| `agreement_logo` | File / Image | Dedicated logo for the agreement PDF and e-sign header | `app_logo` / `white_logo` |
| `agreement_title` | String | Main title header on contract & PDF | `"HOST PARTNERSHIP & SERVICE AGREEMENT"` |
| `agreement_company_legal_name` | String | Platform operator legal company entity name | `legal_name` or `"{app_name} Technologies Pvt. Ltd."` |
| `agreement_company_address` | String | Registered corporate office address in contract | `contact_address` or `"Gangtok, Sikkim, India"` |
| `agreement_default_expiry_days` | Number / String | Duration before signing link expires (days) | `7` days |
| `agreement_template_terms` | JSON / Text | Structured array of clauses `[{"heading": "...", "body": "..."}]` | Standard 6-clause host partnership template |

> [!NOTE]
> When an agreement invitation is created, the system captures a **snapshot** of the active template clauses in `terms_snapshot`. This legal freeze ensures that historical agreements and signed PDFs retain the exact wording agreed to, even if platform terms are updated later in Settings.

---

## 3. TypeScript Models & Interfaces

Create or place in `src/app/core/models/agreement.model.ts`:

```typescript
export type AgreementStatus = 
  | 'draft' 
  | 'sent' 
  | 'viewed' 
  | 'signed' 
  | 'declined' 
  | 'expired' 
  | 'cancelled';

export type AgreementType = 
  | 'host_onboarding' 
  | 'commission_agreement' 
  | 'supplemental';

export type SignatureType = 'typed' | 'drawn';

export interface SignatureFontOption {
  id: string; // e.g. 'dancing_script', 'great_vibes', 'caveat', 'sacramento', 'parisienne', 'alex_brush'
  name: string; // e.g. 'Dancing Script'
  font_family: string; // e.g. "'Dancing Script', cursive"
  category: string; // e.g. 'Cursive & Fluid'
}

export interface VendorAgreementItem {
  id: string; // public_id UUID
  title: string;
  version: string;
  status: AgreementStatus;
  agreement_type: AgreementType;
  commission_percentage: number;
  sent_at: string | null;
  viewed_at: string | null;
  signed_at: string | null;
  expires_at: string;
  signer_name: string | null;
  signer_email: string | null;
  signer_phone: string | null;
  signature_type: SignatureType | null;
  signature_font?: string | null;
  pdf_file_url: string | null;
  vendor: {
    id: string;
    full_name: string;
    email: string;
    phone?: string;
    company?: {
      name: string;
      city?: string;
    };
  };
  created_at: string;
}

export interface PublicAgreementDetail {
  token: string;
  title: string;
  version: string;
  status: AgreementStatus;
  commission_percentage: number;
  expires_at: string;
  host_name: string;
  host_email: string;
  host_phone?: string;
  company_name: string;
  property_address?: string;
  city?: string;
  terms_clauses: Array<{
    heading: string;
    content: string;
  }>;
  pdf_download_url?: string;
  signed_at?: string;
  signer_name?: string;
  signature_type?: SignatureType;
  signature_data?: string;
  signature_font?: string;
  first_party_signer_name?: string;
  first_party_signer_role?: string;
  first_party_signature_type?: string;
  first_party_signature_font?: string;
  operator_name?: string;
  operator_legal_name?: string;
  operator_logo_url?: string;
  operator_address?: string;
  available_signature_fonts?: SignatureFontOption[];
}

export interface SignAgreementPayload {
  signer_name: string;
  signature_type: SignatureType;
  signature_data: string; // Base64 PNG data URL or typed font string
  signature_font?: string; // e.g. 'dancing_script', 'great_vibes', 'caveat', 'sacramento', 'parisienne', 'alex_brush'
  terms_accepted: boolean;
  consent_acknowledged: boolean;
}

export interface AdminOnboardHostPayload {
  full_name: string;
  email: string;
  phone: string;
  password?: string;
  company_name?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  send_agreement?: boolean;
  commission_percentage?: number;
  agreement_notes?: string;
}

export interface AgreementListResponse {
  success: boolean;
  message: string;
  data: VendorAgreementItem[];
  meta: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

export interface AgreementResponse {
  success: boolean;
  message: string;
  data: VendorAgreementItem;
}

export interface PublicAgreementResponse {
  success: boolean;
  message: string;
  data: PublicAgreementDetail;
}
```

---

## 4. API Endpoints & Integration Specifications

### 4.1 Admin Agreement Endpoints

#### 1. Onboard Host & Dispatch Agreement
- **Endpoint**: `POST /api/v1/admin/vendors/onboard`
- **Headers**: `Authorization: Bearer <ADMIN_TOKEN>`, `Content-Type: application/json`
- **Request Body**:
```json
{
  "full_name": "Karma Tenzin",
  "email": "karma@gmail.com",
  "phone": "+919876543210",
  "company_name": "Tenzin Heritage Homestay",
  "city": "Pelling",
  "address_line1": "Upper Pelling",
  "send_agreement": true,
  "commission_percentage": 10.0,
  "agreement_notes": "Standard Sikkimese homestay tier"
}
```

#### 2. Send Agreement to Existing Vendor
- **Endpoint**: `POST /api/v1/admin/vendors/{vendor_id}/agreements/send`
- **Request Body**:
```json
{
  "commission_percentage": 10.0,
  "valid_days": 7,
  "custom_notes": "Seasonal contract renewal"
}
```

#### 3. List All Host Agreements
- **Endpoint**: `GET /api/v1/admin/agreements`
- **Query Params**: `page=1&limit=15&status=sent&search=Karma`
- **Response Model**: `AgreementListResponse`

#### 4. Resend Agreement Email / Renew Token
- **Endpoint**: `POST /api/v1/admin/agreements/{agreement_id}/resend`
- **Response Status**: `200 OK`

#### 5. Cancel / Revoke Agreement
- **Endpoint**: `DELETE /api/v1/admin/agreements/{agreement_id}`
- **Response Status**: `200 OK`

---

### 4.2 Public E-Sign Endpoints

#### 1. Fetch Agreement Details via Token
- **Endpoint**: `GET /api/v1/public/agreements/{token}`
- **Headers**: None required (Public)
- **Response Body**:
```json
{
  "success": true,
  "message": "Agreement retrieved successfully.",
  "data": {
    "token": "d8f3e9a1-7c2b-4e12-8a9d-5f6a7b8c9d0e",
    "title": "TashiHome Host Partnership Agreement",
    "version": "1.0",
    "status": "viewed",
    "commission_percentage": 10.0,
    "expires_at": "2026-09-23T11:30:00Z",
    "host_name": "Karma Tenzin",
    "host_email": "karma@gmail.com",
    "company_name": "Tenzin Heritage Homestay",
    "city": "Pelling",
    "terms_clauses": [
      {
        "heading": "1. Host Obligations & Homestay Standards",
        "content": "The Host represents that the homestay is safe, hygienic, and properly licensed..."
      },
      {
        "heading": "2. Commission & Settlement",
        "content": "Platform fee is 10.0% of booking subtotal..."
      }
    ]
  }
}
```

#### 2. Execute Consent & E-Signature
- **Endpoint**: `POST /api/v1/public/agreements/{token}/sign`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "signer_name": "Karma Tenzin",
  "signature_type": "drawn",
  "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "terms_accepted": true,
  "consent_acknowledged": true
}
```
- **Response Body**:
```json
{
  "success": true,
  "message": "Agreement signed and executed successfully.",
  "data": {
    "token": "d8f3e9a1-7c2b-4e12-8a9d-5f6a7b8c9d0e",
    "status": "signed",
    "signed_at": "2026-09-16T11:45:12Z",
    "pdf_download_url": "https://s3.ap-south-1.amazonaws.com/tashihome-assets/agreements/AGMT-2026-004291.pdf"
  }
}
```

#### 3. Download Executed PDF
- **Endpoint**: `GET /api/v1/public/agreements/{token}/pdf`
- **Redirects to**: Presigned S3 file download URL or streams raw application/pdf.

---

## 5. Angular Implementation Examples

### 5.1 Agreement Service (`agreement.service.ts`)

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { 
  AgreementListResponse, 
  AgreementResponse, 
  PublicAgreementResponse, 
  SignAgreementPayload,
  AdminOnboardHostPayload 
} from '../models/agreement.model';

@Injectable({
  providedIn: 'root'
})
export class AgreementService {
  private readonly http = inject(HttpClient);
  private readonly adminApi = '/api/v1/admin';
  private readonly publicApi = '/api/v1/public/agreements';

  // ── Admin Methods ──────────────────────────────────────────────────────────
  onboardHost(payload: AdminOnboardHostPayload): Observable<any> {
    return this.http.post(`${this.adminApi}/vendors/onboard`, payload);
  }

  getAgreements(params?: { page?: number; limit?: number; status?: string; search?: string }): Observable<AgreementListResponse> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', params.page);
    if (params?.limit) httpParams = httpParams.set('limit', params.limit);
    if (params?.status) httpParams = httpParams.set('status', params.status);
    if (params?.search) httpParams = httpParams.set('search', params.search);

    return this.http.get<AgreementListResponse>(`${this.adminApi}/agreements`, { params: httpParams });
  }

  sendAgreementToVendor(vendorId: string, payload: { commission_percentage?: number; valid_days?: number }): Observable<AgreementResponse> {
    return this.http.post<AgreementResponse>(`${this.adminApi}/vendors/${vendorId}/agreements/send`, payload);
  }

  resendAgreement(agreementId: string): Observable<AgreementResponse> {
    return this.http.post<AgreementResponse>(`${this.adminApi}/agreements/${agreementId}/resend`, {});
  }

  cancelAgreement(agreementId: string): Observable<any> {
    return this.http.delete(`${this.adminApi}/agreements/${agreementId}`);
  }

  // ── Public E-Sign Methods ──────────────────────────────────────────────────
  getPublicAgreement(token: string): Observable<PublicAgreementResponse> {
    return this.http.get<PublicAgreementResponse>(`${this.publicApi}/${token}`);
  }

  signAgreement(token: string, payload: SignAgreementPayload): Observable<PublicAgreementResponse> {
    return this.http.post<PublicAgreementResponse>(`${this.publicApi}/${token}/sign`, payload);
  }

  getSignedPdfUrl(token: string): string {
    return `${this.publicApi}/${token}/pdf`;
  }
}
```

---

### 5.2 Interactive Signature Pad Component (`signature-pad.component.ts`)

```typescript
import { 
  Component, 
  ElementRef, 
  EventEmitter, 
  Output, 
  ViewChild, 
  AfterViewInit, 
  HostListener 
} from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-signature-pad',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="border border-slate-300 rounded-lg p-3 bg-white shadow-inner">
      <canvas #canvas 
        class="w-full h-44 bg-slate-50 rounded border border-dashed border-slate-200 cursor-crosshair touch-none"
        (mousedown)="startDrawing($event)"
        (mousemove)="draw($event)"
        (mouseup)="stopDrawing()"
        (mouseleave)="stopDrawing()"
        (touchstart)="startTouch($event)"
        (touchmove)="touchMove($event)"
        (touchend)="stopDrawing()">
      </canvas>
      <div class="flex justify-between items-center mt-2 text-xs text-slate-500">
        <span>✍️ Draw your legal signature above using your finger or mouse</span>
        <button type="button" (click)="clear()" class="text-amber-700 hover:underline font-medium">
          Clear Pad
        </button>
      </div>
    </div>
  `
})
export class SignaturePadComponent implements AfterViewInit {
  @ViewChild('canvas') canvasRef!: ElementRef<HTMLCanvasElement>;
  @Output() signatureChange = new EventEmitter<string | null>();

  private isDrawing = false;
  private ctx!: CanvasRenderingContext2D;

  ngAfterViewInit(): void {
    const canvas = this.canvasRef.nativeElement;
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    this.ctx = canvas.getContext('2d')!;
    this.ctx.lineWidth = 2.5;
    this.ctx.lineCap = 'round';
    this.ctx.strokeStyle = '#0F2937'; // Navy brand color
  }

  @HostListener('window:resize')
  onResize() {
    // Retain proportions if needed
  }

  startDrawing(e: MouseEvent): void {
    this.isDrawing = true;
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    this.ctx.beginPath();
    this.ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
  }

  draw(e: MouseEvent): void {
    if (!this.isDrawing) return;
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    this.ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    this.ctx.stroke();
    this.emitChange();
  }

  startTouch(e: TouchEvent): void {
    e.preventDefault();
    if (e.touches.length === 1) {
      const touch = e.touches[0];
      const rect = this.canvasRef.nativeElement.getBoundingClientRect();
      this.isDrawing = true;
      this.ctx.beginPath();
      this.ctx.moveTo(touch.clientX - rect.left, touch.clientY - rect.top);
    }
  }

  touchMove(e: TouchEvent): void {
    e.preventDefault();
    if (!this.isDrawing || e.touches.length !== 1) return;
    const touch = e.touches[0];
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    this.ctx.lineTo(touch.clientX - rect.left, touch.clientY - rect.top);
    this.ctx.stroke();
    this.emitChange();
  }

  stopDrawing(): void {
    if (this.isDrawing) {
      this.isDrawing = false;
      this.emitChange();
    }
  }

  clear(): void {
    const canvas = this.canvasRef.nativeElement;
    this.ctx.clearRect(0, 0, canvas.width, canvas.height);
    this.signatureChange.emit(null);
  }

  private emitChange(): void {
    const canvas = this.canvasRef.nativeElement;
    const dataUrl = canvas.toDataURL('image/png');
    this.signatureChange.emit(dataUrl);
  }
}
```

---

### 5.3 Public E-Sign Page Component (`esign-page.component.ts`)

```typescript
import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { AgreementService } from '../../core/services/agreement.service';
import { PublicAgreementDetail } from '../../core/models/agreement.model';
import { SignaturePadComponent } from '../../shared/components/signature-pad.component';

@Component({
  selector: 'app-esign-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, SignaturePadComponent],
  templateUrl: './esign-page.component.html'
})
export class ESignPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly agreementService = inject(AgreementService);
  private readonly fb = inject(FormBuilder);

  token = signal<string>('');
  agreement = signal<PublicAgreementDetail | null>(null);
  loading = signal<boolean>(true);
  submitting = signal<boolean>(false);
  isSigned = signal<boolean>(false);
  errorMessage = signal<string | null>(null);

  signatureData = signal<string | null>(null);
  signatureMode = signal<'drawn' | 'typed'>('drawn');

  signForm: FormGroup = this.fb.group({
    signer_name: ['', [Validators.required, Validators.minLength(3)]],
    terms_accepted: [false, [Validators.requiredTrue]],
    consent_acknowledged: [false, [Validators.requiredTrue]],
  });

  ngOnInit(): void {
    const tokenParam = this.route.snapshot.paramMap.get('token');
    if (!tokenParam) {
      this.errorMessage.set('Invalid agreement link.');
      this.loading.set(false);
      return;
    }
    this.token.set(tokenParam);
    this.loadAgreement(tokenParam);
  }

  loadAgreement(token: string): void {
    this.loading.set(true);
    this.agreementService.getPublicAgreement(token).subscribe({
      next: (res) => {
        this.agreement.set(res.data);
        this.signForm.patchValue({ signer_name: res.data.host_name });
        if (res.data.status === 'signed') {
          this.isSigned.set(true);
        }
        this.loading.set(false);
      },
      error: (err) => {
        this.errorMessage.set(err?.error?.message || 'Agreement has expired or does not exist.');
        this.loading.set(false);
      }
    });
  }

  onSignatureChange(data: string | null): void {
    this.signatureData.set(data);
  }

  submitSignature(): void {
    if (this.signForm.invalid) {
      this.signForm.markAllAsTouched();
      return;
    }

    const sigData = this.signatureMode() === 'drawn' 
      ? this.signatureData() 
      : this.signForm.value.signer_name;

    if (!sigData) {
      alert('Please provide your signature before submitting.');
      return;
    }

    this.submitting.set(true);
    const payload = {
      signer_name: this.signForm.value.signer_name,
      signature_type: this.signatureMode(),
      signature_data: sigData,
      terms_accepted: this.signForm.value.terms_accepted,
      consent_acknowledged: this.signForm.value.consent_acknowledged
    };

    this.agreementService.signAgreement(this.token(), payload).subscribe({
      next: (res) => {
        this.isSigned.set(true);
        this.submitting.set(false);
      },
      error: (err) => {
        alert(err?.error?.message || 'Failed to submit signature. Please try again.');
        this.submitting.set(false);
      }
    });
  }

  downloadPdf(): void {
    window.open(this.agreementService.getSignedPdfUrl(this.token()), '_blank');
  }
}
```

---

## 6. Status Badges & Error Handling Matrix

### Status Badges

| Status | Badge CSS / Colors | Description | Permitted Actions |
|---|---|---|---|
| `sent` | `bg-amber-100 text-amber-800` | Invitation dispatched to host email; pending opening. | `Resend`, `Cancel` |
| `viewed` | `bg-blue-100 text-blue-800` | Host opened link and is reviewing contract. | `Resend`, `Cancel` |
| `signed` | `bg-emerald-100 text-emerald-800` | Legally executed & PDF archived. Host activated. | `Download PDF`, `View Details` |
| `expired` | `bg-slate-100 text-slate-700` | Validity window elapsed without signing. | `Renew & Resend` |
| `declined`| `bg-rose-100 text-rose-800` | Host explicitly rejected terms. | `Contact Host`, `Create New` |
| `cancelled`| `bg-zinc-100 text-zinc-600` | Administrator revoked agreement invitation. | None |

### Error Handling & Edge Cases

1. **Expired Signing Token (`410 Gone` / `400 Bad Request`)**:
   - Render a friendly banner: *"This agreement link expired on [Date]. Please contact TashiHome Host Support or your administrator to receive a fresh signing invitation."*
2. **Already Signed Contract**:
   - If the host re-opens a token link after signing, immediately display the **Confirmation & Download Screen** rather than showing the signing form again.
3. **Touch/Mobile Responsiveness**:
   - Ensure the `<canvas>` component sets `touch-action: none` to prevent screen scrolling while the host is drawing their signature on mobile or tablet devices.

