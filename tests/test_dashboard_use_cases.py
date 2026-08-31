import asyncio
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.application.dto.dashboards.admin_dashboard import AdminDashboardQueryDTO
from app.application.dto.dashboards.vendor_dashboard import VendorDashboardQueryDTO
from app.application.use_case.admin.dashboard.get_admin_dashboard_use_case import (
    GetAdminDashboardUseCase,
    GetAdminSummaryUseCase,
)
from app.application.use_case.vendor.dashboard.get_vendor_dashboard_use_case import (
    GetVendorDashboardUseCase,
    GetVendorSummaryUseCase,
)
from app.deps.auth import CurrentUser
from app.schemas.dashboard_schema import (
    AdminDashboardResponseSchema,
    AdminSummaryResponseSchema,
    VendorDashboardResponseSchema,
    VendorSummaryResponseSchema,
)
from app.services.dashboard_service import DashboardService


def test_admin_dashboard_use_case_success():
    async def run_test():
        mock_repo = AsyncMock()

        mock_repo.get_admin_booking_stats.return_value = {
            "total": 45,
            "pending": 5,
            "confirmed": 20,
            "checked_in": 10,
            "checked_out": 5,
            "cancelled": 3,
            "completed": 2,
            "no_show": 0,
        }
        mock_repo.get_admin_revenue_stats.return_value = {
            "total_revenue": 146500.0,
            "gross_revenue": 150000.0,
            "net_revenue": 146500.0,
            "pending_revenue": 12000.0,
            "refunded_amount": 3500.0,
            "total_refunded": 3500.0,
            "currency": "INR",
        }


        mock_repo.get_admin_property_stats.return_value = {
            "total": 12,
            "active": 9,
            "draft": 2,
            "inactive": 1,
            "archived": 0,
            "featured": 4,
            "by_type": {"homestay": 8, "resort": 4},
        }
        mock_repo.get_admin_user_stats.return_value = {
            "total": 120,
            "active": 110,
            "inactive": 8,
            "suspended": 2,
            "by_role": {"user": 100, "vendor": 15, "admin": 3, "staff": 2},
            "pending_hosts": 3,
        }
        mock_repo.get_admin_refund_stats.return_value = {
            "total_requests": 6,
            "pending": 1,
            "approved": 2,
            "processed": 2,
            "rejected": 1,
            "total_amount_refunded": 7000.0,
        }
        mock_repo.get_admin_occupancy_today.return_value = {
            "today_check_ins": 4,
            "today_check_outs": 2,
            "active_guests": 18,
        }
        mock_repo.get_admin_revenue_trends.return_value = [
            {"month": "2026-07", "revenue": 65000.0, "gross_revenue": 65000.0, "refunded": 0.0, "bookings_count": 18},
            {"month": "2026-08", "revenue": 85000.0, "gross_revenue": 85000.0, "refunded": 0.0, "bookings_count": 27},
        ]

        mock_repo.get_admin_recent_bookings.return_value = [
            {
                "id": str(uuid.uuid4()),
                "booking_reference": "BK-202608-001",
                "guest_name": "John Doe",
                "guest_email": "john@example.com",
                "property_name": "Mountain View Homestay",
                "property_slug": "mountain-view-homestay",
                "check_in_date": date(2026, 9, 1),
                "check_out_date": date(2026, 9, 5),
                "num_guests": 2,
                "num_rooms": 1,
                "total_amount": 14000.0,
                "currency": "INR",
                "status": "confirmed",
                "payment_status": "paid",
                "created_at": datetime.now(timezone.utc),
            }
        ]
        mock_repo.get_admin_recent_host_requests.return_value = [
            {
                "id": str(uuid.uuid4()),
                "full_name": "Tashi Dorji",
                "email": "tashi@example.com",
                "phone": "+97517123456",
                "property_name": "Valley View Haven",
                "property_type": "homestay",
                "city": "Paro",
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
            }
        ]
        mock_repo.get_admin_recent_users.return_value = [
            {
                "id": str(uuid.uuid4()),
                "full_name": "Alice Wonderland",
                "email": "alice@example.com",
                "role": "user",
                "status": "active",
                "created_at": datetime.now(timezone.utc),
            }
        ]
        mock_repo.get_admin_recent_refund_requests.return_value = [
            {
                "id": str(uuid.uuid4()),
                "booking_reference": "BK-202608-001",
                "guest_name": "John Doe",
                "guest_email": "john@example.com",
                "property_name": "Mountain View Homestay",
                "amount": 3500.0,
                "reason": "Guest cancelled within free window",
                "status": "processed",
                "razorpay_refund_id": "rfnd_123456",
                "approved_at": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc),
            }
        ]
        mock_repo.get_admin_top_properties.return_value = [
            {
                "id": str(uuid.uuid4()),
                "name": "Mountain View Homestay",
                "slug": "mountain-view-homestay",
                "city": "Thimphu",
                "type": "homestay",
                "price_per_night": 3500.0,
                "image_url": "https://cdn.example.com/mountain.jpg",
                "total_bookings": 25,
                "total_revenue": 87500.0,
                "average_rating": 4.8,
            }
        ]

        service = DashboardService(dashboard_repository=mock_repo)
        use_case = GetAdminDashboardUseCase(dashboard_service=service)


        result = await use_case.execute(AdminDashboardQueryDTO(months=6))

        assert result["bookings_summary"]["total"] == 45
        assert result["revenue_summary"]["total_revenue"] == 146500.0
        assert result["revenue_summary"]["gross_revenue"] == 150000.0
        assert result["revenue_summary"]["refunded_amount"] == 3500.0
        assert result["properties_summary"]["active"] == 9
        assert result["users_summary"]["total"] == 120
        assert len(result["recent_bookings"]) == 1
        assert len(result["recent_refund_requests"]) == 1
        assert len(result["top_properties"]) == 1


        # Verify Pydantic schema validation
        response_model = AdminDashboardResponseSchema(
            status="success",
            message="Admin dashboard retrieved.",
            data=result,
        )
        assert response_model.data.bookings_summary.confirmed == 20
        assert response_model.data.refunds_summary.processed == 2
        assert response_model.data.refunds_summary.total_amount_refunded == 7000.0
        assert response_model.data.occupancy_today.active_guests == 18

    asyncio.run(run_test())



def test_admin_summary_use_case_success():
    async def run_test():
        mock_repo = AsyncMock()
        mock_repo.get_admin_booking_stats.return_value = {"total": 10, "pending": 2, "confirmed": 8}
        mock_repo.get_admin_revenue_stats.return_value = {
            "total_revenue": 49000.0,
            "gross_revenue": 50000.0,
            "net_revenue": 49000.0,
            "pending_revenue": 5000.0,
            "refunded_amount": 1000.0,
            "total_refunded": 1000.0,
            "currency": "INR",
        }

        mock_repo.get_admin_property_stats.return_value = {"total": 5, "active": 4, "draft": 1, "inactive": 0, "archived": 0, "featured": 1, "by_type": {}}
        mock_repo.get_admin_user_stats.return_value = {"total": 50, "active": 45, "inactive": 5, "suspended": 0, "by_role": {}, "pending_hosts": 1}
        mock_repo.get_admin_refund_stats.return_value = {"total_requests": 1, "pending": 0, "approved": 1, "rejected": 0, "total_amount_refunded": 1000.0}
        mock_repo.get_admin_occupancy_today.return_value = {"today_check_ins": 2, "today_check_outs": 1, "active_guests": 5}

        service = DashboardService(dashboard_repository=mock_repo)
        use_case = GetAdminSummaryUseCase(dashboard_service=service)

        result = await use_case.execute()

        response = AdminSummaryResponseSchema(
            status="success",
            message="Admin summary retrieved.",
            data=result,
        )
        assert response.data.revenue_summary.total_revenue == 49000.0
        assert response.data.revenue_summary.gross_revenue == 50000.0
        assert response.data.revenue_summary.refunded_amount == 1000.0


    asyncio.run(run_test())


def test_vendor_dashboard_use_case_success():
    async def run_test():
        mock_repo = AsyncMock()

        mock_repo.get_vendor_booking_stats.return_value = {
            "total": 15,
            "pending": 2,
            "confirmed": 8,
            "checked_in": 3,
            "checked_out": 2,
            "cancelled": 0,
            "completed": 0,
            "no_show": 0,
        }
        mock_repo.get_vendor_revenue_stats.return_value = {
            "total_revenue": 52500.0,
            "gross_revenue": 52500.0,
            "net_revenue": 52500.0,
            "pending_revenue": 7000.0,
            "refunded_amount": 0.0,
            "total_refunded": 0.0,
            "currency": "INR",
        }


        mock_repo.get_vendor_property_stats.return_value = {
            "total": 3,
            "active": 2,
            "draft": 1,
            "inactive": 0,
            "archived": 0,
            "featured": 1,
            "by_type": {},
        }
        mock_repo.get_vendor_review_stats.return_value = {
            "total_reviews": 12,
            "average_rating": 4.9,
        }
        mock_repo.get_vendor_occupancy_today.return_value = {
            "today_check_ins": 1,
            "today_check_outs": 1,
            "active_guests": 6,
        }
        mock_repo.get_vendor_revenue_trends.return_value = [
            {"month": "2026-08", "revenue": 52500.0, "gross_revenue": 52500.0, "refunded": 0.0, "bookings_count": 15}
        ]

        mock_repo.get_vendor_recent_bookings.return_value = [
            {
                "id": str(uuid.uuid4()),
                "booking_reference": "BK-202608-005",
                "guest_name": "Bob Smith",
                "guest_email": "bob@example.com",
                "property_name": "Riverfront Villa",
                "property_slug": "riverfront-villa",
                "check_in_date": date(2026, 9, 10),
                "check_out_date": date(2026, 9, 12),
                "num_guests": 4,
                "num_rooms": 2,
                "total_amount": 16000.0,
                "currency": "INR",
                "status": "confirmed",
                "payment_status": "paid",
                "created_at": datetime.now(timezone.utc),
            }
        ]
        mock_repo.get_vendor_upcoming_bookings.return_value = [
            {
                "id": str(uuid.uuid4()),
                "booking_reference": "BK-202608-006",
                "guest_name": "Carol Davis",
                "guest_email": "carol@example.com",
                "property_name": "Riverfront Villa",
                "property_slug": "riverfront-villa",
                "check_in_date": date(2026, 9, 15),
                "check_out_date": date(2026, 9, 18),
                "num_guests": 2,
                "num_rooms": 1,
                "total_amount": 10500.0,
                "currency": "INR",
                "status": "confirmed",
                "payment_status": "paid",
                "created_at": datetime.now(timezone.utc),
            }
        ]
        mock_repo.get_vendor_top_properties.return_value = [
            {
                "id": str(uuid.uuid4()),
                "name": "Riverfront Villa",
                "slug": "riverfront-villa",
                "city": "Punakha",
                "type": "villa",
                "price_per_night": 5000.0,
                "image_url": "https://cdn.example.com/villa.jpg",
                "total_bookings": 15,
                "total_revenue": 52500.0,
                "average_rating": 4.9,
            }
        ]

        current_user = CurrentUser(id=77, role="vendor")
        service = DashboardService(dashboard_repository=mock_repo)
        use_case = GetVendorDashboardUseCase(dashboard_service=service, current_user=current_user)

        result = await use_case.execute(VendorDashboardQueryDTO(months=3))

        mock_repo.get_vendor_booking_stats.assert_called_once_with(vendor_id=77)
        mock_repo.get_vendor_revenue_stats.assert_called_once_with(vendor_id=77)

        assert result["bookings_summary"]["total"] == 15
        assert result["reviews_summary"]["average_rating"] == 4.9

        # Validate against schema
        response_model = VendorDashboardResponseSchema(
            status="success",
            message="Vendor dashboard retrieved.",
            data=result,
        )
        assert response_model.data.bookings_summary.confirmed == 8
        assert len(response_model.data.upcoming_bookings) == 1

    asyncio.run(run_test())


def test_vendor_summary_use_case_success():
    async def run_test():
        mock_repo = AsyncMock()
        mock_repo.get_vendor_booking_stats.return_value = {"total": 8, "confirmed": 6}
        mock_repo.get_vendor_revenue_stats.return_value = {
            "total_revenue": 28000.0,
            "gross_revenue": 28000.0,
            "net_revenue": 28000.0,
            "pending_revenue": 0.0,
            "refunded_amount": 0.0,
            "total_refunded": 0.0,
            "currency": "INR",
        }


        mock_repo.get_vendor_property_stats.return_value = {"total": 2, "active": 2, "draft": 0, "inactive": 0, "archived": 0, "featured": 0, "by_type": {}}
        mock_repo.get_vendor_review_stats.return_value = {"total_reviews": 5, "average_rating": 5.0}
        mock_repo.get_vendor_occupancy_today.return_value = {"today_check_ins": 1, "today_check_outs": 0, "active_guests": 2}

        current_user = CurrentUser(id=88, role="vendor")
        service = DashboardService(dashboard_repository=mock_repo)
        use_case = GetVendorSummaryUseCase(dashboard_service=service, current_user=current_user)

        result = await use_case.execute()

        response = VendorSummaryResponseSchema(
            status="success",
            message="Vendor summary retrieved.",
            data=result,
        )
        assert response.data.reviews_summary.average_rating == 5.0
        assert response.data.revenue_summary.total_revenue == 28000.0

    asyncio.run(run_test())

