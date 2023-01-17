"""Программный модуль - имплементация на python графического вьюера параметров полетных данных
Использует пакеты с файлами json, сгенерированными в системе Easyfdr после обработки в ней прямых копий с борта воздушного судна.
Оригинальное приложение - Plotter32 (Plotter64,PlotterDeb) -создано автором на Lazarus и является частью комплекта Easyfdr-система анализа полётных данных 
В данном модуле реализован только базовый функционал, для демонстрации навыков программирования автора
Использование:
    Главное окно приложения:
В верхнем правом углу основного экрана находятся легенды графиков параметров, подписанные мнемоническими обозначениями. Визир- вертикальная линия, отображающая срез значений параметров в момент времени.    
Загрузка пакета: диалог выбора по кнопке "Локальный полёт" или пункт меню Файл->Локальный полёт, в папке flights выбрать подпапку с полетом
Левый клик мыши на экране графиков устанавливает положение визира
PgUp, PgDown- выбор активного параметра, так же клик мыши по легенде или по графику параметра
Key_Up: перемещение выбранного параметра вверх
Key_Down: перемещение выбранного параметра вниз
Key_Left: сдвиг экрана вперед (вправо)
Key_Right: сдавиг экрана назад (влево)
CTRL+Key_Up: масштабирование выбранного параметра в большую сторону. То же самое клавишей А
CTRL+Key_Down: масштабирование выбранного параметра в меньшую сторону. То же самое клавишей Z
CTRL+Key_Left: расширение выделения графика. То же самое клавишей Q
CTRL+Key_Right: уменьшение выделения графика. То же самое клавишей W
Enter: Применение выделения графика. График растягивается по границам выделения
    Окно выбора параметров:
Выбирается пунктом меню "Параметры". В открывшемся окне верхняя панель, на которой EditBox для фильтрации списка и кнопка OK
В левой части окна - список параметров, имеющихся в пакете. В правой- список выбранных параметров. Выбор активируется нажатием кнопки.
В список выбранных параметры попадают по клику мыши на нужной строке списка слева. 
По клику мыши на списке справа, параметр удаляется из выбора   
 """


from PyQt5 import Qt,QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QWidget, QShortcut
from PyQt5.QtGui import QKeySequence
import sys
#import random
import json
from PyQt5.QtWidgets import QFileDialog
import numpy as np
import configparser
import datetime
import csv
import platform
""" читаем ini-файл и сохраненный путь к пакету"""
config = configparser.ConfigParser()
selection_rect=[]		
res=config.read("settings.ini", encoding='utf-8')
#print('confif file',config.sections())
readdir = config["dir"]
filepath = readdir["name"]
altPressed=False
startmovex=0

parameters=[]
timelinescr=[]
vizirx=0
"""инициализация шкалы параметра"""
scale_={'min':0,'max':0,'zero':0,'miny':0,'maxy':0,'name':'','ticks':[]}
selected=''
pindex=0
gloffset=0
scrshift=0
filt=''
ticks=[]
"""массив цветов"""
colorz = ['#FFF8F0','#D3D3D3','#E22B8A','#1E69D2','#B469FF','#B5E4FF','#EBCE87','#00FC7C','#D355BA','#DB7093','#E1E4FF','#8CB4D2','#D0E040','#507FFF','#B9DAFF','#DCF8FF','#F0FFF0','#00D7FF','#00FF7F','#D4FF7F','#00A5FF','#FACE87','#9314FF','#4763FF','#FFFF00','#FFFFF0','#F0FFFF','#7A96E9','#C1B6FF','#90EE90']  
 
saved=[]
param_table=[]
filtered_param_table=[]
""" функция вычисления количества разрядов в числе"""
def number_ofdigits(n):
    i = 0
    while n > 0:
        n = n//10
        i += 1
    return i
def slash():
    """ установка слеша взависимости от ОС"""
    platf=platform.platform()
    if 'Windows' in platf: return '\\'
    else: return '/'
def otherslash(slash):
    if slash=='\\': return '/'
    else: return '\\'    
def tickexists(hour,mint,secs):
    """ при создании массива меток на временной линейке требуется проверка есть ли уже такая метка""" 
    global ticks
    #print(hour,mint,secs)
    if len(ticks)==0:
        
        return False
    for t in ticks:
        if t['hour']==hour and  t['min']==mint and t['sec']==secs: return True
    return False
def maketicks1(tim):# matrix
    """ создание временной линейки в режиме сжатия графика (сжатие означает что на один пиксель экрана выводятся данные за промежуток времени)"""
    global ticks
    
    ticks.clear()
    st=tim[0][0]
    en=tim[-1][-1]
    delta=en-st
    #print('delta',delta)
    cnt=0
    for t in tim:
        cnt+=1
        for tm in t:
            
            curr=datetime.datetime.fromtimestamp(tm//1000).timetuple()
            #print(curr)
            if curr[4] in (15,30,45)and curr[5]==0 and not tickexists(curr[3],curr[4],curr[5]):
                
                posx=cnt
                 
                tick={'hour':curr[3],'min':curr[4],'sec':curr[5],'ticklen':10,'posx':posx,'msecs':tm}
                
                ticks.append(tick)
            if curr[4]==0 and curr[5]==0 and not tickexists(curr[3],curr[4],curr[5]): 
                posx=cnt
                tick={'hour':curr[3],'min':curr[4],'sec':curr[5],'ticklen':20,'posx':posx,'msecs':tm}
                ticks.append(tick)
            if  curr[4] in (5,10,15,20,25,30,35,40,45,50,55) and curr[5]==0 and not tickexists(curr[3],curr[4],curr[5]):
                posx=cnt
                tick={'hour':curr[3],'min':curr[4],'sec':curr[5],'ticklen':7,'posx':posx,'msecs':tm}
                ticks.append(tick)
            if delta<500000  and curr[5] in (5,10,15,20,25,30,35,40,45,50,55) and not tickexists(curr[3],curr[4],curr[5]):
                posx=cnt
                tick={'hour':curr[3],'min':curr[4],'sec':curr[5],'ticklen':5,'posx':posx,'msecs':tm}
                ticks.append(tick)            
    #print(ticks)                
def maketicks2(tim): #plain
    """создание временной шкалы в режиме расширения графика (срез массива меньше чем ширина экрана)"""
    global ticks
    
    ticks.clear()
    st=tim[0]
    en=tim[-1]
    delta=tim[-1]-tim[0]
    print('delta',delta)
    cnt=0
    for tm in tim:
        cnt+=1
        curr=datetime.datetime.fromtimestamp(tm//1000).timetuple()
        if curr[4] in (15,30,45)and curr[5]==0 and not tickexists(curr[3],curr[4],curr[5]):
            posx=cnt
            tick={'hour':curr[3],'min':curr[4],'sec':curr[5],'ticklen':15,'posx':posx,'msecs':tm}
            ticks.append(tick)
        if  curr[5] in (5,10,15,20,25,30,35,40,45,50,55)  and not tickexists(curr[3],curr[4],curr[5]):
            posx=cnt
            tick={'hour':curr[3],'min':curr[4],'sec':curr[5],'ticklen':10,'posx':posx,'msecs':tm}
            ticks.append(tick)
        if delta<100000   and not tickexists(curr[3],curr[4],curr[5]):
            posx=cnt
            tick={'hour':curr[3],'min':curr[4],'sec':curr[5],'ticklen':5,'posx':posx,'msecs':tm}
            ticks.append(tick)
def search_curval(posx,paramindex):
    """вычисление значения параметра по индексу(номеру пикселя по Х)"""
    scr=flt.parameters[paramindex]['screenx']
    a=scr[:posx]
    #если режим растяжения и вместо данных -999999 традиционно используемое мной в качестве пустого числа
    for i in reversed(a):
        if i!=-999999: return i
    return 0        
def search_time(tim,wd):
    #print('search_time',wd,msto_onlytime(tim))
    tim=int(int(tim/1000)*1000)
    if tim<flt.timeline[0]:return 0
    try:
        for t in flt.timeline:
        #
            if msto_onlytime(tim)==msto_onlytime(t):
                print('found',msto_onlytime(t),tim,flt.timeline.index(t))        
                return flt.timeline.index(t)
    except (Exception, Error) as error: print(error)        
    finally:print('end timeline',msto_onlytime(flt.timeline[-1]),'requiered',msto_onlytime(tim))        
    return flt.timeline.index(flt.timeline[-1])        
def filter999(massv):
    #очистка массива от пустот
    newmassv=[]
    for a in massv:
        if a!=-999999: newmassv.append(a)
    return newmassv    
def minim(i):
    """ вычисление минимума в массиве, -999999 игнорируется потому что это пустота"""
    if i==-999999: 
        return 999999
    else: return i
def absz(i):
	if i==-999999: return 999999
	else: return abs(i)    
def mstotime(ms):
    """перевод миллисекунд JS во дата-время python """
    return datetime.datetime.fromtimestamp(ms/1000) 
def msto_onlytime(ms):
    """перевод миллисекунд JS во время python """
    data=datetime.datetime.fromtimestamp(int(ms/1000))
    return datetime.datetime.time(data)    
class flight(object):
    """Класс представляет полётные данные. загружается пакет параметров в структуры экземпляра класса """
    def __init__(self,filepath):
        print('constructor',filepath)
        """массив временной линейки экрана"""
        global timelinescr
        timelinescr.clear()
        self.parameters=[]
        self.parameters.clear()
        self.timeline=[]
        self.header={}
        header=[]
        self.header.clear()
        self.maxopros=8
        cfg=configparser.ConfigParser()
        try: # читаем ини файл пакета
            cfg.read(filepath+slash()+"settings.ini", encoding='utf-8')
        except: return
        try: # читаем индексы параметров, выбранные ранее. При отсутствии файла будет ошибка. В оригинальной версии загружается шаблон
            sav=open(filepath+slash()+'saved.txt','r')
        except:return 
        try: # читаем описание полета. При отсутствии файла будет ошибка. 
            head=open(filepath+slash()+'header.txt','r')
            for lin in head:
                header.append(lin)
            if header[1].strip()=='b737': header[1]='Boeing 737'
            elif header[1]=='b777': header[1]='Boeing 777'
            elif header[1]=='a330': header[1]='Airbus 330'
            self.header['actype']=header[1]
            self.header['tailn'] =header[2]
            self.header['date']  =header[3]
            self.header['origin']=header[4]
            self.header['destin']=header[5]
            self.header['flight']=header[6]
            head.close()            
        except:return         
        savd=[]
        
        for line in sav:
             
            savd.append(int(line))
            #загружаем данные из JSON
            param=self.readJson(int(line))
            mnem=param[4]
            offset=param[3]
            scale=param[5]
            if mnem in cfg:
                scl=cfg[mnem]['scale'];
                try: #читаем настройки отображения параметра на экране - масштабирование и сдвиг по вертикали
                    scale=float(scl)
                except: scl=1
                ofst=cfg[mnem]['ofset']; offset=int(ofst)
            else:
                scl=1
                ofst=0
            screenx=[]
            minscreen=[]
            koeff=param[2]
            #if ofst!=0: offset=ofst
            #else: 
            
            # полный массив данных используется для копирования из него срезов на экран    
            full_len_par=param[6]
            koef_ext=param[7] #коэффициент расширения
            isbin=param[8] # если разовая команда то True
            name=param[9] #наименование параметра, выводится рядом со шкалой
            # полный массив времени отдельно от параметров
            if mnem in ('time_','datetime_'): self.timeline=full_len_par
            parameter={'name':name,'isbin':isbin,'mnem':mnem,'screenx':screenx,'minscreen':minscreen,'koeff':koeff,'offset':offset,'scale':scale,'full_len_par':full_len_par,'koef_ext':koef_ext}
            
            self.parameters.append(parameter)
        for param in self.parameters:
            flp=param['full_len_par']
            #print(param)
            newflp=[]
            ke=param['koef_ext']
            # вычисляем максимальную опросность среди параметров, для синхронности срезов
            if self.maxopros>ke: 
                step=  self.maxopros//ke
                for val in flp:
                    for a in range(step):
                        if a==0: newflp.append(val)
                        else: newflp.append(-999999)
            else:newflp=flp            
            i=self.parameters.index(param)
            #print(newflp)
            self.parameters[i]['full_len_par'] =newflp                       
        global saved
        saved=savd
        self.timeline.clear()
        # пробуем время в формате js
        self.timeline=self.readJson('jstime')
        self.timeline=self.timeline[6]
        
         #если время некорректно, загружаем время delphi и конвертим в js
        if len(self.timeline)<60 or self.timeline[60]<0:
            self.timeline=self.readJson('datetime')
            self.timeline=self.timeline[6]
            newtime=[]
            for item in self.timeline:
                
                seconds = (item - 25569) * 86400.0*1000
                #print(mstotime(seconds))
                newtime.append(int(seconds))
            self.timeline=newtime 
            

        tmp=[] 
        milsec=1000//self.maxopros
        for d in self.timeline:
            for ms in range(self.maxopros):
                msecs=ms*milsec   
                tmp.append(d+msecs)
                
        self.timeline=tmp
         
        #print('end constructor')        
    def to_screen(self):
        """создание среза всех выбранных параметров для отображения на экране. Здесь реализуются режимы сжатия и расширения"""
        global selection_rect
        global timelinescr
        global scrshift
        global scrn
        print('to scr',scrn.wdt)
        if len(selection_rect)!=0:
            #если ранее было сделано выделение участка экрана- делаем срез по началу и концу экранных координат выделения
            stindex=min(selection_rect)
            eindex=max(selection_rect)
            print('rect',stindex,eindex)
        else:
             #Иначе начало и конец горизонтали экрана       
            stindex=0; eindex=scrn.wdt-1
            #print('stindex',stindex,'eindex', eindex)
        if len(timelinescr)>100:
            #приложение развернуто
            tim=timelinescr.copy()
            if msto_onlytime(tim[0])==msto_onlytime(tim[-1]):
                startindex=search_time(tim[stindex],'startindex')-flt.maxopros
                endindex=search_time(tim[eindex],'endindex')+scrshift                
            #индексы полной линейки времени. индексы параметров синхронны
            else: 
                startindex=search_time(tim[stindex],'startindex')+scrshift
                endindex=search_time(tim[eindex],'endindex')+scrshift
             
            if msto_onlytime(self.timeline[startindex])==msto_onlytime(self.timeline[endindex]):return
        else: startindex=0; endindex=len(self.timeline)-1   
        #print('startindex',startindex,'endindex',endindex, 'scrshift',scrshift)
        if scrshift!=0: 
            #если сдвигали вид, избегаем выхода индексов за начало и конец линейки времени
            if startindex<0: 
                startindex=0
            if startindex>len(self.timeline)-1: startindex=len(self.timeline)-60
            if endindex<0: endindex=60
            if endindex>len(self.timeline)-1: endindex=len(self.timeline)-1 
        
         
            #print('tim=self.timeline[startindex:endindex]',startindex,endindex)        
        tim=self.timeline.copy()
        #копия линейки времени и режем нужный участок
        tim=tim[startindex:endindex]
        #print('NEW',msto_onlytime(tim[0]),msto_onlytime(tim[-1]))
        scrshift=0
        delta=tim[-1]-tim[0]
             
        ostatok=-1
        tim2=tim.copy()
        while ostatok!=0:
            tim2.pop(-1)
            lenp=len(tim2)
            #сжатие по пропорции pixel это количество элементов в массиве которые будут в одном пикселе экрана
            if scrn.wdt>0:pixel=lenp//scrn.wdt
            if scrn.wdt>0:ostatok=lenp%scrn.wdt
        a = np.array(tim2)
        if pixel>0:
            b = a.reshape(-1, pixel) #сжатие сначала линейки времени
            maketicks1(b)
            maxx=[]
            for ii in b:
                #ii=filter999(ii)
                if len(ii)>0:
                    av=max(ii); 
                    maxx.append(av);
            tim=maxx
        if pixel==0:maketicks2(tim) #если не сжатие а растяжение    
        timelinescr=tim.copy()
        if len(timelinescr)<scrn.wdt:
            starttime=timelinescr[0]
            endtime=timelinescr[-1]
            delta=endtime-starttime
            stept=int(delta/scrn.wdt)
            
            timelinescr=[starttime+(stept*x) for x in range(scrn.wdt)]
            #print(timelinescr)
        for param in self.parameters:
            i=self.parameters.index(param)
            mnem=param['mnem']
            param['screenx'].clear()
            param['minscreen'].clear()
            flp=param['full_len_par'].copy()
            flp=flp[startindex:endindex]
            #print(' srez ',mnem, len(flp))
            #flp=filter999(flp)
            #print(' filter ',mnem, len(flp))
            #print(len(flp))
            lenp=len(flp)
            olenp=lenp       
            
            #print(mnem)
            ostatok=-1; pixel=0
            while ostatok!=0:
                if ostatok>=len(flp):break
                flp.pop(-1)
                lenp=len(flp)
                pixel=lenp//scrn.wdt
                ostatok=lenp%scrn.wdt
                #print(mnem,ostatok,lenp)
            
            nlenp=len(flp)
            #print(mnem,'nlenp',nlenp)
            if pixel>0:
                
                a = np.array(flp)
                #print(mnem,'reshape',pixel)
                b = a.reshape(-1, pixel)
                #print(mnem,scrn.wdt,len(b))
                maxx=[];minx=[]
                for ii in b:
                #ii=filter999(ii)
                    if len(ii)>0:
                        av=max(ii); 
                        maxx.append(av); 
                    if len(ii)>0:
                        bv=min(ii,key=minim); 
                        minx.append(bv)
            else:  maxx=flp; minx=flp  
            self.parameters[i]['screenx']=maxx # максимум параметра на 1 пиксель экрана
            self.parameters[i]['minscreen']=minx # минимум на 1 пиксель
            #print(mnem,'len(screenx)',len(self.parameters[i]['screenx']))
        #mw.figure.update()           
        #print('end toscr')            
    def readJson(self,param):
        #подпрограмма чтения файла
        filename=filepath+slash()+str(param)+r'.json'
        #print('readJson',filename) 
        with open(filename) as f:
            templates = json.load(f)
        
            keyz=templates.keys()
            koeff=float(templates['koeff'])
            offset=int(templates['ofsetz'])
            scale=float(templates['scale'])
            isbin=bool(templates['isbin'])
            name=templates['name']
            mnem=list(keyz)[0]
            param=templates[mnem]
            parameter=[]
            o=len(param[0])
            if o>self.maxopros:self.maxopros=o
            for opr in param:
                for val in opr:parameter.append(val)
        screenx=[]
        minscreen=[]        
        rezult=[]
        rezult.append(screenx)
        rezult.append(minscreen)
        rezult.append(koeff)
        rezult.append(offset)
        rezult.append(mnem) 
        rezult.append(scale)
        rezult.append(parameter)
        rezult.append(o)
        rezult.append(isbin)
        rezult.append(name)
        return rezult        
     
            
 
class scr(object):
    def __init__(self,wdt,ht):
        self.wdt=wdt
        self.ht=ht
    def update(self,wdt,ht):
        global flt
        self.wdt=wdt
        self.ht=ht
        try:
            flt.to_screen()
        except (Exception, Error) as error:
            print("Ошибка toscr", error)            
 
def save_changes():
    # сохраняем изменения в ини файлах пакета и программы
    global filepath
    cfg=configparser.ConfigParser()
    
    cfg.read(filepath+slash()+"settings.ini", encoding='utf-8')
      
    for p in flt.parameters:
        mnem=p['mnem']
        #print(mnem,cfg.has_section(mnem))  
        if not cfg.has_section(mnem): 
            cfg.add_section(mnem)
            #print('add section',mnem)
        cfg.set(mnem,'scale',str(p['scale']))
        cfg.set(mnem,'ofset',str(p['offset']))
        
    with open(filepath+slash()+'settings.ini', 'w') as configfile:
        cfg.write(configfile)
    cfg.read("settings.ini", encoding='utf-8')
    cfg.set('dir','name',filepath)
    with open('settings.ini', 'w') as configfile:
        cfg.write(configfile)
    #print('end save_changes')
def hex_to_rgb(value):# шестнадцатитеричный код цвета в кортеж
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def createticks(ht,minx,maxx,koeff,scale,offset):
    #метки для шкалы выбранного параметра
    global scale_
    scale_['ticks'].clear()
    ticks=[]
    n=maxx
    dig=number_ofdigits(maxx)-1
    fd=int(str(abs(maxx))[0])
    while n>minx:
        tick=fd*(10**dig)
        #print(tick,minx)
        if tick<minx:break
        tcky=int(ht-tick/koeff*scale+offset)
        newtick={'val':tick,'y':tcky}
        ticks.append(newtick);
        #print(tick,tcky)
        fd-=1; #n-=tick
    scale_['ticks']=ticks    
   #print(scale_)
def param_by_color(pixcolor):
    #сравнение цвета пикселя по указателю мыши с цветами параметров
    cnt=len(flt.parameters)
    for i in range(cnt):
        color=hex_to_rgb(colorz[i])
        color=color = QtGui.QColor(color[0], color[1], color[2], 255).getRgb()
        print(pixcolor,color)
        if pixcolor==color: return i #возвращаем индекс параметра
    return -1        
class PlotFrame(QtWidgets.QFrame):
    #холст на котором рисуем графики 
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet('background-color: black;')
        #self.rand_ranges = [ random.randrange(1, 100) for _ in range(4) ]
    def mousePressEvent(self, e):
        global vizirx
        global selection_rect
        global pindex
        global startmovex
        px=self.grab()
        img = px.toImage()
        pixcol=img.pixelColor(e.x(), e.y())#цвет пикселя
        index=param_by_color(pixcol.getRgb())
        print(index)
        if index>=0:
            pindex=index #pindex это глобальный индекс выбранного параметра
            self.update()
        if altPressed:
            startmovex=e.y()
        if e.buttons() & QtCore.Qt.LeftButton: 
            vizirx=e.x()
            #установка визира
            self.update()
            e.ignore()
            QtWidgets.QWidget.mousePressEvent(self, e)
    def mouseMoveEvent(self, e):
        global selection_rect
        x = e.x()
        if not altPressed:selection_rect.append(x)
        if altPressed:
            #сдвигаем параметр за курсором мыши
            flt.parameters[pindex]['offset']-=startmovex-e.y()
        self.update()
    def mouseReleaseEvent(self, QMouseEvent):
        global selection_rect
        x = QMouseEvent.x()
        #по разжатию кнопки мыши, если сделано выделение перерисовываем экран и снимаем выделение 
        if len(selection_rect)>0:flt.to_screen()
        if len(selection_rect)>0:selection_rect.clear()
        self.update() 
    def plot_update():
        self.update()    

    def paintEvent(self, event):
        global scale_
        global pindex 
        global flt
        global vizirx
        global timelinescr 
        # отрисовка подготовленных массивов       
        if  len(flt.parameters[0]['screenx'])==0:
            # если нечего рисовать выйдем
            return        
        painter = QtGui.QPainter(self)
        rectht=10
        ht=self.size().height()
        wdt=self.size().width()
        timelinecolor = QtGui.QColor(255, 255, 255, 255)
        digitstimelinecolor = QtGui.QColor(0, 0, 0, 255)
        emptyfill = QtGui.QColor(0, 0, 0, 1)
        selectionfill = QtGui.QColor(255, 0, 255, 10)
        selcolor = QtGui.QColor(255, 255, 0, 255) 
        vizircolor =  QtGui.QColor(255, 0, 0, 255)  
        timecolor=QtGui.QColor(255, 255, 0, 255)
        painter.setPen(vizircolor)
        painter.setFont(QtGui.QFont('Decorative', 12))
        # выводим общие данные о полете
        painter.drawText(10,15,"Aircraft Type: "+flt.header['actype']+' '+"Tail N: "+flt.header['tailn'])
        painter.drawText(10,35,"Flight Date: "+flt.header['date']+' '+"Flight Number: "+flt.header['flight']) 
        painter.drawText(10,55,"Origin : "+flt.header['origin']+' '+"Destination: "+flt.header['destin'])         
        painter.setFont(QtGui.QFont('Decorative', 10))        
        for param in flt.parameters:
            index=flt.parameters.index(param)
            alpha=255 
            color = hex_to_rgb(colorz[index])
            color = QtGui.QColor(color[0], color[1], color[2], alpha)
            painter.setPen(color) 
            painter.setBrush(color)
            painter.drawRect(wdt-100, rectht, 80,15)
         
            minscreen=flt.parameters[index]['minscreen']
            screenx=flt.parameters[index]['screenx']
            koeff=flt.parameters[index]['koeff']
            offset=flt.parameters[index]['offset']
            mnem=flt.parameters[index]['mnem']
            name=flt.parameters[index]['name']
            isbin =flt.parameters[index]['isbin']
            painter.drawText(wdt-150,rectht+10,mnem)
            scale=flt.parameters[index]['scale']
            v=0; 
            prev=screenx[0]
            maxval=ht-int(max(screenx)/koeff*scale)+offset
            minval=ht-int(min(minscreen)/koeff*scale)+offset
            try:            
                cnt=0
                txty=0 
                koeff2=1
                #значения для шкалы
                zero=int((ht-0/koeff*scale+offset)*abs(koeff2))
                maxval=int((ht-max(screenx)/koeff*scale)*abs(koeff2))+offset
                minval=int((ht-min(minscreen,key=minim)/koeff*scale)*abs(koeff2))+offset
                maxx=max(screenx)
                minxx=min(minscreen,key=minim)
                fstretch=wdt/len(screenx) 
                if fstretch<=1:istretch=1
                if fstretch>1:istretch=int(fstretch) 
                #istretch>1 режим растяжки, и шаг сдвига 
                x=0 
                prevx=0
                prevy=int(ht-int(screenx[0]/koeff*scale)+offset)
                
                for r in screenx:
                    # перебор массива экранных значений
                                    
                    if istretch==1:mins=minscreen[x]
                    # вычисляем y максимума и минимума
                    cnt+=1
                    if cnt==10: txty=prevy                    
                    y=int(ht-int(r/koeff*scale)+offset)#
                    if istretch==1:miny=int(ht-int(mins/koeff*scale)+offset)#
                    if not isbin and r!=-999999:
                        if istretch>1 and prevy>ht:prevy=y 
                        #рисуем точку в режиме растяжки
                        painter.drawLine(prevx, prevy,x,y )
                        if istretch>1:painter.drawEllipse(x,y-1,3,3)
                        # рисуем минимумы только в режиме сжатия
                        if istretch==1:painter.drawLine(prevx,prevy,x,miny )
                        # пишем значения по координатам визира
                        if x==vizirx: 
                            painter.drawText(x,y,str(search_curval(x,index)))
                    if isbin and r!=0 and r!=-999999: 
                        painter.drawLine(prevx, prevy,x,y )# разовые команды только срабатывание
                        
                    if index==pindex and r!=-999999: 
                        # если параметр выделен, рисуем жирнее
                        if not isbin:painter.drawLine(prevx, prevy+1,x,y+1 )
                        if isbin and r!=0: painter.drawLine(prevx, prevy+1,x,y+1 )
                    if r!=-999999:
                        prev=r
                        prevx=x
                        prevy=y
                    x+=istretch    
                # легенда   
                painter.drawText(10,txty+15,mnem)
            except (Exception, Error) as error:
                print("Ошибка при draw", error)

            painter.setBrush(emptyfill)
            #pen = QtGui.QPen(selcolor, 2, Qt.SolidLine)
            painter.setPen(selcolor)
            if index==pindex:
                # если индекс соответствует выбранному параметру            
                painter.drawRect(wdt-102, rectht-2, 84,19)
                scale_['miny']=minval; scale_['maxy']=maxval; scale_['zero']=zero
                scale_['min']=minxx; scale_['max']=maxx; scale_['name']=name
                createticks(ht,minxx,maxx,koeff,scale,offset)
                #собрали данные для отрисовки шкалы
                showscale()
            rectht+=25
            painter.setPen(vizircolor)
            painter.drawLine(vizirx, 0,vizirx,ht)
            painter.drawText(vizirx+10,ht-40,str(msto_onlytime(timelinescr[vizirx])))
            painter.setPen(selectionfill) 
            painter.setBrush(selectionfill)
             
            if len(selection_rect)>0:
                print(selection_rect)
                #рисуем прямоугольник выделения
                wid=max(selection_rect)-min(selection_rect)                
                painter.drawRect(selection_rect[0], 0, wid,ht)
            painter.setPen(timecolor)    
            #отображаем линейку времени
            if len(timelinescr)>100:
                painter.setPen(timelinecolor) 
                painter.setBrush(timelinecolor)
                painter.drawRect(0, ht-25, wdt,ht)
                painter.setPen(digitstimelinecolor)
                for tm in ticks:
                    tick=tm['ticklen']
                    posx=tm['posx']
                    painter.drawLine(posx*istretch,ht-25,posx*istretch,ht-25+tick)
                painter.drawText(5,ht-5,str(msto_onlytime(timelinescr[0])))
                painter.drawText(wdt-45,ht-5,str(msto_onlytime(timelinescr[-1])))
        
                
def showscale():
    mw.scalez.update()
        
class ScalezFrame(QtWidgets.QFrame):
    """экран для отрисовки шкалы выбранного параметра"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet('background-color: black;')
        
         
    def paintEvent(self, event): 
        painter = QtGui.QPainter(self)      
        selcolor = QtGui.QColor(255, 255, 0, 255)          
        #словарь scale_ подготовлен во время отрисовки основного экрана
        ht=self.size().height()
        painter.setBrush(selcolor)
        painter.setPen(selcolor)
        painter.drawLine(20, scale_['zero'],40,scale_['zero'] )
        painter.drawText(22,scale_['zero']-5,'0')
        painter.drawLine(35, scale_['miny'],55,scale_['miny'] )
        painter.drawLine(35, scale_['maxy'],55,scale_['maxy'] )
        painter.drawLine(55, scale_['miny'],55,scale_['maxy'] )
        painter.drawText(22,scale_['miny']-5,str(round(scale_['min'],2)))
        painter.drawText(22,scale_['maxy']-5,str(round(scale_['max'],2)))
        num=number_ofdigits(scale_['max'])
        maxy=scale_['maxy']
        miny=scale_['miny']
        quarter= (miny-maxy)>(ht//4)
        #рисуем промежуточные метки на шкале если параметр занимает не менее четверти экрана по вертикали
        if quarter:
            for tick in scale_['ticks']:
                painter.drawLine(45, tick['y'],55,tick['y'] )            
                painter.drawText(22,tick['y']-5,str(tick['val']))
        color = hex_to_rgb(colorz[pindex])
        color = QtGui.QColor(color[0], color[1], color[2], 255)
        painter.setPen(color)
        painter.setFont(QtGui.QFont('Decorative', 15))
        painter.rotate(270)
        painter.drawText(-ht+10,15,scale_['name'])
        
         
class FormWidget(Qt.QWidget):
    """панель с кнопками"""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.button1 = Qt.QPushButton(" Локальный полет")
        self.button1.setIcon(QtGui.QIcon('pic\\folders_explorer.png'))
        self.button1.setFixedHeight(30)
        self.button2 = Qt.QPushButton(" База Данных")
        self.button2.setIcon(QtGui.QIcon('pic\\network_clouds.png'))
        self.button2.setFixedHeight(30)
        self.button3 = Qt.QPushButton(" Во всю длину")
        self.button3.setIcon(QtGui.QIcon('pic\\plane.png'))
        self.button3.setFixedHeight(30)
        self.button4 = Qt.QPushButton(" Сдвиг назад")
        self.button4.setIcon(QtGui.QIcon('pic\\arrow_left.png'))
        self.button4.setFixedHeight(30)
        self.button5 = Qt.QPushButton(" Сдвиг вперед")
        self.button5.setIcon(QtGui.QIcon('pic\\arrow_right.png'))
        self.button5.setFixedHeight(30)
        self.button1.setFixedWidth(150)
        self.button2.setFixedWidth(150)
        self.button3.setFixedWidth(150)
        self.button4.setFixedWidth(150)
        self.button5.setFixedWidth(150)
        self.layout = Qt.QHBoxLayout(self)
         
        self.layout.addWidget(self.button1)
        self.layout.addWidget(self.button2)
        self.layout.addWidget(self.button3)
        self.layout.addWidget(self.button4)
        self.layout.addWidget(self.button5)
        self.setLayout(self.layout)
        self.setFixedHeight(35)
        self.layout.setContentsMargins(0, 0, 0, 0)
class MainWindow(Qt.QMainWindow):
    """Форма главного окна. Состоит из меню, панели кнопок и двух экранов-для шкалы(слева) и графиков(справа)"""
    resized = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1000, 600)
        mainMenu = self.menuBar()
        
        fileMenu = mainMenu.addMenu("Файл")
        paramz = mainMenu.addMenu("Параметры")
        b_color = mainMenu.addMenu("Таблица")
        figure = mainMenu.addMenu('Шаблоны')
        self.setChildrenFocusPolicy(QtCore.Qt.NoFocus)
        LFAction = QtWidgets.QAction("Local Folder", self)
        paramaction=QtWidgets.QAction("Parameters", self)
        LFAction.setShortcut("Ctrl + L")
        fileMenu.addAction(LFAction)
        paramz.addAction(paramaction)
        LFAction.triggered.connect(self.showDialog)
        paramaction.triggered.connect(show_params_window)
        SVAction = QtWidgets.QAction("Server", self)
        fileMenu.addAction(SVAction)
        self.form_widget = FormWidget(parent)
        self.form_widget.button1.clicked.connect(self.showDialog)
        self.form_widget.button3.clicked.connect(self.fulllen)
        self.form_widget.button4.clicked.connect(self.shiftbk)
        self.form_widget.button5.clicked.connect(self.shiftfwd)
        
        self.shortcut_left = QShortcut(QKeySequence(QtCore.Qt.Key_Left), self)
        self.shortcut_left.activated.connect(self.shiftbk)
        self.shortcut_right = QShortcut(QKeySequence(QtCore.Qt.Key_Right), self)
        self.shortcut_right.activated.connect(self.shiftfwd)
        self.shortcut_up = QShortcut(QKeySequence(QtCore.Qt.Key_Up), self)
        self.shortcut_up.activated.connect(self.moveUp)
        self.shortcut_down = QShortcut(QKeySequence(QtCore.Qt.Key_Down), self)
        self.shortcut_down.activated.connect(self.moveDown)
        self.shortcut_scaleout = QShortcut(QKeySequence(QtCore.Qt.CTRL |QtCore.Qt.Key_Up), self)
        self.shortcut_scaleout.activated.connect(self.scaleOut)
        self.shortcut_scalein = QShortcut(QKeySequence(QtCore.Qt.CTRL |QtCore.Qt.Key_Down), self)
        self.shortcut_scalein.activated.connect(self.scaleIn)
        self.shortcut_selectout = QShortcut(QKeySequence(QtCore.Qt.CTRL |QtCore.Qt.Key_Left), self)
        self.shortcut_selectout.activated.connect(self.selectOut)
        self.shortcut_selectin = QShortcut(QKeySequence(QtCore.Qt.CTRL |QtCore.Qt.Key_Right), self)
        self.shortcut_selectin.activated.connect(self.selectIn)
        figures_layout = Qt.QHBoxLayout() 
        self.figure = PlotFrame(self)           
        self.scalez = ScalezFrame(self)
        self.scalez.setFixedWidth(60)
        figures_layout.addWidget(self.scalez)        
        figures_layout.addWidget(self.figure)
        self.form_widget.button2.clicked.connect(self.figure.plot_update)
        main_layout = Qt.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.form_widget)
        main_layout.addLayout(figures_layout)
        central_widget = Qt.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.showMaximized()
    def setChildrenFocusPolicy (self, policy):
        def recursiveSetChildFocusPolicy (parentQWidget):
            for childQWidget in parentQWidget.findChildren(QWidget):
                childQWidget.setFocusPolicy(policy)
                recursiveSetChildFocusPolicy(childQWidget)
        recursiveSetChildFocusPolicy(self)
    def selectOut(self):
        global selection_rect
        if len(selection_rect)==0:
            selection_rect=[vizirx-10,vizirx+10]
            #print(vizirx,selection_rect)
        else:
            first=min(selection_rect); last=max(selection_rect) 
            selection_rect=[first-10,last+10]
            self.figure.update()                
    def selectIn(self):
        global selection_rect
        if len(selection_rect)!=0:
            first=min(selection_rect); last=max(selection_rect) 
            selection_rect=[first+10,last-10]
            self.figure.update()
    def resizeEvent(self, event):
        self.resized.emit()
        global scrn
        scrn.update(self.figure.size().width(),self.figure.size().height())
         
        return super(MainWindow, self).resizeEvent(event)
    def fulllen(self):
        global selection_rect
        global timelinescr
        timelinescr.clear()
        selection_rect.clear()
        flt.to_screen()
        self.figure.repaint()
    def shiftbk(self):
        global scrshift
        scrshift=-10*flt.maxopros 
        print("shiftbk calc ",scrshift)        
        flt.to_screen()
        self.figure.repaint()  
        #print("end shiftbk")
    def shiftfwd(self):
        global scrshift
        scrshift=+10*flt.maxopros 
        print("shiftbk calc ",scrshift)        
        flt.to_screen()
        self.figure.repaint()  
        print("end shiftfwd")
    def moveDown(self):
        flt.parameters[pindex]['offset']+=10
        self.figure.update()
    def moveUp(self):
        flt.parameters[pindex]['offset']-=10
        self.figure.update()
    def scaleOut(self):
        flt.parameters[pindex]['scale']*=1.1
        self.figure.update()
    def scaleIn(self):
        flt.parameters[pindex]['scale']/=1.1
        self.figure.update()         
    def showDialog(self):
        global filepath
        global parameters
        global flt        
        dirname = QFileDialog.getExistingDirectory(self, "Выбрать папку", ".")
        filepath=QtCore.QDir.toNativeSeparators(dirname)
        #del flt
        flt=flight(filepath)
        flt.to_screen()
    def keyPressEvent(self, event):
        print ('any key'+str(event.key()))
        global pindex
        global parameters
        global saved
        global vizirx
        global selection_rect
        global altPressed 
        if event.key() == QtCore.Qt.Key_Q:
            #раздвижение селекции
            if len(selection_rect)==0:
                selection_rect=[vizirx-10,vizirx+10]
                print(vizirx,selection_rect)
            else:
                first=min(selection_rect); last=max(selection_rect) 
                selection_rect=[first-10,last+10]
            self.figure.update()                
             
        elif event.key() == QtCore.Qt.Key_W:
            if len(selection_rect)!=0:
                first=min(selection_rect); last=max(selection_rect) 
                selection_rect=[first+10,last-10]
            self.figure.update()
        elif (event.key() == 16777220): 
            if len(selection_rect)>0: 
                flt.to_screen()
                selection_rect.clear()
                self.figure.update()       
        elif event.key() == QtCore.Qt.Key_PageDown:
            pindex=pindex-1
            if pindex<0: pindex=0
            self.figure.update()            
        elif event.key() == QtCore.Qt.Key_PageUp:
            pindex=pindex+1
            if pindex>len(saved)-1:pindex=len(saved)-1
            self.figure.update()
         
        elif event.key() == 65: # нажали a
            flt.parameters[pindex]['scale']*=1.1
            self.figure.update()
        elif event.key() == 90: # нажали z
            flt.parameters[pindex]['scale']/=1.1
            self.figure.update()           
        elif event.key() == QtCore.Qt.Key_Alt: 
            altPressed=True        
        event.accept()
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Alt:
            altPressed=False   
    def closeEvent(self, event):
        save_changes()
        self.pressing = False
 
class FilterEdit(Qt.QTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.textChanged.connect(self.changeText)
    def changeText(self):
        global filt
        
        filt=self.toPlainText()
        filtered_fill()   
def show_params_window():
    global modalWindow
    global selectedpar
    global paramtb
    #окно выбора параметров   
    modalWindow = QtWidgets.QWidget(mw, QtCore.Qt.Window)
    modalWindow.setWindowTitle("Параметры")
    modalWindow.resize(1000, 700)
    modalWindow.setWindowModality(QtCore.Qt.WindowModal)
    modalWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
    modalWindow.move(mw.geometry().center() - modalWindow.rect().center() - 
         QtCore.QPoint(4, 30))
    paramtb=Tb(modalWindow)#основной список
    filtered_fill()    
    selectedpar=selectedp(modalWindow)#список выбранных
    
    selectedpar.setFixedWidth(200)
    modalWindow.text_edit = FilterEdit(modalWindow)
    
    modalWindow.layout = Qt.QVBoxLayout()
    modalWindow.toplayout = Qt.QHBoxLayout()
    modalWindow.bottomlayout = Qt.QHBoxLayout()
    modalWindow.okbutton = Qt.QPushButton(" OK")
    modalWindow.okbutton.setFixedWidth(200)
    modalWindow.okbutton.clicked.connect(setandclosep)
    #modalWindow.text_edit = Qt.QTextEdit()
    modalWindow.toplayout.addWidget(modalWindow.text_edit)
    modalWindow.text_edit.setFixedWidth(500)
    modalWindow.text_edit.setFixedHeight(30)
    modalWindow.toplayout.addWidget(modalWindow.okbutton)
    
    modalWindow.bottomlayout.addWidget(paramtb)
    modalWindow.bottomlayout.addWidget(selectedpar)
    
    modalWindow.layout.addLayout(modalWindow.toplayout)
    modalWindow.layout.addLayout(modalWindow.bottomlayout)
    modalWindow.setLayout(modalWindow.layout)
    modalWindow.show()
    #print('end modal show')
class selectedp(QTableWidget):
    def __init__(self,wg):
        super().__init__(wg)
        global filepath
        global param_table
        global filtered_param_table
        self.setGeometry(10, 10, 100, 100)
        sav=open(filepath+slash()+'saved.txt','r') #в файле saved индексы параметров которые были выбраны ранее
         
        self.setRowCount(0)
        savd=[]
        rn=1
        self.setColumnCount(1)
        
        self.setHorizontalHeaderItem(0, QTableWidgetItem('Selected'))
        for line in sav:
            self.setRowCount(rn)
            savd.append(int(line))
            id=int(line)
            color = hex_to_rgb(colorz[rn-1])
            color = QtGui.QColor(color[0], color[1], color[2], 255)
            item=  QTableWidgetItem(param_table[id][2])
            item.id=param_table[id][0] #находим параметр в списке по индексу
            item.setBackground(color)
            self.setItem(rn-1,0,item)# заполняем таблицу
            
            rn+=1 
        self.resizeColumnsToContents()
        sav.close()
        
    def mousePressEvent(self, e):
        global filepath
        QTableWidget.mousePressEvent(self, e) #  удаление из выбора по клику мыши
        
        savd=[]
        if e.buttons() & QtCore.Qt.LeftButton: 
            t = self.currentItem()
            index = self.currentIndex()
            removed=int(t.id) #индекс удаляемого
            
            self.removeRow(index.row()) #удаляем из таблички
            sav=open(filepath+slash()+'saved.txt','r') #читаем список выбранного
            for line in sav:
                savd.append(int(line))
                
            sav.close()
            savd.remove(removed) #удаляем и сохраняем
            
            sav=open(filepath+slash()+'saved.txt','w')
            for line in savd: sav.write(str(line) + '\n')
            sav.close()
def setandclosep():
    """Применение результатов выбора параметра- пересоздание экземпляра класса flight и закрытие окна выбора"""
    global filepath
    global flt
    global param_table
    global filtered_param_table
    flt=flight(filepath)
    flt.to_screen()
    mw.figure.repaint()
    modalWindow.close()
    param_table.clear()
    filtered_param_table.clear()
def insertnewp(id,name):
    """Добавление в список выбора параметров"""
    global filepath
    global flt
    cnt=selectedpar.rowCount()
    item=QTableWidgetItem(name)
    item.id=id
    selectedpar.setRowCount(cnt+1)
    color = hex_to_rgb(colorz[cnt])
    color = QtGui.QColor(color[0], color[1], color[2], 255)
    item.setBackground(color)
     
    selectedpar.setItem(cnt,0,item)
    sav=open(filepath+slash()+'saved.txt','r')
    savd=[]
    for line in sav:
        savd.append(int(line))
    sav.close()
    savd.append(int(id))
    print(savd)
    sav=open(filepath+slash()+'saved.txt','w')
    for line in savd: sav.write(str(line) + '\n')
    sav.close() 
    
        
class Tb(QTableWidget):
    """Таблица параметров с фильтрацией по имени и мнемонике"""
    def __init__(self,wg):
        global param_table
        global filt
        super().__init__(wg)
        self.setGeometry(10, 10, 570, 500)
        param_table.clear()
        filename=filepath+'\\'+r'paramlist.txt' #список параметров в формате csv
        cf = open(filename)
        tab=[]
        data = cf.read()
        #tab= list(csv.reader(cf, delimiter=","))
        columns='N,mnemonics,name,system,channels,length,startbit,sup,sub,koeff \n'
        lines = data.split('\n')
        for item in lines:
            rw=item.split(',')
            param_table.append(rw)
        
        
        self.resizeColumnsToContents() # ширина столцов подогнать по ширине текста
        
    def keyPressEvent(self, e):
        QTableWidget.keyPressEvent(self, e) #  в начале правильная обработка
        if e.key() == Qt.Key_Return: # отлавливаем нажатие Enter
            print("Нажата Enter")

    def mousePressEvent(self, e):
        QTableWidget.mousePressEvent(self, e) 
        global param_table
        global selectedpar
        global filtered_param_table
        if e.buttons() & QtCore.Qt.LeftButton: 
            t = self.currentItem()
            index = self.currentIndex()
            t.setrc() # изменяем цветовую гамму текущей ячейки
            param=filtered_param_table[index.row()]
            id=param[0]
            name=param[2]
            insertnewp(id,name)

def filtered_fill():
    """Реализация фильтра- пересоздание массива параметров и перерисовка таблицы"""
    global paramtb
    global filt
    global filepath
    global filtered_param_table
    
    
    filename=filepath+slash()+r'paramlist.txt'
    
    cf = open(filename)
    tab=[]
    data = cf.read()
    columns='N,mnemonics,name,system,channels,length,startbit,sup,sub,koeff \n'
    lines = data.split('\n')
    filtered_param_table.clear()
        
    for item in lines:
        if len(item)==0: continue
        rw=item.split(',');
        # если фильтр есть        
        if len(filt)>0 and len(rw)>0:
            result=rw[1].find(filt); 
            if result>-1: tab.append(item); filtered_param_table.append(rw)
            else:
                stroka=rw[2].upper();               
                if stroka.find(filt.upper())>-1:
                    tab.append(item); filtered_param_table.append(rw) 
                    
                          
        else: tab.append(item) #если фильтра нет
    if len(filt)==0: filtered_param_table=param_table.copy()        
    tab.insert(0,columns)
     
    paramtb.setRowCount(0)        
    paramtb.setColumnCount(len(tab[0].split(','))) # количество столбцов
    paramtb.setHorizontalHeaderLabels(tab[0].split(','))
                 
    for i in range(1, len(tab)): # заполнение таблицы
        if tab[i].strip() ==  '':
            continue
        paramtb.setRowCount(paramtb.rowCount() + 1) # задать количество строк
        j, p = 0, tab[i].split(',')
        for t in p:
            paramtb.setItem(i - 1, j, Tbi(t)) # задать поля в строке
            j += 1
                    
class Tbi(QTableWidgetItem):
     def __init__(self, t):
          super().__init__(t)
          self.setrc()

     def setrc(self): # задание случайных цветов элемента
          #r, g, b = getr()
          self.setBackground(QtGui.QColor(255, 255, 0, 255))
          #r, g, b = getr()
          self.setForeground(QtGui.QColor(255, 0, 0, 255))        
if __name__ == '__main__':
    if slash() in filepath!=True:
        filepath.replace(otherslash(slash()),slash())
    app = Qt.QApplication(sys.argv)
    scrn=scr(0,0)
    flt=flight(filepath)
    mw = MainWindow()
    mw.show()
    if len(saved)<0:flt.to_screen()
    ht=mw.figure.size().height()
    wdt=mw.figure.size().width()
    vizirx=int(wdt/2)
    sys.exit(app.exec_())