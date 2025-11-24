def assign_tier(ev):
    if ev>=15: return "DIME"
    if ev>=5: return "NICKEL"
    return "STANDARD"