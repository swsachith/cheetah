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

    tree = ET.parse(xmlfile)
    io_node = _get_io_node(tree, io_obj)
    node = ET.Element("engine")
    node.set('type', engine_type)
    _add_parameters(node, parameters)

    _replace_and_add_elem(io_node, node, "engine")

    # Write the file back
    tree.write(xmlfile, xml_declaration=True)


def set_transport(xmlfile, io_obj, transport_type, parameters=None):
    """
    Set the transport type for an io object

    :param xmlfile: String. The ADIOS2 xml file to be modified
    :param io_obj: String. Name of the io object that contains the engine
    :param transport_type String. The transport type for this io object
    :param parameters: A dict containing the parameter keys and values
    :return: True on success, False on error
    """

    tree = ET.parse(xmlfile)
    io_node = _get_io_node(tree, io_obj)
    node = ET.Element("transport")
    node.set('type', transport_type)
    _add_parameters(node, parameters)

    _replace_and_add_elem(io_node, node, "transport")

    # Write the file back
    tree.write(xmlfile, xml_declaration=True)


def set_var_operation(xmlfile, io_obj, var_name, operation, parameters=None):
    """
    Set an operation on a variable

    :param xmlfile: String. The ADIOS2 xml file to be modified
    :param io_obj: String. Name of the io object that contains the engine
    :param var_name String. Name of the variable
    :param operation String. The operation to be performed on the variable
    :param parameters: A dict containing the parameter keys and values
    :return: True on success, False on error
    """

    tree = ET.parse(xmlfile)
    io_node = _get_io_node(tree, io_obj)
    oper_child = ET.Element("operation")
    oper_child.set('type', operation)
    _add_parameters(oper_child, parameters)

    # Check if a 'variable' element exists. If not, create one
    var_nodes = io_node.findall("variable")
    for varnode in var_nodes:
        if varnode.attrib['name'] == var_name:
            _replace_and_add_elem(varnode, oper_child, "operation")
            return

    # Not found. Create new
    new_var_node = ET.Element("variable")
    new_var_node.set("name", var_name)
    new_var_node.append(oper_child)
    io_node.append(new_var_node)

    # Write the file back
    tree.write(xmlfile, xml_declaration=True)


def _get_io_node(tree, io_obj):

    root = tree.getroot()
    for sub_element in root:
        if sub_element.attrib['name'] == io_obj:
            return sub_element

    raise Exception("Could not find io object matching {0}".format(io_obj))


def _add_parameters(node, parameters):
    if parameters is None:
        return

    for key, value in parameters.items():
        par_elem = ET.Element("parameter")
        par_elem.set(key, str(value))
        node.append(par_elem)


def _replace_and_add_elem(parent, child, elem_tag):
    existing_node = parent.find(elem_tag)
    if existing_node is not None: parent.remove(existing_node)
    parent.append(child)


if __name__=="__main__":
    set_engine("test.xml", "writer", "SST", {"conn":"flexp",
                                            'kutta': 22})
    set_transport("test.xml", "writer", "File2", {'Library':'MPI', 'ProfileUnits':'Seconds'})
    set_var_operation("test.xml", "writer", "T", "zfp", {'rate':180})
