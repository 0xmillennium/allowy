class TestLiveness:
    async def test_live_returns_200(self, client):
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestReadiness:
    async def test_ready_returns_200_when_all_healthy(self, client):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert len(data["components"]) == 2
        assert all(c["status"] == "healthy" for c in data["components"])

    async def test_ready_returns_503_when_scheduler_down(self, client, fake_scheduler):
        fake_scheduler.stopped = True
        fake_scheduler.started = False
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        sched = next(c for c in data["components"] if c["name"] == "scheduler")
        assert sched["status"] == "unhealthy"

    async def test_ready_includes_component_names(self, client):
        response = await client.get("/health/ready")
        data = response.json()
        names = {c["name"] for c in data["components"]}
        assert names == {"database", "scheduler"}
