# Database Design & Architecture

The backend uses **PostgreSQL** with **SQLAlchemy (Async)** ORM models and **Alembic** for schema migrations.

---

## Architectural Principles

- **Dual-Identifier Pattern**: Every major entity uses a fast auto-incrementing integer (`id`, `BigInteger`) as the internal primary key and foreign key reference, alongside a unique `UUIDv4` (`public_id`) exposed in public APIs and external communications.
- **Audit Timestamps**: All tables include timezone-aware `created_at` and `updated_at` timestamps (`TIMESTAMP WITH TIME ZONE`).
- **Audit Authorship**: Master and content entities track `created_by` and `updated_by` referencing `users.id`.
- **Soft State / Enums**: Statuses and types are represented as PostgreSQL native Enums for type safety and integrity.
- **Polymorphic Storage**: Generic models (e.g. `addresses`) support multi-entity ownership using `owner_type` and `owner_id`.

---

## Entity Relationship Overview

```
                      +-------------------+
                      |       users       |
                      +---------+---------+
                                |
       +----------------+-------+-------+---------------+----------------+----------------+
       | 1:N            | 1:N           | 1:1           | 1:N (poly)     | 1:N            | 1:N
       v                v               v               v                v                v
  +----------+    +------------+  +-----------+   +-----------+    +------------+    +-----------+
  |  tokens  |    | login_logs |  | companies |   | addresses |    | properties |    | bookings  |
  +----------+    +------------+  +-----+-----+   +-----------+    +-----+------+    +-----+-----+
                                        |                                |                 |
                                        | 1:N (poly)                     |                 |
                                        +----------------> addresses     |                 |
                                                                         |                 |
  +-------------+          +------------+          +-------------+       |                 |
  |  countries  | --1:N--> |   cities   | --1:N--> |  locations  | <-----+                 |
  +-------------+          +-----+------+          +------+------+       |                 |
                                 |                        |              |                 |
                                 +----------1:N-----------+--------------+                 |
                                                                         |                 |
                                    +------------------------------------+                 |
                                    | 1:N                                                  |
                                    +---------> property_assets                            |
                                    +---------> property_room_types <--> room_types --1:N---+
                                    +---------> property_facilities <--> facilities
                                    +---------> property_amenities  <--> amenities
                                    +---------> property_food_options
                                    +---------> room_blocks
                                    +---------> bookings --1:N--> payments
                                                          --1:N--> reviews
                                    +---------> cancellation_policies (referenced by properties & bookings)

  bookings --1:N--> refund_requests <--N:1-- payments
  users (vendor) --1:N--> payouts
  users (user/vendor) --1:N--> testimonials
```

---

## Schema & Tables

### 1. Authentication & User Management

#### `users`
Stores user identity, credentials, roles, and status.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal unique identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `email` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL`, `INDEX` | User login email |
| `phone` | `VARCHAR(20)` | `UNIQUE`, `NULLABLE`, `INDEX` | Contact phone number |
| `full_name` | `VARCHAR(255)` | `NULLABLE` | Display name |
| `password` | `VARCHAR(255)` | `NOT NULL` | Hashed password |
| `is_profile_image_url` | `VARCHAR(500)` | `NULLABLE`, `default=None` | Profile picture URL |
| `role` | `Enum(UserRole)` | `NOT NULL`, `INDEX`, `default='user'` | Role (`admin`, `vendor`, `user`, `staff`, `agent`) |
| `status` | `Enum(UserStatus)` | `NOT NULL`, `INDEX`, `default='inactive'` | Account status (`active`, `inactive`, `suspended`) |
| `is_subscribed` | `BOOLEAN` | `default=False` | Newsletter subscription status |
| `is_terms_accepted` | `BOOLEAN` | `default=False` | Terms & Conditions acceptance flag |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `tokens` -> 1:N [`Token`](#tokens), `cascade="all, delete-orphan"`
  - `login_logs` -> 1:N [`LoginLog`](#login_logs), `cascade="all, delete-orphan"`
  - `company` -> 1:1 [`Company`](#companies), `uselist=False`, `cascade="all, delete-orphan"`
  - `addresses` -> 1:N [`Address`](#addresses) (polymorphic: `owner_type='user'`), `cascade="all, delete-orphan"`
  - `bookings` -> 1:N [`Booking`](#bookings) (as guest), `cascade="all, delete-orphan"`

---

#### `tokens`
Stores authentication tokens, refresh tokens, and verification/activation tokens.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `user_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> users.id (RESTRICT)` | Linked user |
| `type` | `Enum(TokenType)` | `NULLABLE` | Token type (`access_token`, `refresh_token`, etc.) |
| `token` | `VARCHAR(1000)` | `UNIQUE`, `NOT NULL`, `INDEX` | Token string |
| `is_revoked` | `BOOLEAN` | `NOT NULL`, `default=False` | Revocation flag |
| `expires_at` | `TIMESTAMPTZ` | `NOT NULL` | Token expiration timestamp |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `user` -> N:1 [`User`](#users)

---

#### `login_logs`
Audit log tracking user logins, IP addresses, client devices, and approximate locations.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement`, `INDEX` | Log record ID |
| `user_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> users.id (RESTRICT)` | Linked user |
| `ip_address` | `VARCHAR(100)` | `NOT NULL` | Client IP address |
| `city` | `VARCHAR(100)` | `NULLABLE` | Geo-resolved city name |
| `country` | `VARCHAR(100)` | `NULLABLE` | Geo-resolved country name |
| `device_info` | `JSONB` | `NOT NULL` | Device / OS / browser metadata |
| `user_agent` | `VARCHAR(1024)` | `NULLABLE` | Raw HTTP User-Agent string |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `user` -> N:1 [`User`](#users)

---

#### `companies`
Stores vendor company and business entity details.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `user_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> users.id (CASCADE)` | Associated vendor account |
| `name` | `VARCHAR(255)` | `NOT NULL`, `INDEX` | Registered business name |
| `email` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL`, `INDEX` | Business email |
| `phone` | `VARCHAR(20)` | `UNIQUE`, `NULLABLE`, `INDEX` | Business contact phone |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `uq_companies_user_id_name` (`UNIQUE(user_id, name)`)
- **Relationships**:
  - `user` -> 1:1 [`User`](#users)
  - `addresses` -> 1:N [`Address`](#addresses) (polymorphic: `owner_type='company'`), `cascade="all, delete-orphan"`

---

#### `addresses`
Polymorphic address storage for users and vendor companies.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `owner_type` | `VARCHAR(50)` | `NOT NULL` | Owner entity type (`'user'`, `'company'`) |
| `owner_id` | `BigInteger` | `NOT NULL` | Foreign ID of the owner entity |
| `address_line1` | `VARCHAR(255)` | `NOT NULL` | Primary street address |
| `address_line2` | `VARCHAR(255)` | `NULLABLE` | Secondary address / unit / suite |
| `postal_code` | `VARCHAR(20)` | `NOT NULL` | Postal / PIN / ZIP code |
| `country` | `VARCHAR(100)` | `NOT NULL` | Country name |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `user` -> N:1 [`User`](#users) (when `owner_type='user'`)
  - `company` -> N:1 [`Company`](#companies) (when `owner_type='company'`)

---

### 2. Locations & Geography

#### `countries`
Master directory of countries.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `name` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL`, `INDEX` | Country name |
| `code` | `VARCHAR(10)` | `UNIQUE`, `NOT NULL`, `INDEX` | Country code (e.g. ISO-2/3) |
| `status` | `Enum(CountryStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `inactive`) |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | User who created the record |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | User who last updated the record |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `cities` -> 1:N [`City`](#cities), `cascade="all, delete-orphan"`

---

#### `cities`
Cities linked to countries.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `name` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL`, `INDEX` | City name |
| `image_url` | `VARCHAR(500)` | `NULLABLE` | City banner/feature image URL |
| `country_id` | `BigInteger` | `NOT NULL`, `FK -> countries.id (CASCADE)` | Parent country |
| `tag_line` | `VARCHAR(255)` | `NULLABLE` | Catchy promotional tagline |
| `short_description` | `VARCHAR(500)` | `NULLABLE` | Summary description of the city |
| `is_featured` | `BOOLEAN` | `NULLABLE` | Homepage featured flag |
| `status` | `Enum(CityStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `inactive`) |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Creator user ID |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Updater user ID |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `country` -> N:1 [`Country`](#countries)
  - `locations` -> 1:N [`Location`](#locations), `cascade="all, delete-orphan"`
  - `properties` -> 1:N [`Property`](#properties), `cascade="all, delete-orphan"`

---

#### `locations`
Specific destinations, areas, or neighborhoods within a city.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `name` | `VARCHAR(255)` | `NOT NULL`, `INDEX` | Location/area name |
| `image_url` | `VARCHAR(500)` | `NULLABLE` | Location image URL |
| `city_id` | `BigInteger` | `NOT NULL`, `FK -> cities.id (CASCADE)` | Parent city |
| `status` | `Enum(LocationStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `inactive`) |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Creator user ID |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Updater user ID |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `uq_location_city_name` (`UNIQUE(city_id, name)`)
- **Relationships**:
  - `city` -> N:1 [`City`](#cities)
  - `properties` -> 1:N [`Property`](#properties), `cascade="all, delete-orphan"`

---

### 3. Master Attributes & Metadata

#### `facilities`
General property facilities (e.g., Swimming Pool, Free Parking, Gym).

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `name` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL`, `INDEX` | Facility name |
| `icon_url` | `VARCHAR(500)` | `NULLABLE` | Icon SVG/image URL |
| `status` | `Enum(FacilityStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `inactive`) |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Creator user ID |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Updater user ID |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

---

#### `amenities`
Specific in-room / property amenities (e.g., Air Conditioning, Wi-Fi, Balcony).

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `name` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL`, `INDEX` | Amenity name |
| `icon_url` | `VARCHAR(500)` | `NULLABLE` | Icon SVG/image URL |
| `status` | `Enum(AmenityStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `inactive`) |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Creator user ID |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Updater user ID |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

---

#### `room_types`
Master room categories and base guest capacities (e.g., Deluxe King, Double Bed Room).

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `name` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL`, `INDEX` | Room type title |
| `capacity` | `INTEGER` | `NOT NULL` | Base guest capacity |
| `status` | `Enum(RoomTypeStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `inactive`) |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Creator user ID |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Updater user ID |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `property_room_types` -> 1:N [`PropertyRoomType`](#property_room_types), `cascade="all, delete-orphan"`

---

#### `cancellation_policies`
Master set of configurable refund rules, referenced by `properties` (as the default) and snapshotted onto `bookings` at booking time.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `name` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL` | Policy name (e.g. "Flexible", "Moderate", "Strict") |
| `description` | `TEXT` | `NULLABLE` | Human-readable summary |
| `refund_tiers` | `JSONB` | `NOT NULL` | Ordered refund tiers, e.g. `[{"hours_before_checkin": 168, "refund_percent": 100}, {"hours_before_checkin": 24, "refund_percent": 50}]` |
| `status` | `Enum(CancellationPolicyStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `inactive`) |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Creator user ID |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Updater user ID |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `properties` -> 1:N [`Property`](#properties) (default policy)
  - `bookings` -> 1:N [`Booking`](#bookings) (snapshotted policy at booking time)

---

### 4. Properties & Listings

#### `properties`
Primary listing table representing homestays, hotels, villas, and apartments.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `vendor_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> users.id (SET NULL)` | Vendor / Owner user ID |
| `location_id` | `BigInteger` | `NULLABLE`, `INDEX`, `FK -> locations.id (SET NULL)` | Specific location ID |
| `city_id` | `BigInteger` | `NULLABLE`, `INDEX`, `FK -> cities.id (SET NULL)` | City ID |
| `name` | `VARCHAR(255)` | `NOT NULL`, `INDEX` | Property name |
| `slug` | `VARCHAR(255)` | `NOT NULL`, `INDEX` | URL slug |
| `description` | `TEXT` | `NULLABLE` | Long description / overview |
| `address` | `VARCHAR(1000)` | `NULLABLE` | Full address string |
| `latitude` | `NUMERIC(10, 6)` | `NULLABLE` | GPS Latitude |
| `longitude` | `NUMERIC(10, 6)` | `NULLABLE` | GPS Longitude |
| `price_per_night` | `NUMERIC(12, 2)` | `NOT NULL`, `default=0` | Base price per night |
| `currency` | `VARCHAR(10)` | `NULLABLE`, `default='INR'` | Pricing currency code |
| `sale_per_night` | `NUMERIC(12, 2)` | `NULLABLE`, `default=0` | Discounted / promotional price |
| `is_featured` | `BOOLEAN` | `NULLABLE`, `default=False` | Featured listing badge |
| `type` | `Enum(PropertyType)` | `NULLABLE`, `INDEX` | Property category (`hotel`, `home_stay`, etc.) |
| `status` | `Enum(PropertyStatus)` | `NOT NULL`, `INDEX`, `default='draft'` | Listing status (`draft`, `active`, etc.) |
| `cancellation_policy_id` | `BigInteger` | `NULLABLE`, `INDEX`, `FK -> cancellation_policies.id (SET NULL)` | Default cancellation policy for this listing |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id (SET NULL)` | Creator user ID |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id (SET NULL)` | Updater user ID |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `uq_property_vendor_slug` (`UNIQUE(vendor_id, slug)`)
  - `uq_property_vendor_name` (`UNIQUE(vendor_id, name)`)
- **Relationships**:
  - `vendor` -> N:1 [`User`](#users)
  - `location` -> N:1 [`Location`](#locations)
  - `city` -> N:1 [`City`](#cities)
  - `cancellation_policy` -> N:1 [`CancellationPolicy`](#cancellation_policies)
  - `property_room_types` -> 1:N [`PropertyRoomType`](#property_room_types), `cascade="all, delete-orphan"`
  - `property_assets` -> 1:N [`PropertyAsset`](#property_assets), `cascade="all, delete-orphan"`
  - `property_facilities` -> 1:N [`PropertyFacility`](#property_facilities), `cascade="all, delete-orphan"`
  - `property_amenities` -> 1:N [`PropertyAmenity`](#property_amenities), `cascade="all, delete-orphan"`
  - `property_food_options` -> 1:N [`PropertyFoodOption`](#property_food_options), `cascade="all, delete-orphan"`
  - `bookings` -> 1:N [`Booking`](#bookings), `cascade="restrict"`
  - `reviews` -> 1:N [`Review`](#reviews), `cascade="all, delete-orphan"`

---

#### `property_room_types`
Association table linking properties to supported room types.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `property_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> properties.id (CASCADE)` | Linked property |
| `room_type_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> room_types.id (CASCADE)` | Linked room type |
| `total_units` | `INTEGER` | `NOT NULL`, `default=1`, `CHECK(> 0)` | How many rooms of this type this property has (inventory count) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `uq_property_room_type` (`UNIQUE(property_id, room_type_id)`)
  - `chk_property_room_type_units` (`CHECK(total_units > 0)`)
- **Relationships**:
  - `property` -> N:1 [`Property`](#properties)
  - `room_type` -> N:1 [`RoomType`](#room_types)

> **Note**: `total_units` is the inventory count `bookings` checks against to prevent overbooking (see [`bookings`](#bookings)).

---

#### `property_room_units`
Individual physical rooms belonging to a `property_room_type` (e.g. "Room 204"). Optional — only needed when you want to assign specific rooms rather than treat units as an interchangeable count.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `property_room_type_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> property_room_types.id (CASCADE)` | Parent room-type inventory row |
| `unit_identifier` | `VARCHAR(100)` | `NOT NULL` | Room label/number (e.g. "Room 204") |
| `status` | `Enum(RoomUnitStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `maintenance`, `inactive`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `uq_property_room_unit` (`UNIQUE(property_room_type_id, unit_identifier)`)
- **Relationships**:
  - `property_room_type` -> N:1 [`PropertyRoomType`](#property_room_types)

---

#### `property_assets`
Media items associated with properties (images, videos, documents).

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `property_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> properties.id (CASCADE)` | Linked property |
| `asset_type` | `Enum(PropertyAssetType)` | `NOT NULL`, `INDEX`, `default='image'` | Asset media format (`image`, `video`, `document`) |
| `use_for` | `Enum(PropertyAssetUseFor)` | `NULLABLE`, `default='gallery'` | Usage placement (`gallery`, `feature`, `cover`) |
| `file_url` | `VARCHAR(500)` | `NOT NULL` | CDN / Storage URL |
| `title` | `VARCHAR(255)` | `NULLABLE` | Display caption / title |
| `is_primary` | `BOOLEAN` | `NOT NULL`, `default=False` | Primary cover image flag |
| `sort_order` | `INTEGER` | `NOT NULL`, `default=0` | Display sorting index |
| `status` | `Enum(PropertyAssetStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Media status (`active`, `inactive`) |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Uploader user ID |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id` | Updater user ID |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `property` -> N:1 [`Property`](#properties)

---

#### `property_facilities`
Association table assigning facilities to properties with optional quantity and notes.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `property_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> properties.id (CASCADE)` | Linked property |
| `facility_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> facilities.id (CASCADE)` | Linked facility |
| `quantity` | `INTEGER` | `NOT NULL`, `default=1` | Quantity available |
| `notes` | `VARCHAR(255)` | `NULLABLE` | Facility notes / description |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `uq_property_facility` (`UNIQUE(property_id, facility_id)`)
- **Relationships**:
  - `property` -> N:1 [`Property`](#properties)
  - `facility` -> N:1 [`Facility`](#facilities)

---

#### `property_amenities`
Association table assigning amenities to properties with optional notes.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `property_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> properties.id (CASCADE)` | Linked property |
| `amenity_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> amenities.id (CASCADE)` | Linked amenity |
| `notes` | `VARCHAR(255)` | `NULLABLE` | Amenity notes / details |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `uq_property_amenity` (`UNIQUE(property_id, amenity_id)`)
- **Relationships**:
  - `property` -> N:1 [`Property`](#properties)
  - `amenity` -> N:1 [`Amenity`](#amenities)

---

#### `property_food_options`
Food and dining services offered at a specific property (e.g. Free Breakfast, Candlelight Dinner).

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `property_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> properties.id (CASCADE)` | Linked property |
| `name` | `VARCHAR(255)` | `NOT NULL`, `INDEX` | Food option name |
| `description` | `TEXT` | `NULLABLE` | Detailed description / menu |
| `is_included` | `BOOLEAN` | `NOT NULL`, `default=False` | Included in base room rate flag |
| `status` | `Enum(PropertyFoodOptionStatus)` | `NOT NULL`, `INDEX`, `default='active'` | Status (`active`, `inactive`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `uq_property_food_option_name` (`UNIQUE(property_id, name)`)
- **Relationships**:
  - `property` -> N:1 [`Property`](#properties)

---

### 5. Availability & Blocks

#### `room_blocks`
Lets a host/admin block out units for maintenance or personal use, independent of an actual booking. Subtracted from availability by the `check_booking_availability()` trigger (see [`bookings`](#bookings)).

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `property_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> properties.id (CASCADE)` | Linked property |
| `room_type_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> room_types.id (CASCADE)` | Linked room type |
| `block_start_date` | `DATE` | `NOT NULL` | Start of the blocked range |
| `block_end_date` | `DATE` | `NOT NULL` | End of the blocked range |
| `units_blocked` | `INTEGER` | `NOT NULL`, `default=1`, `CHECK(> 0)` | Number of units taken out of availability |
| `reason` | `VARCHAR(255)` | `NULLABLE` | Why the block was created |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id (SET NULL)` | User who created the block |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `chk_room_block_dates` (`CHECK(block_end_date > block_start_date)`)
  - `chk_room_block_units` (`CHECK(units_blocked > 0)`)
- **Relationships**:
  - `property` -> N:1 [`Property`](#properties)
  - `room_type` -> N:1 [`RoomType`](#room_types)

---

### 6. Bookings & Reservations

#### `bookings`
Reservation records linking a guest to a property (and optionally a specific room type) for a date range.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `booking_reference` | `VARCHAR(20)` | `UNIQUE`, `NOT NULL`, `INDEX` | Human-readable booking code shown to guest/vendor |
| `guest_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> users.id (RESTRICT)` | Guest who made the booking |
| `property_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> properties.id (RESTRICT)` | Booked property |
| `room_type_id` | `BigInteger` | `NULLABLE`, `INDEX`, `FK -> room_types.id (SET NULL)` | Booked room type, if applicable |
| `cancellation_policy_id` | `BigInteger` | `NULLABLE`, `INDEX`, `FK -> cancellation_policies.id (SET NULL)` | Snapshot of the policy in effect at booking time |
| `check_in_date` | `DATE` | `NOT NULL`, `INDEX` | Check-in date |
| `check_out_date` | `DATE` | `NOT NULL`, `INDEX` | Check-out date |
| `num_guests` | `INTEGER` | `NOT NULL`, `default=1` | Total guests on the booking |
| `num_rooms` | `INTEGER` | `NOT NULL`, `default=1` | Number of room units booked |
| `price_per_night` | `NUMERIC(12, 2)` | `NOT NULL` | Snapshot of nightly rate at booking time |
| `discount_amount` | `NUMERIC(12, 2)` | `default=0` | Discount applied (coupon/promo) |
| `tax_amount` | `NUMERIC(12, 2)` | `default=0` | Tax charged on the booking |
| `total_amount` | `NUMERIC(12, 2)` | `NOT NULL` | Final payable amount |
| `currency` | `VARCHAR(10)` | `default='INR'` | Currency code |
| `status` | `Enum(BookingStatus)` | `NOT NULL`, `INDEX`, `default='pending'` | Booking lifecycle status |
| `payment_status` | `Enum(PaymentStatus)` | `NOT NULL`, `INDEX`, `default='pending'` | Payment lifecycle status |
| `special_requests` | `TEXT` | `NULLABLE` | Guest notes / special requests |
| `cancellation_reason` | `VARCHAR(255)` | `NULLABLE` | Reason if cancelled |
| `cancelled_at` | `TIMESTAMPTZ` | `NULLABLE` | Cancellation timestamp |
| `created_by` | `BigInteger` | `NULLABLE`, `FK -> users.id (SET NULL)` | User who created the record (guest or admin/vendor on their behalf) |
| `updated_by` | `BigInteger` | `NULLABLE`, `FK -> users.id (SET NULL)` | User who last updated the record |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `CHECK (check_out_date > check_in_date)`
- **Relationships**:
  - `guest` -> N:1 [`User`](#users)
  - `property` -> N:1 [`Property`](#properties)
  - `room_type` -> N:1 [`RoomType`](#room_types)
  - `cancellation_policy` -> N:1 [`CancellationPolicy`](#cancellation_policies)
  - `payments` -> 1:N [`Payment`](#payments), `cascade="all, delete-orphan"`
  - `refund_requests` -> 1:N [`RefundRequest`](#refund_requests)
  - `review` -> 1:1 [`Review`](#reviews)

> **Note**: `guest_id` and `property_id` use `ON DELETE RESTRICT` so a user or property with existing bookings cannot be hard-deleted — soft-delete (`status`) the property or deactivate the user instead to preserve financial/booking history.

> **Overbooking prevention**: inventory is checked by the `check_booking_availability()` trigger (fires `BEFORE INSERT OR UPDATE` on `bookings`), not by a database exclusion constraint. A plain `EXCLUDE` constraint on `(property_id, room_type_id, daterange)` would incorrectly block *any* second overlapping booking for a room type, even when a property holds several units of it. The trigger sums `num_rooms` already booked (excluding `cancelled`/`no_show`) **plus** any overlapping `room_blocks.units_blocked` for the same `property_id + room_type_id`, and rejects the write only if it would exceed `property_room_types.total_units`.

---

#### `payments`
Payment/transaction history for a booking. Kept separate from `bookings` so a single booking can have multiple payment attempts, partial payments, and refunds.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `booking_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> bookings.id (CASCADE)` | Linked booking |
| `amount` | `NUMERIC(12, 2)` | `NOT NULL`, `CHECK(> 0)` | Transaction amount |
| `currency` | `VARCHAR(10)` | `default='INR'` | Currency code |
| `payment_method` | `Enum(PaymentMethod)` | `NULLABLE` | `card`, `upi`, `netbanking`, `wallet`, `cash`, `bank_transfer` |
| `gateway` | `VARCHAR(50)` | `NULLABLE` | Payment gateway used (e.g. Razorpay, Stripe) |
| `transaction_id` | `VARCHAR(255)` | `UNIQUE`, `NULLABLE`, `INDEX` | Gateway transaction reference |
| `status` | `Enum(TransactionStatus)` | `NOT NULL`, `INDEX`, `default='initiated'` | Transaction lifecycle status |
| `refunded_amount` | `NUMERIC(12, 2)` | `default=0`, `CHECK(0 <= refunded_amount <= amount)` | Amount refunded against this transaction |
| `paid_at` | `TIMESTAMPTZ` | `NULLABLE` | When the payment succeeded |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `booking` -> N:1 [`Booking`](#bookings)

> **Note**: `bookings.payment_status` remains a rolled-up summary field (kept in sync by the application layer) — the `payments` table is the source of truth for individual transactions.

---

### 7. Payouts & Refunds

#### `payouts`
Money paid out to vendors for a settlement period. Separate from `payments`, which tracks money coming in from guests.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `vendor_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> users.id (RESTRICT)` | Vendor being paid out |
| `amount` | `NUMERIC(12, 2)` | `NOT NULL`, `CHECK(> 0)` | Payout amount |
| `currency` | `VARCHAR(10)` | `default='INR'` | Currency code |
| `period_start` | `DATE` | `NOT NULL` | Settlement period start |
| `period_end` | `DATE` | `NOT NULL` | Settlement period end |
| `status` | `Enum(PayoutStatus)` | `NOT NULL`, `INDEX`, `default='pending'` | Payout lifecycle status |
| `transaction_id` | `VARCHAR(255)` | `UNIQUE`, `NULLABLE` | Bank/gateway transfer reference |
| `paid_at` | `TIMESTAMPTZ` | `NULLABLE` | When the payout was completed |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `chk_payouts_amount` (`CHECK(amount > 0)`)
  - `chk_payouts_period` (`CHECK(period_end >= period_start)`)
- **Relationships**:
  - `vendor` -> N:1 [`User`](#users)

> **Note**: `vendor_id` uses `ON DELETE RESTRICT` to protect payout history.

---

#### `refund_requests`
A refund request against a specific payment/booking, with an approval workflow. The actual refunded amount is recorded on `payments.refunded_amount` once processed.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `payment_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> payments.id (RESTRICT)` | Payment the refund applies to |
| `booking_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> bookings.id (RESTRICT)` | Related booking |
| `requested_by` | `BigInteger` | `NULLABLE`, `FK -> users.id (SET NULL)` | User who requested the refund |
| `reason` | `VARCHAR(255)` | `NULLABLE` | Reason for the refund |
| `amount` | `NUMERIC(12, 2)` | `NOT NULL`, `CHECK(> 0)` | Requested refund amount |
| `status` | `Enum(RefundRequestStatus)` | `NOT NULL`, `INDEX`, `default='pending'` | Request lifecycle status |
| `approved_by` | `BigInteger` | `NULLABLE`, `FK -> users.id (SET NULL)` | Admin/vendor who approved it |
| `approved_at` | `TIMESTAMPTZ` | `NULLABLE` | When it was approved |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Relationships**:
  - `payment` -> N:1 [`Payment`](#payments)
  - `booking` -> N:1 [`Booking`](#bookings)

---

### 8. Reviews & Testimonials

#### `reviews`
One review per completed booking, with an optional host reply and moderation status.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `booking_id` | `BigInteger` | `UNIQUE`, `NOT NULL`, `FK -> bookings.id (CASCADE)` | The completed booking being reviewed |
| `guest_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> users.id (CASCADE)` | Reviewer |
| `property_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> properties.id (CASCADE)` | Denormalized for fast average-rating queries |
| `rating` | `SMALLINT` | `NOT NULL`, `CHECK(1-5)` | Star rating |
| `comment` | `TEXT` | `NULLABLE` | Guest's written review |
| `host_reply` | `TEXT` | `NULLABLE` | Vendor's reply, if any |
| `host_replied_at` | `TIMESTAMPTZ` | `NULLABLE` | When the host replied |
| `status` | `Enum(ReviewStatus)` | `NOT NULL`, `INDEX`, `default='pending'` | Moderation status (`pending`, `published`, `hidden`, `flagged`, `rejected`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `chk_reviews_rating` (`CHECK(rating BETWEEN 1 AND 5)`)
  - `booking_id` is `UNIQUE` — enforces one review per booking
- **Relationships**:
  - `booking` -> 1:1 [`Booking`](#bookings)
  - `guest` -> N:1 [`User`](#users)
  - `property` -> N:1 [`Property`](#properties)

---

#### `testimonials`
Platform-level testimonials and endorsements submitted by guests or hosts/vendors with an admin moderation & feature workflow.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Internal identifier |
| `public_id` | `UUID` | `UNIQUE`, `NOT NULL`, `INDEX`, `default=uuid4` | Public identifier |
| `user_id` | `BigInteger` | `NOT NULL`, `INDEX`, `FK -> users.id (CASCADE)` | Submitting user or vendor |
| `user_role` | `VARCHAR(50)` | `NOT NULL`, `INDEX`, `default='user'` | Author role (`user`, `vendor`) |
| `name` | `VARCHAR(255)` | `NOT NULL` | Author display name |
| `designation` | `VARCHAR(255)` | `NULLABLE` | Author designation or subtitle |
| `avatar_url` | `VARCHAR(500)` | `NULLABLE` | Author avatar / profile image URL |
| `rating` | `SMALLINT` | `NULLABLE`, `CHECK(1-5)` | Overall satisfaction rating |
| `content` | `TEXT` | `NOT NULL` | Testimonial message content |
| `status` | `Enum(TestimonialStatus)` | `NOT NULL`, `INDEX`, `default='pending'` | Moderation status (`pending`, `approved`, `rejected`, `hidden`) |
| `is_featured` | `BOOLEAN` | `NOT NULL`, `INDEX`, `default=False` | Flag to feature on landing/marketing pages |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

- **Table Constraints**:
  - `chk_testimonials_rating` (`CHECK(rating IS NULL OR (rating >= 1 AND rating <= 5))`)
- **Relationships**:
  - `user` -> N:1 [`User`](#users)

---

### 9. Application Configuration & Statistics

#### `settings`
Key-value configuration store for system parameters and dynamic configurations.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY` | Setting identifier |
| `key` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL` | Configuration key |
| `value` | `TEXT` | `NOT NULL` | Configuration value (raw text or JSON) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

#### `public_stats`
Pre-aggregated statistics table updated periodically by scheduled jobs / cron to eliminate multi-table joins on high-traffic public API endpoints.

| Column | Type | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BigInteger` | `PRIMARY KEY`, `autoincrement` | Record identifier |
| `key` | `VARCHAR(100)` | `UNIQUE`, `NOT NULL`, `INDEX` | Statistics key (`'overview'`) |
| `total_homes` | `INTEGER` | `NOT NULL`, `server_default='0'` | Total active registered homestays |
| `total_destinations` | `INTEGER` | `NOT NULL`, `server_default='0'` | Total active destinations/cities |
| `verified_percent` | `INTEGER` | `NOT NULL`, `server_default='100'` | Verified homestays percentage |
| `average_rating` | `FLOAT` | `NOT NULL`, `server_default='4.9'` | Overall platform average rating |
| `total_reviews` | `INTEGER` | `NOT NULL`, `server_default='0'` | Published review count |
| `stats` | `JSON` | `NULLABLE` | Serialized frontend stat cards array |
| `metadata_json` | `JSON` | `NULLABLE` | Optional extensible payload for additional metrics |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL`, `server_default=now()`, `onupdate=now()` | Last update timestamp |

---

## Enumerations Reference

| Enum Name | Python Class | Allowed Values |
| :--- | :--- | :--- |
| `userrole` | `UserRole` | `'admin'`, `'vendor'`, `'user'`, `'staff'`, `'agent'` |
| `userstatus` | `UserStatus` | `'active'`, `'inactive'`, `'suspended'` |
| `tokentype` | `TokenType` | `'access_token'`, `'refresh_token'`, `'password_reset_token'`, `'email_verification_token'`, `'account_activation_token'` |
| `countrystatus` | `CountryStatus` | `'active'`, `'inactive'` |
| `citystatus` | `CityStatus` | `'active'`, `'inactive'` |
| `locationstatus` | `LocationStatus` | `'active'`, `'inactive'` |
| `facilitystatus` | `FacilityStatus` | `'active'`, `'inactive'` |
| `amenitystatus` | `AmenityStatus` | `'active'`, `'inactive'` |
| `roomtypestatus` | `RoomTypeStatus` | `'active'`, `'inactive'` |
| `propertytype` | `PropertyType` | `'hotel'`, `'apartment'`, `'villa'`, `'resort'`, `'hostel'`, `'guest_house'`, `'bed_and_breakfast'`, `'cottage'`, `'cabin'`, `'lodge'`, `'motel'`, `'pension'`, `'chalet'`, `'farm_stay'`, `'houseboat'`, `'home_stay'` |
| `propertystatus` | `PropertyStatus` | `'draft'`, `'active'`, `'inactive'`, `'archived'` |
| `propertyassettype` | `PropertyAssetType` | `'image'`, `'video'`, `'document'` |
| `propertyassetusefor` | `PropertyAssetUseFor` | `'gallery'`, `'feature'`, `'cover'` |
| `propertyassetstatus` | `PropertyAssetStatus` | `'active'`, `'inactive'` |
| `propertyfoodoptionstatus` | `PropertyFoodOptionStatus` | `'active'`, `'inactive'` |
| `bookingstatus` | `BookingStatus` | `'pending'`, `'confirmed'`, `'checked_in'`, `'checked_out'`, `'cancelled'`, `'no_show'`, `'completed'` |
| `paymentstatus` | `PaymentStatus` | `'pending'`, `'paid'`, `'partially_paid'`, `'refunded'`, `'failed'` |
| `transactionstatus` | `TransactionStatus` | `'initiated'`, `'success'`, `'failed'`, `'refunded'`, `'partially_refunded'` |
| `paymentmethod` | `PaymentMethod` | `'card'`, `'upi'`, `'netbanking'`, `'wallet'`, `'cash'`, `'bank_transfer'` |
| `cancellationpolicystatus` | `CancellationPolicyStatus` | `'active'`, `'inactive'` |
| `roomunitstatus` | `RoomUnitStatus` | `'active'`, `'maintenance'`, `'inactive'` |
| `reviewstatus` | `ReviewStatus` | `'pending'`, `'published'`, `'hidden'`, `'flagged'`, `'rejected'` |
| `testimonialstatus` | `TestimonialStatus` | `'pending'`, `'approved'`, `'rejected'`, `'hidden'` |
| `payoutstatus` | `PayoutStatus` | `'pending'`, `'processing'`, `'paid'`, `'failed'` |
| `refundrequeststatus` | `RefundRequestStatus` | `'pending'`, `'approved'`, `'rejected'`, `'processed'` |

---

## Database Migrations

Database migrations are managed via **Alembic** under the `versions/` folder.

### Common Migration Commands

```bash
# Apply all pending migrations to the latest revision
alembic upgrade head

# Rollback the most recent migration
alembic downgrade -1

# Generate a new migration after modifying models
alembic revision --autogenerate -m "describe_changes"

# View current migration status and history
alembic current
alembic history
```

---

## Notes & Best Practices

1. **Driver & Connection Strings**:
   - The runtime application requires an asynchronous PostgreSQL connection URI (e.g., `postgresql+asyncpg://user:password@host:5432/dbname`).
   - Alembic automatically transforms the driver URI to sync (`postgresql://`) in `versions/env.py` for CLI operations.
2. **Cascades**:
   - Parent deletion cascades (e.g. deleting a city cascades to locations and properties, deleting a property cascades to assets, facilities, amenities, room types, food options, and room blocks).
   - User deletion protects login history and token records (`ondelete="RESTRICT"`) while cascading vendor company data and setting `properties.vendor_id` to `SET NULL`.
   - `bookings.guest_id` and `bookings.property_id` use `ondelete="RESTRICT"` to protect financial/reservation history — properties and users with bookings must be deactivated (status change) rather than hard-deleted.
   - `payments.booking_id` uses `ondelete="CASCADE"` — payment history is meaningless without its parent booking, and bookings themselves are never hard-deleted in practice due to the `RESTRICT` rules above.
   - `payouts.vendor_id`, `refund_requests.payment_id`, and `refund_requests.booking_id` use `ondelete="RESTRICT"` for the same reason — financial audit trails must not silently disappear.
   - `reviews.booking_id` uses `ondelete="CASCADE"` (deleting a booking removes its review), while `reviews.guest_id`/`property_id` also cascade for consistency with existing entity-cleanup patterns.
   - `testimonials.user_id` uses `ondelete="CASCADE"` (deleting a user account removes their testimonials).
3. **Overbooking Prevention**:
   - Room inventory is enforced by a `BEFORE INSERT OR UPDATE` trigger on `bookings` (`check_booking_availability()`), not a database exclusion constraint — this correctly accounts for properties with multiple units of the same room type, and also subtracts any overlapping `room_blocks`. See the note under [`bookings`](#bookings) for details.
4. **Cancellation & Refund Flow**:
   - `cancellation_policies.refund_tiers` is the source of truth for how much to refund based on how close to check-in a cancellation happens; `bookings.cancellation_policy_id` snapshots the policy in effect at booking time so later policy edits don't retroactively change existing bookings' terms.
   - `refund_requests` is the workflow/approval layer; `payments.refunded_amount` is the ledger of money actually returned.
5. **Public Exposure**:
   - Never expose auto-incrementing integer `id` keys to client-facing APIs. Always use `public_id` (`UUID`) for queries and route parameters.
