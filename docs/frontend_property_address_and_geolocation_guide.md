# Frontend Guide: Property Address & Geolocation Integration

Comprehensive frontend guide for integrating structured manual addresses and geolocation coordinates across the **Vendor Portal (Host)**, **Admin Portal**, and **Public Guest Pages**.

---

## 1. Overview & Permissions Matrix

Properties now support both **structured manual address entries** (stored polymorphically in the `addresses` table) and **precise geographic coordinates** (latitude & longitude).

Strict role-based permission rules apply:

| Actor / Portal | Manual Address Entry | Geolocation (Lat / Long) | Notes |
| :--- | :---: | :---: | :--- |
| **Host / Vendor** (`/vendor/properties`) |  **Allowed** | ❌ **Forbidden (403)** | Hosts fill in their physical street address and postal code. Coordinates are omitted or hidden. Submitting coordinates triggers `GEOLOCATION_ADMIN_ONLY`. |
| **Admin** (`/admin/properties`) |  **Allowed** |  **Allowed** | Admins can enter or modify physical addresses and set/adjust exact map coordinates (via interactive map picker or numeric inputs). |
| **Public / Guest** (`/properties`) | 👁️ **Read-Only** | 👁️ **Read-Only** | Guests receive both formatted address string, structured address breakdown, and latitude/longitude for map rendering. |

---

## 2. TypeScript Interfaces & Data Contracts

```typescript
/**
 * Structured manual address details
 */
export interface PropertyAddressData {
  id?: string | null;           // Address UUID if persisted
  address_line1: string;        // Street name, building name, flat/door number
  address_line2?: string | null;// Landmark, suite, floor, area
  postal_code?: string | null;  // PIN code / Postal code (e.g., "737101")
  country?: string;             // Default: "India"
}

/**
 * Geographic coordinates
 */
export interface PropertyGeolocationData {
  latitude: number;             // Float between -90.0 and +90.0
  longitude: number;            // Float between -180.0 and +180.0
}

/**
 * Host / Vendor Property Create Payload
 * Note: Never send latitude, longitude, or geolocation from Vendor portal!
 */
export interface VendorPropertyCreatePayload {
  name: string;
  slug?: string;
  city_id: string;              // City UUID
  location_id: string;          // Location UUID
  type: string;                 // e.g. "homestay", "resort", "hotel"
  description?: string;
  price_per_night: number;
  sale_per_night?: number;

  // Manual Address fields (Either nested or flat):
  manual_address?: PropertyAddressData;
  // OR flat address fields:
  address_line1?: string;
  address_line2?: string;
  postal_code?: string;
  country?: string;
  address?: string;             // Legacy raw string fallback
}

/**
 * Host / Vendor Property Update Payload
 */
export type VendorPropertyUpdatePayload = Partial<VendorPropertyCreatePayload>;

/**
 * Admin Property Create / Update Payload
 * Admins can provide both manual address and geolocation.
 */
export interface AdminPropertyPayload extends VendorPropertyCreatePayload {
  vendor_id: string;            // Required for Admin Create
  is_featured?: boolean;
  status?: "pending" | "active" | "inactive" | "rejected";

  // Geolocation (Either nested or flat):
  geolocation?: PropertyGeolocationData;
  // OR flat coordinate fields:
  latitude?: number;
  longitude?: number;
}

/**
 * Property Details Response (Unified across Admin, Vendor, Public)
 */
export interface PropertyDetailResponse {
  id: string;                   // Public UUID
  name: string;
  slug: string;
  type: string;
  status: string;
  price_per_night: number;
  sale_per_night?: number | null;
  currency: string;             // Default "INR"

  // Address representations:
  address?: string | null;      // Concatenated single-line address string
  address_details?: PropertyAddressData | null; // Structured manual address
  manual_address?: PropertyAddressData | null;  // Alias of address_details

  // Geolocation representations:
  geolocation?: PropertyGeolocationData | null; // { latitude, longitude } or null
  latitude?: number | null;     // Direct float or null
  longitude?: number | null;    // Direct float or null

  city?: { id: string; name: string; slug?: string } | null;
  location?: { id: string; name: string; slug?: string } | null;
  vendor?: { id: string; full_name: string; email?: string } | null;
  feature_image?: { file_url: string } | null;
  gallery_images?: Array<{ file_url: string }>;
  property_amenities?: Array<{ amenity: { name: string; icon_url: string } }>;
  property_facilities?: Array<{ facility: { name: string; icon_url: string } }>;
  completed_steps?: string[];
  is_complete?: boolean;
}
```

---

## 3. Endpoints Reference

### 3.1. Host / Vendor Portal Endpoints

#### Create Property (Host)
- **Method**: `POST`
- **Path**: `/api/v1/vendor/properties`
- **Headers**: `Authorization: Bearer <HOST_JWT>`, `Content-Type: application/json`
- **Request Body Example**:
```json
{
  "name": "Khangchendzonga View Homestay",
  "city_id": "8bb3e012-64f1-4df0-9426-5b7ef8dca243",
  "location_id": "c1f7da3b-48bc-467a-9a99-923f1b0a8831",
  "type": "homestay",
  "price_per_night": 2500,
  "description": "Peaceful homestay with mountain views.",
  "manual_address": {
    "address_line1": "Upper Sichey, Near Enchey Monastery",
    "address_line2": "Lane 3, House #14",
    "postal_code": "737101",
    "country": "India"
  }
}
```

#### Update Property (Host)
- **Method**: `PUT`
- **Path**: `/api/v1/vendor/properties/{property_id}`
- **Headers**: `Authorization: Bearer <HOST_JWT>`, `Content-Type: application/json`
- **Request Body Example**:
```json
{
  "manual_address": {
    "address_line1": "Upper Sichey, Near Enchey Monastery",
    "address_line2": "Lane 3, House #14, 2nd Floor",
    "postal_code": "737101",
    "country": "India"
  }
}
```

> [!WARNING]
> If a host submits `latitude`, `longitude`, or `geolocation`, the server rejects the request with HTTP **`403 Forbidden`**:
> ```json
> {
>   "success": false,
>   "message": "Hosts can only provide manual address. Geolocation coordinates can only be added by administrators.",
>   "error_code": "GEOLOCATION_ADMIN_ONLY",
>   "field": "latitude"
> }
> ```

---

### 3.2. Admin Portal Endpoints

#### Create Property (Admin)
- **Method**: `POST`
- **Path**: `/api/v1/admin/properties`
- **Headers**: `Authorization: Bearer <ADMIN_JWT>`, `Content-Type: application/json`
- **Request Body Example**:
```json
{
  "vendor_id": "90d16cf6-cb4b-4b10-a42e-1510e14bfba1",
  "name": "Khangchendzonga View Homestay",
  "city_id": "8bb3e012-64f1-4df0-9426-5b7ef8dca243",
  "location_id": "c1f7da3b-48bc-467a-9a99-923f1b0a8831",
  "type": "homestay",
  "price_per_night": 2500,
  "manual_address": {
    "address_line1": "Upper Sichey, Near Enchey Monastery",
    "address_line2": "Lane 3, House #14",
    "postal_code": "737101",
    "country": "India"
  },
  "geolocation": {
    "latitude": 27.3389,
    "longitude": 88.6065
  }
}
```

#### Update Property (Admin)
- **Method**: `PUT`
- **Path**: `/api/v1/admin/properties/{property_id}`
- **Headers**: `Authorization: Bearer <ADMIN_JWT>`, `Content-Type: application/json`
- **Request Body Example**:
```json
{
  "manual_address": {
    "address_line1": "Upper Sichey, Near Enchey Monastery",
    "postal_code": "737101",
    "country": "India"
  },
  "latitude": 27.3401,
  "longitude": 88.6110
}
```

---

### 3.3. Public Guest Endpoints
- **Method**: `GET`
- **Path**: `/api/v1/properties/{slug}` or `/api/v1/properties`
- **Sample JSON Response**:
```json
{
  "id": "1ebdbf65-db0d-45a0-9fb8-4b3c0ebb6bf8",
  "name": "Khangchendzonga View Homestay",
  "slug": "khangchendzonga-view-homestay",
  "type": "homestay",
  "price_per_night": 2500.0,
  "address": "Upper Sichey, Near Enchey Monastery, Lane 3, House #14, 737101, India",
  "address_details": {
    "id": "a548e652-32a1-4ee3-9e4a-950c05fe9e30",
    "address_line1": "Upper Sichey, Near Enchey Monastery",
    "address_line2": "Lane 3, House #14",
    "postal_code": "737101",
    "country": "India"
  },
  "manual_address": {
    "id": "a548e652-32a1-4ee3-9e4a-950c05fe9e30",
    "address_line1": "Upper Sichey, Near Enchey Monastery",
    "address_line2": "Lane 3, House #14",
    "postal_code": "737101",
    "country": "India"
  },
  "geolocation": {
    "latitude": 27.3389,
    "longitude": 88.6065
  },
  "latitude": 27.3389,
  "longitude": 88.6065
}
```

---

## 4. UI Implementation Guide

### 4.1. Host / Vendor Portal: Address Form Component
In the Vendor Portal, **do not render map pickers or coordinate input fields**. Only render clean, intuitive text inputs for manual physical address entry.

```tsx
// React / Next.js / Vite Example for Host Address Form
import React from 'react';

interface HostAddressFormProps {
  formData: {
    address_line1: string;
    address_line2: string;
    postal_code: string;
    country: string;
  };
  onChange: (field: string, value: string) => void;
  errors?: Record<string, string>;
}

export const HostAddressForm: React.FC<HostAddressFormProps> = ({
  formData,
  onChange,
  errors = {},
}) => {
  return (
    <div className="space-y-4 rounded-lg border p-4 bg-white shadow-sm">
      <h3 className="text-lg font-semibold text-gray-800">Property Address</h3>
      <p className="text-sm text-gray-500">
        Enter the physical address where guests will stay. Precise GPS coordinates will be verified and added by the TashiHome administration team.
      </p>

      {/* Address Line 1 */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Street Address / House No. / Building <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formData.address_line1}
          onChange={(e) => onChange('address_line1', e.target.value)}
          placeholder="e.g. Upper Sichey, Near Enchey Monastery"
          className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm focus:border-primary-500 focus:outline-none"
          required
        />
        {errors.address_line1 && (
          <p className="mt-1 text-xs text-red-500">{errors.address_line1}</p>
        )}
      </div>

      {/* Address Line 2 */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Landmark / Area / Floor (Optional)
        </label>
        <input
          type="text"
          value={formData.address_line2}
          onChange={(e) => onChange('address_line2', e.target.value)}
          placeholder="e.g. Lane 3, House #14, 2nd Floor"
          className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm focus:border-primary-500 focus:outline-none"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Postal Code */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            PIN / Postal Code <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.postal_code}
            onChange={(e) => onChange('postal_code', e.target.value)}
            placeholder="e.g. 737101"
            className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm focus:border-primary-500 focus:outline-none"
            required
          />
          {errors.postal_code && (
            <p className="mt-1 text-xs text-red-500">{errors.postal_code}</p>
          )}
        </div>

        {/* Country */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Country</label>
          <input
            type="text"
            value={formData.country || 'India'}
            onChange={(e) => onChange('country', e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm bg-gray-50 focus:outline-none"
            readOnly
          />
        </div>
      </div>
    </div>
  );
};
```

---

### 4.2. Admin Portal: Address & Interactive Map Picker
In the Admin Portal, render both the manual address fields and an interactive Leaflet/Google Map with a draggable pin so admins can verify and set coordinates.

```tsx
// React Example for Admin Address & Map Picker
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default marker icon in leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface AdminAddressAndGeoProps {
  manualAddress: {
    address_line1: string;
    address_line2?: string;
    postal_code: string;
    country: string;
  };
  coordinates: {
    latitude: number | null;
    longitude: number | null;
  };
  onManualAddressChange: (field: string, val: string) => void;
  onCoordinatesChange: (lat: number | null, lon: number | null) => void;
}

function LocationMarker({
  lat,
  lon,
  onPositionChange,
}: {
  lat: number | null;
  lon: number | null;
  onPositionChange: (lat: number, lon: number) => void;
}) {
  useMapEvents({
    click(e) {
      onPositionChange(parseFloat(e.latlng.lat.toFixed(6)), parseFloat(e.latlng.lng.toFixed(6)));
    },
  });

  if (lat === null || lon === null) return null;

  return (
    <Marker
      position={[lat, lon]}
      draggable={true}
      eventHandlers={{
        dragend: (e) => {
          const marker = e.target;
          const pos = marker.getLatLng();
          onPositionChange(parseFloat(pos.lat.toFixed(6)), parseFloat(pos.lng.toFixed(6)));
        },
      }}
    />
  );
}

export const AdminAddressAndGeoPicker: React.FC<AdminAddressAndGeoProps> = ({
  manualAddress,
  coordinates,
  onManualAddressChange,
  onCoordinatesChange,
}) => {
  const centerLat = coordinates.latitude ?? 27.3389; // Default fallback (e.g. Gangtok)
  const centerLon = coordinates.longitude ?? 88.6065;

  return (
    <div className="space-y-6">
      {/* 1. Manual Physical Address */}
      <div className="p-4 bg-white border rounded-lg shadow-sm space-y-4">
        <h4 className="font-semibold text-gray-900">1. Physical Street Address</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="text-xs font-semibold text-gray-600">Address Line 1 *</label>
            <input
              type="text"
              value={manualAddress.address_line1}
              onChange={(e) => onManualAddressChange('address_line1', e.target.value)}
              className="mt-1 w-full border rounded p-2 text-sm"
              placeholder="Building / Street"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-600">Address Line 2</label>
            <input
              type="text"
              value={manualAddress.address_line2 || ''}
              onChange={(e) => onManualAddressChange('address_line2', e.target.value)}
              className="mt-1 w-full border rounded p-2 text-sm"
              placeholder="Landmark / Area"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-600">Postal Code *</label>
            <input
              type="text"
              value={manualAddress.postal_code}
              onChange={(e) => onManualAddressChange('postal_code', e.target.value)}
              className="mt-1 w-full border rounded p-2 text-sm"
              placeholder="737101"
            />
          </div>
        </div>
      </div>

      {/* 2. Geolocation Coordinates & Map */}
      <div className="p-4 bg-white border rounded-lg shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-semibold text-gray-900">2. Geolocation & Map Pin (Admin Exclusive)</h4>
            <p className="text-xs text-gray-500">
              Click on the map or drag the pin to assign exact GPS coordinates for guests.
            </p>
          </div>
          <button
            type="button"
            onClick={() => onCoordinatesChange(null, null)}
            className="text-xs text-red-600 hover:underline"
          >
            Clear Pin
          </button>
        </div>

        {/* Coordinate numeric inputs */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-gray-600">Latitude (-90.0 to 90.0)</label>
            <input
              type="number"
              step="any"
              min="-90"
              max="90"
              value={coordinates.latitude ?? ''}
              onChange={(e) =>
                onCoordinatesChange(e.target.value ? parseFloat(e.target.value) : null, coordinates.longitude)
              }
              className="mt-1 w-full border rounded p-2 text-sm"
              placeholder="27.338900"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-600">Longitude (-180.0 to 180.0)</label>
            <input
              type="number"
              step="any"
              min="-180"
              max="180"
              value={coordinates.longitude ?? ''}
              onChange={(e) =>
                onCoordinatesChange(coordinates.latitude, e.target.value ? parseFloat(e.target.value) : null)
              }
              className="mt-1 w-full border rounded p-2 text-sm"
              placeholder="88.606500"
            />
          </div>
        </div>

        {/* Map Container */}
        <div className="h-72 w-full rounded-md overflow-hidden border">
          <MapContainer
            center={[centerLat, centerLon]}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <LocationMarker
              lat={coordinates.latitude}
              lon={coordinates.longitude}
              onPositionChange={(lat, lon) => onCoordinatesChange(lat, lon)}
            />
          </MapContainer>
        </div>
      </div>
    </div>
  );
};
```

---

### 4.3. Public Guest Property Page: Map & Directions Link
On the guest-facing property page, display both the address description and an embedded map / "Open in Google Maps" link.

```tsx
// Guest Property Location Widget
import React from 'react';

export const PropertyLocationSection: React.FC<{
  address?: string | null;
  addressDetails?: { address_line1: string; address_line2?: string | null; postal_code?: string | null };
  geolocation?: { latitude: number; longitude: number } | null;
  propertyName: string;
}> = ({ address, addressDetails, geolocation, propertyName }) => {
  const googleMapsUrl = geolocation
    ? `https://www.google.com/maps/search/?api=1&query=${geolocation.latitude},${geolocation.longitude}`
    : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address || propertyName)}`;

  return (
    <section className="py-6 border-t border-gray-200">
      <h2 className="text-xl font-bold text-gray-900 mb-2">Location & Neighborhood</h2>
      
      {/* Display address */}
      <p className="text-gray-700 text-sm mb-4">
        📍 {address || addressDetails?.address_line1 || 'Address available upon booking'}
      </p>

      {/* Embedded Map or Google Maps Direct Link */}
      {geolocation ? (
        <div className="space-y-3">
          <div className="h-64 w-full rounded-xl overflow-hidden shadow-inner border border-gray-200">
            <iframe
              title={`Map of ${propertyName}`}
              width="100%"
              height="100%"
              frameBorder="0"
              src={`https://maps.google.com/maps?q=${geolocation.latitude},${geolocation.longitude}&z=14&output=embed`}
            />
          </div>
          <a
            href={googleMapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm font-medium text-emerald-700 hover:text-emerald-800"
          >
            Open in Google Maps & Get Directions ↗
          </a>
        </div>
      ) : (
        <a
          href={googleMapsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-sm font-medium text-blue-600 hover:underline"
        >
          Search location on Google Maps ↗
        </a>
      )}
    </section>
  );
};
```

---

## 5. Error Code Reference

When handling API errors on the frontend, check `error.response.data.error_code`:

| HTTP Status | Error Code | Field | Description | UI Action |
| :---: | :--- | :--- | :--- | :--- |
| **403** | `GEOLOCATION_ADMIN_ONLY` | `latitude` | Host attempted to send latitude, longitude, or geolocation coordinates. | Remove coordinate inputs from vendor payload; notify host that coordinates are set by Admin. |
| **422** | `LATITUDE_OUT_OF_RANGE` | `latitude` | Coordinate is less than `-90.0` or greater than `90.0`. | Show validation banner: *"Latitude must be between -90.0 and 90.0"*. |
| **422** | `LONGITUDE_OUT_OF_RANGE` | `longitude` | Coordinate is less than `-180.0` or greater than `180.0`. | Show validation banner: *"Longitude must be between -180.0 and 180.0"*. |
| **422** | `SALE_PRICE_INVALID` | `sale_per_night` | Sale price per night is greater than regular price. | Show error under price inputs. |
