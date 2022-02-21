import pytest
from sanic_testing import TestManager

from app import app as server


@pytest.yield_fixture
def app():
    TestManager(server)
    yield server


# @pytest.fixture(scope="session", autouse=True)
# def initialize_tests(request):
#     db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
#     initializer(["tests"], db_url=db_url, app_label="models")
#     request.addfinalizer(finalizer)


@pytest.mark.asyncio
async def test_home(app):
    req, res = await app.asgi_client.get('/')
    assert res.status == 200
    assert res.json == {'message': 'hello world'}


@pytest.mark.asyncio
async def test_login(app):
    req, res = await app.asgi_client.post('/login', json={
        'email': 'email@email.com',
        'password': 'password'
    })
    print(res.json)
    assert res.status == 200
