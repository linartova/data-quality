import xml.etree.ElementTree as ET

def check_well_formed_xml(file_name):
    """
    Check if input file can be parsed.

    Args:
        file_name: Name of input file with data.

    Returns: Error or nothing.

    """
    try:
        # Attempt to parse the XML file
        ET.parse("uploads/" + file_name)
        return None
    except ET.ParseError as e:
        return f"XML is not well-formed: {e}"


def elements_out_of_order(root, expected_order, name, namespace):
    """
    Check if elements in root element contents all subelements in correct order.

    Args:
        root: Root element.
        expected_order: Expected tags of subelements.
        name: Name of controlled element.
        namespace: Namespace used in input file.

    Returns:
        bool:
            - True if subelements are in correct order.
            - False if subelements are in incorrect order.

    """
    name = namespace + name
    for i in range(len(expected_order)):
        expected_order[i] = namespace + expected_order[i]
    for element in root.findall(name):
        child_tags = [child.tag for child in element]

        if len(child_tags) != len(expected_order):
            # return f"Incorrect count of elements in {root}"
            return False
        for i in range(len(expected_order)):
            if child_tags[i] != expected_order[i]:
                # return f"Error: Elements in a {name} are out of order"
                return False
    return True


def elements_with_right_name(root, expected_tags, namespace):
    """
    Check if elements in root element contents all subelements with correct names.

    Args:
        root: Root element.
        expected_tags: Expected tags of subelements with names.
        namespace: Namespace used in input file.

    Returns:
        bool:
            - True if subelements are with correct names.
            - False if subelements are with incorrect names.

    """
    for tag in expected_tags.keys():
        element = root.find(namespace + tag)
        if element is not None:
            attributes = element.attrib
            expected_value = expected_tags.get(tag)
            actual_value = attributes.get("name")
            if actual_value != expected_value:
                # return f"Error: Element attribute name {actual_value} does not match with expected {expected_value}"
                return False
    return True

def validate_elements(file_name):
    """
    Check if file contains all needed elements.

    Args:
        file_name: Name of input file with data.

    Returns: Nothing or message with wrong element.

    """
    tree = ET.parse("uploads/" + file_name)
    root = tree.getroot()
    namespace = "{http://registry.samply.de/schemata/import_v1}"

    if root.tag != namespace + "BHImport":
        return "Error: Root element should be '{http://registry.samply.de/schemata/import_v1}BHImport'"

    if not elements_out_of_order(root, ["URL", "Namespace"], "Mdr", namespace):
        return "Elements in Mdr element in wrong order."

    if not elements_out_of_order(root, ["Identifier", "Locations"], "BHPatient", namespace):
        return "Elements in BHPatient element in wrong order."

    for patient in root.findall(namespace + "BHPatient"):
        locations = patient.find(namespace + "Locations")
        for location in locations.findall(namespace + "Location"):
            if not elements_out_of_order(location, ["BasicData", "Events"], "Location", namespace):
                return "Elements in location element are out of order"
            basic_data = location.find(namespace + "BasicData")
            form = basic_data.find(namespace + "Form")
            if "name" not in form.attrib:
                return "Error: Missing form name"
            if form.attrib.get("name") != "form_28_ver-27":
                return "Error: Wrong form name"
            if not elements_out_of_order(form,
                                         ["Dataelement_51_3",
                                          "Dataelement_2_2",
                                          "Dataelement_6_3",
                                          "Dataelement_5_2",
                                          "Dataelement_7_2",
                                          "Dataelement_85_1",
                                          "Dataelement_3_1",
                                          "Dataelement_61_5",
                                          "Dataelement_31_3",
                                          "Dataelement_88_1",
                                          "Dataelement_63_4",
                                          "Dataelement_30_3",
                                          "Dataelement_20_3",
                                          "Dataelement_21_5",
                                          "Dataelement_22_4",
                                          "Dataelement_87_1",
                                          "Dataelement_23_5",
                                          "Dataelement_24_4",
                                          "Dataelement_25_3",
                                          "Dataelement_14_3",
                                          "Dataelement_15_2",
                                          "Dataelement_16_3"],
                                         "Form", namespace) and not elements_out_of_order(form,
                                      ["Dataelement_51_3",
                                       "Dataelement_2_2",
                                       "Dataelement_6_3",
                                       "Dataelement_5_2",
                                       "Dataelement_7_2",
                                       "Dataelement_85_1",
                                       "Dataelement_3_1",
                                       "Dataelement_61_5",
                                       "Dataelement_31_3",
                                       "Dataelement_88_1",
                                       "Dataelement_63_4",
                                       "Dataelement_30_3",
                                       "Dataelement_20_3",
                                       "Dataelement_21_5",
                                       "Dataelement_22_4",
                                       "Dataelement_87_1",
                                       "Dataelement_23_5",
                                       "Dataelement_24_4",
                                       "Dataelement_25_3",
                                       "Dataelement_14_3",
                                       "Dataelement_15_2",
                                       "Dataelement_4_3",
                                       "Dataelement_16_3"],
                                      "Form", namespace):
                return "Elements in patient Form do not have correct order"
            expected_tags_1 = {"Dataelement_51_3" : "Date of diagnosis",
                                          "Dataelement_2_2" : "Participation in clinical study",
                                          "Dataelement_6_3" : "Timestamp of last update of vital status",
                                          "Dataelement_5_2" : "Vital status",
                                          "Dataelement_7_2" : "Overall survival status",
                                          "Dataelement_85_1" : "Biological sex",
                                          "Dataelement_3_1" : "Age at diagnosis (rounded to years)",
                                          "Dataelement_61_5" : "Liver imaging",
                                          "Dataelement_31_3" : "CT",
                                          "Dataelement_88_1" : "Colonoscopy",
                                          "Dataelement_63_4" : "Lung imaging",
                                          "Dataelement_30_3" : "MRI",
                                          "Dataelement_20_3" : "KRAS exon 2 (codons 12 or 13)",
                                          "Dataelement_21_5" : "KRAS exon 3 (codons 59 or 61)",
                                          "Dataelement_22_4" : "KRAS exon 4 (codons 117 or 146) mutation status",
                                          "Dataelement_87_1" : "BRAF, PIC3CA, HER2 mutation status",
                                          "Dataelement_23_5" : "NRAS exon 2 (codons 12 or 13)",
                                          "Dataelement_24_4" : "NRAS exon 3 (codons 59 or 61)",
                                          "Dataelement_25_3" : "NRAS exon 4 (codons 117 or 146)",
                                          "Dataelement_14_3" : "Microsatellite instability",
                                          "Dataelement_15_2" : "Mismatch repair gene expression",
                                          "Dataelement_16_3" : "Risk situation (only HNPCC)"}
            expected_tags_2 = {"Dataelement_51_3": "Date of diagnosis",
                               "Dataelement_2_2": "Participation in clinical study",
                               "Dataelement_6_3": "Timestamp of last update of vital status",
                               "Dataelement_5_2": "Vital status",
                               "Dataelement_7_2": "Overall survival status",
                               "Dataelement_85_1": "Biological sex",
                               "Dataelement_3_1": "Age at diagnosis (rounded to years)",
                               "Dataelement_61_5": "Liver imaging",
                               "Dataelement_31_3": "CT",
                               "Dataelement_88_1": "Colonoscopy",
                               "Dataelement_63_4": "Lung imaging",
                               "Dataelement_30_3": "MRI",
                               "Dataelement_20_3": "KRAS exon 2 (codons 12 or 13)",
                               "Dataelement_21_5": "KRAS exon 3 (codons 59 or 61)",
                               "Dataelement_22_4": "KRAS exon 4 (codons 117 or 146) mutation status",
                               "Dataelement_87_1": "BRAF, PIC3CA, HER2 mutation status",
                               "Dataelement_23_5": "NRAS exon 2 (codons 12 or 13)",
                               "Dataelement_24_4": "NRAS exon 3 (codons 59 or 61)",
                               "Dataelement_25_3": "NRAS exon 4 (codons 117 or 146)",
                               "Dataelement_14_3": "Microsatellite instability",
                               "Dataelement_15_2": "Mismatch repair gene expression",
                               "Dataelement_4_3" : "Time of recurrence (metastasis diagnosis)",
                               "Dataelement_16_3": "Risk situation (only HNPCC)"}
            # print(form.find(namespace + "Dataelement_3_1").text)
            if not elements_with_right_name(form, expected_tags_1, namespace) and not elements_with_right_name(form, expected_tags_2, namespace):
                return "Elements in patient Form do not have correct tag name."

            events = location.find(namespace + "Events")
            for event in events.findall(namespace + "Event"):
                attributes = event.attrib
                if attributes.get("name") is None:
                    return "Error: Missing event name"
                if attributes.get("eventtype") is None:
                    return "Error: Missing eventtype"
                event_type = attributes.get("eventtype")
                logitudinal_data = event.find(namespace + "LogitudinalData")
                if logitudinal_data is None:
                    return "Error: Missing LogitudinalData."

                # Surgery
                form_event = logitudinal_data.find(namespace + "Form")
                if event_type == "Surgery":
                    if form_event.attrib.get("name") != "form_32_ver-8":
                        return "Error: Wrong event name."
                    if not elements_out_of_order(form_event,
                                                 ["Dataelement_8_3",
                                                  "Dataelement_49_1",
                                                  "Dataelement_9_2",
                                                  "Dataelement_93_1"],
                                                 "Form", namespace):
                        return "Incorrect order of nested elements in Surgery element"
                    if not elements_with_right_name(form_event,
                                                    {"Dataelement_8_3" : "Time difference between initial diagnosis and surgery",
                                                     "Dataelement_49_1": "Surgery type",
                                                     "Dataelement_9_2" : "Surgery radicality",
                                                     "Dataelement_93_1": "Location of the tumor"},
                                                    namespace):
                        return "Incorrect tag name in Surgery element"

                    # Sample
                    form_event = logitudinal_data.find(namespace + "Form1")
                    if event_type == "Sample":
                        if form_event.attrib.get("name") != "form_35_ver-6":
                            return "Error: Wrong event name."
                        if not elements_out_of_order(form_event,
                                                         ["Dataelement_56_2",
                                                          "Dataelement_54_2",
                                                          "Dataelement_55_2",
                                                          "Dataelement_89_3"],
                                                         "Form1", namespace):
                            return "Incorrect order of nested elements in Sample element"
                        if not elements_with_right_name(form_event,
                                                            {
                                                                "Dataelement_56_2": "Sample ID",
                                                                "Dataelement_54_2": "Material type",
                                                                "Dataelement_55_2": "Preservation mode",
                                                                "Dataelement_89_3": "Year of sample collection"},
                                                            namespace):
                            return "Incorrect tag name in Sample element"

                    # Histopathology
                    form_event = logitudinal_data.find(namespace + "Form2")
                    if event_type == "Histopathology":
                        if form_event.attrib.get("name") != "form_34_ver-22":
                            return "Error: Wrong event name"
                        if not elements_out_of_order(form_event,
                                                         ["Dataelement_75_1",
                                                          "Dataelement_83_1",
                                                          "Dataelement_70_2",
                                                          "Dataelement_92_1",
                                                          "Dataelement_73_3",
                                                          "Dataelement_53_3",
                                                          "Dataelement_71_1",
                                                          "Dataelement_77_1",
                                                          "Dataelement_91_1",
                                                          "Dataelement_57_3",
                                                          "Dataelement_58_2",
                                                          "Dataelement_82_1",
                                                          "Dataelement_68_2"
                                                          ],
                                                         "Form2", namespace):
                            return "Incorrect order of nested elements in Histopathology element"
                        if not elements_with_right_name(form_event,
                                                            {
                                                                "Dataelement_75_1" : "Distant metastasis",
                                                                "Dataelement_83_1" : "Grade",
                                                                "Dataelement_70_2" : "Stage",
                                                                "Dataelement_92_1" : "Localization of primary tumor",
                                                                "Dataelement_73_3" : "UICC version",
                                                                "Dataelement_53_3" : "WHO version",
                                                                "Dataelement_71_1" : "Primary Tumor",
                                                                "Dataelement_77_1" : "Regional lymph nodes",
                                                                "Dataelement_91_1" : "Morphology",
                                                                "Dataelement_57_3" : "Availability digital imaging",
                                                                "Dataelement_58_2" : "Availability invasion front digital imaging",
                                                                "Dataelement_82_1" : "Biological material from recurrence available",
                                                                "Dataelement_68_2" : "Localization of metastasis"
                                                                },
                                                            namespace):
                            return "Incorrect tag name in Histopathology element"

                    # Pharmacotherapy
                    form_event = logitudinal_data.find(namespace + "Form3")
                    if event_type == "Pharmacotherapy":
                        if form_event.attrib.get("name") != "form_33_ver-10":
                            return "Error: Wrong event name."
                        if not elements_out_of_order(form_event,
                                                             ["Dataelement_10_2",
                                                              "Dataelement_11_2",
                                                              "Dataelement_59_5",
                                                              "Dataelement_81_3"],
                                                             "Form3", namespace):
                            return "Incorrect order of nested elements in Pharmacotherapy element"
                        if not elements_with_right_name(form_event,
                                                                {
                                                                    "Dataelement_10_2": "Date of start of pharamacotherapy",
                                                                    "Dataelement_11_2": "Date of end of pharamcotherapy",
                                                                    "Dataelement_59_5": "Scheme of pharmacotherapy",
                                                                    "Dataelement_81_3": "Other pharmacotherapy scheme"},
                                                                namespace):
                            return "Incorrect tag name in Pharmacotherapy element"

                    # Response to therapy
                    form_event = logitudinal_data.find(namespace + "Form4")
                    if event_type == "Response to therapy":
                        if form_event.attrib.get("name") != "form_31_ver-2":
                            return "Error: Wrong event name"
                        if not elements_out_of_order(form_event,
                                                             ["Dataelement_33_1",
                                                              "Dataelement_34_1"],
                                                             "Form4", namespace):
                            return "Incorrect order of nested elements in Response to therapy element"
                        if not elements_with_right_name(form_event,
                                                                {
                                                                    "Dataelement_33_1": "Specific response",
                                                                    "Dataelement_34_1": "Date response was obtained in weeks since initial diagnosis",
                                                                    },
                                                                namespace):
                            return "Incorrect tag name in Response to therapy element"
                    # Radiation therapy
                    form_event = logitudinal_data.find(namespace + "Form5")
                    if event_type == "Radiation therapy":
                        if form_event.attrib.get("name") != "form_29_ver-5":
                            return "Error: Wrong event name"
                        if not elements_out_of_order(form_event,
                                                             ["Dataelement_12_4",
                                                              "Dataelement_13_2"],
                                                             "Form5", namespace):
                            return "Incorrect order of nested elements in Radiation therapy element"
                        if not elements_with_right_name(form_event,
                                                                {
                                                                    "Dataelement_12_4": "Date of start of radiation therapy",
                                                                    "Dataelement_13_2": "Date of end of radiation therapy",
                                                                    },
                                                                namespace):
                            return "Incorrect tag name in Radiation therapy element"

                    # Radiation to therapy
                    form_event = logitudinal_data.find(namespace + "Form6")
                    if event_type == "Targeted Therapy":
                        if form_event.attrib.get("name") != "form_30_ver-3":
                            return "Error: Wrong event name"
                        if not elements_out_of_order(form_event,
                                                             ["Dataelement_35_3",
                                                              "Dataelement_36_1"],
                                                             "Form6", namespace):
                            return "Incorrect order of nested elements in Targeted Therapy element"
                        if not elements_with_right_name(form_event,
                                                                {
                                                                    "Dataelement_35_3": "Date of start of targeted therapy",
                                                                    "Dataelement_36_1": "Date of end of targeted therapy",
                                                                    },
                                                                namespace):
                            return "Incorrect tag name in Targeted Therapy element"