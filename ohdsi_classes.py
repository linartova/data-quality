
class Patient:
    """
    A class representing a Person.

    Attributes:
        gender_concept_id (int) : The ID representing gender of Person.
        year_of_birth (int) : The year of birth of Person.
        person_source_value (str) : The original identifier.
    """
    def __init__(self, identifier, sex, year_of_birth):
        self.gender_concept_id = sex
        self.year_of_birth = year_of_birth
        self.person_source_value = identifier


class ObservationPeriod:
    """
    A class representing an Observation Period.

    Attributes:
        start_date (date) : The beginning of medical observation.
        start_date (date) : The end of medical observation.
    """
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date


class ConditionOccurrence:
    """
    A class representing a Condition Occurrence.

    Attributes:
        condition_concept_id (int) : ID of condition.
        condition_start_date (date) : Start of diagnosis.
        condition_source_value (str) : Original condition.
    """
    def __init__(self, histopathology, date_diagnosis):
        self.condition_concept_id = histopathology
        self.condition_start_date = date_diagnosis
        self.condition_source_value = histopathology


class Specimen:
    """
    A class representing a Specimen.

    Attributes:
        specimen_concept_id (int) : The ID of type of specimen.
        specimen_date (date) : Year of specimen collection.
        specimen_source_id (int) : Original specimen ID.
        specimen_source_value (str) : The type of specimen.
    """
    def __init__(self, sample_material_type, year_of_sample_connection, sample_id):
        self.specimen_concept_id = sample_material_type
        self.specimen_date = year_of_sample_connection
        self.specimen_source_id = sample_id
        self.specimen_source_value = sample_material_type


class DrugExposure:
    """
    A class representing a Drug Exposure.

    Attributes:
        drug_concept_id (int) : The ID of drug.
        drug_exposure_start_date (date) : Start of usage of drug.
        drug_exposure_start_datetime (datetime) : Start of usage of drug with time.
        drug_exposure_end_date (date) : End of usage of drug.
        drug_exposure_end_datetime (datetime) : End of usage of drug with time.
        drug_source_value (str) : Original value of Pharmacotherapy.
    """
    def __init__(self, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date, drug_source_value):
        self.drug_concept_id = drug_concept_id
        self.drug_exposure_start_date = drug_exposure_start_date
        self.drug_exposure_start_datetime = drug_exposure_start_date
        self.drug_exposure_end_date = drug_exposure_end_date
        self.drug_exposure_end_datetime = drug_exposure_end_date
        self.drug_source_value = drug_source_value


class ProcedureOccurrence:
    """
    A class representing a Procedure Occurrence.

    Attributes:
        procedure_concept_id (int) : The ID of procedure.
        procedure_date (date) : The date of procedure.
        procedure_source_value (str) : Original value of procedure.
    """
    def __init__(self, procedure_concept_id, procedure_date, procedure_source_value):
        self.procedure_concept_id = procedure_concept_id
        self.procedure_date = procedure_date
        self.procedure_source_value = procedure_source_value
