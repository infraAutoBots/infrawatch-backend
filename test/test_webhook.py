import pytest
import aiohttp
from app.webhook import send_webhook


@pytest.mark.asyncio
async def test_send_webhook(mocker):
    mock_session = mocker.patch("aiohttp.ClientSession")
    mock_post = mock_session.return_value.__aenter__.return_value.post
    mock_post.return_value.__aenter__.return_value = None
    payload = {"message": "Test"}
    await send_webhook("https://example.com", payload)
    mock_post.assert_called_with("https://example.com", json=payload)

@pytest.mark.asyncio
async def test_send_webhook_failure(mocker):
    mock_session = mocker.patch("aiohttp.ClientSession")
    mock_post = mock_session.return_value.__aenter__.return_value.post
    mock_post.side_effect = aiohttp.ClientError
    payload = {"message": "Test"}
    # Não deve levantar erro
    await send_webhook("https://example.com", payload)
    mock_post.assert_called()
