import time,glob
import pymysql

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


def read_row():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines


def read_temp():
	lines = read_row()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_row()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string)/1000.0  # 摄氏度
		#temp_f = temp_c*9.0/5.0 + 32.0		# 华氏度
	return temp_c


def store_temp():
	db = pymysql.connect("localhost", "root", "123456", "sensordb" )
	cursor = db.cursor()
	temp_c = read_temp()
	sql = "INSERT INTO temp(T) VALUES(%2.3f)" %\
			(temp_c)
	try:
		cursor.execute(sql)
		db.commit()
	except:
		db.rollback()
		print("失败")
	db.close()
	return temp_c


if __name__ == '__main__':
	store_temp()