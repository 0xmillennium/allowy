import pytest


class TestConfigEndpoints:

    async def test_get_nginx_config_returns_200(self, client, fake_filer):
        await fake_filer.write("allow 192.168.1.0/24;\ndeny all;", "nginx.conf")
        response = await client.get("/configs/nginx")
        assert response.status_code == 200
        assert "allow 192.168.1.0/24;" in response.text

    async def test_get_traefik_config_returns_200(self, client, fake_filer):
        await fake_filer.write("http:\n  middlewares:", "traefik.yml")
        response = await client.get("/configs/traefik")
        assert response.status_code == 200
        assert "http:" in response.text

    async def test_get_raw_config_returns_200(self, client, fake_filer):
        await fake_filer.write("192.168.1.0/24\n2001:4860::/32", "raw.txt")
        response = await client.get("/configs/raw")
        assert response.status_code == 200
        assert "192.168.1.0/24" in response.text

    async def test_config_returns_empty_when_no_data(self, client):
        response = await client.get("/configs/nginx")
        assert response.status_code == 200
        assert response.text == ""
