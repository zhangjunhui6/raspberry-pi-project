from flask import Flask,render_template,url_for
import json,pymysql,datetime,decimal
import Ds18b20
import RPi.GPIO as GPIO

#设置GPIO为BCM编码
GPIO.setmode(GPIO.BCM)
#RGB灯初始化设置
R,G,B = 18,15,14
GPIO.setup(R,GPIO.OUT)  #设置端口为输出
GPIO.setup(G,GPIO.OUT)
GPIO.setup(B,GPIO.OUT)
pwmR = GPIO.PWM(R,0.2)  #设置频率为0.2,即周期为5s
pwmG = GPIO.PWM(G,0.2)
pwmB = GPIO.PWM(B,0.2)
pwmR.start(0)   #设置占空比为0
pwmG.start(0)
pwmB.start(0)
#Buzzer蜂鸣器初始化设置
FMD = 26
GPIO.setup(FMD,GPIO.IN)  #设置为输入，不响
#MQ2烟雾传感器初始化
MQ2 = 23  
GPIO.setup(MQ2,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)  #设置上拉电阻
#火焰传感器初始化
FIRE = 24  
GPIO.setup(FIRE,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)


app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/getData', methods=['POST'])
def getData():
    # 1.获取烟雾和火焰状态，并控制蜂鸣器状态
    fire = GPIO.input(FIRE)
    mq2 = GPIO.input(MQ2)
    if fire == 0 or mq2 == 0:
        GPIO.setup(FMD, GPIO.OUT)
        GPIO.output(FMD, GPIO.LOW)
    else:
        GPIO.setup(FMD, GPIO.IN)

    # 2.读取温度，存到数据库中，然后进行RGB灯的控制
    temp_c = Ds18b20.store_temp()
    color = 0 # 按钮显示
    if temp_c > 30.0:   # 红色
        pwmR.ChangeDutyCycle(100)   # 硬件RGB
        pwmG.ChangeDutyCycle(0)
        pwmB.ChangeDutyCycle(0)
    elif temp_c >= 28.0 and temp_c <= 30.0:   # 黄色
        pwmR.ChangeDutyCycle(100)
        pwmG.ChangeDutyCycle(100)
        pwmB.ChangeDutyCycle(0)
        color = 1
    elif temp_c >= 23.0 and temp_c < 28.0:   #绿色
        pwmR.ChangeDutyCycle(0)
        pwmG.ChangeDutyCycle(100)
        pwmB.ChangeDutyCycle(0)
        color = 2
    else:  # 蓝色
        pwmR.ChangeDutyCycle(0)
        pwmG.ChangeDutyCycle(0)
        pwmB.ChangeDutyCycle(100)
        color = 3
    # 3.接着返回数据库的温度值，在浏览器中显示
    connection = pymysql.connect(host='localhost',user='root',passwd='123456',db='sensordb')
    cur = connection.cursor()
    sql = 'SELECT * FROM temp'
    cur.execute(sql)
    result = cur.fetchall()
    v1 = []
    v2 = []
    for i in result:
        v1.append(i[0])
        t = round(i[1], 2)
        v2.append(t)
    cur.close()


    j={}
    v3 = json.dumps(v1, cls=DateEncoder)
    v4 = json.dumps(v2, cls=DecimalEncoder)
    j['v1'] = v3
    j['v2'] = v4
    j['fire'] = fire
    j['mq2'] = mq2
    j['color'] = color
    j = json.dumps(j)

    return j


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self, obj)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)