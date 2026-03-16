current_table = None


def set_table(name: str):
    global current_table
    current_table = name


def get_table():
    return current_table