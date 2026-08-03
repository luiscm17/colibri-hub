"""Re-export shared error_json_response for backward compatibility."""

from infra.http.error_envelope import error_json_response

__all__ = ["error_json_response"]
