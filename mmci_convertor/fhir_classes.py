
class Patient:
    """
    A class representing a Patient.

    Attributes:
        sex (int) : The sex of Patient.
        age (int) : The age of Patient.
        identifier (str) : The original identifier.
    """
    def __init__(self, identifier, sex, age):
        self.identifier = identifier
        self.sex = sex
        self.age = age


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
        year_of_sample_connection (int) : Year of specimen collection.
        sample_material_type (str) : The type of specimen.
    """
    def __init__(self, sample_material_type, year_of_sample_connection):
        self.year_of_sample_connection = year_of_sample_connection
        self.sample_material_type = sample_material_type

