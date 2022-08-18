# code to generate eEventTypes
import xml.etree.ElementTree as ET
import asyncua.ua.object_ids as ob_ids
import generate_model_event as gme
from pathlib import Path
import datetime

BASE_DIR = Path.cwd().parent


class EventsCodeGenerator:

    def __init__(self, event_model, output_file, input_path=None):
        self.output_file = output_file
        self.input_path = input_path
        self.event_model = event_model
        self.indent = "    "
        self.iidx = 0  # indent index

    def event_list(self):
        tree = ET.parse(self.event_model)
        root = tree.getroot()
        for child in root:
            if child.tag.endswith("UAObjectType"):
                print(child.attrib)

    def write(self, line):
        if line:
            line = self.indent * self.iidx + line
        self.output_file.write(line + "\n")

    def make_header(self, events: list):
        tree = ET.parse(self.input_path)
        model_ = ""
        for child in tree.iter():
            if child.tag.endswith("Model"):
                # check if ModelUri X, in Version Y from time Z was already imported
                model_ = child
                break

        self.write(f'''
"""
Autogenerated code from xml"

Model Uri:{model_.attrib['ModelUri']}"
Version:{model_.attrib['Version']}"
Publication date:{model_.attrib['PublicationDate']}"

File creation Date:{datetime.datetime.utcnow()}"
"""
from asyncua import ua
from .events import Event

''')
        names = ", ".join(f'"{event.browseName}"' for event in events)
        self.write(f"__all__ = [{names}]\n")

    def add_properties_and_variables(self, event):
        for ref in event.references:
            if ref.referenceType == "HasProperty":
                self.write("self.add_property('{0}', {1}, {2})".format(
                    ref.refBrowseName, self.get_value(ref),
                    self.get_data_type(ref)
                ))
            elif ref.referenceType == "HasComponent":
                self.write("self.add_variable('{0}', {1}, {2})".format(
                    ref.refBrowseName, self.get_value(ref),
                    self.get_data_type(ref)
                ))

    @staticmethod
    def get_value(reference):
        if reference.refBrowseName == "SourceNode":
            return "sourcenode"
        elif reference.refBrowseName == "Severity":
            return "severity"
        elif reference.refBrowseName == "Status":
            return "False"
        elif reference.refBrowseName == "Message":
            return "ua.LocalizedText(message)"
        elif reference.refBrowseName == "LocalTime":
            return "ua.uaprotocol_auto.TimeZoneDataType()"
        elif reference.refDataType == "NodeId":
            return "ua.NodeId(ua.ObjectIds.{0})".format(
                str(ob_ids.ObjectIdNames[int(str(reference.refId).split("=")[1])]).split("_")[0])
        else:
            return "None"

    @staticmethod
    def get_data_type(reference):
        if str(reference.refBrowseName) in ("Time", "ReceiveTime"):
            return "ua.VariantType.DateTime"
        elif str(reference.refBrowseName) == "LocalTime":
            return "ua.VariantType.ExtensionObject"
        elif str(reference.refDataType).startswith("i="):
            return "ua.NodeId(ua.ObjectIds.{0})".format(
                str(ob_ids.ObjectIdNames[int(str(reference.refDataType).split("=")[1])]).split("_")[0])
        else:
            return "ua.VariantType.{0}".format(reference.refDataType)

    def generate_event_class(self, event, *parent_event_browse_name):
        self.write("")
        if event.browseName == "BaseEvent":
            self.write(f"""
class {event.browseName}(Event):""")
            self.iidx += 1
            self.write('"""')
            if event.description:
                self.write(event.browseName + ": " + event.description)
            else:
                self.write(event.browseName + ":")
            self.write('"""')
            self.write("def __init__(self, sourcenode=None, message=None, severity=1):")
            self.iidx += 1
            self.write("Event.__init__(self)")
            self.add_properties_and_variables(event)
        else:
            self.write(f"""
class {event.browseName}({parent_event_browse_name[0]}):""")
            self.iidx += 1
            self.write('"""')
            if event.description:
                self.write(event.browseName + ": " + event.description)
            else:
                self.write(event.browseName + ":")
            self.write('"""')
            self.write("def __init__(self, sourcenode=None, message=None, severity=1):")
            self.iidx += 1
            self.write("super().__init__(sourcenode, message, severity)")
            self.write("self.EventType = ua.NodeId(ua.ObjectIds.{0}Type)".format(event.browseName))
            self.add_properties_and_variables(event)
        self.iidx -= 2

    def generate_events_code(self, model_):
        self.make_header(model_.values())
        for event in model_.values():
            if event.browseName == "BaseEvent":
                self.generate_event_class(event)
            else:
                parent_node = model_[event.parentNodeId]
                self.generate_event_class(event, parent_node.browseName)
        self.write("")
        self.write("")
        self.write("IMPLEMENTED_EVENTS = {")
        self.iidx += 1
        for event in model_.values():
            self.write("ua.ObjectIds.{0}Type: {0},".format(event.browseName))
        self.write("}")


if __name__ == "__main__":
    xmlPath = BASE_DIR / 'schemas' / 'UA-Nodeset-master' / 'Schema' / 'Opc.Ua.NodeSet2.xml'
    output_path = BASE_DIR / 'asyncua' / 'common' / 'event_objects.py'
    p = gme.Parser(str(xmlPath))
    model = p.parse()
    with open(output_path, "w") as fp:
        ecg = EventsCodeGenerator(model, fp, xmlPath)
        ecg.generate_events_code(model)
