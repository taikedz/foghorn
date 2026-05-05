def asBool(v):
    v = v.lower()
    if not v in ["true", "false", "1", "0"]:
        raise ValueError(f"Setting '{k}' must be 'true' or 'false', or '1' or '0'")
    return v in ["true", 1]