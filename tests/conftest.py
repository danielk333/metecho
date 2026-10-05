import pytest


def pytest_addoption(parser):
    parser.addoption("--plot", action="store_true")
    parser.addoption("--impl", action="store", default="numpy", help="analysis implementation")


@pytest.fixture(scope="session")
def plot(request):
    return request.config.getoption("--plot")
