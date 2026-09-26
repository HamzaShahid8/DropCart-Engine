# DropCart — High-Concurrency Limited-Stock Commerce Backend

DropCart is a production-oriented backend for **limited-stock drops, reservations, checkout, payments, webhooks, and concurrent traffic**.

The project focuses on solving real backend problems such as:

* Concurrent inventory reservations
* PostgreSQL row-level locking
* Transactional stock updates
* Reservation expiry
* Order state machines
* Payment processing
* Idempotent checkout
* Webhook security
* Duplicate and out-of-order webhook events
* HMAC-SHA256 signature verification
* Redis and Celery background processing
* Dockerized services
* Health/readiness checks
* High-concurrency load testing

---

## Architecture

```text
                    ┌──────────────────────┐
                    │       Client         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    DropCart API      │
                    │     Django / DRF     │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
      │ PostgreSQL  │   │    Redis    │   │    Celery   │
      │             │   │             │   │ Worker/Beat │
      └─────────────┘   └─────────────┘   └─────────────┘
                              
                    ┌──────────────────────┐
                    │ Mock Payment Gateway │
                    │   dropcart-gateway   │
                    └──────────┬───────────┘
                               │
                               │ Webhooks
                               ▼
                    ┌──────────────────────┐
                    │ DropCart Webhook API │
                    └──────────────────────┘
```

---

# Core Technologies

* Python
* Django
* Django REST Framework
* PostgreSQL
* Redis
* Celery
* Celery Beat
* JWT Authentication
* Docker
* Docker Compose
* k6
* HMAC-SHA256
* REST APIs

---

# Core Backend Features

## Authentication

The API uses JWT-based authentication.

Protected endpoints require:

```http
Authorization: Bearer <access_token>
```

---

# Drops

A drop represents a limited-stock product release.

Important fields include:

```text
id
name
price
currency
total_stock
available_stock
starts_at
is_deleted
deleted_at
created_at
updated_at
```

The system supports:

* Drop creation
* Drop updates
* Soft deletion
* Drop restoration
* Start-time validation
* Stock management

---

# Reservation System

The reservation system is designed for high-concurrency limited-stock scenarios.

Reservation flow:

```text
User
 │
 ▼
Reserve Drop
 │
 ▼
Lock Drop Row
 │
 ▼
Validate Drop
 │
 ├── Not Started → Reject
 ├── Deleted → Reject
 ├── Already Reserved → Reject
 └── Sold Out → Reject
 │
 ▼
Create Reservation
 │
 ▼
Decrease Available Stock
 │
 ▼
Create Order
 │
 ▼
Commit Transaction
```

---

# Concurrency Control

The critical inventory operation uses PostgreSQL row-level locking:

```python
Drop.objects.select_for_update().get(id=drop_id)
```

Combined with:

```python
@transaction.atomic
```

This ensures concurrent requests cannot simultaneously modify the same stock row.

The important invariant is:

```text
available_stock >= 0
```

and:

```text
successful reservations <= total_stock
```

The reservation, stock decrement, and order creation are executed inside the same database transaction.

If a later operation fails, the transaction rolls back.

---

# Reservation Expiry

Reservations have an expiration time.

Celery Beat periodically triggers the expiry task.

```text
Celery Beat
    │
    ▼
expire_reservations
    │
    ▼
Find expired ACTIVE reservations
    │
    ▼
Lock reservation
    │
    ▼
Lock drop
    │
    ▼
Reservation → EXPIRED
    │
    ▼
Restore stock
    │
    ▼
Create audit/state information
```

This prevents expired reservations from permanently consuming inventory.

---

# Orders

Orders use an explicit state machine.

```text
RESERVED
    │
    ├──► PAYMENT_PENDING
    │        │
    │        ├──► PAID
    │        │      │
    │        │      ├──► CONFIRMED
    │        │      └──► REFUNDED
    │        │
    │        ├──► FAILED
    │        └──► EXPIRED
    │
    └──► EXPIRED
             │
             └──► REFUNDED
```

Invalid state transitions are rejected.

Order transitions are protected with row-level locking:

```python
Order.objects.select_for_update().get(id=order_id)
```

Every transition is recorded in `OrderStateTransition`.

---

# Payment Integration

DropCart uses a separate **Mock Payment Gateway** service for payment-flow testing.

The architecture is:

```text
DropCart
   │
   │ Payment Intent
   ▼
Mock Payment Gateway
   │
   ├── payment.processing
   ├── payment.succeeded
   └── payment.failed
          │
          ▼
      Webhook
          │
          ▼
      DropCart
```

The gateway simulates real-world payment-provider behavior including:

* Successful payments
* Failed payments
* Processing states
* Delayed events
* Duplicate events
* Out-of-order events
* Webhook signatures

This allows the payment architecture to be tested without depending on a real payment provider.

---

# Checkout

Checkout validates the reservation before initiating payment.

High-level flow:

```text
Reservation
    │
    ▼
Validate ACTIVE reservation
    │
    ▼
Idempotency validation
    │
    ▼
Create PAYMENT_PENDING order
    │
    ▼
Create Payment
    │
    ▼
Create Payment Intent
    │
    ▼
Mock Payment Gateway
```

External payment communication is kept separate from long-running database transactions.

---

# Idempotency

Checkout supports idempotency keys to prevent duplicate payment/order operations caused by:

* Client retries
* Network failures
* Duplicate requests
* Request timeouts

Example:

```http
Idempotency-Key: unique-request-key
```

The same idempotency key can safely be retried without unintentionally creating another payment operation.

---

# Webhook Security

Payment webhooks are protected using:

```text
HMAC-SHA256
```

The webhook verification process validates:

* Raw request body
* Signature
* Timestamp
* Replay window

Requests outside the allowed timestamp window are rejected.

This protects the payment webhook endpoint against forged and replayed requests.

---

# Webhook Processing

Webhook events are processed safely even when payment providers deliver events more than once or in the wrong order.

Supported protections include:

### Duplicate Events

Previously processed event IDs are detected and safely ignored.

### Out-of-Order Events

Order/payment state transitions are validated through the order state machine.

An invalid transition is not blindly applied.

### Late Payment

If a payment succeeds after the reservation/order has already expired, the system handles the late payment according to the refund policy instead of incorrectly confirming the expired reservation.

---

# Redis

Redis is used as an infrastructure component for asynchronous/background processing and caching-related workloads.

It works with Celery as the message broker.

```text
Django API
    │
    ▼
Redis
    │
    ▼
Celery Worker
```

---

# Celery

Celery handles asynchronous background tasks.

Celery Beat is used for scheduled jobs such as reservation expiration.

Example:

```text
Celery Beat
     │
     ▼
Scheduled Task
     │
     ▼
Redis
     │
     ▼
Celery Worker
     │
     ▼
Django
```

---

# Health & Readiness

The application exposes separate health/readiness concepts.

### Health

Used to determine whether the application process is alive.

```text
/health
```

### Readiness

Used to determine whether required dependencies are available.

```text
/ready
```

Readiness checks infrastructure dependencies such as:

* PostgreSQL
* Redis

This distinction is useful for container orchestration and deployment environments.

---

# Testing

The project includes automated tests covering important backend behavior.

Test areas include:

* Reservation creation
* Stock management
* Concurrent reservations
* Sold-out behavior
* Reservation expiry
* Order transitions
* Checkout
* Idempotency
* Payment processing
* Webhook verification
* Duplicate webhooks
* Out-of-order events
* Late payment handling

---

# Load Testing

k6 is used to test high-concurrency reservation traffic.

The key scenario is:

```text
Concurrent Requests: 2,000
In
```