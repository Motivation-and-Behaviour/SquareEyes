def load_main_classes():
    main_classes = {
        0: {"label": "Desktop Computer", "model": "Screens Only"},
        1: {"label": "Computer Monitor", "model": "Screens Only"},
        2: {"label": "Laptop Computer", "model": "Screens Only"},
        3: {"label": "Mobile Phone", "model": "Screens Only"},
        4: {"label": "iPod", "model": "Screens Only"},
        5: {"label": "Tablet", "model": "Screens Only"},
        6: {"label": "Television", "model": "Screens Only"},
        7: {"label": "Computer Mouse", "model": "Screens + Indicators"},
        8: {"label": "Computer Keyboard", "model": "Screens + Indicators"},
        9: {"label": "Remote", "model": "Screens + Indicators"},
    }

    return main_classes


def load_coco_classes():
    coco_classes = {
        "62": 6,  # tv        -> Television
        "63": 2,  # laptop    -> Laptop Computer
        "64": 7,  # mouse     -> Computer Mouse
        "65": 9,  # remote    -> Remote
        "66": 8,  # keyboard  -> Computer Keyboard
        "67": 3,  # cellphone -> Mobile Phone
    }

    return coco_classes


def load_obj365_classes():
    obj365_classes = {
        "61": 3,  #  CellPhone   -> Mobile Phone
        "73": 2,  #  Laptop      -> Laptop Computer
        "106": 8,  # keyboard    -> Computer Keyboard
        "115": 7,  # Mouse       -> Computer Mouse
        "132": 9,  # Remote      -> Remote
        "159": 0,  # ComputerBox -> Desktop Computer
    }

    return obj365_classes


def load_imagenet_classes():
    imagenet_classes = {
        "n03180011": 0,  # desktop computer -> Desktop Computer
        "n03782006": 1,  # monitor -> Computer Monitor
        "n03642806": 2,  # laptop, laptop computer -> Laptop Computer
        "n03832673": 2,  # notebook, notebook computer -> Laptop Computer
        "n02992529": 3,  # cellular telephone, cellular phone, cellphone, cell, mobile phone -> Mobile Phone
        "n03584254": 4,  # iPod -> iPod
        "n03485407": 5,  # hand-held computer, hand-held microcomputer -> Tablet
        "n04404412": 6,  # television, television system -> Television
        "n04152593": 6,  # screen, CRT screen -> Television
        "n03793489": 7,  # mouse, computer mouse -> Computer Mouse
        "n03085013": 8,  # computer keyboard, keypad -> Computer Keyboard
    }

    return imagenet_classes


def load_openimages_classes():
    openimages_classes = {
        "/m/02522": 1,  # Computer monitor -> Computer Monitor
        "/m/01c648": 2,  # Laptop -> Laptop Computer
        "/m/050k8": 3,  # Mobile phone -> Mobile Phone
        "/m/0mcx2": 4,  # Ipod -> iPod
        "/m/07c52": 6,  # Television -> Television
        "/m/020lf": 7,  # Computer mouse -> Computer Mouse
        "/m/01m2v": 8,  # Computer keyboard -> Computer Keyboard
        "/m/0qjjc": 9,  # Remote control -> Remote
    }

    return openimages_classes
