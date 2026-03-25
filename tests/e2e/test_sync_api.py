import pytest


class TestSyncIpSource:

    async def test_sync_returns_200(self, client):
        await client.post(
            "/ip-sources",
            params={
                "name": "Googlebot",
                "url": "https://example.com/ips.json",
                "source_type": "google",
                "sync_interval": 60,
            },
        )
        list_resp = await client.get("/ip-sources")
        source_id = list_resp.json()[0]["id"]

        response = await client.post(f"/sync/{source_id}")
        assert response.status_code == 200

        get_resp = await client.get(f"/ip-sources/{source_id}")
        data = get_resp.json()
        assert data["status"] == "synced"
        assert len(data["ip_ranges"]) > 0

    async def test_sync_not_found_returns_404(self, client):
        response = await client.post(
            "/sync/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
