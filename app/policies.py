"""Small shared policy predicates; callers still own locks and transactions."""


def requires_mfa(user, config):
    return bool(user.mfa_secret or (user.role == "admin" and config.admin_mfa_required))


def eligible_account(user):
    return bool(user and user.active and user.approved and user.email_verified)
