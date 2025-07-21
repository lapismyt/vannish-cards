def validate_username(username: str) -> bool:
    if not (17 > len(username) > 4):
        return False

    if not username.isalnum():
        return False

    return True


def validate_user_id(user_id: str) -> bool:
    if not (20 > len(user_id) > 0):
        return False

    if not user_id.isdigit():
        return False

    return True
