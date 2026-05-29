_D='enable'
_C=None
_B=False
_A=True
import pcf8563,timezone,datetime
from machine import I2C,UART,Pin,PWM,ADC,reset
from config import*
from user_config import*
import time,_thread,io,sys,json,os,deflate,io,hashlib,binascii
from ina219 import INA219
MAX_U16=65535
sw_ignore='ignore'
sw_open='open'
sw_closed='closed'
sw_and='and'
sw_or='or'
i2c=I2C(id=0,scl=Pin(PIN_SCL),sda=Pin(PIN_SDA))
class Spool:
	def __init__(self,i2c=i2c,rpi_uart=_C):self.h_in1=PWM(Pin(PIN_H_IN_1),freq=20000);self.h_in1.duty_u16(0);self.h_in2=PWM(Pin(PIN_H_IN_2),freq=20000);self.h_in2.duty_u16(0);self.direction='stop';self.clock=Clock(i2c);self.rpi_uart=rpi_uart;self.spool_reset_pin=Pin(PIN_SPOOL_RESET,Pin.IN,Pin.PULL_UP);self.en_photo_interrupter=Pin(PIN_EN_PHOTO_INTERRUPTER,Pin.OUT);self.en_photo_interrupter.on();self.photo_interrupter_home=Pin(PIN_PHOTO_INTERRUPTER_HOME,Pin.IN);self.photo_interrupter_reset=Pin(PIN_PHOTO_INTERRUPTER_RESET,Pin.IN);self.electromagnet_en_pin=Pin(PIN_ELECTROMAGNET_RELEASE,Pin.OUT);self.electromagnet_en_pin.off();self.home_to_reset_duration=HOME_TO_RESET_DURATION;self.ina219=INA219(SHUNT_OHMS,i2c);self.ina219.configure(gain=INA219.GAIN_8_320MV);self.buzzer=Buzzer()
	def stop(self):self.h_in1.duty_u16(MAX_U16);self.h_in2.duty_u16(MAX_U16);self.speed=0;self.direction='stop'
	def enable_check(self):
		if self.at_home():return _A,''
		else:return _B,'spool not home'
	def _drive_cw(self,speed=100):
		if self.at_reset():self.stop();return
		if self.direction=='cw'and self.speed==speed:return
		self.h_in1.duty_u16(int(speed*MAX_U16/100));self.h_in2.duty_u16(0);self.speed=speed;self.direction='cw'
	def _drive_ccw(self,speed=100):
		A='ccw'
		if self.at_home():self.stop();return
		if self.direction==A and self.speed==speed:return
		self.h_in2.duty_u16(int(speed*MAX_U16/100));self.h_in1.duty_u16(0);self.speed=speed;self.direction=A
	def at_home(self):return self.photo_interrupter_home.value()==1
	def at_reset(self):return self.photo_interrupter_reset.value()==1
	def spool_is_reset(self):return self.spool_reset_pin.value()==0
	def reset_sequence(self,steps=4):
		print('======== Running reset sequence ========');self.stop();time.sleep(.5);self.move_to_home();time.sleep(.5)
		if SPOOL_REED_CHECK and self.spool_is_reset():print('Spool already reset');return
		step_size=self.home_to_reset_duration/steps;steps=steps-1
		for i in range(steps):sleep_duration=step_size*(i+1);self.move_to_reset(timeout=sleep_duration,timeout_error=_B);time.sleep(.5);self.move_to_home();time.sleep(.5)
		start_time=time.time();self.move_to_reset(timeout=self.home_to_reset_duration+5,timeout_error=_A);self.home_to_reset_duration=time.time()-start_time;print('Time to reset spool: ',self.home_to_reset_duration);time.sleep(.5);print('Moving to home, checking the spool stays reset.');self._drive_ccw();self._wait_to_stop_spool(self.at_home,self.home_to_reset_duration+5,_A,reed_check=SPOOL_REED_CHECK)
		if self.rpi_uart is not _C:self.rpi_uart.send_message(Message(0,'SPOOL_RESET'))
		print('Finished reset sequence =================')
	def move_to_reset(self,timeout=15,timeout_error=_A):
		print('Moving to reset')
		if self.at_reset():print('Already at reset');return _A
		self._drive_cw();return self._wait_to_stop_spool(self.at_reset,timeout,timeout_error)
	def move_to_home(self,timeout=15,timeout_error=_A):
		print('Moving to home')
		if self.at_home():print('Already at home');return _A
		self._drive_ccw();return self._wait_to_stop_spool(self.at_home,timeout,timeout_error)
	def release(self):
		if not self.at_home():return _B
		self.electromagnet_en_pin.on();time.sleep(.5);self.electromagnet_en_pin.off()
		if self.rpi_uart is not _C:self.rpi_uart.send_message(Message(0,'TRIGGERED'))
		if SPOOL_REED_CHECK and self.spool_is_reset():error_code(ERROR_SPOOL_NOT_RELEASING)
		return _A
	def _wait_to_stop_spool(self,checker_function,timeout,error_on_timeout,reed_check=_B):
		start_time=time.time();self.ina219.wake();avg=RingAvg(30);max_avg_current=0;max_current=0
		while _A:
			if checker_function():self.stop();print('Finished move. Reason: Got to target');self.ina219.sleep();print('Max current ',max_current);print('Max average current ',max_avg_current);return _A
			if time.time()-start_time>timeout:
				self.stop();print('Finished move. Reason: Timed out')
				if error_on_timeout:error_code(ERROR_MOVEMENT_TIMEOUT)
				self.ina219.sleep();return _B
			if reed_check:
				if not self.spool_is_reset():print("Spool didn't reset properly.");self.stop();error_code(ERROR_FAILED_TO_RESET);self.ina219.sleep();return _B
			try:
				current=self.ina219.current()
				if current>max_current:max_current=current
				avg.add(abs(current));avg_current=avg.avg()
				if avg_current>max_avg_current:max_avg_current=avg_current
			except Exception as e:print('ina error',e)
			if avg.avg()>MAX_CURRENT:self.stop();print('Finished move. Reason: Over current');error_code(ERROR_OVER_CURRENT);self.ina219.sleep();return _B
class Switches:
	def __init__(self):
		self.sw1=Pin(PIN_SW_1,Pin.IN,Pin.PULL_UP);self.sw2=Pin(PIN_SW_2,Pin.IN,Pin.PULL_UP);self.sw1_disable_when=SWITCH1_DISABLE.lower();self.sw2_disable_when=SWITCH2_DISABLE.lower();self.sw_logic=SWITCH_LOGIC.lower()
		if self.sw1_disable_when not in[sw_closed,sw_open,sw_ignore]:raise ValueError("SWITCH1_DISABLE must be either 'OPEN', 'CLOSED', or 'IGNORE'")
		if self.sw2_disable_when not in[sw_closed,sw_open,sw_ignore]:raise ValueError("SWITCH2_DISABLE must be either 'OPEN' or 'CLOSED' or 'IGNORE'")
		if self.sw_logic not in[sw_and,sw_or]:raise ValueError("SWITCH_LOGIC must be either 'AND' or 'OR'")
	def enable_check(self):
		sw1_disabled=_B
		if self.sw1_disable_when!=sw_ignore:
			sw1_state=self.sw1.value()
			if sw1_state==1 and self.sw1_disable_when==sw_open:sw1_disabled=_A
			if sw1_state==0 and self.sw1_disable_when==sw_closed:sw1_disabled=_A
		sw2_disabled=_B
		if self.sw2_disable_when!=sw_ignore:
			sw2_state=self.sw2.value()
			if sw2_state==1 and self.sw1_disable_when==sw_open:sw2_disabled=_A
			if sw2_state==0 and self.sw1_disable_when==sw_closed:sw2_disabled=_A
		if self.sw_logic==sw_and:disabled=sw1_disabled and sw2_disabled
		if self.sw_logic==sw_or:disabled=sw1_disabled or sw2_disabled
		if disabled:return _B,'switches'
		return _A,''
class RingAvg:
	def __init__(self,size):assert size>0;self.size=size;self.buf=[.0]*size;self.sum=.0;self.count=0;self.idx=0
	def add(self,x):
		x=float(x)
		if self.count<self.size:self.buf[self.idx]=x;self.sum+=x;self.count+=1
		else:old=self.buf[self.idx];self.buf[self.idx]=x;self.sum+=x-old
		self.idx+=1
		if self.idx==self.size:self.idx=0
	def avg(self):return self.sum/self.size
class Buzzer:
	def __init__(self):self.pwm_instance=PWM(Pin(PIN_BUZZER));self.off()
	def on(self):self.pwm(1000,50)
	def off(self):self.pwm(1000,0)
	def pwm(self,freq,duty):self.pwm_instance.freq(freq);self.pwm_instance.duty_u16(int(duty*MAX_U16/100))
	def beep_trap_ready(self):
		for i in range(5):time.sleep(.5);self.on();time.sleep(.5);self.off()
		print('Trap is ready.')
class RotaryEncoder:
	def __init__(self):self.pin_1=Pin(PIN_ROT_ENC_1,Pin.IN,Pin.PULL_UP);self.pin_2=Pin(PIN_ROT_ENC_2,Pin.IN,Pin.PULL_UP);self.pin_4=Pin(PIN_ROT_ENC_4,Pin.IN,Pin.PULL_UP);self.pin_8=Pin(PIN_ROT_ENC_8,Pin.IN,Pin.PULL_UP)
	def position(self):return 15-self.pin_1.value()-2*self.pin_2.value()-4*self.pin_4.value()-8*self.pin_8.value()
class Clock:
	def __init__(self,i2c=i2c):self.r=pcf8563.PCF8563(i2c);self.latitude=LATITUDE;self.longitude=LONGITUDE;dst=timezone.time_change_rule(-1,6,9,2,780);st=timezone.time_change_rule(0,6,4,2,720);self.nz_tz=timezone.timezone(dst,st);self.night_only=Pin(PIN_SW_NIGHT_ONLY,Pin.IN,Pin.PULL_UP)
	def get_local_time(self,utc_time=_C):
		if utc_time is _C:utc_time=self.get_utc_time()
		return self.nz_tz.get_local_time(utc_time)
	def write_time(self,**kwargs):self.r.write_all(**kwargs)
	def get_utc_time(self):year,month,date,day,hour,minute,second=self.r.datetime();return datetime.datetime(year=year+2000,month=month,day=date,hour=hour,minute=minute,second=second)
	def is_night(self):utc=self.get_utc_time();local_time=self.get_local_time(utc);tz=self.nz_tz.get_current_tz(utc).timezone;sunrise=timezone.get_sunrise(utc,LATITUDE,LONGITUDE,tz);sunset=timezone.get_sunset(utc,LATITUDE,LONGITUDE,tz);return local_time.time()<sunrise or sunset<local_time.time()
	def in_active_window(self):
		if self.night_only.value()==1:return self.is_night()
		return _A
	def enable_check(self):
		if self.in_active_window():return _A,''
		else:return _B,'time window'
	def check_low_voltage(self):return self.r.check_low_voltage()
class PIRs:
	def __init__(self,i2c=i2c):self.i2c=i2c;self.pir_1=Pin(PIN_PIR_1,Pin.IN);self.pir_2=Pin(PIN_PIR_2,Pin.IN);self.set_pir_sensitivity(PIR_SENSITIVITY)
	def read(self):return self.pir_1.value()or self.pir_2.value()
	def read_sensitivity(self):return self.pir_sensitivity.read()
	def set_pir_sensitivity(self,value):
		value=127-value;bytearray(0)+bytearray([value])
		if value>=128:value=128
		if value<0:value=0
		self.i2c.writeto(62,bytes([0,value]))
class RPi_UART:
	def __init__(self,shared_dict,i2c=_C):self.shared_dict=shared_dict;self._running=_A;self.uart=UART(0,baudrate=9600,tx=Pin(PIN_UART_TX),rx=Pin(PIN_UART_RX));_thread.start_new_thread(self._uart_loop,())
	def close(self):self._running=_B;self.uart.deinit()
	def _uart_loop(self):
		C='READ';B='LS';A=','
		while self._running:
			try:
				message=self.check_for_message()
				if message is _C:continue
				print(f"Received {message.type} message")
				if message.type=='ACK':continue
				elif message.type=='NACK':continue
				elif message.type=='ENABLE':
					if self.shared_dict.set(_D,_A):self.send_ack(message.id)
					else:self.send_bad_key(message.id)
				elif message.type=='DISABLE':
					if self.shared_dict.set(_D,_B):self.send_ack(message.id)
					else:self.send_bad_key(message.id)
				elif message.type=='RESTART':print('Restarting...');self.send_ack(message.id);time.sleep(1);reset()
				elif message.type==B:
					if message.payload=='':all_files=get_file_hashes();payload=json.dumps(all_files);print(payload);self.send_message(Message(message.id,B,payload));continue
					files=get_file_hashes(target_files=message.payload.split(A));payload=json.dumps(files);print(payload);self.send_message(Message(message.id,B,payload))
				elif message.type==C:parts=message.payload.split(A);filename=parts[0];offset=int(parts[1]);count=int(parts[2]);lines=read_file(filename,offset,count);self.send_message(Message(message.id,C,json.dumps(lines)))
				elif message.type=='WRITE':
					parts=message.payload.split(A,1);filename=parts[0];lines=json.loads(parts[1])
					with open(filename,'a')as f:
						for line in lines:f.write(line+'\n')
					self.send_ack(message.id)
				elif message.type=='DELETE':filename=message.payload;os.remove(filename);self.send_ack(message.id)
				elif message.type=='DECOMPRESS':
					parts=message.payload.split(A);src=parts[0];dst=parts[1];bin_src=src+'.bin'
					with open(src,'rb')as f_in,open(bin_src,'wb')as f_out:
						for line in f_in:
							line=line.strip()
							if line:f_out.write(binascii.a2b_base64(line))
					os.remove(src)
					with open(bin_src,'rb')as f_in,open(dst,'wb')as f_out:
						try:
							with deflate.DeflateIO(f_in,deflate.ZLIB)as d:
								while _A:
									chunk=d.read(256)
									if not chunk:break
									f_out.write(chunk)
						except EOFError:pass
					os.remove(bin_src);self.send_ack(message.id)
				elif message.type=='MV':parts=message.payload.split(A);src=parts[0];dst=parts[1];os.rename(src,dst);self.send_ack(message.id)
				elif message.type=='PING':self.send_ack(message.id)
				else:print('Received unknown message type: {}'.format(message.type));self.send_nack(message.id)
			except Exception as e:print(get_err_str(e))
	def check_for_message(self):
		A='|'
		if not self.uart.any():return
		line_raw=bytearray()
		while _A:
			if self.uart.any():
				char=self.uart.read(1)
				if char==b'\n':break
				line_raw.extend(char)
		line=line_raw.decode('utf-8');last_index=line.rfind('>');message_str=line[:last_index+1];checksum=line[last_index+1:]
		try:
			if self._compute_checksum(message_str)!=int(checksum):self.send_nack(payload='Invalid checksum');return
		except ValueError:self.send_nack(payload='Failed to send message');return
		if not message_str.startswith('<')or message_str.count(A)<2 or not message_str.endswith('>'):print(f"Invalid message format {message_str}");self.send_nack('Invalid message format');return
		message_str=message_str[1:-1];parts=message_str.split(A);id=int(parts[0]);type=parts[1];payload=A.join(parts[2:]);message=Message(id,type,payload);return message
	CHUNK_SIZE=256
	def send_message(self,message):
		message_str=f"<{message.id}|{message.type}|{message.payload}>";checksum=self._compute_checksum(message_str);line=f"{message_str}{checksum}\n";print(f"Sending: {line}")
		for i in range(0,len(line),self.CHUNK_SIZE):self.uart.flush();self.uart.write(line[i:i+self.CHUNK_SIZE])
	def _compute_checksum(self,message):return sum(message.encode())%256
	def send_nack(self,message_id=0,payload=''):self.send_message(Message(message_id,'NACK',payload))
	def send_ack(self,message_id=0):self.send_message(Message(message_id,'ACK'))
	def send_error_code(self,error_id):self.send_message(Message(0,'ERROR',error_id))
	def send_bad_key(self,message_id=0):self.send_message(Message(message_id,'BAD_KEY'))
class Message:
	def __init__(self,id,type,payload=''):self.id=id;self.type=type;self.payload=payload;print('New message, id: {}, type: {}, payload: {}'.format(self.id,self.type,self.payload))
def motion_message():return Message(0,'MOTION')
class SharedDict:
	def __init__(self):self._data={};self._lock=_thread.allocate_lock()
	def get(self,key,default=_C):
		self._lock.acquire()
		try:return self._data.get(key,default)
		finally:self._lock.release()
	def set(self,key,value,new_key=_B):
		self._lock.acquire()
		try:
			if key not in self._data and not new_key:return _B
			self._data[key]=value;return _A
		finally:self._lock.release()
	def contains(self,key):
		self._lock.acquire()
		try:return key in self._data
		finally:self._lock.release()
	def enable_check(self):
		if self.get(_D,default=_B):return _A,'Camera set trap to enabled'
		else:return _B,'Camera set trap to disabled'
class APIR:
	def __init__(self):self.AnalogPin=ADC(27);self.min=0;self.max=43000;self.avg=(self.min+self.max)/2;self.displacement_threshold=(self.max-self.min)/2*APIR_DISPLACEMENT_THRESHOLD;self.gradient_threshold=APIR_GRADIENT_THRESHOLD;self.previous_value=self.AnalogPin.read_u16();self.last_time=time.time_ns();self.displacement_triggered=_B;self.gradient_triggered=_B
	def motion(self):
		if time.time_ns()-self.last_time<1000000:return
		new_value=self.AnalogPin.read_u16();new_time=time.time_ns();displacement=abs(new_value-self.avg);self.displacement_triggered=displacement>self.displacement_threshold;gradient=abs((new_value-self.previous_value)/(new_time-self.last_time)*1000000);self.gradient_triggered=gradient>self.gradient_threshold;self.previous_value=new_value;self.last_time=new_time;return self.displacement_triggered or self.gradient_triggered
def check_checks(enable_checks):
	failed_reasons=[];all_passed=_A
	for check in enable_checks:
		check_passed,reason=check()
		if not check_passed:all_passed=_B;failed_reasons.append(reason)
	return all_passed,', '.join(failed_reasons)
def run_sequence(spool,motion_check,enabled_checks,rpi_uart=_C):
	while _A:
		print('Resetting spool.');spool.reset_sequence();print(f"Waiting {POST_RESET_COOLDOWN_SECONDS}s until running trap checks.");time.sleep(POST_RESET_COOLDOWN_SECONDS);print('Waiting for motion check and all enable checks to pass.');last_motion_message=-MOTION_MESSAGE_GAP;old_enabled=_C;old_state=_C;old_failed_check_reasons=_C
		while _A:
			motion=motion_check();now=time.time()
			if motion and last_motion_message+MOTION_MESSAGE_GAP<now:
				if rpi_uart:rpi_uart.send_message(motion_message())
				last_motion_message=now
			enabled,failed_check_reasons=check_checks(enabled_checks)
			if not enabled and failed_check_reasons!=old_failed_check_reasons:
				if rpi_uart:rpi_uart.send_message(Message(0,'DISABLED',failed_check_reasons))
				else:print(failed_check_reasons)
			old_failed_check_reasons=failed_check_reasons
			if old_enabled!=enabled:
				if enabled:
					if rpi_uart:rpi_uart.send_message(Message(0,'ENABLED'))
				old_enabled=enabled
			if motion and enabled:break
			state=f"Motion: {motion}, Enabled: {enabled}"
			if state!=old_state:print(state);old_state=state
		print('Releasing spool.');spool.release();print(f"Waiting {SPOOL_RESET_DELAY_MINUTES} minutes until resetting.");time.sleep(SPOOL_RESET_DELAY_MINUTES*60)
def error_code(code,extra=_C):
	A='ERROR_CODE';print(f"ERROR_CODE: {code}");buzzer=Buzzer()
	for _ in range(3):
		for _ in range(3):buzzer.on();time.sleep(.2);buzzer.pwm(800,50);time.sleep(.2)
		buzzer.off();time.sleep(1)
		for i in range(code):buzzer.on();time.sleep(.2);buzzer.off();time.sleep(.2)
		time.sleep(1)
	if extra:error(A,f"{code}: {extra}")
	else:error(A,code)
def get_err_str(exception):buf=io.StringIO();sys.print_exception(exception,buf);return buf.getvalue()
def error_exception(exception):buf=io.StringIO();sys.print_exception(exception,buf);exception_str=get_err_str(exception);print('EXCEPTION:',exception_str);error('EXCEPTION',exception_str.splitlines())
def error(type,payload,rpi_uart=_C):
	message=Message(0,type,payload)
	try:
		if not rpi_uart:rpi_uart=RPi_UART(_C)
		rpi_uart.send_message(message)
	except:
		print('Failed to send error via UART. Saving error to file')
		with open('error.json','w')as f:json.dump({'type':type,'payload':payload},f)
	time.sleep(5);reset()
def get_file_hashes(target_files=_C):
	files={}
	for entry in os.ilistdir('/'):
		name,size=entry[0],entry[3]
		if target_files and name not in target_files:continue
		h=hashlib.sha256()
		with open('/'+name,'rb')as f:
			while _A:
				chunk=f.read(512)
				if not chunk:break
				h.update(chunk)
		files[name]=binascii.hexlify(h.digest()).decode()[:10]
	return files
def read_file(filename,offset,count):
	with open(filename,'r')as f:
		for _ in range(offset):
			if not f.readline():break
		lines=[]
		for _ in range(count):
			line=f.readline()
			if not line:break
			lines.append(line.rstrip('\n'))
	return lines