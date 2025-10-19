from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


class TestModelsProviderAvailability:
    """Test suite for Models Provider Availability endpoint."""

    @patch("api.routers.models.os.environ.get")
    @patch("api.routers.models.AIFactory.get_available_providers")
    def test_generic_env_var_enables_all_modes(self, mock_esperanto, mock_env):
        """Test that OPENAI_COMPATIBLE_BASE_URL enables all 4 modes."""

        # Mock environment: only generic var is set
        def env_side_effect(key):
            if key == "OPENAI_COMPATIBLE_BASE_URL":
                return "http://localhost:1234/v1"
            return None

        mock_env.side_effect = env_side_effect

        # Mock Esperanto response
        mock_esperanto.return_value = {
            "language": ["openai-compatible"],
            "embedding": ["openai-compatible"],
            "speech_to_text": ["openai-compatible"],
            "text_to_speech": ["openai-compatible"],
        }

        response = client.get("/api/models/providers")

        assert response.status_code == 200
        data = response.json()

        # openai-compatible should be available
        assert "openai-compatible" in data["available"]

        # Should support all 4 types
        assert "openai-compatible" in data["supported_types"]
        supported = data["supported_types"]["openai-compatible"]
        assert "language" in supported
        assert "embedding" in supported
        assert "speech_to_text" in supported
        assert "text_to_speech" in supported
        assert len(supported) == 4

    @patch("api.routers.models.os.environ.get")
    @patch("api.routers.models.AIFactory.get_available_providers")
    def test_mode_specific_env_vars_llm_embedding(self, mock_esperanto, mock_env):
        """Test mode-specific env vars (LLM + EMBEDDING) enable only those 2 modes."""

        # Mock environment: only LLM and EMBEDDING specific vars are set
        def env_side_effect(key):
            if key == "OPENAI_COMPATIBLE_BASE_URL_LLM":
                return "http://localhost:1234/v1"
            if key == "OPENAI_COMPATIBLE_BASE_URL_EMBEDDING":
                return "http://localhost:8080/v1"
            return None

        mock_env.side_effect = env_side_effect

        # Mock Esperanto response
        mock_esperanto.return_value = {
            "language": ["openai-compatible"],
            "embedding": ["openai-compatible"],
            "speech_to_text": ["openai-compatible"],
            "text_to_speech": ["openai-compatible"],
        }

        response = client.get("/api/models/providers")

        assert response.status_code == 200
        data = response.json()

        # openai-compatible should be available
        assert "openai-compatible" in data["available"]

        # Should support only language and embedding
        assert "openai-compatible" in data["supported_types"]
        supported = data["supported_types"]["openai-compatible"]
        assert "language" in supported
        assert "embedding" in supported
        assert "speech_to_text" not in supported
        assert "text_to_speech" not in supported
        assert len(supported) == 2

    @patch("api.routers.models.os.environ.get")
    @patch("api.routers.models.AIFactory.get_available_providers")
    def test_no_env_vars_set(self, mock_esperanto, mock_env):
        """Test that openai-compatible is not available when no env vars are set."""

        # Mock environment: no openai-compatible vars are set
        def env_side_effect(key):
            return None

        mock_env.side_effect = env_side_effect

        # Mock Esperanto response
        mock_esperanto.return_value = {
            "language": ["openai-compatible"],
            "embedding": ["openai-compatible"],
        }

        response = client.get("/api/models/providers")

        assert response.status_code == 200
        data = response.json()

        # openai-compatible should NOT be available
        assert "openai-compatible" not in data["available"]
        assert "openai-compatible" in data["unavailable"]

        # Should not have supported_types entry
        assert "openai-compatible" not in data["supported_types"]

    @patch("api.routers.models.os.environ.get")
    @patch("api.routers.models.AIFactory.get_available_providers")
    def test_mixed_config_generic_and_mode_specific(self, mock_esperanto, mock_env):
        """Test mixed config: generic + mode-specific (generic should enable all)."""

        # Mock environment: both generic and mode-specific vars are set
        def env_side_effect(key):
            if key == "OPENAI_COMPATIBLE_BASE_URL":
                return "http://localhost:1234/v1"
            if key == "OPENAI_COMPATIBLE_BASE_URL_LLM":
                return "http://localhost:5678/v1"
            return None

        mock_env.side_effect = env_side_effect

        # Mock Esperanto response
        mock_esperanto.return_value = {
            "language": ["openai-compatible"],
            "embedding": ["openai-compatible"],
            "speech_to_text": ["openai-compatible"],
            "text_to_speech": ["openai-compatible"],
        }

        response = client.get("/api/models/providers")

        assert response.status_code == 200
        data = response.json()

        # openai-compatible should be available
        assert "openai-compatible" in data["available"]

        # Generic var enables all, so all 4 should be supported
        assert "openai-compatible" in data["supported_types"]
        supported = data["supported_types"]["openai-compatible"]
        assert "language" in supported
        assert "embedding" in supported
        assert "speech_to_text" in supported
        assert "text_to_speech" in supported
        assert len(supported) == 4

    @patch("api.routers.models.os.environ.get")
    @patch("api.routers.models.AIFactory.get_available_providers")
    def test_individual_mode_llm_only(self, mock_esperanto, mock_env):
        """Test individual mode-specific var (LLM only)."""

        # Mock environment: only LLM specific var is set
        def env_side_effect(key):
            if key == "OPENAI_COMPATIBLE_BASE_URL_LLM":
                return "http://localhost:1234/v1"
            return None

        mock_env.side_effect = env_side_effect

        # Mock Esperanto response
        mock_esperanto.return_value = {
            "language": ["openai-compatible"],
            "embedding": ["openai-compatible"],
            "speech_to_text": ["openai-compatible"],
            "text_to_speech": ["openai-compatible"],
        }

        response = client.get("/api/models/providers")

        assert response.status_code == 200
        data = response.json()

        # Should support only language
        supported = data["supported_types"]["openai-compatible"]
        assert supported == ["language"]

    @patch("api.routers.models.os.environ.get")
    @patch("api.routers.models.AIFactory.get_available_providers")
    def test_individual_mode_embedding_only(self, mock_esperanto, mock_env):
        """Test individual mode-specific var (EMBEDDING only)."""

        # Mock environment: only EMBEDDING specific var is set
        def env_side_effect(key):
            if key == "OPENAI_COMPATIBLE_BASE_URL_EMBEDDING":
                return "http://localhost:8080/v1"
            return None

        mock_env.side_effect = env_side_effect

        # Mock Esperanto response
        mock_esperanto.return_value = {
            "language": ["openai-compatible"],
            "embedding": ["openai-compatible"],
            "speech_to_text": ["openai-compatible"],
            "text_to_speech": ["openai-compatible"],
        }

        response = client.get("/api/models/providers")

        assert response.status_code == 200
        data = response.json()

        # Should support only embedding
        supported = data["supported_types"]["openai-compatible"]
        assert supported == ["embedding"]

    @patch("api.routers.models.os.environ.get")
    @patch("api.routers.models.AIFactory.get_available_providers")
    def test_individual_mode_stt_only(self, mock_esperanto, mock_env):
        """Test individual mode-specific var (STT only)."""

        # Mock environment: only STT specific var is set
        def env_side_effect(key):
            if key == "OPENAI_COMPATIBLE_BASE_URL_STT":
                return "http://localhost:9000/v1"
            return None

        mock_env.side_effect = env_side_effect

        # Mock Esperanto response
        mock_esperanto.return_value = {
            "language": ["openai-compatible"],
            "embedding": ["openai-compatible"],
            "speech_to_text": ["openai-compatible"],
            "text_to_speech": ["openai-compatible"],
        }

        response = client.get("/api/models/providers")

        assert response.status_code == 200
        data = response.json()

        # Should support only speech_to_text
        supported = data["supported_types"]["openai-compatible"]
        assert supported == ["speech_to_text"]

    @patch("api.routers.models.os.environ.get")
    @patch("api.routers.models.AIFactory.get_available_providers")
    def test_individual_mode_tts_only(self, mock_esperanto, mock_env):
        """Test individual mode-specific var (TTS only)."""

        # Mock environment: only TTS specific var is set
        def env_side_effect(key):
            if key == "OPENAI_COMPATIBLE_BASE_URL_TTS":
                return "http://localhost:9000/v1"
            return None

        mock_env.side_effect = env_side_effect

        # Mock Esperanto response
        mock_esperanto.return_value = {
            "language": ["openai-compatible"],
            "embedding": ["openai-compatible"],
            "speech_to_text": ["openai-compatible"],
            "text_to_speech": ["openai-compatible"],
        }

        response = client.get("/api/models/providers")

        assert response.status_code == 200
        data = response.json()

        # Should support only text_to_speech
        supported = data["supported_types"]["openai-compatible"]
        assert supported == ["text_to_speech"]
