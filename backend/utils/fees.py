def calculate_kumbalo_fee(price: float) -> float:
    """
    Calcula la comisión fija basada en el valor de la moto.
    Estrategia "Adiós al 3%":
    - >= 20,000,000 -> $500,000
    - 10,000,000 - 19,999,999 -> $250,000
    - < 10,000,000 -> $150,000
    """
    if price >= 20000000:
        return 500000.0
    elif price >= 10000000:
        return 250000.0
    else:
        return 150000.0
