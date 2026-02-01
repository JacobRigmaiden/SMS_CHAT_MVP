import uuid


class PhoneVerificationService:
    def send_verification_code(self, phone_number: str) -> str:
        return str(uuid.uuid4())

    def check_verification_code(self, phone_number: str, code: str) -> bool:
        return len(code) == 6 and code.isdigit()


_service = PhoneVerificationService()


def get_verification_service() -> PhoneVerificationService:
    return _service
