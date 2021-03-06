import bpy
from bpy.types import NodeTree, Node, NodeSocket
from bpy.props import *
from mathutils import Vector
import time
from random import seed
from bpy.app.handlers import persistent
import nodeitems_utils
from .icons import register_icons, unregister_icons, get_icon
from nodeitems_utils import NodeCategory, NodeItem

helperMaterialName = "Helper Material for Modular Tree"


class FloatSocket(NodeSocket):
    # Description string
    '''Custom float socket type'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'FloatSocket'
    # Label for nice name display
    bl_label = 'Custom Float Socket'

    default_value = bpy.props.FloatProperty(name="value", default=0, min=0, soft_max=1)

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)

    # Socket color
    def draw_color(self, context, node):
        return .06, 0.2, 0.5, 0.5


class FreeFloatSocket(NodeSocket):
    # Description string
    '''Custom float socket type'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'FreeFloatSocket'
    # Label for nice name display
    bl_label = 'Custom Float Socket with no mim or max'

    default_value = bpy.props.FloatProperty(name="value", default=0, soft_min=-5, soft_max=5)

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)

    # Socket color
    def draw_color(self, context, node):
        return .06, 0.2, 0.5, 0.5


class AngleFloatSocket(NodeSocket):
    # Description string
    '''Custom float socket type'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'AngleFloatSocket'
    # Label for nice name display
    bl_label = 'from 0 to 360'

    default_value = bpy.props.FloatProperty(name="value", default=0, min=0, max=360)

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)

    # Socket color
    def draw_color(self, context, node):
        return .06, 0.2, 0.5, 0.5


class ModularTreeNodeTree(NodeTree):
    # Description string
    '''Modular tree Node workflow'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'ModularTreeNodeType'
    # Label for nice name display
    bl_label = 'Modular Tree Node Tree'
    # Icon identifier
    bl_icon = 'NODETREE'

    time_lap = 0

    def update(self):
        if bpy.context.scene.mtree_props.use_node_workflow:
            for node in self.nodes:
                node.update()


@persistent
def update_all_trees(scene):
    sel_obj = bpy.context.selected_objects
    if bpy.context.scene.mtree_props.use_node_workflow:
        try:
            test = len(sel_obj) == 1 and sel_obj[0].get('is_tree')
        except:
            test = False
        if test is None:
            test = False
        bpy.context.scene.mtree_props.is_tree_selected = test

        trees = [n for n in bpy.data.node_groups if n.bl_idname == 'ModularTreeNodeType' and n.name == bpy.context.scene.mtree_props.node_tree]
        for t in trees:
            if time.time() - t.time_lap > 1:
                t.update()


class ModularTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ModularTreeNodeType'


class ModularTreeNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ModularTreeNodeType'


class RootNode(Node, ModularTreeNodeTree):
    ''' Roots configuration Node '''
    bl_idname = 'RootNode'
    bl_label = 'Roots'
    bl_width_default = 190

    iterations = bpy.props.IntProperty(default=1)
    stay_under_ground = bpy.props.BoolProperty(default=True)
    radius =  bpy.props.FloatProperty(default=.5, min=0.0001)

    def init(self, context):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props

        self.inputs.new('FloatSocket', "Length").default_value = mtree_props.roots_length
        self.inputs.new('FloatSocket', "split_proba").default_value = mtree_props.roots_split_proba
        self.inputs.new('FreeFloatSocket', "ground_height").default_value = mtree_props.roots_ground_height

        self.outputs.new('NodeSocketShader', "Trunk")

    def update(self):
        try:
            if self.iterations == 0 and len([i for i in self.inputs if i.hide]) != 3:
                for s in self.inputs:
                    s.hide = True
            elif self.iterations > 0 and len([i for i in self.inputs if i.hide]) > 0:
                for s in self.inputs:
                    s.hide = False
        except: pass
        scene = bpy.context.scene
        mtree_props = scene.mtree_props
        mtree_props.roots_iteration = self.iterations
        mtree_props.roots_stay_under_ground = self.stay_under_ground


    def draw_buttons(self, context, layout):
        layout.prop(self, "iterations")
        if self.iterations >0:
            layout.prop(self, "stay_under_ground")


class TrunkNode(Node, ModularTreeNodeTree):
    ''' Trunk configuration Node '''
    bl_idname = 'TrunkNode'
    bl_label = 'Trunk'
    bl_width_default = 200

    preserve_trunk = bpy.props.BoolProperty(default=True)
    finish_trunk = bpy.props.BoolProperty(default=False)
    use_grease_pencil = bpy.props.BoolProperty(default=False)
    radius = bpy.props.FloatProperty(default=1)
    trunk_iterations = bpy.props.IntProperty(default=6, min=0)
    trunk_end = bpy.props.IntProperty(default=20, min=0)

    def init(self, context):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props

        self.inputs.new('NodeSocketShader', "Trunk")
        self.inputs.new('FloatSocket', "Trunk_length").default_value = mtree_props.trunk_space
        self.inputs.new('FloatSocket', "split_proba").default_value = mtree_props.trunk_split_proba
        self.inputs.new('FloatSocket', "split_angle").default_value = mtree_props.trunk_split_angle
        self.inputs.new('FreeFloatSocket', "randomness").default_value = mtree_props.trunk_variation
        self.inputs.new('FloatSocket', "Radius_decrease").default_value = mtree_props.trunk_radius_dec

        self.outputs.new('NodeSocketShader', "Branches")

    def draw_buttons(self, context, layout):
        layout.prop(self, "preserve_trunk")
        if self.preserve_trunk:
            layout.prop(self, "finish_trunk")
        layout.prop(self, "use_grease_pencil")
        layout.prop(self, "radius")
        layout.prop(self, "trunk_iterations")
        layout.prop(self, "trunk_end")

    def update(self):
        try:
            if self.preserve_trunk:
                if len([i for i in self.inputs if i.hide]) > 0:
                    self.inputs["split_proba"].hide = False
                    self.inputs["split_angle"].hide = False

            elif len([i for i in self.inputs if i.hide]) == 0:
                self.inputs["split_proba"].hide = True
                self.inputs["split_angle"].hide = True
        except: pass
        scene = bpy.context.scene
        mtree_props = scene.mtree_props
        mtree_props.preserve_trunk = self.preserve_trunk
        mtree_props.finish_trunk = self.finish_trunk
        mtree_props.use_grease_pencil = self.use_grease_pencil
        mtree_props.trunk_length = self.trunk_iterations
        mtree_props.preserve_end = self.trunk_end
        mtree_props.radius = self.radius


class BranchNode(Node, ModularTreeNodeTree):
    ''' Branch configuration Node '''
    bl_idname = 'BranchNode'
    bl_label = 'Branches'
    bl_width_default = 170

    iterations = bpy.props.IntProperty(default=25)

    # radius_decrease = bpy.props.IntProperty(default = mtree_props.radius_dec)

    def init(self, context):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props

        self.inputs.new('NodeSocketShader', "Branches")
        self.inputs.new('FloatSocket', "length")
        self.inputs.new('FreeFloatSocket', "variations")
        self.inputs.new('FloatSocket', "split_proba")
        self.inputs.new('FloatSocket', "split_angle")
        self.inputs.new('FloatSocket', "break_chance")
        self.inputs.new('FloatSocket', "radius_decrease")
        self.inputs.new('FloatSocket', "min_radius")
        self.inputs.new('AngleFloatSocket', "branches_rotation_angle")
        self.inputs.new('AngleFloatSocket', "branches_random_rotation_angle")


        self.inputs["length"].default_value = mtree_props.branch_length
        self.inputs["variations"].default_value = mtree_props.randomangle
        self.inputs["split_proba"].default_value = mtree_props.split_proba
        self.inputs["split_angle"].default_value = mtree_props.split_angle
        self.inputs["break_chance"].default_value = mtree_props.break_chance
        self.inputs["radius_decrease"].default_value = mtree_props.radius_dec
        self.inputs["min_radius"].default_value = mtree_props.branch_min_radius
        self.inputs["branches_rotation_angle"].default_value = mtree_props.branch_rotate
        self.inputs["branches_random_rotation_angle"].default_value = mtree_props.branch_random_rotate
        self.outputs.new('NodeSocketShader', "Tree")


    def draw_buttons(self, context, layout):
        layout.prop(self, "iterations")
        # layout.prop(self, "radius_decrease")

    def update(self):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props
        mtree_props.iteration = self.iterations


class TreeOutput(Node, ModularTreeNodeTree):
    ''' Tree configuration Node '''
    bl_idname = 'TreeOutput'
    bl_label = 'Tree_Output'
    bl_width_default = 170

    Seed = bpy.props.IntProperty(default=42)
    uv = bpy.props.BoolProperty(default=True)
    create_material = bpy.props.BoolProperty(default=False)
    material = bpy.props.StringProperty(default="")

    def init(self, context):

        self.use_custom_color = True
        self.color = (0.0236563, 0.0913065, 0.173356)
        self.inputs.new('NodeSocketShader', "Tree")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.scale_y = 1.5
        try:
            if bpy.context.selected_objects[-1].get("is_tree"):
                row.operator("mod_tree.update_tree", icon_value=get_icon("TREE_UPDATE"))
            else:
                row.operator("mod_tree.add_tree", icon_value=get_icon("TREE"))
        except:
            row.operator("mod_tree.add_tree", icon_value=get_icon("TREE"))
        layout.prop(self, "Seed")
        layout.prop(self, "uv")
        layout.prop(self, "create_material")
        if not self.create_material:
            layout.prop_search(self, "material", bpy.data, "materials", text="", icon="MATERIAL_DATA")

    def update(self):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props
        mtree_props.uv = self.uv
        mtree_props.SeedProp = self.Seed
        seed(self.Seed)
        mtree_props.mat = self.create_material
        mtree_props.bark_material = self.material


class TwigNode(Node, ModularTreeNodeTree):
    ''' Twig configuration Node '''
    bl_idname = 'TwigNode'
    bl_label = 'Twig'
    bl_width_default = 170

    Seed = bpy.props.IntProperty(default=42)
    leaf_size = bpy.props.FloatProperty(default=1)
    leaf_object = bpy.props.StringProperty(default='')
    leaf_proba = bpy.props.FloatProperty(default=.5)
    leaf_weight = bpy.props.FloatProperty(default=.2)
    iterations = bpy.props.IntProperty(default=9)
    material = bpy.props.StringProperty(default="")

    def init(self, context):

        self.use_custom_color = True
        self.color = (0.0236563, 0.0913065, 0.173356)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.scale_y = 1.5
        try:
            if bpy.context.selected_objects[-1].get("is_tree"):
                row.operator("mod_tree.update_twig", icon="FILE_REFRESH")
            else:
                row.operator("mod_tree.add_twig", icon_value=get_icon("TWIG"))
        except:
            row.operator("mod_tree.add_twig", icon_value=get_icon("TWIG"))

        layout.prop(self, "Seed")
        layout.prop(self, "leaf_size")
        layout.prop_search(self, "leaf_object", bpy.data, "objects", text="", icon="OBJECT_DATA")
        layout.prop(self, "leaf_proba")
        layout.prop(self, "leaf_weight")
        layout.prop(self, "iterations")
        layout.prop_search(self, "material", bpy.data, "materials", text="", icon="MATERIAL_DATA")

    def update(self):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props
        bpy.context.scene.mtree_props.SeedProp = self.Seed
        bpy.context.scene.mtree_props.leaf_object = self.leaf_object
        mtree_props.leaf_size = self.leaf_size
        mtree_props.TwigSeedProp = self.Seed
        mtree_props.leaf_object = self.leaf_object
        mtree_props.leaf_weight = self.leaf_weight
        mtree_props.leaf_chance = self.leaf_proba
        mtree_props.twig_iteration = self.iterations
        mtree_props.twig_bark_material = self.material


class ForcesNode(Node, ModularTreeNodeTree):
    ''' Forces configuration Node '''
    bl_idname = 'ForcesNode'
    bl_label = 'Forces'
    bl_width_default = 170

    use_force_field = bpy.props.BoolProperty(default=False)

    def init(self, context):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props

        self.inputs.new('NodeSocketShader', "Tree")
        self.inputs.new('FreeFloatSocket', "gravity_strength").default_value = mtree_props.gravity_strength
        self.inputs.new('FreeFloatSocket', "Point_force_strength").default_value = mtree_props.fields_point_strength
        self.inputs.new('FreeFloatSocket', "wind_strength").default_value = mtree_props.fields_wind_strength
        self.inputs.new('FreeFloatSocket', "strength_limit").default_value = mtree_props.fields_strength_limit
        self.outputs.new('NodeSocketShader', "Tree")

    def update(self):
        try:
            if self.use_force_field:
                if len([i for i in self.inputs if i.hide]) > 0:
                    self.inputs['Point_force_strength'].hide = False
                    self.inputs['wind_strength'].hide = False
                    self.inputs['strength_limit'].hide = False

            elif len([i for i in self.inputs if i.hide]) <= 3:
                self.inputs['Point_force_strength'].hide = True
                self.inputs['wind_strength'].hide = True
                self.inputs['strength_limit'].hide = True
        except: pass

    def draw_buttons(self, context, layout):
        layout.prop(self, "use_force_field")


class VertexNode(Node, ModularTreeNodeTree):
    ''' Vertex group/color configuration Node '''
    bl_idname = 'VertexNode'
    bl_label = 'Vertex'
    bl_width_default = 190

    create_leaf_vertex_group = bpy.props.BoolProperty(default=True)
    create_radius_vertex_paint = bpy.props.BoolProperty(default=True)
    group_expansion = bpy.props.IntProperty(default=5, name='vertex_group_expansion')

    def init(self, context):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props

        self.inputs.new('NodeSocketShader', "Tree")
        self.outputs.new('NodeSocketShader', "Tree")

    def draw_buttons(self, context, layout):
        layout.prop(self, "create_radius_vertex_paint")
        layout.prop(self, "create_leaf_vertex_group")
        if self.create_leaf_vertex_group:
            layout.prop(self, "group_expansion")

    def update(self):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props
        mtree_props.create_leaf_vertex_group = self.create_leaf_vertex_group
        mtree_props.create_vertex_paint = self.create_radius_vertex_paint
        mtree_props.leafs_iteration_length = self.group_expansion


class ObstacleNode(Node, ModularTreeNodeTree):
    ''' obstacle configuration Node '''
    bl_idname = 'ObstacleNode'
    bl_label = 'Obstacle'
    bl_width_default = 190

    obstacle = bpy.props.StringProperty(default="")
    flip_normals = bpy.props.BoolProperty(default=False)

    modes = [
        ("AVOID", "avoid", "The branches avoid the boundaries of the obstacle"),
        ("CUT", "cut", "The branches are cut by the boundaries of the obstacle"),
    ]
    mode = bpy.props.EnumProperty(name="mode", description="mode", items=modes,
                                    default='AVOID')

    def init(self, context):
        scene = bpy.context.scene

        self.inputs.new('NodeSocketShader', "Tree")
        self.inputs.new('FloatSocket', 'avoidance_strength').default_value = 1
        self.outputs.new('NodeSocketShader', "Tree")

    def draw_buttons(self, context, layout):
        layout.prop_search(self, "obstacle", bpy.data, "objects", text="", icon="OBJECT_DATA")
        layout.prop(self, 'mode')
        layout.prop(self, 'flip_normals')

    def update(self):
        try:
            if self.mode == "AVOID":
                if len([i for i in self.inputs if i.hide]) > 0:
                    self.inputs["avoidance_strength"].hide = False

            elif len([i for i in self.inputs if i.hide]) == 0:
                self.inputs["avoidance_strength"].hide = True
        except: pass
        bpy.context.scene.mtree_props.obstacle = self.obstacle


class ParticleNode(Node, ModularTreeNodeTree):
    ''' particles configuration Node '''
    bl_idname = 'ParticleNode'
    bl_label = 'Particles'
    bl_width_default = 190

    number = bpy.props.IntProperty(default=1000)
    viewport_number = bpy.props.IntProperty(default=500)
    leaf_object = bpy.props.StringProperty(default="")
    leaf_size = bpy.props.FloatProperty(default=1.0)
    emitter = bpy.props.BoolProperty(default=True, name='create particle emitter')

    def init(self, context):
        self.inputs.new('NodeSocketShader', "Tree")
        self.outputs.new('NodeSocketShader', "Tree")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'emitter')
        layout.prop_search(self, "leaf_object", bpy.data, "objects", text="", icon="OBJECT_DATA")
        layout.prop(self, 'number')
        layout.prop(self, 'viewport_number')
        layout.prop(self, 'leaf_size')

    def update(self):
        scene = bpy.context.scene
        mtree_props = scene.mtree_props
        mtree_props.number = self.number
        mtree_props.display = self.viewport_number
        mtree_props.twig_particle = self.leaf_object
        mtree_props.particle_size = self.leaf_size


class PruningNode(Node, ModularTreeNodeTree):
    ''' pruning configuration Node '''
    bl_idname = 'PruningNode'
    bl_label = 'Pruning'
    bl_width_default = 190

    voxel_size = bpy.props.IntProperty(default = 1)

    def init(self, context):
        self.inputs.new('NodeSocketShader', "Tree")
        self.inputs.new('FreeFloatSocket', "intensity")
        self.outputs.new('NodeSocketShader', "Tree")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'voxel_size')

    def update(self):
        bpy.context.scene.mtree_props.pruning = True



class ArmatureNode(Node, ModularTreeNodeTree):
    ''' armature configuration Node '''
    bl_idname = 'ArmatureNode'
    bl_label = 'Armature'
    bl_width_default = 120

    max_bones_iteration = bpy.props.IntProperty(default=5)

    def init(self, context):
        self.inputs.new('NodeSocketShader', "Tree")
        self.outputs.new('NodeSocketShader', "Tree")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'max_bones_iteration')

    def update(self):
        pass


def get_node_group():
    if 'curve_node_group' not in bpy.data.node_groups:
        print('creating group')
        node_group = bpy.data.node_groups.new('curve_node_group', 'ShaderNodeTree')
        # node_group.use_fake_user = True
    return bpy.data.node_groups['curve_node_group'].nodes

curve_node_mapping = {}


def CurveData(name):
    return get_node_group()[name]


class CurveNode(Node, ModularTreeNodeTree):
    ''' Curve node to map values, heavily inspired by the animation node addon code'''

    bl_idname = 'CurveNode'
    bl_label = 'Curve_Mapping'
    bl_width_default = 200

    x_min = bpy.props.FloatProperty(default=0, name='x_min', description="the left bound of the x axis")
    x_max = bpy.props.FloatProperty(default=1, name='x_max', description="the right bound of the x axis")
    y_min = bpy.props.FloatProperty(default=0, name='y_min', description="the lower bound of the y axis")
    y_max = bpy.props.FloatProperty(default=1, name='y_max', description="the left bound of the x axis")

    drivers = [
        ("ITERATION", "Iteration", "The current iteration of the branch"),
        ("RADIUS", "Radius", "The current radius of the branch"),
        ("HEIGHT", "height", "The height of the current branch")
    ]
    driver = bpy.props.EnumProperty(name="input", description="The X axis of the curve", items=drivers, default='ITERATION')

    def init(self, context):
        self.outputs.new('FreeFloatSocket', "value")
        self.initialize()

    def initialize(self):
        nodes = get_node_group()
        node = nodes.new("ShaderNodeRGBCurve")
        node.name = self.name
        return node

    def draw_buttons(self,context, layout):
        layout.prop(self, 'driver')
        layout.template_curve_mapping(self.node, "mapping", use_negative_slope=True)
        if self.driver != 'ITERATION':
            col = layout.box()
            col.prop(self, "x_min")
            col.prop(self, "x_max")
        col = layout.column()
        col.prop(self, "y_min")
        col.prop(self, "y_max")

    def update(self):
        pass

    @property
    def curve(self):
        return self.node.mapping.curves[3]

    @property
    def node(self):
        # nodes = get_node_group()
        # node = nodes.get(self.name)
        # if node is None:
        #     node = self.createCurveNode()
        # return node
        node = CurveData(self.name)
        return node


nodes_to_register = [ModularTreeNodeTree, RootNode, TrunkNode, BranchNode, TreeOutput, CurveNode, FloatSocket,
                     FreeFloatSocket, ForcesNode, VertexNode, AngleFloatSocket, ObstacleNode, ParticleNode,
                     PruningNode, ArmatureNode, TwigNode]


bpy.app.handlers.scene_update_post.append(update_all_trees)


node_categories = [
    # identifier, label, items list
    ModularTreeNodeCategory("Tree", "Tree Nodes",
                            items=[NodeItem("RootNode"), NodeItem("TrunkNode"), NodeItem("BranchNode")]),
    ModularTreeNodeCategory("Input", "Input",
                            items=[NodeItem("CurveNode")]),
    ModularTreeNodeCategory("Output", "Output",
                            items=[NodeItem("TreeOutput"), NodeItem("TwigNode")]),
    ModularTreeNodeCategory("Modifiers", "Modifiers",
                            items=[NodeItem("ForcesNode"), NodeItem("VertexNode"), NodeItem("ObstacleNode"),
                                   NodeItem("ParticleNode"), NodeItem("PruningNode"), NodeItem("ArmatureNode")]),
]


def setup_node_tree(node_tree):
    names = ['RootNode', 'TrunkNode', 'BranchNode', 'TreeOutput']
    nodes = node_tree.nodes
    last_node = None
    for i, name in enumerate(names):
        new_node = nodes.new(name)
        new_node.location = Vector((i*260, 0))
        if i == 0:
            last_node = new_node
        else:
            node_tree.links.new(last_node.outputs[0], new_node.inputs[0])
            last_node = new_node


