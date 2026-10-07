"""Small shared policy predicates; callers still own locks and transactions."""


def requires_mfa(user, config):
    return bool(user.mfa_secret or (user.role == "admin" and config.admin_mfa_required))
