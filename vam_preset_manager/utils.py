def parse_preset_name(name: str):
    # 去除 Preset_ 前缀
    if name.startswith("Preset_"):
        name = name[7:]
    parts = name.split('.')
    if len(parts) >= 3:
        author = parts[0]
        title = '.'.join(parts[1:-1])
        version = parts[-1]
        return author, title, version
    elif len(parts) == 2:
        return parts[0], parts[1], None
    else:
        return None, name, None