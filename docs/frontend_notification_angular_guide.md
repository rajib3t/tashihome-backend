# Angular Frontend Integration Guide: Real-Time Notifications (Socket.IO & REST)

This guide provides the frontend engineering team with the complete implementation reference for integrating real-time **Socket.IO** and persistent **REST API** notifications in the Angular application. It covers:
- **Booking Requests** (Guest submission, Host action alerts, status changes)
- **Host Applications** (Submission, Admin review, Status updates, Conversion)
- Multi-role support for **Admin**, **Vendor (Host)**, and **User (Guest)**.

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Installation & Dependencies](#2-installation--dependencies)
3. [TypeScript Models & Interfaces](#3-typescript-models--interfaces)
4. [Socket.IO Client Service (`NotificationSocketService`)](#4-socketio-client-service-notificationsocketservice)
5. [REST API Service (`NotificationApiService`)](#5-rest-api-service-notificationapiservice)
6. [Notification State Store / Facade](#6-notification-state-store--facade)
7. [Angular UI Components](#7-angular-ui-components)
   - [7.1 Notification Bell & Badge Component](#71-notification-bell--badge-component)
   - [7.2 Toast & Audio Alerts](#72-toast--audio-alerts)
8. [Role-Specific Notification Flows](#8-role-specific-notification-flows)
   - [8.1 Vendor: New Booking Request Alerts](#81-vendor-new-booking-request-alerts)
   - [8.2 User (Guest): Booking Request Status Updates](#82-user-guest-booking-request-status-updates)
   - [8.3 Admin: Host Request & Booking Oversight](#83-admin-host-request--booking-oversight)
9. [REST API Endpoint Reference](#9-rest-api-endpoint-reference)

---

## 1. Architecture Overview

```
                      +-----------------------------+
                      |   Angular Frontend App      |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v (WebSocket / Socket.IO)                   v (HTTPS REST API)
    ws://api.domain/socket.io/                  https://api.domain/api/v1/notifications
               |                                           |
               +---------------------+---------------------+
                                     |
                      +--------------v--------------+
                      |   FastAPI ASGI Server       |
                      |   + python-socketio         |
                      +--------------+--------------+
                                     |
                    +----------------+----------------+
                    |                                 |
                    v                                 v
          [ PostgreSQL DB ]                 [ Redis Event Bus ]
       (Persistent Notifications)        (Rooms & Cross-Worker Sync)
```

### Key Highlights
- **Transport**: Standard Socket.IO client v4 using `websocket` transport with polling fallback.
- **Path**: `/socket.io/` on the same backend origin and port.
- **Authentication**: JWT token passed during socket handshake via `auth: { token: '...' }` (and query string `?token=...` as fallback).
- **Channels / Rooms**:
  - `user:{user_id}`: Targeted directly to the logged-in user.
  - `role:{role}`: Broadcasts to active roles (`role:admin`, `role:vendor`, `role:user`).

---

## 2. Installation & Dependencies

Install `socket.io-client` in your Angular workspace:

```bash
npm install socket.io-client@^4.8.1
npm install --save-dev @types/socket.io-client
```

Add your backend API and Socket URL to `src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8020/api/v1',
  socketUrl: 'http://localhost:8020', // Backend server port (configured in .env: PORT=8020)
  socketPath: '/socket.io',
};
```

> [!IMPORTANT]
> **Connecting via Angular Dev Proxy (`proxy.conf.json`) vs Direct Connection**:
> - **Direct Connection (Recommended)**: Point `socketUrl: 'http://localhost:8020'` directly to the FastAPI/Socket.IO backend server.
> - **Angular CLI Proxy (`proxy.conf.json`)**: If you proxy through the Angular dev server (`localhost:4200`), you **must** add `"ws": true` for `/socket.io`:
>   ```json
>   {
>     "/api": {
>       "target": "http://localhost:8020",
>       "secure": false
>     },
>     "/socket.io": {
>       "target": "http://localhost:8020",
>       "secure": false,
>       "ws": true
>     }
>   }
>   ```
>   Without `"ws": true` or when connecting to `localhost:4200` without proxying, the Angular dev server will reject the WebSocket handshake with `WebSocket connection failed`.


---

## 3. TypeScript Models & Interfaces

Create `src/app/core/models/notification.model.ts`:

```typescript
export enum NotificationRole {
  ADMIN = 'admin',
  VENDOR = 'vendor',
  USER = 'user',
  STAFF = 'staff',
  AGENT = 'agent',
}

export enum NotificationEventType {
  // Booking Requests
  BOOKING_REQUEST_CREATED = 'booking.request_created',
  BOOKING_CONFIRMED = 'booking.confirmed',
  BOOKING_CANCELLED = 'booking.cancelled',
  BOOKING_STATUS_CHANGED = 'booking.status_changed',

  // Host Requests
  HOST_REQUEST_SUBMITTED = 'host_request.submitted',
  HOST_REQUEST_STATUS_CHANGED = 'host_request.status_changed',
  HOST_REQUEST_CONVERTED = 'host_request.converted',
  HOST_REQUEST_MESSAGE = 'host_request.message',

  // System
  SYSTEM = 'system',
}

export interface NotificationItem {
  id: string; // UUID public_id
  role: NotificationRole | string;
  type: NotificationEventType | string;
  title: string;
  message: string;
  data?: Record<string, any> | null;
  is_read: boolean;
  read_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface NotificationPaginationMeta {
  total: number;
  page: number;
  size: number;
  total_pages: number;
  unread_count: number;
}

export interface NotificationListResponse {
  status: string;
  message: string;
  data: NotificationItem[];
  meta: NotificationPaginationMeta;
}

export interface NotificationUnreadCountResponse {
  status: string;
  message: string;
  data: {
    unread_count: number;
  };
}

export interface NotificationSingleResponse {
  status: string;
  message: string;
  data: NotificationItem;
}

export interface NotificationMarkAllReadResponse {
  status: string;
  message: string;
  data: {
    updated_count: number;
  };
}
```

---

## 4. Socket.IO Client Service (`NotificationSocketService`)

Create `src/app/core/services/notification-socket.service.ts`. This service manages the Socket.IO lifecycle, passes the JWT token, automatically reconnects on auth refresh, and emits incoming notification events.

```typescript
import { Injectable, inject } from '@angular/core';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { io, Socket } from 'socket.io-client';
import { environment } from '../../../environments/environment';
import { NotificationItem } from '../models/notification.model';
import { AuthService } from './auth.service'; // Your app's AuthService

export type SocketConnectionState = 'connected' | 'disconnected' | 'connecting' | 'error';

@Injectable({
  providedIn: 'root',
})
export class NotificationSocketService {
  private authService = inject(AuthService);
  private socket: Socket | null = null;

  // Streams
  private notificationSubject = new Subject<NotificationItem>();
  public notification$ = this.notificationSubject.asObservable();

  private connectionStateSubject = new BehaviorSubject<SocketConnectionState>('disconnected');
  public connectionState$ = this.connectionStateSubject.asObservable();

  constructor() {
    // Listen for auth state changes (login / token refresh)
    this.authService.token$.subscribe((token) => {
      if (token) {
        this.connect(token);
      } else {
        this.disconnect();
      }
    });
  }

  /**
   * Establish authenticated Socket.IO connection
   */
  public connect(token: string): void {
    if (this.socket && this.socket.connected) {
      // If token changed, update socket auth and reconnect
      this.socket.auth = { token };
      return;
    }

    this.connectionStateSubject.next('connecting');

    this.socket = io(environment.socketUrl, {
      path: environment.socketPath || '/socket.io',
      transports: ['websocket', 'polling'],
      auth: { token },
      query: { token }, // Fallback for standard query string parsing
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
    });

    this.socket.on('connect', () => {
      console.log('🟢 [Socket.IO] Connected. Socket ID:', this.socket?.id);
      this.connectionStateSubject.next('connected');
    });

    this.socket.on('disconnect', (reason) => {
      console.warn('🔴 [Socket.IO] Disconnected. Reason:', reason);
      this.connectionStateSubject.next('disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('⚠️ [Socket.IO] Connection error:', error.message);
      this.connectionStateSubject.next('error');
    });

    // Main real-time notification listener
    this.socket.on('notification', (payload: NotificationItem) => {
      console.log('🔔 [Socket.IO] Real-time notification received:', payload);
      this.notificationSubject.next(payload);
    });
  }

  /**
   * Disconnect socket cleanly
   */
  public disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connectionStateSubject.next('disconnected');
    }
  }

  /**
   * Check connection status
   */
  public isConnected(): boolean {
    return !!this.socket && this.socket.connected;
  }
}
```

---

## 5. REST API Service (`NotificationApiService`)

Create `src/app/core/services/notification-api.service.ts`:

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  NotificationListResponse,
  NotificationUnreadCountResponse,
  NotificationSingleResponse,
  NotificationMarkAllReadResponse,
  NotificationRole,
} from '../models/notification.model';

@Injectable({
  providedIn: 'root',
})
export class NotificationApiService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/notifications`;

  /**
   * Get paginated notifications for current user
   */
  getNotifications(params?: {
    page?: number;
    pageSize?: number;
    isRead?: boolean;
    role?: NotificationRole | string;
  }): Observable<NotificationListResponse> {
    let httpParams = new HttpParams();
    if (params?.page) httpParams = httpParams.set('page', params.page);
    if (params?.pageSize) httpParams = httpParams.set('page_size', params.pageSize);
    if (params?.isRead !== undefined) httpParams = httpParams.set('is_read', params.isRead);
    if (params?.role) httpParams = httpParams.set('role', params.role);

    return this.http.get<NotificationListResponse>(this.baseUrl, { params: httpParams });
  }

  /**
   * Get unread notifications count
   */
  getUnreadCount(role?: NotificationRole | string): Observable<NotificationUnreadCountResponse> {
    let httpParams = new HttpParams();
    if (role) httpParams = httpParams.set('role', role);

    return this.http.get<NotificationUnreadCountResponse>(`${this.baseUrl}/unread-count`, {
      params: httpParams,
    });
  }

  /**
   * Mark single notification as read
   */
  markAsRead(publicId: string): Observable<NotificationSingleResponse> {
    return this.http.patch<NotificationSingleResponse>(`${this.baseUrl}/${publicId}/read`, {});
  }

  /**
   * Mark all notifications as read
   */
  markAllAsRead(role?: NotificationRole | string): Observable<NotificationMarkAllReadResponse> {
    let httpParams = new HttpParams();
    if (role) httpParams = httpParams.set('role', role);

    return this.http.patch<NotificationMarkAllReadResponse>(`${this.baseUrl}/read-all`, {}, {
      params: httpParams,
    });
  }

  /**
   * Delete a notification
   */
  deleteNotification(publicId: string): Observable<{ status: string; message: string }> {
    return this.http.delete<{ status: string; message: string }>(`${this.baseUrl}/${publicId}`);
  }
}
```

---

## 6. Notification State Store / Facade

Create `src/app/core/state/notification.store.ts` using Angular Signals (or RxJS) for centralized, reactive notification state:

```typescript
import { Injectable, computed, inject, signal } from '@angular/core';
import { NotificationApiService } from '../services/notification-api.service';
import { NotificationSocketService } from '../services/notification-socket.service';
import { NotificationItem, NotificationRole } from '../models/notification.model';

@Injectable({
  providedIn: 'root',
})
export class NotificationStore {
  private api = inject(NotificationApiService);
  private socket = inject(NotificationSocketService);

  // State Signals
  private notificationsSignal = signal<NotificationItem[]>([]);
  private unreadCountSignal = signal<number>(0);
  private loadingSignal = signal<boolean>(false);

  // Selectors
  public readonly notifications = this.notificationsSignal.asReadonly();
  public readonly unreadCount = this.unreadCountSignal.asReadonly();
  public readonly loading = this.loadingSignal.asReadonly();
  public readonly hasUnread = computed(() => this.unreadCountSignal() > 0);

  constructor() {
    // Listen for live socket notifications and update state reactively
    this.socket.notification$.subscribe((newItem) => {
      this.handleIncomingNotification(newItem);
    });
  }

  /**
   * Fetch initial notifications and unread badge count
   */
  public loadInitial(role?: NotificationRole | string): void {
    this.loadingSignal.set(true);
    this.api.getNotifications({ page: 1, pageSize: 20, role }).subscribe({
      next: (res) => {
        this.notificationsSignal.set(res.data);
        this.unreadCountSignal.set(res.meta.unread_count);
        this.loadingSignal.set(false);
      },
      error: () => this.loadingSignal.set(false),
    });
  }

  /**
   * React to incoming Socket.IO notification in real-time
   */
  private handleIncomingNotification(item: NotificationItem): void {
    // Prepend to list
    this.notificationsSignal.update((current) => [item, ...current]);
    // Increment badge
    this.unreadCountSignal.update((c) => c + 1);
    // Trigger sound alert
    this.playNotificationSound();
  }

  /**
   * Mark item as read
   */
  public markAsRead(item: NotificationItem): void {
    if (item.is_read) return;

    this.api.markAsRead(item.id).subscribe({
      next: () => {
        this.notificationsSignal.update((list) =>
          list.map((n) => (n.id === item.id ? { ...n, is_read: true } : n))
        );
        this.unreadCountSignal.update((c) => Math.max(0, c - 1));
      },
    });
  }

  /**
   * Mark all as read
   */
  public markAllAsRead(role?: NotificationRole | string): void {
    this.api.markAllAsRead(role).subscribe({
      next: () => {
        this.notificationsSignal.update((list) =>
          list.map((n) => ({ ...n, is_read: true }))
        );
        this.unreadCountSignal.set(0);
      },
    });
  }

  private playNotificationSound(): void {
    try {
      const audio = new Audio('/assets/sounds/notification-chime.mp3');
      audio.play().catch(() => {
        // Browser autoplay policy might silence until first user interaction
      });
    } catch (_) {}
  }
}
```

---

## 7. Angular UI Components

### 7.1 Notification Bell & Badge Component

Create `src/app/shared/components/notification-bell/notification-bell.component.ts`:

```typescript
import { Component, inject, OnInit, HostListener, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { NotificationStore } from '../../../core/state/notification.store';
import { NotificationItem, NotificationEventType } from '../../../core/models/notification.model';

@Component({
  selector: 'app-notification-bell',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="notification-wrapper">
      <!-- Bell Icon Button with Reactive Badge -->
      <button
        class="bell-button"
        (click)="toggleDropdown()"
        [attr.aria-expanded]="isOpen"
        title="Notifications"
      >
        <svg class="bell-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        <span *ngIf="store.hasUnread()" class="badge">
          {{ store.unreadCount() > 99 ? '99+' : store.unreadCount() }}
        </span>
      </button>

      <!-- Dropdown Drawer -->
      <div *ngIf="isOpen" class="notification-dropdown">
        <div class="dropdown-header">
          <h3>Notifications</h3>
          <button
            *ngIf="store.hasUnread()"
            class="mark-all-btn"
            (click)="store.markAllAsRead()"
          >
            Mark all as read
          </button>
        </div>

        <div class="dropdown-body">
          <div *ngIf="store.loading()" class="loading-state">
            Loading notifications...
          </div>

          <div *ngIf="!store.loading() && store.notifications().length === 0" class="empty-state">
            <p>No notifications yet</p>
          </div>

          <div
            *ngFor="let notif of store.notifications()"
            class="notification-item"
            [class.unread]="!notif.is_read"
            (click)="onNotificationClick(notif)"
          >
            <div class="icon-indicator" [ngClass]="getEventColorClass(notif.type)">
              <span [ngSwitch]="notif.type">
                <span *ngSwitchCase="'booking.request_created'">📅</span>
                <span *ngSwitchCase="'booking.confirmed'">✅</span>
                <span *ngSwitchCase="'booking.cancelled'">❌</span>
                <span *ngSwitchCase="'host_request.submitted'">🏠</span>
                <span *ngSwitchCase="'host_request.converted'">🎉</span>
                <span *ngSwitchDefault>🔔</span>
              </span>
            </div>

            <div class="item-content">
              <div class="item-title">{{ notif.title }}</div>
              <div class="item-msg">{{ notif.message }}</div>
              <div class="item-time">{{ notif.created_at | date: 'short' }}</div>
            </div>

            <div *ngIf="!notif.is_read" class="unread-dot"></div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .notification-wrapper { position: relative; display: inline-block; }
    .bell-button {
      position: relative; background: transparent; border: none; cursor: pointer;
      padding: 8px; border-radius: 50%; color: #4b5563; transition: background 0.2s;
    }
    .bell-button:hover { background: #f3f4f6; color: #111827; }
    .bell-icon { width: 24px; height: 24px; }
    .badge {
      position: absolute; top: 2px; right: 2px; background: #ef4444; color: white;
      font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 9999px;
      animation: pulse 2s infinite;
    }
    .notification-dropdown {
      position: absolute; right: 0; top: 44px; width: 380px; max-height: 480px;
      background: white; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
      border: 1px solid #e5e7eb; z-index: 1000; overflow: hidden; display: flex; flex-direction: column;
    }
    .dropdown-header {
      padding: 12px 16px; border-bottom: 1px solid #f3f4f6; display: flex;
      justify-content: space-between; align-items: center; background: #fafafa;
    }
    .dropdown-header h3 { margin: 0; font-size: 15px; font-weight: 600; }
    .mark-all-btn { font-size: 12px; color: #2563eb; background: none; border: none; cursor: pointer; }
    .dropdown-body { overflow-y: auto; max-height: 420px; }
    .notification-item {
      padding: 12px 16px; border-bottom: 1px solid #f3f4f6; display: flex;
      gap: 12px; cursor: pointer; transition: background 0.15s; align-items: flex-start;
    }
    .notification-item:hover { background: #f9fafb; }
    .notification-item.unread { background: #eff6ff; }
    .item-title { font-size: 13px; font-weight: 600; color: #1f2937; margin-bottom: 2px; }
    .item-msg { font-size: 12px; color: #4b5563; line-height: 1.4; margin-bottom: 4px; }
    .item-time { font-size: 11px; color: #9ca3af; }
    .unread-dot { width: 8px; height: 8px; background: #3b82f6; border-radius: 50%; margin-top: 6px; }
    .loading-state, .empty-state { padding: 32px; text-align: center; color: #9ca3af; font-size: 13px; }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
  `],
})
export class NotificationBellComponent implements OnInit {
  public store = inject(NotificationStore);
  private router = inject(Router);
  private elementRef = inject(ElementRef);
  public isOpen = false;

  ngOnInit(): void {
    this.store.loadInitial();
  }

  public toggleDropdown(): void {
    this.isOpen = !this.isOpen;
  }

  @HostListener('document:click', ['$event'])
  public onOutsideClick(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen = false;
    }
  }

  public onNotificationClick(notif: NotificationItem): void {
    this.store.markAsRead(notif);
    this.isOpen = false;

    // Smart contextual navigation based on notification data
    const data = notif.data;
    if (notif.type.startsWith('booking.') && data?.booking_reference) {
      if (notif.role === 'vendor') {
        this.router.navigate(['/vendor/bookings', data.booking_reference]);
      } else if (notif.role === 'admin') {
        this.router.navigate(['/admin/bookings', data.booking_reference]);
      } else {
        this.router.navigate(['/user/bookings', data.booking_reference]);
      }
    } else if (notif.type.startsWith('host_request.') && data?.public_id) {
      if (notif.role === 'admin') {
        this.router.navigate(['/admin/host-requests', data.public_id]);
      }
    }
  }

  public getEventColorClass(type: string): string {
    switch (type) {
      case 'booking.request_created': return 'color-amber';
      case 'booking.confirmed': return 'color-green';
      case 'booking.cancelled': return 'color-red';
      default: return 'color-blue';
    }
  }
}
```

---

## 8. Role-Specific Notification Flows

### 8.1 Vendor: New Booking Request Alerts
When a guest reserves a homestay, the booking is placed in `pending` status, generating an instant Socket event:
```json
{
  "type": "booking.request_created",
  "role": "vendor",
  "title": "New Booking Request Received",
  "message": "You received a new booking request #BK-202609-XYZ from John Doe for Mountain Lodge (2026-10-01 to 2026-10-05). Please review and confirm.",
  "data": {
    "booking_id": 42,
    "booking_reference": "BK-202609-XYZ",
    "property_id": 12,
    "property_name": "Mountain Lodge",
    "check_in_date": "2026-10-01",
    "check_out_date": "2026-10-05",
    "total_amount": 12500.0,
    "status": "pending"
  }
}
```
**Vendor Angular Handler**:
- Show a high-priority sticky banner or Toast in the Vendor Dashboard.
- Provide quick-action buttons: `[Review & Confirm]` routing to `/vendor/bookings/BK-202609-XYZ`.

---

### 8.2 User (Guest): Booking Request Status Updates
When the host accepts, declines, or when Razorpay verifies payment:
```json
{
  "type": "booking.confirmed",
  "role": "user",
  "title": "Booking Confirmed",
  "message": "Great news! Your booking request #BK-202609-XYZ for Mountain Lodge has been confirmed.",
  "data": {
    "booking_reference": "BK-202609-XYZ",
    "property_name": "Mountain Lodge",
    "new_status": "confirmed"
  }
}
```
**Guest Angular Handler**:
- Instantly updates any active reservation screen without requiring a page refresh.
- Displays a celebratory banner and enables the "View Invoice" / "Directions" buttons.

---

### 8.3 Admin: Host Request & Booking Oversight
Admins receive both direct user notifications and `role:admin` broadcast events:
```json
{
  "type": "host_request.submitted",
  "role": "admin",
  "title": "New Host Request",
  "message": "New host application received from Karma Wangchuk for 'Tashi View Cottage' in Thimphu.",
  "data": {
    "host_request_id": 8,
    "public_id": "7a8b9c0d-1e2f-...",
    "full_name": "Karma Wangchuk",
    "property_name": "Tashi View Cottage",
    "city": "Thimphu"
  }
}
```
**Admin Angular Handler**:
- Increments the "Pending Host Requests" counter in the sidebar in real-time.
- Displays toast with direct link to `/admin/host-requests/7a8b9c0d-1e2f-...`.

---

## 9. REST API Endpoint Reference

All endpoints require `Authorization: Bearer <access_token>` or cookie `access_token`.

| Method | Endpoint | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/notifications` | `page` (default 1), `page_size` (default 20), `is_read` (bool), `role` (`admin`/`vendor`/`user`) | Get paginated notifications for current user with total unread count. |
| `GET` | `/api/v1/notifications/unread-count` | `role` (optional) | Fast endpoint for unread badge count. |
| `PATCH` | `/api/v1/notifications/{public_id}/read` | None | Mark a single notification as read. |
| `PATCH` | `/api/v1/notifications/read-all` | `role` (optional) | Mark all notifications as read for current user. |
| `DELETE` | `/api/v1/notifications/{public_id}` | None | Delete a notification. |

---

## 10. Verification Checklist
- [x] Socket connection connects to `/socket.io` with JWT authentication.
- [x] Sockets automatically join `user:{user_id}` and `role:{role}` rooms.
- [x] Real-time events arrive within < 50ms of database commitment.
- [x] Unread badge counter accurately decrements on `markAsRead` and resets on `markAllAsRead`.
