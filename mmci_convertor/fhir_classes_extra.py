
class Patient:
    """
    A class representing a Patient.

    Attributes:
        identifier (str) : The original identifier.
        deceased_boolean (bool) : If patient is alive, this value is false.
        timestamp (date) : If the patient is deceased,
        sex (int) : The sex of Patient.
        birth_date (FHIRDate) : The birth_date of Patient.
    """
    def __init__(self, identifier, deceased_boolean, timestamp, sex, birth_date):
        self.identifier = identifier
        self.deceased_boolean = deceased_boolean
        self.timestamp = timestamp
        self.sex = sex
        self.birth_date = birth_date


class TimeObservation:
    """
    A class representing time information about Patient.

    Attributes:
        overall_survival (str) : Number of weeks between Date of diagnosis and Timestamp of last update of vital status.
        last_update (str) : Timestamp of last update of vital status = date of death or last clinical checkup.
    """
    def __init__(self, overall_survival, last_update):
        self.overall_survival = overall_survival
        self.last_update = last_update


class TNM:
    """
    A class representing tnm and other histopathological information about Patient.

    Attributes:
         pT_code (str) : Primary Tumor code.
         pT_display (str) : Primary Tumor display.
         pN_code (str) : Regional lymph nodes code.
         pN_display (str) : Regional lymph nodes display.
         pM_code (str) : Distant metastasis code.
         pM_display (str) : Distant metastasis display.
         uicc_stage_code (str) : Stage code.
         uicc_stage_display (str) : Stage display.
         uicc_version_code (str) : UICC version code.
         uicc_version_display (str) : UICC version display.
         grade_code (str) : Grade code.
         grade_display (str) : Grade display.
         morphology_code (str) : Morphology code.
         morphology_display (str) : Morphology display.
    """
    def __init__(self, pT_code, pT_display, pN_code, pN_display,
                 pM_code, pM_display, uicc_stage_code, uicc_stage_display,
                 uicc_version_code, uicc_version_display, grade_code,
                 grade_display, morphology_code, morphology_display):
        self.pT_code = pT_code
        self.pT_display = pT_display
        self.pN_code = pN_code
        self.pN_display = pN_display
        self.pM_code = pM_code
        self.pM_display = pM_display
        self.uicc_stage_code = uicc_stage_code
        self.uicc_stage_display = uicc_stage_display
        self.uicc_version_code = uicc_version_code
        self.uicc_version_display = uicc_version_display
        self.grade_code = grade_code
        self.grade_display = grade_display
        self.morphology_code = morphology_code
        self.morphology_display = morphology_display


class Surgery:
    """
    A class representing Surgery.

    Attributes:
        start (str) : Supposed date of surgery, calculated from
        number of week between surgery and date of diagnosis and
        date of diagnosis.
        surgery_name (str) : Surgery type display.
        surgery_code (int) : Surgery type code.
        surgery_radicality_name (str) : Surgery radicality display.
        surgery_radicality_code (int) : Surgery radicality code.
        body_site_name (str) : Location of the tumor display.
        body_site_code (int) : Location of the tumor code.
        note (str) : Space for "Other surgery type".
    """
    def __init__(self, start, surgery_name, surgery_code, surgery_radicality_name,
                 surgery_radicality_code, body_site_name, body_site_code, note):
        self.start = start
        self.surgery_name = surgery_name
        self.surgery_code = surgery_code
        self.surgery_radicality_name = surgery_radicality_name
        self.surgery_radicality_code = surgery_radicality_code
        self.body_site_name = body_site_name
        self.body_site_code = body_site_code
        self.note = note


class RadiationTherapy:
    """
    A class representing Radiation Therapy.

    Attributes:
        start (FHIRDate) : Date of start of radiation therapy derived from number of weeks between therapy and date of diagnosis.
        end (FHIRDate) : Date of end of radiation therapy derived from number of weeks between therapy and date of diagnosis.
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end


class TargetedTherapy:
    """
    A class representing Targeted Therapy.

    Attributes:
        start (FHIRDate) : Date of start of targeted therapy derived from number of weeks between therapy and date of diagnosis.
        end (FHIRDate) : Date of end of targeted therapy derived from number of weeks between therapy and date of diagnosis.
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end


class Response:
    """
    A class representing Response to therapy.

    Attributes:
        code (int) : Specific response code.
        display (str) : Specific response display.
        time (int) : Date of start of evaluation of response derived
         from number of weeks between therapy and date of diagnosis.
    """
    def __init__(self, code, display, time):
        self.code = code
        self.display = display
        self.time = time


# class Medication:
#     def __init__(self, start, end, scheme, other):
#         self.start = start
#         self.end = end
#         self.scheme = scheme
#         self.other = other
#

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
    def __init__(self, identifier, sample_material_type_code,
                 sample_material_type_display, year_of_sample_connection):
        self.identifier = identifier
        self.year_of_sample_connection = year_of_sample_connection
        self.sample_material_type_code = sample_material_type_code
        self.sample_material_type_display = sample_material_type_display


class Record:
    """
     A class representing a container for all classes needed for building resources.

    Attributes:
        patient (Patient) : Class Patient for resource Patient.
        time_observation (TimeObservation) : Class TimeObservation for resource Observation.
        responses (List[Response]) : List of classes Response for resource Observation.
        surgeries (List[Surgery]) : List of classes Surgery for resource Procedure.
        radiations (List[RadiationTherapy]) : List of classes RadiationTherapy for resource Procedure.
        targeteds (List[TargetedTherapy]) : List of classes TargetedTherapy for resource Procedure.
        tnm (TNM) : Class TNM for resource Observation.
        condition (Condition) : Class Condition for resource Condition.
        specimens (List[Specimen]) : List of classes Specimen for resource Procedure.
    """
    def __init__(self, patient, time_observation, responses, surgeries, radiations, targeteds, tnm, condition, specimens):
        self.patient = patient
        self.time_observation = time_observation
        self.responses = responses
        self.surgeries = surgeries
        self.radiations = radiations
        self.targeteds = targeteds
        self.tnm = tnm
        self.condition = condition
        self.specimens = specimens
