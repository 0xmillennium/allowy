import pytest


class TestCreateIpSource:

    async def test_create_returns_201(self, client):
        response = await client.post(
            "/ip-sources",
            params={
                "name": "Googlebot",
                "url": "https://example.com/ips.json",
                "source_type": "google",
                "sync_interval": 60,
            },
        )
        assert response.status_code == 201

    async def test_created_source_is_retrievable(self, client):
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
        data = list_resp.json()[0]
        assert data["name"] == "Googlebot"
        assert data["url"] == "https://example.com/ips.json"
        assert data["source_type"] == "google"
        assert data["sync_interval"] == 60
        assert data["status"] == "created"
        assert "id" in data

    async def test_create_duplicate_url_returns_409(self, client):
        params = {
            "name": "Googlebot",
            "url": "https://example.com/ips.json",
            "source_type": "google",
            "sync_interval": 60,
        }
        await client.post("/ip-sources", params=params)
        response = await client.post("/ip-sources", params=params)
        assert response.status_code == 409

    async def test_create_invalid_interval_returns_422(self, client):
        response = await client.post(
            "/ip-sources",
            params={
                "name": "Googlebot",
                "url": "https://example.com/ips.json",
                "source_type": "google",
                "sync_interval": 2,
            },
        )
        assert response.status_code == 422


class TestListIpSources:

    async def test_list_returns_200_with_list(self, client):
        await client.post(
            "/ip-sources",
            params={
                "name": "Googlebot",
                "url": "https://example.com/ips.json",
                "source_type": "google",
                "sync_interval": 60,
            },
        )
        response = await client.get("/ip-sources")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    async def test_list_empty_returns_200(self, client):
        response = await client.get("/ip-sources")
        assert response.status_code == 200
        assert response.json() == []


class TestRetrieveIpSource:

    async def test_get_returns_200(self, client):
        create_resp = await client.post(
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

        response = await client.get(f"/ip-sources/{source_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Googlebot"
        assert data["sync_interval"] == 60

    async def test_get_not_found_returns_404(self, client):
        response = await client.get(
            "/ip-sources/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestDeleteIpSource:

    async def test_delete_returns_204(self, client):
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

        response = await client.delete(f"/ip-sources/{source_id}")
        assert response.status_code == 204

    async def test_delete_not_found_returns_404(self, client):
        response = await client.delete(
            "/ip-sources/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestUpdateSyncInterval:

    async def test_update_interval_returns_200(self, client):
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

        response = await client.patch(
            f"/ip-sources/{source_id}/interval",
            params={"sync_interval": 120},
        )
        assert response.status_code == 200

        get_resp = await client.get(f"/ip-sources/{source_id}")
        data = get_resp.json()
        assert data["sync_interval"] == 120


class TestPauseResume:

    async def test_pause_returns_200(self, client):
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

        response = await client.post(f"/ip-sources/{source_id}/pause")
        assert response.status_code == 200

    async def test_resume_returns_200(self, client):
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
        await client.post(f"/ip-sources/{source_id}/pause")

        response = await client.post(f"/ip-sources/{source_id}/resume")
        assert response.status_code == 200

    async def test_pause_all_returns_200(self, client):
        response = await client.post("/ip-sources/pause-all")
        assert response.status_code == 200

    async def test_resume_all_returns_200(self, client):
        response = await client.post("/ip-sources/resume-all")
        assert response.status_code == 200
