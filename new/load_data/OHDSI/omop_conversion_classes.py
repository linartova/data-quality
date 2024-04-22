class Patient:
    def __init__(self, identifier, sex, year_of_birth):
        self.gender_concept_id = sex
        self.year_of_birth = year_of_birth
        self.person_source_value = identifier


class ObservationPeriod:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date


class ConditionOccurrence:
    def __init__(self, histopathology, date_diagnosis):
        self.condition_concept_id = histopathology
        self.condition_start_date = date_diagnosis
        self.condition_source_value = histopathology


class Specimen:
    def __init__(self, sample_material_type, year_of_sample_connection, sample_id):
        self.specimen_concept_id = sample_material_type
        self.specimen_date = year_of_sample_connection
        self.specimen_source_id = sample_id
        self.specimen_source_value = sample_material_type


class DrugExposure:
    def __init__(self, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date):
        self.drug_concept_id = drug_concept_id
        self.drug_exposure_start_date = drug_exposure_start_date
        self.drug_exposure_end_date = drug_exposure_end_date


class ProcedureOccurrence:
    def __init__(self, procedure_concept_id, procedure_date, procedure_source_value):
        self.procedure_concept_id = procedure_concept_id
        self.procedure_date = procedure_date
        self.procedure_source_value = procedure_source_value
