from types import SimpleNamespace

from coinappraiser import vision


def test_identify_coin_sends_both_sides_in_one_model_request(monkeypatch) -> None:
    request = {}

    class FakeResponses:
        def create(self, **kwargs):
            request.update(kwargs)
            return SimpleNamespace(
                output_text=(
                    '{"country":"France","denomination":"1 franc","year":1935,'
                    '"mint":null,"metal":null,"description":"Morlon coin",'
                    '"confidence":0.95}'
                )
            )

    class FakeOpenAI:
        def __init__(self, api_key):
            self.responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(vision, "OpenAI", FakeOpenAI)

    result = vision.identify_coin(
        [(b"front", "image/jpeg"), (b"back", "image/png")]
    )

    content = request["input"][0]["content"]
    images = [item for item in content if item["type"] == "input_image"]
    assert len(images) == 2
    assert images[0]["image_url"].startswith("data:image/jpeg;base64,")
    assert images[1]["image_url"].startswith("data:image/png;base64,")
    assert "both views together" in content[0]["text"]
    assert result.year == 1935
