import xml.etree.ElementTree as ET
import tools.xmlhelper as xmlhelper
import os 

class ShaderParameter:

    def __init__(self):
        self.type = ""
        self.name = ""
        self.value = None

    def read_xml(self, root):
        self.type = root.attrib["type"]
        self.name = root.attrib["name"]

        if(type == "Texture"):
            self.value = "#givemechecker" #? 
        elif(self.type == "Vector"):
            self.value = xmlhelper.ReadQuaternion(root)

class Shader:

    def __init__(self):
        self.name = ""
        self.filename = []
        self.renderbucket = []
        self.layout = {}
        self.parameters = []

    def read_xml(self, root):
        self.name = root.find("Name").text
        
        filenames = root.find("FileName")
        for fn in filenames:
            self.filename.append(fn.text)

        self.renderbucket = xmlhelper.StringListToIntList(root.find("RenderBucket").text.split())
        
        layouts = root.find("Layout")
        idx = 0
        for layout in layouts:
            lay = []
            for semantic in layout:
                lay.append(semantic.tag)
            self.layout["0x" + str(idx)] = lay   
            idx += 1

        params = root.find("Parameters")
        for param in params:
            p = ShaderParameter()
            p.read_xml(param)
            self.parameters.append(p)

class ShaderManager():

    def __init__(self):
        self.shaderxml = os.path.join(os.path.dirname(__file__), 'Shaders.xml')
        self.shaders = {}
        self.load_shaders()

    def load_shaders(self):
        tree = ET.parse(self.shaderxml)
        for node in tree.getroot():
            s = Shader()
            s.read_xml(node)
            self.shaders[s.name] = s