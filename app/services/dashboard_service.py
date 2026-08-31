from typing import Any, Dict

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, dashboard_repository: DashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def get_admin_dashboard(self, months: int = 12) -> Dict[str, Any]:
        """Fetch full admin dashboard dataset including KPI summaries, trends, and recent activities."""
        bookings_summary = await self.dashboard_repository.get_admin_booking_stats()
        revenue_summary = await self.dashboard_repository.get_admin_revenue_stats()
        properties_summary = await self.dashboard_repository.get_admin_property_stats()
        users_summary = await self.dashboard_repository.get_admin_user_stats()
        refunds_summary = await self.dashboard_repository.get_admin_refund_stats()
        payouts_summary = await self.dashboard_repository.get_admin_payout_stats()
        occupancy_today = await self.dashboard_repository.get_admin_occupancy_today()
        revenue_trends = await self.dashboard_repository.get_admin_revenue_trends(months=months)
        recent_bookings = await self.dashboard_repository.get_admin_recent_bookings(limit=5)
        recent_host_requests = await self.dashboard_repository.get_admin_recent_host_requests(limit=5)
        recent_users = await self.dashboard_repository.get_admin_recent_users(limit=5)
        recent_refund_requests = await self.dashboard_repository.get_admin_recent_refund_requests(limit=5)
        recent_payouts = await self.dashboard_repository.get_admin_recent_payouts(limit=5)
        top_properties = await self.dashboard_repository.get_admin_top_properties(limit=5)

        return {
            "bookings_summary": bookings_summary,
            "revenue_summary": revenue_summary,
            "properties_summary": properties_summary,
            "users_summary": users_summary,
            "refunds_summary": refunds_summary,
            "payouts_summary": payouts_summary,
            "occupancy_today": occupancy_today,
            "revenue_trends": revenue_trends,
            "recent_bookings": recent_bookings,
            "recent_host_requests": recent_host_requests,
            "recent_users": recent_users,
            "recent_refund_requests": recent_refund_requests,
            "recent_payouts": recent_payouts,
            "top_properties": top_properties,
        }


    async def get_admin_summary(self) -> Dict[str, Any]:
        """Fetch quick KPI cards summary for Admin."""
        bookings_summary = await self.dashboard_repository.get_admin_booking_stats()
        revenue_summary = await self.dashboard_repository.get_admin_revenue_stats()
        properties_summary = await self.dashboard_repository.get_admin_property_stats()
        users_summary = await self.dashboard_repository.get_admin_user_stats()
        refunds_summary = await self.dashboard_repository.get_admin_refund_stats()
        payouts_summary = await self.dashboard_repository.get_admin_payout_stats()
        occupancy_today = await self.dashboard_repository.get_admin_occupancy_today()

        return {
            "bookings_summary": bookings_summary,
            "revenue_summary": revenue_summary,
            "properties_summary": properties_summary,
            "users_summary": users_summary,
            "refunds_summary": refunds_summary,
            "payouts_summary": payouts_summary,
            "occupancy_today": occupancy_today,
        }

    async def get_vendor_dashboard(self, vendor_id: int, months: int = 12) -> Dict[str, Any]:
        """Fetch full vendor dashboard dataset scoped to properties owned by this vendor."""
        bookings_summary = await self.dashboard_repository.get_vendor_booking_stats(vendor_id=vendor_id)
        revenue_summary = await self.dashboard_repository.get_vendor_revenue_stats(vendor_id=vendor_id)
        properties_summary = await self.dashboard_repository.get_vendor_property_stats(vendor_id=vendor_id)
        payouts_summary = await self.dashboard_repository.get_vendor_payout_stats(vendor_id=vendor_id)
        reviews_summary = await self.dashboard_repository.get_vendor_review_stats(vendor_id=vendor_id)
        occupancy_today = await self.dashboard_repository.get_vendor_occupancy_today(vendor_id=vendor_id)
        revenue_trends = await self.dashboard_repository.get_vendor_revenue_trends(vendor_id=vendor_id, months=months)
        recent_bookings = await self.dashboard_repository.get_vendor_recent_bookings(vendor_id=vendor_id, limit=5)
        upcoming_bookings = await self.dashboard_repository.get_vendor_upcoming_bookings(vendor_id=vendor_id, limit=5)
        recent_payouts = await self.dashboard_repository.get_vendor_recent_payouts(vendor_id=vendor_id, limit=5)
        top_properties = await self.dashboard_repository.get_vendor_top_properties(vendor_id=vendor_id, limit=5)

        return {
            "bookings_summary": bookings_summary,
            "revenue_summary": revenue_summary,
            "properties_summary": properties_summary,
            "payouts_summary": payouts_summary,
            "reviews_summary": reviews_summary,
            "occupancy_today": occupancy_today,
            "revenue_trends": revenue_trends,
            "recent_bookings": recent_bookings,
            "upcoming_bookings": upcoming_bookings,
            "recent_payouts": recent_payouts,
            "top_properties": top_properties,
        }

    async def get_vendor_summary(self, vendor_id: int) -> Dict[str, Any]:
        """Fetch quick KPI cards summary for Vendor."""
        bookings_summary = await self.dashboard_repository.get_vendor_booking_stats(vendor_id=vendor_id)
        revenue_summary = await self.dashboard_repository.get_vendor_revenue_stats(vendor_id=vendor_id)
        properties_summary = await self.dashboard_repository.get_vendor_property_stats(vendor_id=vendor_id)
        payouts_summary = await self.dashboard_repository.get_vendor_payout_stats(vendor_id=vendor_id)
        reviews_summary = await self.dashboard_repository.get_vendor_review_stats(vendor_id=vendor_id)
        occupancy_today = await self.dashboard_repository.get_vendor_occupancy_today(vendor_id=vendor_id)

        return {
            "bookings_summary": bookings_summary,
            "revenue_summary": revenue_summary,
            "properties_summary": properties_summary,
            "payouts_summary": payouts_summary,
            "reviews_summary": reviews_summary,
            "occupancy_today": occupancy_today,
        }


