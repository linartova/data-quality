
class Patient:
    def __init__(self, identifier, sex, age):
        self.identifier = identifier
        self.sex = sex
        self.age = age


class Condition:
    def __init__(self, histopathology, age_at_primary_diagnosis, date_diagnosis):
        self.age_at_primary_diagnosis = age_at_primary_diagnosis
        self.date_diagnosis = date_diagnosis
        self.histopathology = histopathology


class Specimen:
    def __init__(self, sample_material_type, year_of_sample_connection):
        self.year_of_sample_connection = year_of_sample_connection
        self.sample_material_type = sample_material_type
