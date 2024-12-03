
class Patient:
    """
    A class representing a Patient.

    Attributes:
        identifier (str) : The original identifier.
        sex (int) : The sex of Patient.
        birth_date (FHIRDate) : The birth_date of Patient.
    """
    def __init__(self, identifier, sex, birth_date):
        self.identifier = identifier
        self.sex = sex
        self.birth_date = birth_date


class Condition:
    """
    A class representing a Condition.

    Attributes:
        date_diagnosis (date) : Start of diagnosis.
        histopathology (str) : Histopathology.
    """
    def __init__(self, histopathology, date_diagnosis):
        self.date_diagnosis = date_diagnosis
        self.histopathology = histopathology


class Specimen:
    """
    A class representing a Specimen.

    Attributes:
        identifier (str) : The external identifier.
        sample_material_type_code (int) : The type of specimen.
        sample_material_type_display (str) : The type of specimen.
        year_of_sample_connection (int) : Year of specimen collection.
    """
    def __init__(self, identifier, sample_material_type_code, sample_material_type_display, year_of_sample_connection):
        self.identifier = identifier
        self.year_of_sample_connection = year_of_sample_connection
        self.sample_material_type_code = sample_material_type_code
        self.sample_material_type_display = sample_material_type_display
