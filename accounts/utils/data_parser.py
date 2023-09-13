def remove_extra_spaces(data):
    for key, value in data.items():
        if value and type(value) == str:
            # To remove extra whitespace from the start and end of value
            data[key] = value.strip()
    return data
