bl_info = {'name':"TimeNodeTree", 'author':"ugorek",
           'version':(1,2,3), 'blender':(4,0,2), #2024.01.19
           'description':"Time-Mind-Map using Blender nodes.",
           'location':"NodeTreeEditor",
           'warning':"",
           'category':"User",
           'wiki_url':"https://github.com/ugorek000/TimeNodeTree/wiki", 'tracker_url':"https://github.com/ugorek000/TimeNodeTree/issues"}
thisAddonName = bl_info['name']

from builtins import len as length
import bpy, re, datetime
import ctypes, functools
import nodeitems_utils
import math, mathutils

list_classes = []
list_clsToAddon = []
list_clsToChangeTag = []

class AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = thisAddonName

def GetDicsIco(tgl):
    return 'DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT'

def TxtToTripleTxt(txt, annex="\""):
    def InsertTripleSpaces(txt):
        len = length(txt)
        return ' '.join(([txt[:len%3]] if len%3 else [])+[ txt[len-cyc*3-3:len-cyc*3] for cyc in reversed(range(0,len//3)) ])
    return annex+InsertTripleSpaces(txt)+annex

def AddNiceColorProp(where, who, prop, align=False, txt="", decor=3):
    rowCol = where.row(align=align)
    rowLabel = rowCol.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=txt if txt else who.bl_rna.properties[prop].name+":")
    rowLabel.active = decor%2
    rowProp = rowCol.row()
    rowProp.alignment = 'EXPAND'
    rowProp.prop(who, prop, text="")
    rowProp.active = decor//2%2

class TimeTree(bpy.types.NodeTree):
    """Time manipulation with using nodes"""
    bl_idname = 'TimeNodeTree'
    bl_label = "Time Node Tree"
    bl_icon = 'TIME' #MOD_TIME  TIME
list_classes += [TimeTree]

class AtHomePoll(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type==TimeTree.bl_idname

dict_tupleShiftAList = {}

class Sacat:
    def __init__(self, ClsPoll):
        self.ClsPoll = ClsPoll
        self.list_orderBlid = []

def AddToSacat(list_orderClass, name, ClsPoll):
    dict_tupleShiftAList.setdefault(name, Sacat(ClsPoll))
    for li in list_orderClass:
        len = length(li)
        sett = li[2] if len>2 else {}
        labl = li[3] if len>3 else None
        dict_tupleShiftAList[name].list_orderBlid.append( (li[0], li[1].bl_idname, labl, sett) )

def TemplateRegisterNdMainstream(cls, order, cat, label=""):
    list_classes.append(cls)
    tupl = (order,cls,{},label) if label else (order,cls)
    AddToSacat([tupl], cat, AtHomePoll)
    list_clsToChangeTag.append(cls)

list_sacatOrder = ["Input", "Manupulation", "Outputs", "Specials"]
dist_sacatOrderMap = {li:cyc for cyc, li in enumerate(list_sacatOrder)}
mntSaCatName = 'TIME_NODES'
def RegisterNodeCategories():
    list_nodeCategories = []
    for li in sorted(dict_tupleShiftAList.items(), key=lambda a: dist_sacatOrderMap.get(a[0], -1)):
        name = li[0]
        items = [nodeitems_utils.NodeItem(li[1], label=li[2], settings=li[3]) for li in sorted(li[1].list_orderBlid, key=lambda a:a[0])]
        list_nodeCategories.append(li[1].ClsPoll(name.replace(" ", ""), name.replace("_", ""), items=items))
    try:
        nodeitems_utils.register_node_categories(mntSaCatName, list_nodeCategories)
    except:
        nodeitems_utils.unregister_node_categories(mntSaCatName)
        nodeitems_utils.register_node_categories(mntSaCatName, list_nodeCategories)
def UnregisterNodeCategories():
    nodeitems_utils.unregister_node_categories(mntSaCatName)

class TntTnPads:
    nclass = 0
    def InitNodePreChain(self,context):pass
    def InitNode(self,context):pass
    def DrawExtPreChain(self,context,colLy):pass
    def DrawExtNode(self,context,colLy):pass
    def DrawPreChain(self,context,colLy):pass
    def DrawNode(self,context,colLy):pass
    def DrawPostChain(self,context,colLy):pass
    def ExecuteNodePreChain(self):pass
    def ExecuteNode(self):pass
class TntTnBase(bpy.types.Node, TntTnPads):
    @classmethod
    def poll(cls, tree):
        return tree.bl_idname==TimeTree.bl_idname
    def init(self, context):
        if isDataOnRegisterDoneTgl:
            bpy.app.timers.register(functools.partial(MnUpdateAllNclassFromTree, True))
        self.InitNodePreChain(context)
        self.InitNode(context)
    def draw_buttons_ext(self, context, layout):
        colLy = layout.column()
        self.DrawExtPreChain(context, colLy)
        self.DrawExtNode(context, colLy)
    def draw_buttons(self, context, layout):
        dict_ndInExecuting.setdefault(self, 0)
        colLy = layout.column()
        self.DrawPreChain(context, colLy)
        self.DrawNode(context, colLy)
        self.DrawPostChain(context, colLy)
        if dict_ndInExecuting[self]!=0:
            dict_ndInExecuting[self] -= 1
    def GetSksForEvaluate(self): #Pad.
        return (sk for sk in self.inputs)
    def Execute(self):
        self.ExecuteNodePreChain()
        self.ExecuteNode()

class TntTnWithErrorReport(TntTnBase):
    txtErrorInExecute: bpy.props.StringProperty(name="Error", default="")
    def DrawPostChain(self, context, colLy):
        if self.txtErrorInExecute:
            colLy.alert = True
            colLy.prop(self,'txtErrorInExecute', text="", icon="ERROR")
            #colLy.alert = False
    def Execute(self):
        try:
            self.ExecuteNodePreChain()
            self.ExecuteNode()
            self.txtErrorInExecute = ""
        except Exception as ex:
            self.txtErrorInExecute = str(ex)

def DoExecuteForNodeTimer(txt):
    try: ExecuteForOneNodeFull(eval(txt))
    except: pass
class TntTnExecutableOnDraw(TntTnBase):
    def DrawPreChain(self, context, colLy):
        bpy.app.timers.register(functools.partial(DoExecuteForNodeTimer, repr(self)))

class EraZStated:
    def __init__(self, eraz, state):
        self.eraz = eraz
        self.state = state
class TntSocketEraZ(bpy.types.NodeSocket):
    bl_idname = 'NodeSocketEraZ'
    bl_label = "EraZ"
    bl_description = "Raw time as text"
    txtEraZ: bpy.props.StringProperty(name="EraZ", default="") #Заметка: наличие update будет всё время перерисовывать.
    stateHhError: bpy.props.IntProperty(name="State", default=1, min=-1, max=2)
    txtDisplay: bpy.props.StringProperty(name="Display", default="")
    txtErrorInEvaluated: bpy.props.StringProperty(name="ErrorInEvaluated", default="")
    isDisplayAsEditable: bpy.props.BoolProperty(name="Display as editable", default=False)
    @classmethod
    def draw_color_simple(cls):
        return (0.899461, 0.525433, 0.181989, 0.95)
    def GetHhState(self, nd):
        return -1 if not dict_ndInExecuting.get(nd, None) else self.stateHhError
    def draw_color(self, context, node):
        match self.GetHhState(node):
            case 0: return (0.899461, 0.525433, 0.181989, 0.95)
            case -1|1: return (0.5, 0.5, 0.5, 0.8)
            case 2: return (1.0, 0.0, 0.0, 0.8)
    def draw(self, context, layout, node, text):
        layout.alignment = 'EXPAND'
        colRoot = layout.column(align=True)
        colRoot.alignment = 'RIGHT'
        rowMain = colRoot.row(align=True)
        if self.isDisplayAsEditable:
            rowMain.prop(self,'txtEraZ', text="")
        else:
            rowMain.active = abs(self.GetHhState(node))!=1
            rowMain.alert = self.stateHhError==2
            if self.is_output:
                rowMain.alignment = 'RIGHT'
            rowMain.label(text=self.txtDisplay if self.txtDisplay else text)
        if not not self.txtErrorInEvaluated:
            rowError = colRoot.row(align=True)
            rowError.alert = True
            rowError.prop(self,'txtErrorInEvaluated', text="", icon="ERROR")
    def SetAllRaw(self, txt, state, display=None):
        self.txtEraZ = txt
        self.stateHhError = state
        if display is not None:
            self.txtDisplay = display
    def SetEraZState(self, eraZ, state):
        self.txtEraZ = str(eraZ)
        self.stateHhError = state
    def EvaluateGetEraZStated(self):
        result = None
        match self.stateHhError:
            case 0:
                try:
                    result = int(self.txtEraZ)
                    self.txtErrorInEvaluated = ""
                except Exception as ex:
                    self.txtErrorInEvaluated = str(ex)
                    self.stateHhError = 2
            case -1|1: result = 0
        return EraZStated(result, self.stateHhError)
    def TransferFromSkEz(self, another):
        self.txtEraZ =      another.txtEraZ
        self.stateHhError = another.stateHhError
list_classes += [TntSocketEraZ]

def NdAddSkDefault(puts, identifier, display="\1", data="0", editable=False):
    sk = puts.new(TntSocketEraZ.bl_idname, identifier)
    sk.txtDisplay = identifier if display=="\1" else display
    sk.txtEraZ = data
    sk.isDisplayAsEditable = editable
    return sk

dict_ndInExecuting = {}
def ExecuteForOneNodeFull(nd):
    dict_soldLinksSkIn = {}
    tree = nd.id_data
    for lk in tree.links:
        if (lk.is_muted)or(not lk.is_valid):
            if lk.is_muted:
                #def PopupMessage(self, context): self.layout.label(text="Disabled links are not supported.", icon='ERROR')
                #bpy.context.window_manager.popup_menu(PopupMessage, title="Time node tree", icon='NONE') #Для второго монитора сообщение всё равно показывается на первом.
                rr = tree.nodes.new('NodeReroute')
                rr.location = tree.view_center
                rr.label = "Disabled links are not supported."
            lk.is_muted = False
            lk.is_valid = True #Заметка: их изменение так же заставляет всё перерисовываться.
        dict_soldLinksSkIn[lk.to_socket] = lk
    def RecrExecuteWalker(nd):
        dict_ndInExecuting[nd] = 2
        for sk in nd.GetSksForEvaluate():
            lk = dict_soldLinksSkIn.get(sk, None) #От этого поддерживается только один линк на входящий сокет. Легально иначе не получить, но всё же..
            if lk:
                RecrExecuteWalker(lk.from_node)
                lk.to_socket.TransferFromSkEz(lk.from_socket)
            else:
                sk.stateHhError = 1
                sk.txtErrorInEvaluated = ""
        nd.Execute()
    try:
        RecrExecuteWalker(nd)
    except Exception as ex:
        #Todo: определить линк, возвращающий на глубину выше, чтобы пометить только его.
        #^ а ешё как-то не затирать от других успешно выполненных.
        for lk in tree.links:
            lk.is_valid = False

class StructBase(ctypes.Structure):
    _subclasses = []
    __annotations__ = {}
    def __init_subclass__(cls):
        cls._subclasses.append(cls)
    def InitStructs():
        for cls in StructBase._subclasses:
            fields = []
            for field, value in cls.__annotations__.items():
                fields.append((field, value))
            if fields:
                cls._fields_ = fields
            cls.__annotations__.clear()
        StructBase._subclasses.clear()

class BNodeType(StructBase):
    idname:         ctypes.c_char*64
    type:           ctypes.c_int
    ui_name:        ctypes.c_char*64
    ui_description: ctypes.c_char*256
    ui_icon:        ctypes.c_int
    char:           ctypes.c_void_p
    width:          ctypes.c_float
    minwidth:       ctypes.c_float
    maxwidth:       ctypes.c_float
    height:         ctypes.c_float
    minheight:      ctypes.c_float
    maxheight:      ctypes.c_float
    nclass:         ctypes.c_int16 #https://github.com/ugorek000/ManagersNodeTree
class BNode(StructBase):
    next:       ctypes.c_void_p
    prev:       ctypes.c_void_p
    inputs:     ctypes.c_void_p*2
    outputs:    ctypes.c_void_p*2
    name:       ctypes.c_char*64
    identifier: ctypes.c_int
    flag:       ctypes.c_int
    idname:     ctypes.c_char*64
    typeinfo:   ctypes.POINTER(BNodeType)
    @classmethod
    def get_fields(cls, so):
        return cls.from_address(so.as_pointer())

StructBase.InitStructs()

def MnUpdateAllNclassFromTree(withCleanUp=True):
    global isDataOnRegisterDoneTgl
    isDataOnRegisterDoneTgl = False
    nameTree = "tehn"+chr(8203)
    tree = bpy.data.node_groups.get(nameTree) or bpy.data.node_groups.new(nameTree, TimeTree.bl_idname)
    for li in list_clsToChangeTag:
        nameNd = li.bl_idname
        nd = tree.nodes.get(nameNd) or tree.nodes.new(nameNd)
        nd.name = nameNd
        if hasattr(nd,'nclass'):
            BNode.get_fields(nd).typeinfo.contents.nclass = nd.nclass
        if withCleanUp: #Нужно ли удаление нодов, если всё равно удаляется дерево?
            tree.nodes.remove(nd)
    if withCleanUp:
        bpy.data.node_groups.remove(tree)

#Далее список функций для шифрования (пайки) в эру и обратно. День эры = индекс порядкового дня начиная с 0000.01.01 Julian.
#Неведомые мне корректировки на реальность Julian'а отсутствуют; только чистая математика. Отрицательные года не обработаны и обрабатываются как есть.

class Julian:
    def __init__(self, yr=0, nh=0, dy=0, hr=0, mn=0, sc=0, zz=0):
        self.yr=yr
        self.nh=nh
        self.dy=dy
        self.hr=hr
        self.mn=mn
        self.sc=sc
        self.zz=zz
    def __repr__(self):
        return f"Julian({self.yr}, {self.nh}, {self.dy}, {self.hr}, {self.mn}, {self.sc}, {self.zz})"
    def __str__(self):
        return f"{self.yr:04}.{self.nh:02}.{self.dy:02}  {self.hr:02}:{self.mn:02}:{self.sc:02}:{self.zz:03}"

def IsLeapYear(year):
    return (year%4==0)and(year%100!=0)or(year%400==0)
def YearAndDayInYearToEraDay(year, day): #FloorFrac --> Float.
    def LeapsCount(year):
        return 1+(year//4)-(year//100)+(year//400) #Добавляется '+1' в начале, потому что 0000г. -- весокосный год.
    if year==0:
        return day
    return year*365+LeapsCount(year-1)+day
def EraDayToYear(eraD): #Float --> Floor.
    result = eraD-1 #Связанно с 0000г. -- весокосным годом.
    result -= result//146097
    result += result//36524 #Заметка: обратить внимание на `+`.
    result -= result//1461
    return result//365
def EraDayToDayInYear(eraD): #Float --> Frac.
    def NegMod(a,b):
        return a%(b*((a>0)*2-1))
    #Победа. Исследование этого было не таким уж и простым.
    result = NegMod(NegMod((eraD%146097-366),36524),1461)
    result += (result<0)*1461
    return result%365+(result>1459)*365

tuple_tupleMonthSumMap = ( (0,0,31,59,90,120,151,181,212,243,273,304,334,365), (0,0,31,60,91,121,152,182,213,244,274,305,335,366) )
def JulianToEraZ(jul):
    result = YearAndDayInYearToEraDay(jul.yr, tuple_tupleMonthSumMap[IsLeapYear(jul.yr)][jul.nh]+jul.dy-1) #Заметка: день у Julian не в "режиме индекса", поэтому `-1`.
    return (result*24+jul.hr)*3600_000+jul.mn*60000+jul.sc*1000+jul.zz
def EraZToJulian(eraZ):
    def DayInYearToMonth(dayInYear, isLeapYear):
        diy60 = dayInYear-59-isLeapYr
        return ( math.floor(diy60/153)*5+2+math.floor(diy60%153/30.44) )*(dayInYear-30.5>0)
    jul = Julian()
    jul.zz = eraZ%1000
    jul.sc = eraZ//1000%60
    jul.mn = eraZ//60000%60
    jul.hr = eraZ//3600000%24
    eraD = eraZ//86400000
    jul.yr = EraDayToYear(eraD)
    day = EraDayToDayInYear(eraD)
    isLeapYr = IsLeapYear(jul.yr)
    jul.nh = 1+DayInYearToMonth(day, isLeapYr)
    jul.dy = 1+day-tuple_tupleMonthSumMap[isLeapYr][jul.nh]
    return jul

def GetNowEraZ():
    systime = datetime.datetime.now()
    jul = Julian(systime.year, systime.month, systime.day, systime.hour, systime.minute, systime.second, systime.microsecond//1000)
    return JulianToEraZ(jul)

class EzttgDisplayMethods:
    edmAll = 0
    edmNonLeft = 1
    edmOnlyFirst = 2
    edmNonLeftNonZ = 3
    edmTwoFirst = 4
list_edmNames = ["All", "NonLeft", "OnlyFirst", "NonLeftNonZ", "TwoFirst"]
Edm = EzttgDisplayMethods
def EraZToTxtGreat(eraZ, displayMethod, formatString="- y d h m s z", constMunis="–", constZeroTime="0t"):
    if eraZ==0:
        return constZeroTime
    result = formatString
    if eraZ<0:
        result = result.replace("-",constMunis)
        eraZ = -eraZ
    else:
        result = result.replace("- ","")
        result = result.replace("-","")
    done = False
    ray = 0
    toMod = 31536000000 #Бесполезно, ибо isFirstEntry и концепция.
    isFirstEntry = True
    for cyc in range(1, 7): #Todo: отшлифовать всё для 0 -- начало; будет range(6).
        ch = "_ydhmsz"[cyc]
        if formatString.find(ch)==-1:
            continue
        extLastCh = ch
        toDiv = (0, 31536000000, 86400000, 3600000, 60000, 1000, 1)[cyc]
        if isFirstEntry:
            zmuv = eraZ//toDiv
        else:
            zmuv = eraZ%toMod//toDiv
        isFirstEntry = False
        toMod = toDiv
        ##
        ray = ray+((ray)or(zmuv!=0))
        match displayMethod:
            case Edm.edmAll:
                can = True
            case Edm.edmNonLeft|Edm.edmOnlyFirst:
                can = not not ray
            case Edm.edmNonLeftNonZ:
                can = (ray)and(cyc!=6)or(not ray)and(cyc==5)
            case Edm.edmTwoFirst:
                if ray>2:
                    done = True
                can = (ray)or(cyc==5)
        match cyc:
            case 1|2:   len = 1
            case 3|4|5: len = 2
            case 6:     len = 3
        if (can)and(not done):
            result = result.replace(ch,str(zmuv).zfill(len)+ch)
        else:
            result = result.replace(ch+" ", "")
            result = result.replace(ch, "")
        match displayMethod:
            case Edm.edmOnlyFirst:
                if zmuv!=0:
                    done = True
    if not result:
        return '0'+extLastCh
    if result[-1]==" ":
        return result[:-1]
    return result

tuple_tupleDayCountOfJulMonthMap = ( (31,28,31,30,31,30,31,31,30,31,30,31), (31,29,31,30,31,30,31,31,30,31,30,31) )

class NodeReroute(TntTnBase):
    bl_idname = 'TntNodeReroute'
    bl_label = "Reroute"
    nclass = 13
    def InitNode(self, context):
        NdAddSkDefault(self.inputs, "Time")
        NdAddSkDefault(self.outputs, "Time")
    def ExecuteNode(self):
        self.outputs[0].TransferFromSkEz(self.inputs[0])
TemplateRegisterNdMainstream(NodeReroute, 0, "Specials")

class NodeSwitcher(TntTnBase):
    bl_idname = 'TntNodeSwitcher'
    bl_label = "Switcher"
    nclass = 13
    switch: bpy.props.BoolProperty(name="Switch", default=False)
    def InitNode(self, context):
        NdAddSkDefault(self.inputs, "Time")
        NdAddSkDefault(self.inputs, "Time")
        NdAddSkDefault(self.outputs, "Time")
    def DrawNode(self, context, colLy):
        colLy.prop(self,'switch')
        colLy.active = (self.inputs[0].is_linked)and(self.inputs[1].is_linked)
    def GetHhSk(self):
        sk1 = self.inputs[0] if self.inputs[0].is_linked else None
        sk2 = self.inputs[1] if self.inputs[1].is_linked else None
        return sk1, sk2
    def GetSksForEvaluate(self):
        sk1, sk2 = self.GetHhSk()
        if sk1 and sk2:
            return [self.inputs[self.switch]]
        elif sk1 or sk2:
            return [sk1 or sk2]
        return []
    def ExecuteNode(self):
        sk1, sk2 = self.GetHhSk()
        if sk1 and sk2:
            self.outputs[0].TransferFromSkEz(self.inputs[self.switch])
            self.inputs[not self.switch].stateHhError = 1
        elif sk1 or sk2:
            self.outputs[0].TransferFromSkEz(sk1 or sk2)
        else:
            self.outputs[0].SetEraZState(0, 1)
TemplateRegisterNdMainstream(NodeSwitcher, 1, "Specials")

def SetUnchangeNdLabelTimer(txt):
    nd = eval(txt)
    nd.label = nd.label
class NodeAlwaysRedraw(TntTnBase):
    bl_idname = 'TntNodeAlwaysRedraw'
    bl_label = "Always Redraw"
    nclass = 13
    isActive: bpy.props.BoolProperty(name="Active", default=True)
    def DrawNode(self, context, colLy):
        #import random; colLy.label(text=str(random.random()), icon='SEQUENCE_COLOR_0'+str(random.randint(1, 9))) #debug
        colLy.prop(self,'isActive')
        if self.isActive:
            bpy.app.timers.register(functools.partial(SetUnchangeNdLabelTimer, repr(self)))
TemplateRegisterNdMainstream(NodeAlwaysRedraw, 2, "Specials")

class NodeInputRaw(TntTnBase):
    bl_idname = 'TntNodeInputRaw'
    bl_label = "Raw Input"
    nclass = 13
    bl_width_default = 200
    def InitNode(self, context):
        NdAddSkDefault(self.outputs, "Raw", editable=True)
    def ExecuteNode(self):
        self.outputs[0].stateHhError = 0
TemplateRegisterNdMainstream(NodeInputRaw, 0, "Inputs", label="Raw")

class NodeInputNow(TntTnBase):
    bl_idname = 'TntNodeInputNow'
    bl_label = "Now"
    nclass = 13
    def InitNode(self, context):
        NdAddSkDefault(self.outputs, "Now")
    def ExecuteNode(self):
        self.outputs[0].SetEraZState(GetNowEraZ(), 0)
TemplateRegisterNdMainstream(NodeInputNow, 1, "Inputs")

niezSafeSetTgl = True
def NiezTxtUpdate(self, context):
    global niezSafeSetTgl
    if niezSafeSetTgl:
        niezSafeSetTgl = False
        sucess = False
        try:
            self.txtInput = re.sub("[a-zA-Z ]", "", self.txtInput)
            num = abs(eval(self.txtInput))
            self.txtInput = str(num).split(".")[0]
            self.txtInputError = ""
            sucess = True
        except Exception as ex:
            self.txtInputError = str(ex)
        if not self.txtInput:
            self.txtInput = "0"
            self.txtInputError = ""
            sucess = True
        if sucess:
            self.txtLastSucess = self.txtInput
        niezSafeSetTgl = True
    bpy.app.timers.register(functools.partial(SetUnchangeNdLabelTimer, repr(self)), first_interval=0.01) #Костыль.
class NodeInputEraZ(TntTnBase):
    bl_idname = 'TntNodeInputEraZ'
    bl_label = "Era Z"
    nclass = 13
    bl_width_default = 220
    txtInput: bpy.props.StringProperty(name="Input", default="", description="Time in milliseconds from \" 0000.00.00  00:00:00 \" as a string", update=NiezTxtUpdate)
    txtLastSucess: bpy.props.StringProperty(name="txtLastSucess", default="")
    txtInputError: bpy.props.StringProperty(name="Error", default="")
    def InitNode(self, context):
        self.outputs.new(TntSocketEraZ.bl_idname, "Time")
        global niezSafeSetTgl
        niezSafeSetTgl = False #Для сырого ввода далее.
        num = GetNowEraZ()
        self.txtInput = f"{num//1000000*1000000} + {num%1000000} * 1"
        niezSafeSetTgl = True
        self.txtLastSucess = self.txtInput
    def DrawNode(self, context, colLy):
        colLy.prop(self,'txtInput', text="")
        if self.txtInputError:
            colLy.alert = True
            colLy.prop(self,'txtInputError', text="", icon="ERROR")
    def ExecuteNode(self):
        txt = TxtToTripleTxt(self.txtLastSucess)#, annex="").replace(" ","_")
        self.outputs[0].SetAllRaw(self.txtLastSucess, 0, txt)
TemplateRegisterNdMainstream(NodeInputEraZ, 2, "Inputs")

class NodeInputJulianRaw(TntTnBase):
    bl_idname = 'TntNodeInputJulianRaw'
    bl_label = "Julian Raw"
    nclass = 13
    bl_width_default = 180
    julYear:   bpy.props.IntProperty(name="Year", min=1800, max=2200)
    julMonth:  bpy.props.IntProperty(name="Month",  min=1, max=12)
    julDay:    bpy.props.IntProperty(name="Day",    min=1, max=31)
    julHour:   bpy.props.IntProperty(name="Hour",   min=0, max=23)
    julMinute: bpy.props.IntProperty(name="Minute", min=0, max=59)
    julSecond: bpy.props.IntProperty(name="Second", min=0, max=59)
    julZ:      bpy.props.IntProperty(name="Z",      min=0, max=999)
    def InitNode(self, context):
        self.outputs.new(TntSocketEraZ.bl_idname, "Julian")
        systime = datetime.datetime.now()
        self.julYear   = systime.year
        self.julMonth  = systime.month
        self.julDay    = systime.day
        self.julHour   = systime.hour
        self.julMinute = systime.minute
        self.julSecond = systime.second
        #self.julZ      = systime.microsecond//1000
    def DrawExtNode(self, context, colLy):
        colLy.prop(self,'julZ')
    def GetIsCorrectDay(self):
        return self.julDay<=tuple_tupleDayCountOfJulMonthMap[IsLeapYear(self.julYear)][self.julMonth-1]
    def DrawNode(self, context, colLy):
        col = colLy#.column(align=True)
        col.prop(self,'julYear')
        col.row().prop(self,'julMonth')
        row = col.row()
        row.alert = not self.GetIsCorrectDay()
        row.prop(self,'julDay')
        col = colLy#.column(align=True)
        col.prop(self,'julHour')
        col.row().prop(self,'julMinute')
        col.prop(self,'julSecond')
    def ExecuteNode(self):
        jul = Julian(self.julYear, self.julMonth, self.julDay, self.julHour, self.julMinute, self.julSecond, self.julZ)
        num = JulianToEraZ(jul)# if self.GetIsCorrectDay() else 0
        self.outputs[0].SetEraZState(num, 0)
        self.outputs[0].txtDisplay = str(EraZToJulian(int(self.outputs[0].txtEraZ)))
TemplateRegisterNdMainstream(NodeInputJulianRaw, 3, "Inputs")

class NodeInputOffset(TntTnBase):
    bl_idname = 'TntNodeInputOffset'
    bl_label = "Offset"
    nclass = 13
    bl_width_default = 220
    txtOffset: bpy.props.StringProperty(name="Offset", default="")
    def InitNode(self, context):
        self.outputs.new(TntSocketEraZ.bl_idname, "Time")
        self.txtOffset = "1111s 111s"
    def DrawNode(self, context, colLy):
        colLy.prop(self,'txtOffset', text="")
    def ExecuteNode(self):
        list_re = re.findall("[\d.]+[ydhmsz]", self.txtOffset)
        offset = 0
        for li in list_re:
            fac = float(li[:-1])
            match li[-1]:
                case "y": fac *= 31_536_000_000
                case "d": fac *= 86_400_000
                case "h": fac *= 3_600_000
                case "m": fac *= 60_000
                case "s": fac *= 1_000
            offset += int(fac)
        self.outputs[0].SetEraZState(offset, 0)
        self.outputs[0].txtDisplay = EraZToTxtGreat(offset, Edm.edmNonLeft)
TemplateRegisterNdMainstream(NodeInputOffset, 4, "Inputs")

class NodeTimeMath(TntTnWithErrorReport):
    bl_idname = 'TntNodeTimeMath'
    bl_label = "Time Math"
    nclass = 13
    operation: bpy.props.EnumProperty(name="Operation", default='ADD', items=( ('ADD',"Add",""), ('SUB',"Sub","") ))
    def InitNode(self, context):
        NdAddSkDefault(self.inputs, "Time")
        NdAddSkDefault(self.inputs, "Time")
        NdAddSkDefault(self.outputs, "Time")
    def DrawNode(self, context, colLy):
        #colLy.prop(self,'operation', text="")
        colLy.row().prop(self,'operation', expand=True)
    def ExecuteNode(self):
        ezs1 = self.inputs[0].EvaluateGetEraZStated()
        ezs2 = self.inputs[1].EvaluateGetEraZStated()
        if (ezs1.state==1)and(ezs2.state==1): #Если они оба не активные.
            self.outputs[0].SetEraZState(0, 1)
            return #Заметка: см. топологию.
        elif (ezs1.state!=2)and(ezs2.state!=2): #Если они оба не ошибки.
            match self.operation:
                case 'ADD': num = ezs1.eraz+ezs2.eraz
                case 'SUB': num = ezs1.eraz-ezs2.eraz
            self.outputs[0].txtEraZ = str(num)
        self.outputs[0].stateHhError = 2*( (self.inputs[0].stateHhError==2)or(self.inputs[1].stateHhError==2) )
TemplateRegisterNdMainstream(NodeTimeMath, 0, "Manupulation")

class NodeRawProbe(TntTnExecutableOnDraw):
    bl_idname = 'TntNodeRawProbe'
    bl_label = "Raw Probe"
    nclass = 13
    bl_width_default = 200
    def InitNode(self, context):
        NdAddSkDefault(self.inputs, "Raw", editable=True)
TemplateRegisterNdMainstream(NodeRawProbe, 0, "Outputs")

class NodeViewer(TntTnExecutableOnDraw):
    bl_idname = 'TntNodeViewer'
    bl_label = "Viewer"
    nclass = 13
    bl_width_default = 220
    typeView: bpy.props.IntProperty(name="Type view", default=0, min=0, max=3)
    def InitNode(self, context):
        self.inputs.new(TntSocketEraZ.bl_idname, "Time")
        self.typeView = 2
    def DrawExtNode(self, context, colLy):
        colLy.prop(self,'typeView')
    def DrawNode(self, context, colLy):
        try:
            jul = EraZToJulian(int(self.inputs[0].txtEraZ))
            match self.typeView:
                case 0: colLy.label(text=TxtToTripleTxt(self.inputs[0].txtEraZ))
                case 1: colLy.label(text=repr(jul))
                case 2: colLy.label(text=str(jul))
                case 3: colLy.label(text=EraZToTxtGreat(int(self.inputs[0].txtEraZ), Edm.edmAll)) #Заметка: "Вот такой год" и "Вот столько лет" -- это разное.
        except Exception as ex:
            colLy.alert = True
            colLy.label(text=str(ex))
            colLy.alert = False
TemplateRegisterNdMainstream(NodeViewer, 1, "Outputs")

class NsOp(bpy.types.Operator):
    bl_idname = 'tnt.node_op_ns'
    bl_label = "NsOp"
    who: bpy.props.StringProperty()
    opt: bpy.props.StringProperty()
    def execute(self, context):
        match self.opt:
            case 'Copy':
                ndRepr = eval(self.who)
                txt = ndRepr.GetTextGreat() #Заметка: никакой пайки, конструировать с нуля.
                context.window_manager.clipboard = txt
                ci = ndRepr.captures.add()
                ci.name = str(length(ndRepr.captures))
                ci.txtCap = txt
            case 'Exec':
                exec(self.who)
        return {'FINISHED'}
list_classes += [NsOp]

class NsCapture(bpy.types.PropertyGroup):
    txtCap: bpy.props.StringProperty(name="Capture", default="")
list_classes += [NsCapture]

class NodeStopwatch(TntTnExecutableOnDraw):
    bl_idname = 'TntNodeStopwatch'
    bl_label = "Stopwatch"
    nclass = 13
    bl_width_default = 220
    displayMethod: bpy.props.IntProperty(name="Display method", default=0, min=0, max=4)
    formatString: bpy.props.StringProperty(name="Format string", default="- y d h m s z")
    captures: bpy.props.CollectionProperty(type=NsCapture)
    def InitNode(self, context):
        self.inputs.new(TntSocketEraZ.bl_idname, "Time")
        self.inputs[0].txtEraZ = "0"
    def DrawExtNode(self, context, colLy):
        rowProp = colLy.row(align=True)
        row = rowProp.row(align=True)
        row.alignment = 'CENTER'
        row.label(text=self.bl_rna.properties['displayMethod'].name+":")
        rowProp.prop(self,'displayMethod', text=list_edmNames[self.displayMethod])
        AddNiceColorProp(colLy, self,'formatString')
        #colLy.label(text="Captures: "+str(length(self.captures)))
    def GetTextGreat(self):
        return EraZToTxtGreat(int(self.inputs[0].txtEraZ), self.displayMethod, formatString=self.formatString)
    def DrawNode(self, context, colLy):
        try:
            txt = self.GetTextGreat()
            op = colLy.operator(NsOp.bl_idname, text=txt)
            op.who = repr(self)
            op.opt = 'Copy'
        except Exception as ex:
            colLy.alert = True #Todo: возможно стоит это в класс отправить.
            colLy.label(text=str(ex))
            colLy.alert = False
        colItems = colLy.column(align=True)
        for cyc, li in enumerate(self.captures):
            rowItem = colItems.row().row(align=True)
            rowItem.prop(li,'txtCap', text="")
            op = rowItem.operator(NsOp.bl_idname, text="", icon='TRASH')
            op.who = repr(self)+f".captures.remove({cyc})"
            op.opt = 'Exec'
TemplateRegisterNdMainstream(NodeStopwatch, 2, "Outputs")

isDataOnRegisterDoneTgl = True

@bpy.app.handlers.persistent
def DataOnRegister(dummy, d):
    if isDataOnRegisterDoneTgl:
        MnUpdateAllNclassFromTree()

def register():
    bpy.app.handlers.load_post.append(DataOnRegister)
    for li in list_classes:
        bpy.utils.register_class(li)
    RegisterNodeCategories()
def unregister():
    for li in list_classes:
        bpy.utils.unregister_class(li)
    UnregisterNodeCategories()

if __name__=="__main__":
    register()
    MnUpdateAllNclassFromTree(False)
