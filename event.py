#Pi88_107.py からコピー
#04:SW情報表示
#05:辞書型に変更
#08:GUI充実 思うところに表示　トリガー:複数可
#09:CAN送信をストック化
#10:CAN送信を複数ストック化
#11:信号機の状態変更 Cmd(0x17)追加
#12:NotAnd追加など　正常　220308
#14:cmdのDebug表示見直し
#20:データ配列に、EventのOnOffを追加 テスト中
#21:ランプ
#22:ヤードなど追加
#23:
#24:ACS_Data 配列変更
#25:Dataファイル分けるEvent_Data01 ほぼいけるがタイミングで閉鎖区間に侵入するエラーあり
#26:M-S3ほぼ完璧
#27:
#28:バグ修正：Loopの集合Lampの判断を入れる O123−S12　M123-S3の同時　動作OK
#29:to を複数対応　Event_Data04　更新 ヤード１２OK
#30:ヤードin 追加　Event＿Data07 08:OK
#31:Stooop時可視化 EventData09　Tri大幅変更
#40:Data構造変更　Event_Data10
#41:gitの利用 git回目

#from getch import getch, pause
import readchar
import sys
import can
import PySimpleGUI as sg
import time
import random
import pickle                   #JSONでデータ(辞書型など)保存用
from marklin_can import *
from Event_Data10 import *

#print=sg.Print

can_interface = 'can0'
pi88_mode = [False,0x00]
pibo_mode = [False,0x00]
send = 0
time_mode2 = 0
#init_sw_sk = [True,False]     #[スキャン処理中、送信完了受信待ち]
init_sw_sk = [False,False]
debug_l = 0
debug_print = 0


#Pi88_UID = 0x53383BF7
Pi88_UID = bytes([0x53,0x38,0x3B,0x88])

Pi88_HASH = 0x4730
#Link88
Lk88_HASH = 0x474C

#暫定（CS3）
Pi88_ID = Pi88_UID[3]
Pi88_SW = {}

#Pibo_UID = bytes([0x42,0x6F,0x4C,0x88])
#Pibo_HASH = 0x7767
#Booster88_UID = bytes([0x42,0x6F,0x4C,0x50]) 60172
Booster_HASH = 0x733F
#Pibo_UID = bytes([0x42,0x6F,0x4C,0x50]) #60172
#Pibo_HASH = 0x733F

#暫定
CS_HASH = 0xFFFF   #init
#CS_HASH = 0xCF1F   #CS2
#CS_HASH = 0x8B68   #CS3
HASH_Data = {CS_HASH:'CS3 ',Booster_HASH:'BoSr', Pi88_HASH:'RbPi', Lk88_HASH:'Lk88'}

Can_Send_Buffer = [None]
Can_Send_Delay = 0

Disp_Size = [13,12]

bus = can.interface.Bus(can_interface, bustype='socketcan')
#sg.theme('BluePurple')
sg.theme('LightBlue1')
#sg.theme_previewer()

#S88_Sw_Disp = [21002,21003,21004,21005,21006,21007]

#for x in S88_Sw_Disp:
#    S88_Sw_Data[x] = [x//10000,x%10000,99,99]
print('S88_Sw_Data{}=',S88_Sw_Data)

layout = []

#S88_Sw_Data_list = list(S88_Sw_Data)
#print(Station_Data_list)
#print(S88_Sw_Data_list)
layout_insert = []
Disp_Location = {}

if init_sw_sk[0] == True:

    ACS_list = (list(ACS_Data.items()))

    for row in range(Disp_Size[1]):
        for col in range(Disp_Size[0]):
            color_temp = 'sky blue'
            type_temp = 'none'
            ACS_ID_temp = 0x00
            for row_ACS_Data in ACS_list:
#            print(row_ACS_Data)
                if row_ACS_Data[1]['xy'][0] == col and row_ACS_Data[1]['xy'][1] == row:
                    print(row,col,row_ACS_Data[0],row_ACS_Data[1]['Type'],row_ACS_Data[1][0x0101]['color'])
                    color_temp = 'White'
                    type_temp = row_ACS_Data[1]['Type']
                    ACS_ID_temp = row_ACS_Data[0]
                    break
            Disp_Location.setdefault(f'{col:02}{row:02}',{'ACS_ID':ACS_ID_temp,'color':color_temp, 'type':type_temp})
else:

    with open('Disp_Location.json','rb') as fp:
        Disp_Location = pickle.load(fp)
        print('Disp_Location Load')
    with open('ACS_Data.json','rb') as fp:
        ACS_data = pickle.load(fp)
        print('ACS_Data Load')

#Disp_Location['0402']= {'color':'yellow','ID':'21003'}
#print(Disp_Location)
#print(Disp_Location['0202'])
start_time = time.perf_counter() * 1000

layout = [[sg.Button(f'{col:02},{row:02}',size=(4,2) ,enable_events=True,key=f'bt{col:02}{row:02}',
        button_color=('white',Disp_Location[f'{col:02}{row:02}']['color'])) for col in range(Disp_Size[0])] for row in range(Disp_Size[1])]
#print(layout_insert)
#Disp_Location = [f'{col:02}{row:02}' for col in range(4) for row in range(10)]

#for  row_S88_Sw_Data in S88_Sw_Data:
#    print(row_S88_Sw_Data)
#    layout_insert.append(sg.Button(str(row_S88_Sw_Data)[0]+' '+str(row_S88_Sw_Data)[1:5],enable_events=True,key='bt'+str(row_S88_Sw_Data)))
#layout.append(layout_insert)

layout.append(   [sg.Text('Type(name):LinkS88('+str((Pi88_UID[2]-56)*256+Pi88_UID[3])+')  '),sg.Text('Pi88_ID: '+str(Pi88_ID),key='-ID-')])

#layout.append([sg.Checkbox('Can Read Log',enable_events=True,key='can_read',default=True),sg.Checkbox('Can Write Log',enable_events=True,key='can_write')])
layout.append([sg.Button('LOAD',size=(10,1),button_color=("white", "blue")),
               sg.Button('SAVE',size=(10,1),button_color=("white", "blue")),
               sg.Button('RESET',size=(10,1),button_color=("white", "blue")),
               sg.Button('SCAN',size=(10,1),button_color=("white", "blue"))])
layout.append([sg.Button('TEST 00',size=(10,1),button_color=("white", "blue")),sg.Button('TEST 01',size=(10,1),button_color=("white", "blue"))])
#print(layout)
#exit()
# ウィンサイズはsizeに(縦の大きさ,横の大きさ)で記載
window = sg.Window(title='Pi88 Status',font='Courier 12', size=(1200, 900),button_color=("white", "red")).Layout(layout)
#window = sg.Window(title='Pi88 Status',layout,font='Courier 12', size=(700, 400))
#window=sg.Window("Gui",layout,location=(20,20))
#window.Layout(layout).Finalize()
def reset_data():
    Disp_Location = {}
#Disp_Location.setdefault(str((f'{col:02}'),1) for col in range(4))
#print((f'{col:02}{row:02}',f'{col}') for col in range(4) for row in range(10))
#ACS_list = (list(ACS_Data.values()))
    ACS_list = (list(ACS_Data.items()))

    for row in range(Disp_Size[1]):
        for col in range(Disp_Size[0]):
            color_temp = 'sky blue'
            type_temp = 'none'
            ACS_ID_temp = 0x00
            for row_ACS_Data in ACS_list:
#            print(row_ACS_Data)
                if row_ACS_Data[1]['xy'][0] == col and row_ACS_Data[1]['xy'][1] == row:
                    print(row,col,row_ACS_Data[0],row_ACS_Data[1]['Type'],row_ACS_Data[1][0x0101]['color'])
                    color_temp = 'white'
                    type_temp = row_ACS_Data[1]['Type']
                    ACS_ID_temp = row_ACS_Data[0]
                    break
            Disp_Location.setdefault(f'{col:02}{row:02}',{'ACS_ID':ACS_ID_temp,'color':color_temp, 'Type':type_temp})

def save_data():
    with open('Disp_Location.json','wb') as fp:
        pickle.dump(Disp_Location, fp)
        print('Disp_Location SAVE')
    with open('ACS_Data.json','wb') as fp:
        pickle.dump(ACS_Data, fp)
        print('ACS_Data SAVE')


def analysis_can_data(CanID,Hash,Dlc,Data):
    Cmd = CanID // 2
    
    rw = CanID % 2
    r = 0
    Info_Message = '{:02x}:'.format(Cmd)
#    print(hex(Cmd),hex(CanID),rw,end='')

    if CanID == 0x80:
        Info_Message += 'CMD=0x80 Mfx New?Res? -> '
        r = 0x80
    else:
        if debug_print > 1:
            try:
#                print(cmd_list[CanID],end=':')
                Info_Message += '{}'.format(cmd_list[CanID]) 
            except:
                Info_Message = Info_Message + 'Err CanID:'+hex(CanID)

        if Cmd == 0x00:
          if Dlc > 4:
            sub_cmd = Data[4]
            try:
                print(sub_cmd_list[sub_cmd])
                if sub_cmd == 0x0C and rw == 1 and Pi88_UID == Data[0:4]:
                    Info_Message += 'Get pi88_ID='
                    r = 0xFF0C

                elif sub_cmd == 0x0B:
                    Info_Message += 'System Status'
                    r = 0xFF0B
                elif sub_cmd == 0x03:
                    Info_Message += 'Lok Emagency Stop: {}'.format(hex(Data[2]*0x100+Data[3]))
                    r = 0xFF03

            except:
                if sub_cmd == 0x80:
                    Info_Message += 'System Reset'
                elif sub_cmd == 0x30:
                    if Data[5] == 0x00:
                        if debug_print > 1:
                            Info_Message += 'MfxSeek End'
                        r = 0x0300
                    elif Data[5] == 0x01:
                        if debug_print > 1:
                            Info_Message += 'MfxSeek Start'
                        r = 0x0301
                    elif Data[5] == 0x02:
                        Info_Message += 'MfxSeek 0x02'
                        r = 0x0302
                else:
                    print('Unknown SubCmd:',hex(sub_cmd))
    #    elif Cmd == '0x00':
    #    elif Cmd == '0x00':
        elif CanID == 0x03 and Dlc == 5:
            Info_Message += 'Mfx UID Verify Completed'
            r = 0x03
        elif CanID == 0x04:
            Info_Message += 'Mfx BIND'
            r = 0x04
        elif CanID == 0x06:
            Info_Message += 'Mfx Verify'
            r = 0x06
        elif CanID == 0x0E:
            Info_Message += 'Read Cfg'
            r = 0x0E
        elif CanID == 0x0F:
            Info_Message += 'Data Chk'
            r = 0x0F
        elif CanID == 0x30 and Dlc == 0:
            if debug_print > 1:
                Info_Message += 'Ping Request all'
            r = 0x30
        elif CanID == 0x31:
            if debug_print > 1:
                Info_Message += 'Ping Repr.'
    #    elif Cmd == '0x00':
    #    elif Cmd == '0x00':
        elif CanID == 0x36 and Dlc == 0:
            if debug_print > 1:
                Info_Message += 'Bootloader Request!!'
            r = 0x36

        elif CanID == 0x3A and Dlc == 5:
            Info_Message += 'Status Request'
            r = 0x3A

#        elif CanID == 0x22 and get_hash == CS_HASH:
        elif CanID == 0x22:
            Info_Message += 'S88 Event -> '
            r = 0x22
        elif CanID == 0x23:
            #print(' :',hex(Hash),'Bus:',Data[0],Data[1],' No',Data[2]*0x100 + Data[3],hex(Data[2]),hex(Data[3]),':',Data[4],'->', Data[5], Data[6]*0x100+ Data[7])
            Info_Message += 'S88 Change(0x23):{} Bus {:02} {:02} No{}({:04x}) {}->{}'.format(hex(Hash),Data[0],Data[1],Data[2]*0x100 + Data[3],Data[2]*0x100+Data[3],Data[4],Data[5])
            r = 0x23
        elif CanID == 0x16:
            Info_Message += 'Switch 0x16:'
            r = 0x16
        elif CanID == 0x17:
            Info_Message += 'Switch 0x17:'
            r = 0x17

        else:
            if debug_print > 1:
                print('Unknow!!!')

    print('Info_Message:',Info_Message)

    return r

while True:
    #*********************************************************************    
    #    GUI の処理
    
    event, values = window.read(timeout=50,timeout_key='-guitimeout-')
#    print(event,values)
    if event in (None,):
        break
    elif event in '-guitimeout-':
#        update_text = 'Pi88_ID:'+str(Pi88_ID)
        update_text = 'Pi88_ID: '+str(Pi88_ID)
        window['-ID-'].update(update_text)
#        update_text = str(pi88_mode[1])
#        window['-pi88_mode-'].update(update_text)
#        update_text = str(pibo_mode[1])
#        window['-pibo_mode-'].update(update_text)

        if debug_l >= 10:
            print('*',end='')
    elif event == '実行ボタン':
        update_text = "Button clicked."
        # 表示内容を更新する際はウィジェットに指定されたkeyの値に.update("文字列")を入れることで可能
        window['-TEXT-'].update(update_text)
#    elif event[0:2] == 'sw':
#        print(event,values[event])

    elif event[0:2] == 'bt':
#        print(event[2:6],event[2:6] in Disp_Location)
        sw_color = ['gray','gray']
        if Disp_Location[event[2:6]]['Type'] == 'Lamp3':
            if Disp_Location[event[2:6]]['color'] == 'white':
                sw_color = ['gray','red']
            elif Disp_Location[event[2:6]]['color'] == 'red':
                sw_color = ['gray','green']
            elif Disp_Location[event[2:6]]['color'] == 'green':
                sw_color = ['gray','yellow']
            elif Disp_Location[event[2:6]]['color'] == 'yellow':
                sw_color = ['gray','white']
        elif  Disp_Location[event[2:6]]['Type'] == 'LampBlue':
            ACS_ID_Temp = Disp_Location[event[2:6]]['ACS_ID']
            if Disp_Location[event[2:6]]['color'] != 'blue':
                sw_color = ['gray','blue']
                Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,(ACS_ID_Temp & 0xFF000000) // 0x1000000,(ACS_ID_Temp & 0xFF0000) //0x10000,0x01,0x01]}])
                Disp_Location[event[2:6]]['color'] = 'blue'
            else:
                sw_color = ['gray','gray']
                Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,(ACS_ID_Temp & 0xFF000000) // 0x1000000,(ACS_ID_Temp & 0xFF0000) //0x10000,0x00,0x01]}])
                Disp_Location[event[2:6]]['color'] = 'gray'
        elif  Disp_Location[event[2:6]]['Type'] == 'SW1':
            ACS_ID_Temp = Disp_Location[event[2:6]]['ACS_ID']
            if Disp_Location[event[2:6]]['color'] != 'green':
                sw_color = ['gray','green']
                Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,(ACS_ID_Temp & 0xFF000000) // 0x1000000,(ACS_ID_Temp & 0xFF0000) //0x10000,0x01,0x01]}])
                Disp_Location[event[2:6]]['color'] = 'green'
            else:
                sw_color = ['gray','gray']
                Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,(ACS_ID_Temp & 0xFF000000) // 0x1000000,(ACS_ID_Temp & 0xFF0000) //0x10000,0x00,0x01]}])
                Disp_Location[event[2:6]]['color'] = 'gray'
                                
            print((Disp_Location[event[2:6]]['ACS_ID'] & 0xFF0000) // 0x10000,(Disp_Location[event[2:6]]['ACS_ID'] & 0xFF00) // 0x100)

        print(event[2:6],hex(Disp_Location[event[2:6]]['ACS_ID']),Disp_Location[event[2:6]])
        window.FindElement(event).Update(button_color=(sw_color))

    elif event == 'Go':
        msg = can.Message(arbitration_id=0x00000000+Pi88_HASH, dlc=5, data=[0x00,0x00,0x00,0x00,0x01], is_extended_id=True)
        send = 1
        print('Go')
    elif event == 'Stop':
        msg = can.Message(arbitration_id=0x00000000+Pi88_HASH, dlc=5, data=[0x00,0x00,0x00,0x00,0x00], is_extended_id=True)
        send = 1
        print('Stop')

    elif event == '-SEND-':
        msg = can.Message(arbitration_id=0x00310000+Pi88_HASH, dlc=4, data=bytes([int(values['-IN00-']),int(values['-IN01-']),int(values['-IN02-']),int(values['-IN03-']),int(values['-IN04-']),int(values['-IN05-']),int(values['-IN06-']),int(values['-IN07-'])]), is_extended_id=True)
        message_data_print(values['can_read'],(msg.arbitration_id >> 16) & 0x00FF,msg.arbitration_id & 0xFFFF,msg.data)
        bus.send(msg)
    elif event == 'SAVE':
        save_data()
    elif event == 'TEST 00':
#        msg = can.Message(arbitration_id=0x0016_0000+Pi88_HASH, dlc=6, data=[0x00,0x00,S88_Sw_Data[sw_id]['Tri']['Lamp3']//0x100,S88_Sw_Data[sw_id]['Tri']['Lamp3']%0x100,0x01,0x01], is_extended_id=True)
        msg = can.Message(arbitration_id=0x0016_0000+Pi88_HASH, dlc=6, data=[0x00,0x00,0x30,0x00,0x00,0x01], is_extended_id=True)
        bus.send(msg)
#        msg = can.Message(arbitration_id=0x0016_0000+Pi88_HASH, dlc=6, data=[0x00,0x00,S88_Sw_Data[sw_id]['Tri']['Lamp3']//0x100,S88_Sw_Data[sw_id]['Tri']['Lamp3']%0x100,0x01,0x00], is_extended_id=True)
#        bus.send(msg)
    elif event == 'TEST 01':
#        msg = can.Message(arbitration_id=0x0016_0000+Pi88_HASH, dlc=6, data=[0x00,0x00,S88_Sw_Data[sw_id]['Tri']['Lamp3']//0x100,S88_Sw_Data[sw_id]['Tri']['Lamp3']%0x100,0x01,0x01], is_extended_id=True)
        msg = can.Message(arbitration_id=0x0016_0000+Pi88_HASH, dlc=6, data=[0x00,0x00,0x30,0x00,0x01,0x01], is_extended_id=True)
        bus.send(msg)
    elif event == 'SCAN':
        #アクセサリ更新
        for row_id in ACS_Data.keys():
            xy_temp = ACS_Data[row_id]['xy']
            print(hex(row_id),xy_temp,Disp_Location['{:02}{:02}'.format(xy_temp[0],xy_temp[1])],ACS_Data[row_id]['Type'])
            Disp_Location['{:02}{:02}'.format(xy_temp[0],xy_temp[1])] = {'ACS_ID': row_id,'color':'gray','Type':ACS_Data[row_id]['Type']}
            print(' New:',Disp_Location['{:02}{:02}'.format(xy_temp[0],xy_temp[1])])

#        sorted_S88_Sw_Data = sorted(S88_Sw_Data.items())
#        print(sorted_S88_Sw_Data)
        for S88_id_temp in S88_Sw_Data.keys():
            #print(row_S88_Data[1]['Befor'])
            S88_Sw_Data[S88_id_temp]['After'] == 99
            print(S88_Sw_Data[S88_id_temp])
        
        init_sw_sk = [True,False]
#
    else:
        print('Error Bottun!!!!',event,values)

    #*********************************************************************    
    #    CanBus の処理
    message = bus.recv(0.1)
    if not message is None:
        get_cmd = (message.arbitration_id >> 16) & 0x00FF
        get_hash = message.arbitration_id & 0xFFFF
        get_dlc = message.dlc
        get_data = message.data
        if debug_print > 1 :
            message_data_print(values['can_read'],get_cmd,get_hash,get_data)  #Read Can Data
        ana_cmd = analysis_can_data(get_cmd,get_hash,get_dlc,get_data)
        #S88 Change *********************************************************
        if  ana_cmd == 0x23:
            sw_id =  get_data[0]*1000000 +get_data[1]*10000 +get_data[2]*0x100 +get_data[3]
            print(' cmd=0x23:',get_dlc,sw_id,end=' ')
            if sw_id in S88_Sw_Data.keys():
#                print('Resp!!!!')
                S88_Sw_Data[sw_id]['Befor'] = get_data[4]
                S88_Sw_Data[sw_id]['After'] = get_data[5]
#                    row_Station_Data[1][3:5] = [get_data[4],get_data[5]]
                print('S88_Data->',S88_Sw_Data[sw_id],S88_Sw_Data[sw_id])
                print('XY:',S88_Sw_Data[sw_id]['xy'])
                if S88_Sw_Data[sw_id]['xy'] != [99,99]:
                    print('XY 9999:',S88_Sw_Data[sw_id]['xy'])
                    if get_data[5] == 1:
                        sw_color = ['gray','yellow']
#                    print('St_Data:ON',S88_Sw_Data[sw_id])
                    else:
                        sw_color = ['gray','white']
                
                    window.FindElement('bt{:02}{:02}'.format(S88_Sw_Data[sw_id]['xy'][0],S88_Sw_Data[sw_id]['xy'][1])).Update(button_color=(sw_color))
#                print(S88_Sw_Data[sw_id]['Tri'])
#####                Temp_Disp_Location = list(Disp_Location.values())
#####            print('Temp_Disp_Location:',Temp_Disp_Location)

                #閉鎖区間に電車突っ込んだ　停止せDisp_Locationよ
                if 'in' in S88_Sw_Data[sw_id]['Tri'] and S88_Sw_Data[sw_id]['After'] == 1:
                    print('Event Triger:',S88_Sw_Data[sw_id]['Tri'],end='')               
                    print(' ',S88_Sw_Data[S88_Sw_Data[sw_id]['Tri']['in']]['After'])
                    if S88_Sw_Data[S88_Sw_Data[sw_id]['Tri']['in']]['After'] != 0:
                        msg = can.Message(arbitration_id=0x0000_0000+Pi88_HASH, dlc=5, data=[0x00,0x00,0x00,0x00,0x00], is_extended_id=True)
                        bus.send(msg)
                        print('Stoooop!!!!')
                        sw_color = ['black','black']
                        window.FindElement('bt{:02}{:02}'.format(S88_Sw_Data[sw_id]['xy'][0],S88_Sw_Data[sw_id]['xy'][1])).Update(button_color=(sw_color))

                #閉鎖区間 出たら　信号を赤に
                if 'Exit' in S88_Sw_Data[sw_id]['Tri'].keys() and S88_Sw_Data[sw_id]['After'] == 0:
                    if S88_Sw_Data[sw_id]['Tri']['Exit'] != None:
                        Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,S88_Sw_Data[sw_id]['Tri']['Exit']//0x100,S88_Sw_Data[sw_id]['Tri']['Exit']%0x100,0x00,0x01]}])
                
                #Lamp処理
                if 'Lamp3' in S88_Sw_Data[sw_id]['Tri'].keys():
                    if S88_Sw_Data[sw_id]['After'] == 1:
                        print('Lamp3 Triger:{:04x}'.format(S88_Sw_Data[sw_id]['Tri']['Lamp3']))
                        Can_Send_Buffer.append([Can_Send_Delay ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,S88_Sw_Data[sw_id]['Tri']['Lamp3']//0x100,S88_Sw_Data[sw_id]['Tri']['Lamp3']%0x100,0x01,0x01]}])
                    else:
                        print('Lamp3 Triger:{:04x}'.format(S88_Sw_Data[sw_id]['Tri']['Lamp3']))
                        Can_Send_Buffer.append([Can_Send_Delay ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,S88_Sw_Data[sw_id]['Tri']['Lamp3']//0x100,S88_Sw_Data[sw_id]['Tri']['Lamp3']%0x100,0x00,0x01]}])

                if init_sw_sk == [True,True]:
                    init_sw_sk[1] = False
        
#            if sw_id in Disp_Location.keys():
#                print(Disp_Location[sw_id])
                print([x] for x in Disp_Location)

        elif  ana_cmd == 0x16:
#            print('ID:',hex(get_hash),'Bus:',get_data[0]*0x1000000+get_data[1]*0x10000+get_data[2]*0x100+get_data[3],'No4',get_data[4],'No5',get_data[5],':',get_data[6],'7', get_data[7])
#            print('HASH:',hex(get_hash),'ID:',get_data[0]*0x1000000+get_data[1]*0x10000+get_data[2]*0x100+get_data[3],'',get_data[4],'',get_data[5])
            print('HASH:{:04x} ID:{:02x}{:02x}-{:02x}{:02x}-{:02x} {:02x}'.format(get_hash,get_data[0],get_data[1],get_data[2],get_data[3],get_data[4],get_data[5]))

#                print(S88_Sw_Data[sw_id]['Tri'])
#                Temp_Disp_Location = list(Disp_Location.values())
#                print('Temp_Disp_Location:',Temp_Disp_Location)

        if  ana_cmd == 0x17 and get_data[5] == 1:
#            print('ID:',hex(get_hash),'Bus:',get_data[0]*0x1000000+get_data[1]*0x10000+get_data[2]*0x100+get_data[3],'No4',get_data[4],'No5',get_data[5],':',get_data[6],'7', get_data[7])
            ACS_id = get_data[2] * 0x100 + get_data[3]
            print(' ACS_id:{:04x} HASH:{:04x} ID:{:02x}{:02x}-{:02x}{:02x}-{:02x} {:02x}'.format(ACS_id,get_hash,get_data[0],get_data[1],get_data[2],get_data[3],get_data[4],get_data[5]))
#            print('HASH:',hex(get_hash),'ID:',get_data[0]*0x1000000+get_data[1]*0x10000+get_data[2]*0x100+get_data[3],'',get_data[4],'',get_data[5])
            if ACS_id in ACS_Data.keys():
#                ASS_Data_row = ASS_Data[ASS_id]['Tri']
#                print(ACS_Data[ACS_id]['Tri'])
                if 'Tri' in ACS_Data[ACS_id][get_data[4]*0x100+get_data[5]]:
                    Send_Delay = ACS_Data[ACS_id][get_data[4]*0x100+get_data[5]]['Tri'][0]
                    print('ACS_Data:',ACS_Data[ACS_id][get_data[4]*0x100+get_data[5]]['Tri'][1:],'  Send_Delay:',ACS_Data[ACS_id][get_data[4]*0x100+get_data[5]]['Tri'][0])
                    for ACS_Data_row in ACS_Data[ACS_id][get_data[4]*0x100+get_data[5]]['Tri'][1:]:
                        Can_Send_Buffer.append([Can_Send_Delay + Send_Delay[0] ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':ACS_Data_row}])
                    start_time = time.perf_counter() * 1000
            #ACS_Data 更新
                if    ACS_Data[ACS_id]['Type'] == 'Lamp2':
#                    ACS_Data[ACS_id  ]['Befor'] = get_data[4] + 0x10
                    ACS_Data[ACS_id  ]['After'] = get_data[4] + 0x10
#                    ACS_Data[ACS_id-1]['Befor'] = get_data[4] + 0x10
                    ACS_Data[ACS_id-1]['After'] = get_data[4] + 0x10
                elif  ACS_Data[ACS_id]['Type'] == 'Lamp3':
#                    ACS_Data[ACS_id  ]['Befor'] = get_data[4]
                    ACS_Data[ACS_id  ]['After'] = get_data[4]
#                    ACS_Data[ACS_id+1]['Befor'] = get_data[4]
                    ACS_Data[ACS_id+1]['After'] = get_data[4]
                else:
#                    ACS_Data[ACS_id]['Befor'] = get_data[4]
                    ACS_Data[ACS_id]['After'] = get_data[4]
#                    row_Station_Data[1][3:5] = [get_data[4],get_data[5]]
            #画面更新処理
                print(' ACS_Data->',ACS_Data[ACS_id],end='')
                print(' XY:',ACS_Data[ACS_id]['xy'])
#                if ACS_Data[ACS_id]['xy'][0:2] != [99,99]:
                try:
                    color_temp = ACS_Data[ACS_id][get_data[4]*0x100+get_data[5]]['color']
                    Disp_Location['{:02}{:02}'.format(ACS_Data[ACS_id]['xy'][0],ACS_Data[ACS_id]['xy'][1])]['color'] = color_temp
                    print('color:',color_temp)
                    sw_color = ['gray',color_temp]
                    print(' Disp_Location:',Disp_Location['{:02}{:02}'.format(ACS_Data[ACS_id]['xy'][0],ACS_Data[ACS_id]['xy'][1])])

                    window.FindElement('bt{:02}{:02}'.format(ACS_Data[ACS_id]['xy'][0],ACS_Data[ACS_id]['xy'][1])).Update(button_color=(sw_color))
                except:
                    print('Not include [Disp?] or [xy]!!!!')

                #集合Lamp処理　一つでも黄→黄／一つでも白→白／その他の赤、緑→赤
                if 'And' in ACS_Data[ACS_id]:
#                    print(ACS_Data[ACS_id]['AndLamp'])
                    AndLamp_id = ACS_Data[ACS_id]['AndLamp']
                    sw_color = ['gray','red']
                    for And_id in ACS_Data[ACS_id]['And']:
#                        print(ACS_Data[And_id])
                        color_temp = Disp_Location['{:02}{:02}'.format(ACS_Data[And_id]['xy'][0],ACS_Data[And_id]['xy'][1])]['color']
                        print(color_temp)
                        if color_temp == 'yellow':
                            sw_color = ['gray','yellow']
                            Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,AndLamp_id//0x100,AndLamp_id%0x100+1,0x01,0x01]}])
                            break
                    else:                        
                        for And_id in ACS_Data[ACS_id]['And']:
                            color_temp = Disp_Location['{:02}{:02}'.format(ACS_Data[And_id]['xy'][0],ACS_Data[And_id]['xy'][1])]['color']
                            print(color_temp)
                            if color_temp == 'white':
                                sw_color = ['gray','white']
                                Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,AndLamp_id//0x100,AndLamp_id%0x100,0x00,0x01]}])
                                break
                        else:
                            print('All Red!!!!!!')
                            Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,AndLamp_id//0x100,AndLamp_id%0x100,0x01,0x01]}])
                    Disp_Location['{:02}{:02}'.format(ACS_Data[And_id]['xy'][0],ACS_Data[And_id]['xy'][1])]['color'] = sw_color[1]

    ################################################
    # 送信データが 無いとき
    if send == 0:
        if init_sw_sk == [True,False]:
            sorted_S88_Sw_Data = sorted(S88_Sw_Data.items())
            print(sorted_S88_Sw_Data)
            for row_S88_Data in sorted_S88_Sw_Data:
                #print(row_S88_Data[1]['Befor'])
                if row_S88_Data[1]['After'] == 99 and row_S88_Data[0] > 10000:
                    print(row_S88_Data[1])
                    msg = can.Message(arbitration_id=0x0022_0000+Pi88_HASH, dlc=4, data=[row_S88_Data[1]['Bus']//100,row_S88_Data[1]['Bus']%100,row_S88_Data[1]['No'] // 0x100,row_S88_Data[1]['No'] % 0x100])
                    bus.send(msg)
                    print('init_sw_scan',row_S88_Data[0])
                    init_sw_sk = [True,True]
                    break
            if init_sw_sk == [True,False]:
                init_sw_sk[0] = False
        else:
#        代表Lamp　SW

#Yout-S3
#        0x30a7: [{'Sw_id':0x30EA, 'Wait':0,'From':[0x30CF],'To':[0x3099]},
#M123-S3
#                 {'Sw_id':0x30E6, 'Wait':0,'From':[0x309F,0x30A1,0x30A3],'To':[0x3099], 'Tri':[[300],[0x00,0x00,0x30,0x0b,0x01,0x01]]},
#M123-G1
#                 {'Sw_id':0x30EB, 'Wait':0,'From':[0x309F,0x30A1,0x30A3],'To':[0x30C7]}],
            loop_message = ''
            for daihyou_lamp in Loop_Data.keys():
                #入線可SW
#                print('代表Lamp:',hex(daihyou_lamp),' Loop_Data:',Loop_Data[daihyou_lamp],' to:',Loop_Data[daihyou_lamp].keys())
#                print('代表Lamp:',hex(daihyou_lamp),' To:',Loop_Data[daihyou_lamp].keys())
                loop_message += '代表Lamp:{} {} '.format(hex(daihyou_lamp),ACS_Data[daihyou_lamp]['After'])
                if ACS_Data[daihyou_lamp]['After'] == 0x0:
                #代表Lamp＝白−＞侵入可               
                    from_lamp_list = []
#                    print('Loop_Data[daihyou_lamp]=',Loop_Data[daihyou_lamp])
                    for row_from_data_dic in Loop_Data[daihyou_lamp]:
                        loop_message += '{}'.format(row_from_data_dic)
                        if ACS_Data[row_from_data_dic['Sw_id']]['After'] == 0x1:
                            print('From:',ACS_Data[row_from_data_dic['From']]['After'],' To:',ACS_Data[row_from_data_dic['To']]['After'])
                            if  ACS_Data[row_from_data_dic['From']]['After'] == 0x1 and ACS_Data[row_from_data_dic['To']]['After'] == 0x0:
                                print(' From id:',hex(row_from_data_dic['From']),'=',ACS_Data[row_from_data_dic['From']]['After'],end='')
                                print(' To id:',hex(row_from_data_dic['To']),'=',ACS_Data[row_from_data_dic['To']]['After'],end='')
#                                from_lamp_list.append([row_from_data_dic['From'], row_from_data_dic])
                                from_lamp_list.append(row_from_data_dic)
                    print('from_lamp_list=',from_lamp_list)
#                    if len(from_lamp_list)<0:
#                        sys.exit()
#
                    if len(from_lamp_list) > 0:
                        try:
#                            ch_to_temp = Loop_Data[row_loop]['To'][random.randint(0, len(Loop_Data[row_loop])+1)]
                            select_root = from_lamp_list[random.randint(0, len(from_lamp_list))]
                        except:
                            select_root = from_lamp_list[0]
                        
                        print('Select_root From=',hex(select_root['From']),'  To=',hex(select_root['To']))    
                        wait_temp = time.perf_counter() - Loop_Data[daihyou_lamp][select_root['Row']]['Wait']

#                        sys.exit()

                        if wait_temp > 50:
                            for row_wait in Loop_Data[daihyou_lamp]:
                            #Loop_Data[daihyou_lamp][select_root['Row']]['Wait'] = time.perf_counter()
                                row_wait['Wait'] = time.perf_counter()
                            #出発元'From'を緑（青）に
                            Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,select_root['From']//0x100,select_root['From']%0x100+1,0x00,0x01]}])
                            #行き先'To'を黄色に
                            Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':[0x00,0x00,select_root['To']//0x100,select_root['To']%0x100+1,0x01,0x01]}])
                            #ルート設定
                            for tri_list in select_root['Tri'][1:]:
                                Can_Send_Buffer.append([300 ,{'id':0x0016_0000, 'HASH':Pi88_HASH, 'dlc':6, 'data':tri_list}])  

                            print(loop_message)
                            break
                        
                        else:
                            print('Event Loop Waiting:',wait_temp,end='')

        if Can_Send_Buffer[-1] != None:
            print('Can Send Buffer:',Can_Send_Buffer[-1][0],'ID:',hex(Can_Send_Buffer[-1][1]['id']),Can_Send_Buffer[-1][1]['data'])
            if Can_Send_Buffer[-1][0] <= 0:
                msg = can.Message(arbitration_id=Can_Send_Buffer[-1][1]['id']+Pi88_HASH, dlc=Can_Send_Buffer[-1][1]['dlc'], data=Can_Send_Buffer[-1][1]['data'], is_extended_id=True)
#OK                msg = can.Message(arbitration_id=0x0016_0000+Pi88_HASH, dlc=6, data=[0x00,0x00,0x30,0x00,0x01,0x01], is_extended_id=True)
#                print(Can_Send_Buffer[-1][1]['dlc'])
#                msg = can.Message(arbitration_id=Can_Send_Buffer[-1][1]['id']+Pi88_HASH, dlc=Can_Send_Buffer[-1][1]['dlc'], data=[0x00,0x00,0x30,0x00,0x01,0x01], is_extended_id=True)
                Can_Send_Buffer.pop()
                send = 1
            else:
                end_time = time.perf_counter()*1000 - start_time
                start_time = time.perf_counter()*1000
                Can_Send_Buffer[-1][0] -= end_time
                print(end_time)
                
    elif send == 1:
#        print(msg)
        bus.send(msg)
        send = 0

window.close()


def can_message(message):
    print(message.arbitration,message.data)

#Stop
#        msg = can.Message(arbitration_id=0x0000CF1F, data=[0,0,0,0,0], is_extended_id=True)
#        bus.send(msg)
#        send = 0
