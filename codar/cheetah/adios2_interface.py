"""
ADIOS2 Interface
"""

# from lxml import etree as ET
import xml.etree.ElementTree as ET
# import xml.dom.minidom as minidom

"""
@TODO:
Implement exception handling

Questions for myself:
- Is there a way to know if the input file is an adios2 or adios1 xml file?
"""

# A list of engines in adios2 and their parameters
_adios2_engines={}


def set_engine(xmlfile, io_obj, engine_type, parameters=None):
    """
    Set the engine type for an input IO object.

    :param xmlfile: String. The ADIOS2 xml file to be modified
    :param io_obj: String. Name of the io object which contains the engine
    :param engine_type: String. The engine type to be set for the io object
    :param parameters: List. A list of dicts containing 'key and 'value' keys
    :return: True on success, False on error
    """

    _set_element(xmlfile, io_obj, "engine", engine_type, None, parameters)


def set_transport(xmlfile, io_obj, transport_type, parameters=None):
    """
    Set the transport type for an io object

    :param xmlfile: String. The ADIOS2 xml file to be modified
    :param io_obj: String. Name of the io object that contains the engine
    :param transport_type String. The transport type for this io object
    :param parameters: A dict containing the parameter keys and values
    :return: True on success, False on error
    """

    _set_element(xmlfile, io_obj, "transport", transport_type, None, 
                 parameters)


def set_var_operation(xmlfile, io_obj, var, op_type, parameters=None):
    """
    Set an operation on a variable

    :param xmlfile: String. The ADIOS2 xml file to be modified
    :param io_obj: String. Name of the io object that contains the engine
    :param var String. Name of the variable
    :param parameters: A dict containing the parameter keys and values
    :return: True on success, False on error
    """

    _set_element(xmlfile, io_obj, "variable", "var", op_type, parameters)


def _set_element(xmlfile, io_obj, io_child_tag, tag_value,
                 op_type, parameters=None):
    """

    :param xmlfile: The ADIOS2 xml file to be modified
    :param io_obj: Name of the io object
    :param io_child_tag: engine/transport/variable
    :param tag_value: value to be inserted
    :param op_type: operation value (compression type) for variable
    compression
    :param parameters: dict of parameters with a key and value
    :return:
    """

    # Ensure parameters is a list of dicts
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    io_found = False
    for child in root:
        if child.attrib['name'] == io_obj:
            io_found = True
            break

    if not io_found:
        raise Exception("Could not find io object matching {0}".format(io_obj))

    # Whats the keyword that follows the tag
    if io_child_tag == "engine" or io_child_tag == 'transport':
        tag_key = 'type'
    else:  # if io_child_tag == 'variable'
        tag_key = 'name'

    # Create new node for the new child tag
    new_node = ET.Element(io_child_tag)
    new_node.set(tag_key, tag_value)

    if io_child_tag == 'variable':
        optype_node = ET.Element("operation")
        optype_node.set('type', op_type)
        new_node.append(optype_node)
        new_node = optype_node

    # Add parameters
    if parameters is not None:
        for key, value in parameters.items():
            par_elem = ET.Element("parameter")
            par_elem.set(key, str(value))
            new_node.append(par_elem)

    # Remove old node
    existing_node = child.find(io_child_tag)
    if existing_node is not None: child.remove(existing_node)
    child.append(new_node)

    # Write the file back
    tree.write(xmlfile, xml_declaration=True)

    # All done
    return True


if __name__=="__main__":
    set_engine("test.xml", "writer", "SST", {"conn":"flexp",
                                            'kutta': 22})
    set_transport("test.xml", "writer", "File2", {'Library':'MPI', 'ProfileUnits':'Seconds'})
    set_var_operation("test.xml", "writer", "T", "zfp", {'rate':18})
