from pydantic import BaseModel


class StatsResponse(BaseModel):
    total_vehicles: int
    today_access_total: int
    today_denied_total: int
    active_subscriptions: int = 0
    expiring_soon_count: int = 0
