import bpy
import os
import xml.etree.ElementTree as ET
from mathutils import Vector
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
import time
import random 

class v_vertex:

    def __init__(self, p, tc, tc1, tc2, tc3, tc4, tc5, c, c1, n, t, bw, bi):
        self.Position = p
        self.TexCoord = tc
        self.TexCoord1 = tc1
        self.TexCoord2 = tc2
        self.TexCoord3 = tc3
        self.TexCoord4 = tc4
        self.TexCoord5 = tc5
        self.Color = c
        self.Color1 = c1
        self.Normal = n
        self.Tangent = t
        self.BlendWeights = bw
        self.BlendIndices = bi

def get_related_texture(texture_dictionary, img_name):

    props = None 
    format = None
    usage = None 
    not_half = False
    hd_split = False
    full = False
    maps_half = False
    
    for t in texture_dictionary:
        tname = t.find("FileName").text 
        if(tname == img_name):
            
            format = t.find("Format").text.split("_")[1] 
            usage = t.find("Usage").text
            uf = t.find("UsageFlags").text
            not_half = False
            hd_split = False    
            full = False
            maps_half = False
            if("NOT_HALF" in uf):
                not_half = True
            if("HD_SPLIT" in uf):
                hd_split = True
            if("FLAG_FULL" in uf):
                full = True
            if("MAPS_HALF" in uf):
                maps_half = True
            
            extra_flags = int(t.find("ExtraFlags").attrib["value"])
            
            props = []
            props.append(format)
            props.append(usage)
            props.append(not_half) 
            props.append(hd_split) 
            props.append(full) 
            props.append(maps_half) 
            props.append(extra_flags)
        
    return props 

def create_material(filepath, td_node, shader):
    params = shader.find("Parameters")
    
    filename = os.path.basename(filepath)[:-8]
    texture_dir = os.path.dirname(os.path.abspath(filepath)) + "\\" + filename + "\\"
    
    texture_dictionary = None
    if(td_node != None):
        texture_dictionary = []
        for i in td_node:
            texture_dictionary.append(i)
    
    shadern = shader.find("FileName").text
    bpy.ops.sollum.createvshader(shadername = shadern)
    mat = bpy.context.scene.last_created_material
    
    nodes = mat.node_tree.nodes 
    for p in params:
        for n in nodes: 
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                if(p.attrib["name"] == n.name):
                    texture_pos = p.find("Name")
                    if(hasattr(texture_pos, 'text')):
                        texture_name = texture_pos.text + ".dds" 
                        texture_path = texture_dir + texture_name
                        if(os.path.isfile(texture_dir + texture_name)):
                            img = bpy.data.images.load(texture_path, check_existing=True)
                            n.image = img 

                        #deal with special situations
                        if(p.attrib["name"] == "BumpSampler" and hasattr(n.image, 'colorspace_settings')):
                            n.image.colorspace_settings.name = 'Non-Color'

            elif(isinstance(n, bpy.types.ShaderNodeValue)):
                if(p.attrib["name"].lower() == n.name[:-2].lower()): #remove _X
                    value_key = n.name[-1] #X,Y,Z,W
                    value = p.attrib[value_key]
                    n.outputs[0].default_value = float(value)      
        
    #assign all embedded texture properties
    #### FIND A BETTER WAY TO DO THIS ####
    if(texture_dictionary != None):
        for node in nodes:
            if(isinstance(node, bpy.types.ShaderNodeTexImage)):
                if(node.image != None):
                    texturepath = node.image.filepath
                    texturename = os.path.basename(texturepath)
                    texture_properties = get_related_texture(texture_dictionary, texturename)
                    if(texture_properties != None):
                        node.embedded = True
                        node.format_type = texture_properties[0] 
                        node.usage = texture_properties[1]
                        node.not_half = texture_properties[2] 
                        node.hd_split = texture_properties[3] 
                        node.full = texture_properties[4] 
                        node.maps_half = texture_properties[5]
                        node.extra_flags = texture_properties[6] 
    
    mat.sollumtype = "GTA" 
    
    return mat

def create_model(self, context, index_buffer, vertexs, filepath, shader, td_node, name):
    
    verts = []
    faces = index_buffer
    normals = []
    texcoords = []
    texcoords1 = []
    texcoords2 = []
    texcoords3 = []
    texcoords4 = []
    texcoords5 = []
    tangents = []
    vcolors = [] 
    vcolors1 = [] 
    
    for v in vertexs:
        if(v.Position != None):
            verts.append(Vector((v.Position[0], v.Position[1], v.Position[2])))
        else:
            return None #SHOULD NEVER HAPPEN
        if(v.Normal != None):
            normals.append(v.Normal)
        if(v.TexCoord != None):
            texcoords.append(v.TexCoord)
        if(v.TexCoord1 != None):
            texcoords1.append(v.TexCoord1)
        if(v.TexCoord2 != None):
            texcoords2.append(v.TexCoord2)
        if(v.TexCoord3 != None):
            texcoords3.append(v.TexCoord3)
        if(v.TexCoord4 != None):
            texcoords4.append(v.TexCoord4)
        if(v.TexCoord5 != None):
            texcoords5.append(v.TexCoord5)
        if(v.Tangent != None):
            tangents.append(Vector((v.Tangent[0], v.Tangent[1], v.Tangent[2])))
        if(v.Color != None):
            vcolors.append(v.Color)
        if(v.Color1 != None):
            vcolors1.append(v.Color1)
        
    #create mesh
    mesh = bpy.data.meshes.new("Geometry")
    mesh.from_pydata(verts, [], faces)
    
    mesh.create_normals_split()
    normals_fixed = []
    for l in mesh.loops:
        normals_fixed.append(normals[l.vertex_index])
    
    mesh.normals_split_custom_set(normals_fixed)
    mesh.use_auto_smooth = True

    # set uv 
    if(texcoords):
        uv0 = mesh.uv_layers.new()
        uv_layer0 = mesh.uv_layers[0]
        for i in range(len(uv_layer0.data)):
            uv = texcoords[mesh.loops[i].vertex_index]
            u = uv[0]
            v = uv[1] * -1
            uv = [u, v]
            uv_layer0.data[i].uv = uv 
    if(texcoords1):
        uv1 = mesh.uv_layers.new()
        uv_layer1 = mesh.uv_layers[1]
        for i in range(len(uv_layer1.data)):
            uv = texcoords[mesh.loops[i].vertex_index]
            uv_layer1.data[i].uv = uv 
    if(texcoords2):
        uv2 = mesh.uv_layers.new()
        uv_layer2 = mesh.uv_layers[2]
        for i in range(len(uv_layer2.data)):
            uv = texcoords[mesh.loops[i].vertex_index]
            uv_layer2.data[i].uv = uv 
    if(texcoords3):
        uv3 = mesh.uv_layers.new()
        uv_layer3 = mesh.uv_layers[3]
        for i in range(len(uv_layer3.data)):
            uv = texcoords[mesh.loops[i].vertex_index]
            uv_layer3.data[i].uv = uv 
    if(texcoords4):
        uv4 = mesh.uv_layers.new()
        uv_layer4 = mesh.uv_layers[4]
        for i in range(len(uv_layer4.data)):
            uv = texcoords[mesh.loops[i].vertex_index]
            uv_layer4.data[i].uv = uv 
    if(texcoords5):
        uv5 = mesh.uv_layers.new()
        uv_layer5 = mesh.uv_layers[5]
        for i in range(len(uv_layer5.data)):
            uv = texcoords[mesh.loops[i].vertex_index]
            uv_layer5.data[i].uv = uv 
    
    #set vertex colors 
    if(vcolors):
        clr0 = mesh.vertex_colors.new(name = "Vertex Colors") 
        color_layer = mesh.vertex_colors[0]
        for i in range(len(color_layer.data)):
            rgba = vcolors[mesh.loops[i].vertex_index]
            color_layer.data[i].color = rgba
    if(vcolors1):
        clr1 = mesh.vertex_colors.new(name = "Vertex illumiation") 
        color_layer1 = mesh.vertex_colors[1]
        for i in range(len(color_layer.data)):
            rgba = vcolors1[mesh.loops[i].vertex_index]
            color_layer1.data[i].color = rgba
    
    #set tangents - .tangent is read only so can't set them
    #for poly in mesh.polygons:
        #for idx in poly.loop_indicies:
            #mesh.loops[i].tangent = tangents[i]    
    
    #load shaders 
    mat = create_material(filepath, td_node, shader)
    mesh.materials.append(mat)
        
    obj = bpy.data.objects.new(name, mesh)
    
    return obj
    #context.collection.objects.link(obj)

def get_vertexs_from_data(vb):
    #set to -1 cause I can tell if they have not been found
    pos_idx = -1
    tc_idx = -1
    tc1_idx = -1
    tc2_idx = -1
    tc3_idx = -1
    tc4_idx = -1
    tc5_idx = -1
    color_idx = -1
    color1_idx = -1
    normal_idx = -1
    tangents_idx = -1
    blendw_idx = -1
    blendi_idx = -1

    #find the position of the variable in the vertex layout
    layout = vb.find("Layout")
    for idx in range(len(layout)):
        if(layout[idx].tag == "Position"):
            pos_idx = idx
        if(layout[idx].tag == "Normal"):
            normal_idx = idx
        if(layout[idx].tag == "Colour0"):
            color_idx = idx
        if(layout[idx].tag == "Colour1"):
            color1_idx = idx
        if(layout[idx].tag == "TexCoord0"):
            tc_idx = idx
        if(layout[idx].tag == "TexCoord1"):
            tc1_idx = idx
        if(layout[idx].tag == "TexCoord2"):
            tc2_idx = idx
        if(layout[idx].tag == "TexCoord3"):
            tc3_idx = idx
        if(layout[idx].tag == "TexCoord4"):
            tc4_idx = idx
        if(layout[idx].tag == "TexCoord5"):
            tc5_idx = idx
        if(layout[idx].tag == "Tangent"):
            tangents_idx = idx
        if(layout[idx].tag == "BlendWeights"):
            blendw_idx = idx
        if(layout[idx].tag == "BlendIndices"):
            blendi_idx = idx
        
    v_buffer = vb[2].text.strip().replace("\n", "").split(" " * 7)

    vertexs = []
    for v in v_buffer:
        n = v.split(" " * 3) #each vert value is split by 3 spaces
        position = []
        if(pos_idx != -1):
            for num in n[pos_idx].split():
                position.append(float(num))
        else:
            position = None
        texcoords = []
        if(tc_idx != -1):
            for num in n[tc_idx].split():
                texcoords.append(float(num))
        else:
            texcoords = None
        texcoords1 = []
        if(tc_idx != -1):
            for num in n[tc1_idx].split():
                texcoords1.append(float(num))
        else:
            texcoords = None
        texcoords2 = []
        if(tc_idx != -1):
            for num in n[tc2_idx].split():
                texcoords2.append(float(num))
        else:
            texcoords2 = None
        texcoords3 = []
        if(tc_idx != -1):
            for num in n[tc3_idx].split():
                texcoords3.append(float(num))
        else:
            texcoords3 = None
        texcoords4 = []
        if(tc_idx != -1):
            for num in n[tc4_idx].split():
                texcoords4.append(float(num))
        else:
            texcoords4 = None
        texcoords5 = []
        if(tc_idx != -1):
            for num in n[tc5_idx].split():
                texcoords5.append(float(num))
        else:
            texcoords5 = None
        color = []
        if(color_idx != -1):
            for num in n[color_idx].split():
                num = round(float(num) / 255)
                color.append(num)
        else:
            color = None
        color1 = []
        if(color1_idx != -1):
            for num in n[color1_idx].split():
                num = round(float(num) / 255)
                color1.append(num)
        else: 
            color1 = None
        normal = []
        if(normal_idx != -1):
            for num in n[normal_idx].split():
                normal.append(float(num))
        tangents = []
        if(tangents_idx != -1):
            for num in n[tangents_idx].split():
                tangents.append(float(num))
        else:
            tangents = None
        blendw = []
        if(blendw_idx != -1):
            for num in n[blendw_idx].split():
                blendw.append(float(num))
        else:
            blendw = None
        blendi = []
        if(blendi_idx != -1):
            for num in n[blendi_idx].split():
                blendi.append(float(num))
        else:
            blendi = None 
            
        vertexs.append(v_vertex(position, texcoords, texcoords1, texcoords2, texcoords3, texcoords4, texcoords5, color, color1, normal, tangents, blendw, blendi))

    return vertexs

def read_model_info(self, context, filepath, model, shd_node, td_node, name):
    
    v_buffer = []
    i_buffer = []
    shader_index = 0

    shader_index = int(model.find("ShaderIndex").attrib["value"])
    vb = model.find("VertexBuffer")
    v_buffer = vb[2].text.strip().replace("\n", "").split(" " * 7) #split by 7 gets you each line of the data
    ib = model.find("IndexBuffer")
    i_buffer = ib[0].text.strip().replace("\n", "").split()

    vertexs = get_vertexs_from_data(vb)

    i_buf = []
    for num in i_buffer:
        i_buf.append(int(num))

    index_buffer = [i_buf[i * 3:(i + 1) * 3] for i in range((len(i_buf) + 3 - 1) // 3 )] #split index buffer into 3s for each triangle

    obj = create_model(self, context, index_buffer, vertexs, filepath, shd_node[shader_index], td_node, name) #supply shaderindex into texturepaths because the shaders are always in order
    
    return obj

def read_drawable_models(self, context, filepath, root, name, shd_node, td_node, key):

    dm_node = root.find("DrawableModels" + key)
    drawable_models = []
    rm_nodes = []
    drawable_objects = []
    
    for dm in dm_node:
        drawable_models.append(dm)
        render_mask = int(dm.find("RenderMask").attrib["value"])
        
        g_node = []
        for geo_node in dm.iter('Geometries'):
            g_node = geo_node
            
        models = []
        for model in g_node:
            models.append(model)
        
        idx = 0
        for model in models:
            d_obj = read_model_info(self, context, filepath, model, shd_node, td_node, name)
            
            #set sollum properties 
            d_obj.sollumtype = "Geometry"
            d_obj.level_of_detail = key
            d_obj.mask = render_mask
            
            drawable_objects.append(d_obj)
            idx += 1
        
    return drawable_objects

def read_ydr_xml(self, context, filepath, root):

    fname = os.path.basename(filepath)
    name = fname[:-8] #removes file extension

    model_name = root.find("Name").text

    #get texture info
    shd_group = root.find("ShaderGroup")
    shd_node = shd_group.find("Shaders")
    td_node = shd_group.find("TextureDictionary")  
    
    
    #get objects from drawable info
    high_objects = []
    med_objects = []
    low_objects = []
    
    if(root.find("DrawableModelsHigh") != None):
        high_objects = read_drawable_models(self, context, filepath, root, model_name, shd_node, td_node, "High")
    if(root.find("DrawableModelsMedium") != None):
        med_objects = read_drawable_models(self, context, filepath, root, model_name, shd_node, td_node, "Medium")
    if(root.find("DrawableModelsLow") != None):
        low_objects = read_drawable_models(self, context, filepath, root, model_name, shd_node, td_node, "Low")

    all_objects = []
    for o in high_objects:
        all_objects.append(o)
    for o in med_objects:
        all_objects.append(o)
    for o in low_objects:
        all_objects.append(o)
    return all_objects

def read_ydd_xml(self, context, filepath, root):

    all_objects = []

    for ydr in root:
        all_objects.append(read_ydr_xml(self, context, filepath, ydr))

    return all_objects

class ImportYDR(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ydr"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ydr"

    # ImportHelper mixin class uses this
    filename_ext = ".ydr.xml"

    filter_glob: StringProperty(
        default="*.ydr.xml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        start = time.time()
        
        tree = ET.parse(self.filepath)
        root = tree.getroot()

        vmodel_obj = bpy.data.objects.new("", None)
        ydr_objs = read_ydr_xml(self, context, self.filepath, root)
        for obj in ydr_objs:
            context.scene.collection.objects.link(obj)
            obj.parent = vmodel_obj
    
        context.scene.collection.objects.link(vmodel_obj)
        vmodel_obj.name = os.path.basename(self.filepath)[:-8]
        
        #set sollum properties 
        dd_high = float(root.find("LodDistHigh").attrib["value"])
        dd_med = float(root.find("LodDistMed").attrib["value"])
        dd_low = float(root.find("LodDistLow").attrib["value"])
        dd_vlow = float(root.find("LodDistVlow").attrib["value"])
        
        vmodel_obj.sollumtype = "Drawable"
        vmodel_obj.drawble_distance_high = dd_high 
        vmodel_obj.drawble_distance_medium = dd_med
        vmodel_obj.drawble_distance_low = dd_low
        vmodel_obj.drawble_distance_vlow = dd_vlow
    
        finished = time.time()
        
        difference = finished - start
        
        print("start time: " + str(start))
        print("end time: " + str(finished))
        print("difference in seconds: " + str(difference))
        print("difference in milliseconds: " + str(difference * 1000))
                
        return {'FINISHED'}

class ImportYDD(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ydd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ydd"

    # ImportHelper mixin class uses this
    filename_ext = ".ydd.xml"

    filter_glob: StringProperty(
        default="*.ydd.xml",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        tree = ET.parse(self.filepath)
        root = tree.getroot()
        name = os.path.basename(self.filepath)[:-8]

        
        vmodels = []
        ydd_objs = read_ydd_xml(self, context, self.filepath, root)
        for ydd in ydd_objs:
            vmodel_obj = bpy.data.objects.new("", None)
            context.scene.collection.objects.link(vmodel_obj)
            for obj in  ydd:
                context.scene.collection.objects.link(obj)
                obj.parent = vmodel_obj
                
            vmodels.append(vmodel_obj)
        
        vmodel_dict_obj = bpy.data.objects.new("", None)
        for vmodel in vmodels:
            vmodel.parent = vmodel_dict_obj
        
        context.scene.collection.objects.link(vmodel_dict_obj)
        vmodel_dict_obj.name = name

        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func_import_ydr(self, context):
    self.layout.operator(ImportYDR.bl_idname, text="Ydr (.ydr.xml)")
# Only needed if you want to add into a dynamic menu
def menu_func_import_ydd(self, context):
    self.layout.operator(ImportYDD.bl_idname, text="Ydd (.ydd.xml)")

def register():
    bpy.utils.register_class(ImportYDR)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ydr)
    bpy.utils.register_class(ImportYDD)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ydd)

def unregister():
    bpy.utils.unregister_class(ImportYDR)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ydr)
    bpy.utils.unregister_class(ImportYDD)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ydd)